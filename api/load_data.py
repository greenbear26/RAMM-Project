"""
Load lobbyfacts_with_policies.csv into the ramm_lobbying database.

Populates:
  - organization
  - policy_area
  - lobbying_activity  (links orgs to policy areas so the search filter works)

Run from inside the api container, or locally if mysql-connector + the DB are reachable.
Usage:  python load_data.py /path/to/lobbyfacts_with_policies.csv
"""

import sys
import ast
import os
import pandas as pd
import mysql.connector

# ── DB connection ────────────────────────────────────────
# Reads the same env vars your Flask app uses. Adjust host if running
# outside Docker (use "localhost" + the mapped port instead of "db").
DB_CONFIG = {
    "host":     os.getenv("DB_HOST", "db"),
    "port":     int(os.getenv("DB_PORT", "3306")),
    "user":     os.getenv("DB_USER", "root"),
    "password": os.getenv("MYSQL_ROOT_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "ramm_lobbying"),
}

CSV_PATH = sys.argv[1] if len(sys.argv) > 1 else "lobbyfacts_with_policies.csv"


def clean_num(val):
    """Return a float or None for messy numeric cells."""
    if pd.isna(val):
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


def main():
    print(f"Reading {CSV_PATH} ...")
    df = pd.read_csv(CSV_PATH)
    print(f"  {len(df)} rows")

    conn = mysql.connector.connect(**DB_CONFIG)
    cur = conn.cursor()

    # ── 1. Collect + insert distinct policy areas ────────
    all_areas = set()
    for raw in df["policy_areas"].dropna():
        try:
            for a in ast.literal_eval(raw):
                all_areas.add(a.strip())
        except (ValueError, SyntaxError):
            continue

    area_to_id = {}
    for i, area in enumerate(sorted(all_areas), start=1):
        area_to_id[area] = i
        cur.execute(
            "INSERT IGNORE INTO policy_area (policy_area_id, name) VALUES (%s, %s)",
            (i, area),
        )
    print(f"  inserted {len(area_to_id)} policy areas")

    # ── 2. Insert organizations + their lobbying_activity rows ──
    org_count = 0
    activity_id = 1
    for idx, row in df.iterrows():
        org_id = idx + 1  # 1-based stable id

        cur.execute(
            """INSERT INTO organization
                 (org_id, name, members_fte, lobbying_cost,
                  interest_represented, country_code)
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (
                org_id,
                str(row["Name"])[:255],
                clean_num(row.get("Members FTE")),
                clean_num(row.get("Lobbying cost")),
                (str(row.get("Interest represented"))[:255]
                 if not pd.isna(row.get("Interest represented")) else None),
                (str(row.get("Head office"))[:10]
                 if not pd.isna(row.get("Head office")) else None),
            ),
        )
        org_count += 1

        # link to policy areas
        raw = row.get("policy_areas")
        if not pd.isna(raw):
            try:
                for area in ast.literal_eval(raw):
                    pa_id = area_to_id.get(area.strip())
                    if pa_id:
                        cur.execute(
                            """INSERT INTO lobbying_activity
                                 (activity_id, org_id, policy_area_id, activity_type)
                               VALUES (%s, %s, %s, %s)""",
                            (activity_id, org_id, pa_id, "lobbying"),
                        )
                        activity_id += 1
            except (ValueError, SyntaxError):
                pass

        if org_count % 2000 == 0:
            conn.commit()
            print(f"  ...{org_count} orgs")

    conn.commit()
    print(f"  inserted {org_count} organizations, {activity_id - 1} activities")

    cur.close()
    conn.close()
    print("Done.")


if __name__ == "__main__":
    main()
