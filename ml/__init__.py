"""Offline data and model pipeline for upay Shield.

Modules here run offline (never at request time): synthetic data generation,
feature building, training, evaluation and artifact packaging.

`ml.scenarios` holds the simulator scenario library; `ml.generate_data` is
the command-line entry point that materialises a world to Parquet, writes a
manifest and emits small committed sample fixtures.
"""
