"""Parse the MA Secretary of the Commonwealth "Registered Voters and Party
Enrollment" PDF into a town-level CSV.

Usage: python -I parse_enrollment.py <pdf> <out_csv>

Layout (Feb 1 2025 edition): pages 2..N each start with the county aggregate
row (repeated on continuation pages), then one row per city/town with four
numeric columns: Total Registered, Democrat, Republican, Unenrolled.
"Other" (all other political parties/designations) is not printed per town,
so it is derived as registered - D - R - U. Page 1 is the county summary and
the last row of the last page is the statewide total; both are used as checks.
"""
import csv
import re
import sys

import pymupdf

NUM = re.compile(r"^[\d,]+$")


def num(s):
    return int(s.replace(",", ""))


def rows_on_page(page):
    words = page.get_text("words")
    hdr = {w[4]: (w[0] + w[2]) / 2 for w in words if w[1] < 112}
    # Column centres taken from this page's own header words.
    cols = {
        "registered": hdr.get("Registered"),
        "democrat": hdr.get("Democrat"),
        "republican": hdr.get("Republican"),
        "unenrolled": hdr.get("Unenrolled"),
    }
    assert all(cols.values()), f"header missing on page {page.number + 1}: {cols}"
    body = [w for w in words if w[1] > 108]
    names = [w for w in body if w[0] < 230 and not NUM.match(w[4])]
    nums = [w for w in body if NUM.match(w[4]) and w[0] >= 230]

    # Cluster numbers into lines by y.
    lines = []
    for w in sorted(nums, key=lambda w: w[1]):
        if lines and abs(lines[-1]["y"] - w[1]) < 4:
            lines[-1]["w"].append(w)
        else:
            lines.append({"y": w[1], "w": [w]})

    out = []
    for ln in lines:
        rec = {}
        for w in ln["w"]:
            cx = (w[0] + w[2]) / 2
            col = min(cols, key=lambda c: abs(cols[c] - cx))
            assert col not in rec, f"two values in {col} on p{page.number + 1} y={ln['y']}"
            rec[col] = num(w[4])
        assert len(rec) == 4, f"incomplete line p{page.number + 1} y={ln['y']}: {rec}"
        nm = sorted((w for w in names if abs(w[1] - ln["y"]) < 4), key=lambda w: w[0])
        name = " ".join(w[4] for w in nm)
        name = re.sub(r"\.{2,}.*$", "", name).strip().rstrip(".").strip()
        name = re.sub(r"\s+", " ", name)
        assert name, f"no name for line p{page.number + 1} y={ln['y']}"
        rec["name"] = name
        out.append(rec)
    return out


def main(pdf, out_csv):
    doc = pymupdf.open(pdf)
    towns, counties, state = [], {}, None
    for i in range(1, doc.page_count):
        rows = rows_on_page(doc[i])
        county = rows[0]["name"]
        counties[county] = rows[0]
        body = rows[1:]
        if body and body[-1]["name"].lower().startswith("totals"):
            state = body.pop()
        for r in body:
            r["county"] = county
            towns.append(r)

    # Checks: towns sum to each county aggregate, counties + towns sum to state.
    keys = ["registered", "democrat", "republican", "unenrolled"]
    for c, agg in counties.items():
        for k in keys:
            s = sum(t[k] for t in towns if t["county"] == c)
            assert s == agg[k], f"{c} {k}: towns {s} != county {agg[k]}"
    assert state, "statewide Totals row not found"
    for k in keys:
        s = sum(t[k] for t in towns)
        assert s == state[k], f"state {k}: towns {s} != {state[k]}"
    assert len(towns) == 351, f"expected 351 towns, got {len(towns)}"

    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["town", "county", "registered", "democrat", "republican",
                    "unenrolled", "other", "pct_dem", "pct_rep", "pct_unenrolled",
                    "pct_other"])
        for t in towns:
            other = t["registered"] - t["democrat"] - t["republican"] - t["unenrolled"]
            assert other >= 0, t
            reg = t["registered"]
            w.writerow([t["name"].title(), t["county"].title(), reg, t["democrat"],
                        t["republican"], t["unenrolled"], other]
                       + [round(100 * x / reg, 2) for x in
                          (t["democrat"], t["republican"], t["unenrolled"], other)])
    print(f"{len(towns)} towns, {len(counties)} counties; statewide "
          + ", ".join(f"{k}={state[k]:,}" for k in keys))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
