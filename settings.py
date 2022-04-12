""" Settings for extractapplehealth.py, preparedatasets.py.
"""
from pathlib import Path

# preparedatasets.py file output naming conventions
OUTPUT_SUBDIR = str(Path(Path.cwd(), 'data'))
AGG_D_SUFFIX = "dailyAggregate"  # Daily aggregate {exportDate}_{AGG_D_SUFFIX}csv
AGG_W_SUFFIX = "weeklyAggregate"  # Weekly aggregate
AGG_M_SUFFIX = "monthlyAggregate"  # Monthly aggregate
RESAMPLE_D_SUFFIX = "resampledDaily"  # Daily resample
