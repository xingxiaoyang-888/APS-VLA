#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json

from diwa.data.tfrecord import verify_tfrecord


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("path")
    args = parser.parse_args()
    print(json.dumps(verify_tfrecord(args.path).__dict__, sort_keys=True))


if __name__ == "__main__":
    main()
