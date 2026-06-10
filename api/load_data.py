"""
Load lobbyfacts_with_policies.csv into the ramm_lobbying database.

Populates:
  - organization
  - policy_area
  - lobbying_activity  (links orgs to policy areas so the search filter works)
  - meeting            (one summary row per org; attendees_count = total EP meetings)
  - access_pass        (one row per EP pass holder, count = "EP passes on 2026-05-25")

Run from inside the api container, or locally if mysql-connector + the DB are reachable.
Usage:  python load_data.py /path/to/lobbyfacts_with_policies.csv
"""

import sys
import ast
import os
import pandas as pd
import mysql.connector

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

    # ── 1. Collect + insert distinct policy areas ────────────────────────────
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

    # ── 2. Insert orgs, lobbying_activity, meeting, and access_pass rows ─────
    org_count = 0
    activity_id = 1
    pass_id = 1

    for idx, row in df.iterrows():
        org_id = idx + 1  # 1-based stable id

        # organization
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

        # lobbying_activity — link org to each of its policy areas
        raw_areas = row.get("policy_areas")
        if not pd.isna(raw_areas):
            try:
                for area in ast.literal_eval(raw_areas):
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

        # meeting — one summary row; attendees_count holds the total EP meetings
        meetings = int(clean_num(row.get("Meetings")) or 0)
        if meetings > 0:
            cur.execute(
                """INSERT INTO meeting (meeting_id, org_id, attendees_count, source)
                   VALUES (%s, %s, %s, %s)""",
                (org_id, org_id, meetings, "lobbyfacts_csv"),
            )

        # access_pass — one row per current EP pass holder
        ep_passes = int(clean_num(row.get("EP passes on 2026-05-25")) or 0)
        for _ in range(ep_passes):
            cur.execute(
                """INSERT INTO access_pass (pass_id, org_id, source)
                   VALUES (%s, %s, %s)""",
                (pass_id, org_id, "lobbyfacts_csv"),
            )
            pass_id += 1

        if org_count % 500 == 0:
            conn.commit()
            print(f"  ...{org_count} orgs, {pass_id - 1} passes")

    conn.commit()
    print(
        f"  inserted {org_count} organizations, "
        f"{activity_id - 1} activities, "
        f"{pass_id - 1} access passes"
    )

    cur.close()
    conn.close()
    print("Done.")


if __name__ == "__main__":
    main()
