"""Convert the fixed records; usage: python3 normalize.py INPUT.csv OUTPUT.csv."""

import csv
import sys

SCALE = 0.5

with open(sys.argv[1], newline="", encoding="utf-8") as source:
    rows = list(csv.DictReader(source))

with open(sys.argv[2], "w", newline="", encoding="utf-8") as destination:
    writer = csv.DictWriter(destination, fieldnames=["record_id", "converted_value"])
    writer.writeheader()
    for row in rows:
        writer.writerow({
            "record_id": row["record_id"],
            "converted_value": SCALE * float(row["raw_value"]),
        })
