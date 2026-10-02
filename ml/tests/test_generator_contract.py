"""Contract tests for the synthetic data generator.

These assert the properties the rest of the pipeline depends on: determinism,
integer-poisha money, UTC timestamps, chronological order, causal device use,
quarantined labels and overlapping class distributions. They deliberately do
*not* test implementation details of individual episodes.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from ml.generate_data import (
    FORBIDDEN_INPUT_COLUMNS,
    PARQUET_TABLES,
    main,
    scoring_frame,
)
from ml.scenarios import (
    CHANNEL_AGENT,
    GENERATOR_VERSION,
    SimConfig,
    World,
    build_world,
)

TABLE_FRAMES = {
    "entities": "entities",
    "devices": "devices",
    "transactions": "transactions",
    "login_events": "login_events",
    "scenario_truth": "scenario_truth",
    "locations": "locations",
}


# ---------------------------------------------------------------------------
# Shape and population
# ---------------------------------------------------------------------------


def test_entity_counts_match_configuration(world: World) -> None:
    config = world.config
    kinds = world.entities["kind"].value_counts().to_dict()
    assert kinds.get("customer") == config.n_wallets
    assert kinds.get("merchant") == config.n_merchants
    assert kinds.get("agent") == config.n_agents
    assert len(world.entities) == (
        config.n_wallets + config.n_merchants + config.n_agents
    )


def test_transaction_total_matches_request(medium_world: World) -> None:
    assert len(medium_world.transactions) == medium_world.config.n_transactions


def test_expected_columns_present(world: World) -> None:
    assert list(world.transactions.columns) == [
        "id",
        "sender_id",
        "receiver_id",
        "amount_poisha",
        "type",
        "timestamp",
        "device_id",
        "location",
        "status",
        "scenario_run_id",
    ]
    assert list(world.entities.columns) == [
        "entity_id",
        "kind",
        "created_at",
        "region",
        "peer_group",
    ]
    assert list(world.devices.columns) == [
        "device_id",
        "entity_id",
        "first_seen_at",
        "channel",
    ]
    assert list(world.login_events.columns) == [
        "entity_id",
        "timestamp",
        "device_id",
        "success",
        "location",
    ]


def test_all_episode_families_are_present(world: World) -> None:
    truth = world.scenario_truth
    families = set(truth.loc[truth["is_fraud"], "fraud_family"].dropna())
    assert families == {
        "ato",
        "velocity_burst",
        "mule_fanin",
        "circular",
        "agent_cashout_spike",
        "scam_escalation",
        "scam_split",
    }


def test_benign_confounders_are_labelled_normal(world: World) -> None:
    truth = world.scenario_truth
    confounders = truth[truth["confounder_family"].notna()]
    assert len(confounders) > 0
    assert set(confounders["confounder_family"]) == {
        "salary_day_spike",
        "bulk_merchant_receipts",
        "travel_new_device",
    }
    # A confounder is genuinely benign: it must never carry a fraud label.
    assert not confounders["is_fraud"].any()


def test_fraud_rate_is_low_but_nonzero(medium_world: World) -> None:
    truth = medium_world.scenario_truth
    rate = float(truth["is_fraud"].mean())
    assert 0.01 < rate < 0.10


# ---------------------------------------------------------------------------
# Money, time and ordering
# ---------------------------------------------------------------------------


def test_money_is_integer_poisha(world: World) -> None:
    amount = world.transactions["amount_poisha"]
    assert pd.api.types.is_integer_dtype(amount)
    assert (amount > 0).all()
    # No monetary value is ever stored as a float anywhere in the tables.
    for name, frame in _tables(world).items():
        float_columns = [
            column
            for column in frame.columns
            if pd.api.types.is_float_dtype(frame[column])
            and any(token in column for token in ("amount", "poisha", "bdt", "balance"))
        ]
        assert not float_columns, f"{name} has float money columns: {float_columns}"


def test_timestamps_are_timezone_aware_utc(world: World) -> None:
    for frame, columns in (
        (world.transactions, ["timestamp"]),
        (world.login_events, ["timestamp"]),
        (world.entities, ["created_at"]),
        (world.devices, ["first_seen_at"]),
    ):
        for column in columns:
            dtype = frame[column].dtype
            assert isinstance(dtype, pd.DatetimeTZDtype), f"{column} is not tz-aware"
            assert str(dtype.tz) == "UTC", f"{column} is in {dtype.tz}"


def test_transactions_are_chronological(world: World) -> None:
    assert world.transactions["timestamp"].is_monotonic_increasing
    assert world.transactions["id"].is_unique
    assert world.transactions["id"].is_monotonic_increasing


def test_transaction_ids_are_unique_and_match_truth(world: World) -> None:
    truth = world.scenario_truth
    assert len(truth) == len(world.transactions)
    assert truth["transaction_id"].is_unique
    assert set(truth["transaction_id"]) == set(world.transactions["id"])


def test_devices_are_only_used_at_or_after_first_seen(world: World) -> None:
    first_seen = world.devices.set_index("device_id")["first_seen_at"]
    used = world.transactions[["device_id", "timestamp"]].copy()
    used["first_seen_at"] = used["device_id"].map(first_seen)
    assert used["first_seen_at"].notna().all(), "a transaction cites an unknown device"
    # One second of slack absorbs the second-resolution timestamp storage.
    violations = used["timestamp"] < (used["first_seen_at"] - pd.Timedelta(seconds=1))
    assert not violations.any(), f"{int(violations.sum())} transactions predate their device"


def test_entity_creation_precedes_their_transactions(world: World) -> None:
    created = world.entities.set_index("entity_id")["created_at"]
    txns = world.transactions
    for side in ("sender_id", "receiver_id"):
        merged = txns[[side, "timestamp"]].copy()
        merged["created_at"] = merged[side].map(created)
        assert merged["created_at"].notna().all()
        violations = merged["timestamp"] < (merged["created_at"] - pd.Timedelta(seconds=1))
        assert not violations.any(), f"{side} used before the entity existed"


# ---------------------------------------------------------------------------
# Label quarantine
# ---------------------------------------------------------------------------


def test_labels_exist_only_in_scenario_truth(world: World) -> None:
    label_columns = {"is_fraud", "fraud_family", "confounder_family", "scenario_severity"}
    for name, frame in _tables(world).items():
        if name == "scenario_truth":
            continue
        assert not (label_columns & set(frame.columns)), f"{name} exposes a label column"


def test_scoring_frame_drops_outcomes(world: World) -> None:
    frame = scoring_frame(world)
    assert "status" in world.transactions.columns
    assert "status" not in frame.columns
    assert not (FORBIDDEN_INPUT_COLUMNS & set(frame.columns))
    # The ground truth is not reachable from the returned frame in any form.
    assert "is_fraud" not in frame.columns
    assert "scenario_truth" not in frame.columns


def test_forbidden_columns_match_the_frozen_backend_contract() -> None:
    from app.intelligence.features.schema import FORBIDDEN_INPUT_COLUMNS as backend_forbidden

    assert backend_forbidden == FORBIDDEN_INPUT_COLUMNS


def test_generated_column_names_are_known_to_the_backend_contract(world: World) -> None:
    """Every emitted category value must exist in the frozen vocabularies."""
    from app.intelligence.features.schema import CHANNELS, TRANSACTION_TYPES

    assert set(world.transactions["type"]).issubset(set(TRANSACTION_TYPES))
    assert set(world.devices["channel"]).issubset(set(CHANNELS))
    assert CHANNEL_AGENT in set(world.devices["channel"])


# ---------------------------------------------------------------------------
# Overlap: the simulator must not be trivially separable
# ---------------------------------------------------------------------------


def test_fraud_and_normal_amounts_overlap(medium_world: World) -> None:
    txns = medium_world.transactions
    fraud = medium_world.scenario_truth["is_fraud"].to_numpy()
    normal_amounts = txns.loc[~fraud, "amount_poisha"]
    fraud_amounts = txns.loc[fraud, "amount_poisha"]

    # A large share of fraudulent transactions are unremarkable in size.
    below_normal_p90 = (fraud_amounts < normal_amounts.quantile(0.90)).mean()
    assert below_normal_p90 > 0.25, below_normal_p90

    # And plenty of ordinary transactions are larger than a typical fraud one.
    above_fraud_median = (normal_amounts > fraud_amounts.median()).mean()
    assert above_fraud_median > 0.05, above_fraud_median


def test_no_single_amount_threshold_separates_the_classes(medium_world: World) -> None:
    txns = medium_world.transactions
    labels = medium_world.scenario_truth["is_fraud"].to_numpy()
    amounts = txns["amount_poisha"].to_numpy()

    best_f1 = 0.0
    for threshold in np.quantile(amounts, np.linspace(0.5, 0.995, 60)):
        predicted = amounts >= threshold
        tp = int(np.sum(predicted & labels))
        fp = int(np.sum(predicted & ~labels))
        fn = int(np.sum(~predicted & labels))
        if tp == 0:
            continue
        precision = tp / (tp + fp)
        recall = tp / (tp + fn)
        f1 = 2 * precision * recall / (precision + recall)
        best_f1 = max(best_f1, f1)
    assert best_f1 < 0.45, f"amount alone reaches F1={best_f1:.3f}"


def test_ordinary_activity_shares_signals_with_fraud(medium_world: World) -> None:
    """Benign confounders must reproduce the fraud-looking structures.

    Each confounder family should be similar in *shape* (many payments from
    many senders, or several transactions inside a short window) to at least
    one fraud family, so that a rule matching the shape cannot separate them.
    """
    truth = medium_world.scenario_truth
    confounders = truth[truth["confounder_family"].notna()]
    assert len(confounders) > 0
    # Bulk merchant receipts are a many-senders-same-recipient pattern, the
    # same structure a mule fan-in has.
    bulk = confounders[confounders["confounder_family"] == "bulk_merchant_receipts"]
    assert len(bulk) > 5


# ---------------------------------------------------------------------------
# Determinism
# ---------------------------------------------------------------------------


def _hash_frame(frame: pd.DataFrame) -> str:
    digest = hashlib.sha256()
    digest.update(str(list(frame.columns)).encode())
    digest.update(str(list(frame.dtypes)).encode())
    digest.update(frame.to_csv(index=False).encode("utf-8"))
    return digest.hexdigest()


def test_same_seed_reproduces_the_same_world_in_process() -> None:
    config = SimConfig.small(seed=99)
    first = build_world(config)
    second = build_world(config)
    for name, frame in _tables(first).items():
        other = _tables(second)[name]
        assert _hash_frame(frame) == _hash_frame(other), f"{name} is not reproducible"


def test_different_seeds_produce_different_worlds() -> None:
    a = build_world(SimConfig.small(seed=1))
    b = build_world(SimConfig.small(seed=2))
    assert _hash_frame(a.transactions) != _hash_frame(b.transactions)


def test_cli_writes_parquet_manifest_and_samples(tmp_path: Path) -> None:
    out_dir = tmp_path / "generated"
    manifest_dir = tmp_path / "manifests"
    sample_dir = tmp_path / "samples"
    exit_code = main(
        [
            "--small",
            "--seed",
            "5",
            "--out",
            str(out_dir),
            "--manifest-dir",
            str(manifest_dir),
            "--sample-dir",
            str(sample_dir),
            "--quiet",
        ]
    )
    assert exit_code == 0
    for table in PARQUET_TABLES:
        assert (out_dir / f"{table}.parquet").exists()
    manifest_path = manifest_dir / "generator_manifest_seed5.json"
    assert manifest_path.exists()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["generator_version"] == GENERATOR_VERSION
    assert manifest["seed"] == 5
    assert manifest["class_mix"]["fraud"] > 0
    assert set(manifest["outputs"]["files"]) == {f"{t}.parquet" for t in PARQUET_TABLES}
    for table in PARQUET_TABLES:
        assert (sample_dir / f"sample_{table}.csv").exists()
        digest = hashlib.sha256((out_dir / f"{table}.parquet").read_bytes()).hexdigest()
        assert manifest["outputs"]["files"][f"{table}.parquet"]["sha256"] == digest


def test_cli_parquet_bytes_are_stable_across_runs(tmp_path: Path) -> None:
    digests: list[dict[str, str]] = []
    for run in ("a", "b"):
        out_dir = tmp_path / run
        exit_code = main(
            [
                "--small",
                "--seed",
                "11",
                "--out",
                str(out_dir),
                "--manifest-dir",
                str(tmp_path / "manifests"),
                "--no-samples",
                "--quiet",
            ]
        )
        assert exit_code == 0
        digests.append(
            {
                table: hashlib.sha256((out_dir / f"{table}.parquet").read_bytes()).hexdigest()
                for table in PARQUET_TABLES
            }
        )
    assert digests[0] == digests[1]


def test_generator_rejects_impossible_configurations() -> None:
    with pytest.raises(ValueError):
        SimConfig(n_wallets=1)
    with pytest.raises(ValueError):
        SimConfig(n_transactions=10)
    with pytest.raises(ValueError):
        SimConfig(days=2)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _tables(world: World) -> dict[str, pd.DataFrame]:
    """Return every generated table keyed by its output name."""
    return {name: getattr(world, attribute) for name, attribute in TABLE_FRAMES.items()}
