#!/usr/bin/env python3
"""Fit susceptibility data with a free gamma exponent.

Usage: python3 fit-exponent.py <data-file> <lmin> <lmax>
"""
import sys

def main(argv):
    data_file, lmin, lmax = argv[1], int(argv[2]), int(argv[3])
    print(f"fit {data_file} over L in [{lmin}, {lmax}] with gamma free")

if __name__ == "__main__":
    main(sys.argv)
