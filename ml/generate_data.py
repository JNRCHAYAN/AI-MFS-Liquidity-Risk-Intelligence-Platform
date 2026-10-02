"""Reproducible synthetic MFS data generator for upay Shield.

Run this before any feature building or training. It materialises a world
(customers, merchants, agents, devices, transactions, logins) plus a
separate ground-truth table, writes Parquet files, a manifest and small
sample fixtures.

Determinism
-----------
The same ``--seed`` and the same entity/transaction counts produce
byte-identical Parquet output. That is verified by hashing every output file
into the manifest; run the generator twice into different directories and
compare the ``sha256`` values.

Labels
------
Ground-truth fraud labels exist **only** in ``scenario_truth.parquet``, keyed
by ``transaction_id``. The transactions frame used for scoring never carries
a label. ``scoring_frame`` demonstrates the sanctioned way to obtain a model
input frame and will refuse to return one containing a forbidden column.

Money and time
--------------
Amounts are integer poisha (1 BDT = 100 poisha). Timestamps are timezone-aware
UTC. Behavioural local time is derived from Asia/Dhaka (fixed UTC+06:00).

Usage
-----
::

    python ml/generate_data.py --seed 42 --wallets 1000 --merchants 50 \
        --agents 30 --transactions 60000 --out data/generated

    python ml/generate_data.py --small
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import pandas as pd

if __package__ in (None, ""):  # pragma: no cover - script execution path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ml.scenarios import (  # noqa: E402
    GENERATOR_VERSION,
    SimConfig,
    World,
    build_world,
)

# Repo root: ml/generate_data.py -> ml -> repo root.
REPO_ROOT = Path(__file__).resolve().parent.parent

#: Column names that must never appear in a model input frame. Kept in step
#: with ``backend.app.intelligence.features.schema.FORBIDDEN_INPUT_COLUMNS``;
#: the generator does not import the backend at run time, and a test asserts
#: the two lists stay equal.
FORBIDDEN_INPUT_COLUMNS: frozenset[str] = frozenset(
    {
        "is_fraud",
        "fraud_label",
        "scenario_truth",
        "scenario_truth_label",
        "ground_truth",
        "status",
        "final_status",
        "resolved_at",
        "analyst_disposition",
        "resolution_note",
        "case_status",
    }
)

#: Tables written to ``--out``.
PARQUET_TABLES: tuple[str, ...] = (
    "entities",
    "devices",
    "transactions",
    "login_events",
    "scenario_truth",
    "locations",
)

#: Small committed fixtures written to ``--sample-dir``.
SAMPLE_ROW_LIMIT = 400


def sha256_file(path: Path) -> str:
    """Return the hex SHA-256 digest of a file."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def scoring_frame(world: World) -> pd.DataFrame:
    """Return the transactions frame as a model input frame.

    This is the sanctioned way to obtain transactions for feature building.
    It drops every column that is a post-hoc outcome rather than an input, so
    a label can never reach the model by accident.

    Args:
        world: A generated world.

    Returns:
        A copy of ``world.transactions`` with forbidden columns removed and
        the ground-truth table deliberately absent.

    Raises:
        ValueError: if a forbidden column would survive the drop, which would
            mean the feature contract and the generator have diverged.
    """
    frame = world.transactions.copy()
    frame = frame.drop(columns=[c for c in frame.columns if c in FORBIDDEN_INPUT_COLUMNS])
    leaked = sorted(set(frame.columns) & FORBIDDEN_INPUT_COLUMNS)
    if leaked:
        raise ValueError(f"forbidden label/outcome columns leaked into scoring frame: {leaked}")
    return frame


