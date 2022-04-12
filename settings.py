""" Settings for preparedatasets.py and Dash app.
"""
from pathlib import Path

# preparedatasets.py file output naming conventions
PD_OUTPUT_SUBDIR = 'data/'
PD_OUTPUT_PATH = str(Path(Path.cwd(), PD_OUTPUT_SUBDIR))
AGG_D_SUFFIX = "dailyAggregate"  # Daily aggregate {exportDate}_{AGG_D_SUFFIX}csv
AGG_W_SUFFIX = "weeklyAggregate"  # Weekly aggregate
AGG_M_SUFFIX = "monthlyAggregate"  # Monthly aggregate
RESAMPLE_D_SUFFIX = "resampledDaily"  # Daily resample
