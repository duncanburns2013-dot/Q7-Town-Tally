"""Join town Q7 results (AP via Boston Globe) to town party enrollment.

Usage: python -I join_q7_enrollment.py <q7_csv> <enroll_csv> <out_csv>
"""
import csv
import re
import sys


def key(name):
    return re.sub(r"[^a-z]", "", name.lower())


def main(q7_csv, enroll_csv, out_csv):
    q7 = {key(r["town"]): r for r in csv.DictReader(open(q7_csv, encoding="utf-8"))}
    en = {key(r["town"]): r for r in csv.DictReader(open(enroll_csv, encoding="utf-8"))}
    missing = sorted(set(q7) ^ set(en))
    assert not missing, f"unmatched towns: {missing}"
    assert sum(int(r["other"]) for r in en.values()) == 49401, "other != statewide 49,401"

    cols = ["town", "county", "registered", "democrat", "republican", "unenrolled",
            "other", "pct_dem", "pct_rep", "pct_unenrolled", "pct_other",
            "q7_yes", "q7_no", "q7_yes_pct", "q7_margin_pts", "q7_result",
            "q7_votes_per_registered_pct", "precincts_reporting", "precincts_total"]
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(cols)
        for k in sorted(en, key=lambda k: en[k]["town"]):
            e, q = en[k], q7[k]
            yes, no, reg = int(q["yes"]), int(q["no"]), int(e["registered"])
            tot = yes + no
            yp = round(100 * yes / tot, 2) if tot else ""
            w.writerow([q["town"], e["county"], reg, e["democrat"], e["republican"],
                        e["unenrolled"], e["other"], e["pct_dem"], e["pct_rep"],
                        e["pct_unenrolled"], e["pct_other"], yes, no, yp,
                        round(yp - (100 - yp), 2) if tot else "",
                        ("Yes" if yes > no else "No" if no > yes else "Tie") if tot else "No results",
                        round(100 * tot / reg, 1),
                        q["precincts_reporting"], q["precincts_total"]])
    print(f"joined {len(en)} towns -> {out_csv}")


if __name__ == "__main__":
    main(*sys.argv[1:4])
