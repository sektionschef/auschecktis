#!/usr/bin/env python3
"""
Sanity checks for input/heurigen_list.json and data/*.json.
Exits with status 1 if any error is found, so the build/deploy stops.
"""

import json
import os
import sys
from datetime import datetime

REQUIRED_MASTER_FIELDS = ["label", "website", "link_opening_hours_page", "comment", "location", "lat", "lng"]
REQUIRED_EVENT_FIELDS = ["title", "start", "end"]


def validate(base_dir: str = ".") -> list:
    errors = []
    data_dir = os.path.join(base_dir, "data")

    try:
        with open(os.path.join(base_dir, "input", "heurigen_list.json"), encoding="utf-8") as f:
            master = json.load(f)
    except Exception as e:
        return [f"input/heurigen_list.json: {e}"]

    for key, entry in master.items():
        for field in REQUIRED_MASTER_FIELDS:
            if field not in entry:
                errors.append(f"heurigen_list.json [{key}]: field '{field}' missing")
        if not isinstance(entry.get("lat"), (int, float)) or not isinstance(entry.get("lng"), (int, float)):
            errors.append(f"heurigen_list.json [{key}]: lat/lng must be numbers")
        if not os.path.exists(os.path.join(data_dir, f"{key}.json")):
            errors.append(f"heurigen_list.json [{key}]: data/{key}.json missing")

    for filename in sorted(os.listdir(data_dir)):
        if not filename.endswith(".json"):
            continue
        key = filename[:-5]
        name = f"data/{filename}"
        if key not in master:
            errors.append(f"{name}: no entry '{key}' in heurigen_list.json")
            continue
        try:
            with open(os.path.join(data_dir, filename), encoding="utf-8") as f:
                events = json.load(f)
        except Exception as e:
            errors.append(f"{name}: invalid JSON ({e})")
            continue
        if not isinstance(events, list):
            errors.append(f"{name}: must contain a JSON array")
            continue

        seen = set()
        for i, event in enumerate(events):
            where = f"{name} #{i}"
            missing = [f for f in REQUIRED_EVENT_FIELDS if f not in event]
            if missing:
                errors.append(f"{where}: fields missing: {', '.join(missing)}")
                continue
            where = f"{name} {event['start']}"
            try:
                start = datetime.fromisoformat(event["start"])
                end = datetime.fromisoformat(event["end"])
            except ValueError as e:
                errors.append(f"{where}: invalid date ({e})")
                continue
            if end <= start:
                errors.append(f"{where}: end is not after start")
            if start.date() != end.date():
                errors.append(f"{where}: end is on a different day")
            if event["title"] != master[key]["label"]:
                errors.append(f"{where}: title '{event['title']}' != label '{master[key]['label']}'")
            if event["start"] in seen:
                errors.append(f"{where}: duplicate entry")
            seen.add(event["start"])

    return errors


if __name__ == "__main__":
    errors = validate()
    for error in errors:
        print(f"❌ {error}")
    if errors:
        print(f"\n{len(errors)} error(s) in the data")
        sys.exit(1)
    print("✅ Data is valid")