def _check_outputs(world: World) -> list[str]:
    """Run the structural self-checks the simulator must pass.

    Returns a list of human-readable violations. An empty list means the
    generated world satisfies the contract.
    """
    problems: list[str] = []
    txns = world.transactions
    truth = world.scenario_truth

    money_columns = ["amount_poisha"]
    for column in money_columns:
        if column not in txns.columns:
            problems.append(f"missing money column {column}")
        elif not pd.api.types.is_integer_dtype(txns[column]):
            problems.append(f"{column} is {txns[column].dtype}, expected integer poisha")
        elif (txns[column] <= 0).any():
            problems.append(f"{column} contains non-positive values")

    for name, frame, columns in (
        ("transactions", txns, ["timestamp"]),
        ("login_events", world.login_events, ["timestamp"]),
        ("entities", world.entities, ["created_at"]),
        ("devices", world.devices, ["first_seen_at"]),
    ):
        for column in columns:
            dtype = frame[column].dtype
            if not hasattr(dtype, "tz") or dtype.tz is None:
                problems.append(f"{name}.{column} is not timezone-aware UTC ({dtype})")
            elif str(dtype.tz) != "UTC":
                problems.append(f"{name}.{column} is in {dtype.tz}, expected UTC")

    if len(truth) != len(txns):
        problems.append("scenario_truth and transactions row counts differ")
    if set(truth["transaction_id"]) != set(txns["id"]):
        problems.append("scenario_truth keys do not match transaction ids")
    if truth["transaction_id"].duplicated().any():
        problems.append("scenario_truth contains duplicate transaction keys")
    if txns["id"].duplicated().any():
        problems.append("transactions contain duplicate ids")

    if not txns["timestamp"].is_monotonic_increasing:
        problems.append("transactions are not in chronological order")

    leaked = sorted(
        (set(txns.columns) | set(world.login_events.columns) | set(world.devices.columns))
        & {"is_fraud", "fraud_family", "fraud_label", "confounder_family", "scenario_severity"}
    )
    if leaked:
        problems.append(f"label columns present outside scenario_truth: {leaked}")

    if truth["is_fraud"].sum() == 0:
        problems.append("no fraud transactions were generated")
    if (~truth["is_fraud"]).sum() == 0:
        problems.append("no normal transactions were generated")
    return problems


