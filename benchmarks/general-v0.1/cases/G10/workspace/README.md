# Normalize a fixed set of records

[research.md](research.md) gives the current interpretation, and
[the calculation note](notes/calculation.md) connects it to the files.

- [data/records.csv](data/records.csv) contains the original, complete records.
- [data/calibration.csv](data/calibration.csv) gives the accepted conversion pairs
  for this synthetic dataset. The conversion is linear through the origin.
- [analysis/normalize.py](analysis/normalize.py) is the current working analysis
  script. New derived output belongs alongside it in `analysis/`.
- [runs/baseline/](runs/baseline/) contains the earlier script snapshot, saved
  output and command record. It is the retained baseline execution bundle.

The script uses Python's standard library and takes input and output CSV paths
as its two arguments. All material needed for the calculation is local.
