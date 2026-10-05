#!/usr/bin/env python3
"""Regenerate this topic's study deck from deck_config.json."""
import json, sys
from pathlib import Path
HERE = Path(__file__).parent
sys.path.insert(0, '/Users/vr/Code/Career_upskill/topics/09_databricks_ml_associate/pptx')
from build_all_pptx import build_deck  # noqa
cfg = json.loads((HERE / 'deck_config.json').read_text())
out = HERE / 'Databricks_ML_Professional_study_deck.pptx'
build_deck(out, cfg)
print(f'Wrote {out}')