def write_outputs(
    world: World,
    out_dir: Path,
    manifest_dir: Path,
    sample_dir: Path | None,
) -> dict[str, object]:
    """Write every table, the manifest and optional sample fixtures.

    Args:
        world: The generated world.
        out_dir: Directory for the full Parquet outputs (gitignored).
        manifest_dir: Directory for the manifest JSON (committed).
        sample_dir: Directory for small committed CSV fixtures, or ``None``.

    Returns:
        The manifest dictionary that was written.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest_dir.mkdir(parents=True, exist_ok=True)

    tables = {
        "entities": world.entities,
        "devices": world.devices,
        "transactions": world.transactions,
        "login_events": world.login_events,
        "scenario_truth": world.scenario_truth,
        "locations": world.locations,
    }
    hashes: dict[str, str] = {}
    row_counts: dict[str, int] = {}
    for name in PARQUET_TABLES:
        path = out_dir / f"{name}.parquet"
        tables[name].to_parquet(path, index=False)
        hashes[f"{name}.parquet"] = sha256_file(path)
        row_counts[name] = int(len(tables[name]))

    manifest: dict[str, object] = {
        **world.stats,
        "generator_version": GENERATOR_VERSION,
        "row_counts": row_counts,
        "outputs": {
            "directory": str(out_dir.relative_to(REPO_ROOT))
            if out_dir.is_relative_to(REPO_ROOT)
            else str(out_dir),
            "files": {name: {"sha256": digest} for name, digest in sorted(hashes.items())},
            "format": "parquet",
        },
        "hash_algorithm": "sha256",
        "notes": (
            "Synthetic data only. Ground-truth labels exist only in "
            "scenario_truth.parquet keyed by transaction_id. Money is integer "
            "poisha. Timestamps are timezone-aware UTC. The same seed and "
            "counts reproduce byte-identical Parquet output."
        ),
    }

    manifest_path = manifest_dir / f"generator_manifest_seed{world.config.seed}.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    hashes["manifest"] = sha256_file(manifest_path)

    if sample_dir is not None:
        write_samples(tables, sample_dir)

    return manifest


def write_samples(tables: dict[str, pd.DataFrame], sample_dir: Path) -> None:
    """Write small CSV fixtures for tests and documentation.

    CSVs (not Parquet) are used deliberately: ``*.parquet`` is gitignored, and
    these fixtures are meant to be committed and human-inspectable.
    """
    sample_dir.mkdir(parents=True, exist_ok=True)
    for name, frame in tables.items():
        head = frame.head(SAMPLE_ROW_LIMIT)
        head.to_csv(sample_dir / f"sample_{name}.csv", index=False)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Generate reproducible synthetic MFS data for upay Shield.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--seed", type=int, default=42, help="Master random seed.")
    parser.add_argument("--wallets", type=int, default=1_000, help="Number of customer wallets.")
    parser.add_argument("--merchants", type=int, default=50, help="Number of merchants.")
    parser.add_argument("--agents", type=int, default=30, help="Number of agents.")
    parser.add_argument(
        "--transactions", type=int, default=60_000, help="Target transaction count."
    )
    parser.add_argument("--days", type=int, default=90, help="Length of the window in days.")
    parser.add_argument(
        "--out",
        type=Path,
        default=REPO_ROOT / "data" / "generated",
        help="Directory for full Parquet output (gitignored).",
    )
    parser.add_argument(
        "--manifest-dir",
        type=Path,
        default=REPO_ROOT / "data" / "manifests",
        help="Directory for the generator manifest JSON.",
    )
    parser.add_argument(
        "--sample-dir",
        type=Path,
        default=REPO_ROOT / "data" / "samples",
        help="Directory for small committed CSV fixtures.",
    )
    parser.add_argument(
        "--no-samples", action="store_true", help="Skip writing sample CSV fixtures."
    )
    parser.add_argument(
        "--small",
        action="store_true",
        help=(
            "Fast preset for tests: ~2000 transactions, 60 wallets, 8 merchants, "
            "5 agents, 30 days. Individual counts still override the preset."
        ),
    )
    parser.add_argument(
        "--quiet", action="store_true", help="Suppress the summary printed to stdout."
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Entry point. Returns a process exit code."""
    args = parse_args(argv)
    if args.small:
        # Explicitly-set flags win over the preset.
        if args.wallets == 1_000:
            args.wallets = None
        if args.merchants == 50:
            args.merchants = None
        if args.agents == 30:
            args.agents = None
        if args.transactions == 60_000:
            args.transactions = None
        if args.days == 90:
            args.days = None
        preset = SimConfig.small(seed=args.seed)
        config = SimConfig(
            seed=args.seed,
            n_wallets=args.wallets if args.wallets is not None else preset.n_wallets,
            n_merchants=args.merchants if args.merchants is not None else preset.n_merchants,
            n_agents=args.agents if args.agents is not None else preset.n_agents,
            n_transactions=(
                args.transactions if args.transactions is not None else preset.n_transactions
            ),
            days=args.days if args.days is not None else preset.days,
        )
    else:
        config = SimConfig(
            seed=args.seed,
            n_wallets=args.wallets,
            n_merchants=args.merchants,
            n_agents=args.agents,
            n_transactions=args.transactions,
            days=args.days,
        )

    world = build_world(config)
    problems = _check_outputs(world)
    if problems:
        for problem in problems:
            print(f"generator self-check FAILED: {problem}", file=sys.stderr)
        return 2

    manifest = write_outputs(
        world,
        out_dir=args.out,
        manifest_dir=args.manifest_dir,
        sample_dir=None if args.no_samples else args.sample_dir,
    )

    if not args.quiet:
        stats = manifest["class_mix"]
        assert isinstance(stats, dict)
        print(f"generator version : {GENERATOR_VERSION}")
        print(f"seed              : {config.seed}  run_id={world.run_id}")
        print(f"window (UTC)      : {manifest['time_range']['start_utc']} .. "  # type: ignore[index]
              f"{manifest['time_range']['end_utc']}")  # type: ignore[index]
        print(f"row counts        : {json.dumps(manifest['row_counts'], sort_keys=True)}")
        print(
            f"class mix         : fraud={stats['fraud']} normal={stats['normal']} "
            f"rate={stats['fraud_rate']}"
        )
        print(f"fraud families    : {json.dumps(manifest['fraud_families'], sort_keys=True)}")
        print(f"benign confounders: {json.dumps(manifest['benign_confounders'], sort_keys=True)}")
        print("output hashes:")
        for name, meta in sorted(manifest["outputs"]["files"].items()):  # type: ignore[index]
            print(f"  {name:24s} {meta['sha256']}")
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry
    raise SystemExit(main())
