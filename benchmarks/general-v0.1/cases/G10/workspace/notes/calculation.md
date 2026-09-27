# Baseline and later code change

The [baseline command record](../runs/baseline/command.txt) used the script copied
in that run's directory. Its [output](../runs/baseline/output.csv) contains
converted values 4, 8 and 12, with arithmetic mean 8.

The [calibration pairs](../data/calibration.csv) were then checked. The current
[analysis script](../analysis/normalize.py) was changed to use the corresponding
linear conversion, but no output from executing that revised script is saved
in this fixture yet. The original records have not changed.
