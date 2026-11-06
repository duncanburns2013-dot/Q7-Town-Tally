# Question 7 by Town

Massachusetts 2026 ballot Question 7 would have required cities and towns to allow
single-family homes on lots of at least 5,000 sq ft. It was defeated. This project
maps the result for all 351 cities and towns and sets it beside each town's party
enrollment.

**Live map:** https://duncanburns2013-dot.github.io/Q7-Town-Tally/

## Statewide result (unofficial)

| | Votes | Share |
|---|---:|---:|
| No | 1,287,917 | 50.6% |
| Yes | 1,255,595 | 49.4% |
| Margin | 32,322 | |

No carried 274 towns and Yes carried 75. New Ashford and Plainfield had not
reported. The count covers 2,374 of 2,384 precincts.

## What the page shows

- A town map colored by Question 7 vote, % Democrat, % Republican or % Unenrolled,
  with zoom presets, town search and a pinned town card.
- A scatter of each town's Yes share against its party enrollment shares.
- A sortable, searchable table of all 351 towns.

Across towns, Yes share rises with Democratic enrollment (r = 0.76) and falls with
Republican (r = −0.77) and unenrolled (r = −0.61) enrollment, across the 349
towns with results. These are
correlations between town totals. They do not show how any individual voter voted,
and they are not evidence that party enrollment caused the result.

## Sources

| File | Source |
|---|---|
| `raw/q7_globe_ap_20261106.csv` | AP unofficial town results as displayed on the Boston Globe results page, captured 2026-11-06 at about 1:37 PM ET with 98.99% of precincts counted |
| `raw/enrollment_count_20250201.pdf` | MA Secretary of the Commonwealth, *Registered Voters and Party Enrollment*, as of February 1, 2025 (the newest edition published) |
| `raw/census/` | U.S. Census Bureau 2023 cartographic boundary file, county subdivisions, Massachusetts (1:500k) |

## Caveats

- **The results are unofficial.** Ten towns were incomplete when captured: Dover
  0/1, Erving 0/1, Holbrook 3/4, Malden 26/27, Mattapoisett 1/2, Nahant 0/1,
  Needham 9/10, New Ashford 0/1, North Andover 7/8 and Plainfield 0/1 precincts.
  Certified results from the Secretary of the Commonwealth will replace these
  numbers once they are posted.
- Enrollment is from February 2025, about 21 months before the election.
- "Other" enrollment (minor parties and designations) is not printed per town in
  the PDF. It is derived as registered − D − R − U, and those values sum to the
  statewide 49,401.

## Files

| File | What it is |
|---|---|
| `index.html` | The published map (the GitHub Pages copy) |
| `site/template.html` | Page source; the build injects the data into it |
| `site/q7-town-map.html` | The same page without the document skeleton, for the Claude artifact host |
| `site/og-template.html` → `og.html` → `og.png` | The 1200×630 social preview card, painted from the same data and color ramp |
| `scripts/render_og.ps1` | Renders `og.html` to `og.png` with headless Chrome |
| `enrollment_by_town_20250201.csv` | Town enrollment parsed from the PDF |
| `q7_by_town_with_enrollment.csv` | Question 7 results joined to enrollment |
| `scripts/parse_enrollment.py` | PDF → enrollment CSV |
| `scripts/join_q7_enrollment.py` | Joins the results and enrollment tables |
| `scripts/build_map_data.py` | Projects the boundaries, joins the data and writes both pages |

## Rebuild

Each script stops with an error if its output does not match the source totals:
towns must sum to each county and to the statewide row in the PDF, every town
must match between the tables and the map, and vote and enrollment totals must
match the sources.

```bash
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt
.venv/Scripts/python scripts/parse_enrollment.py raw/enrollment_count_20250201.pdf enrollment_by_town_20250201.csv
.venv/Scripts/python scripts/join_q7_enrollment.py raw/q7_globe_ap_20261106.csv enrollment_by_town_20250201.csv q7_by_town_with_enrollment.csv
.venv/Scripts/python scripts/build_map_data.py
```

On macOS or Linux, use `.venv/bin/python`. Then refresh the social card (Windows,
needs Chrome and a network connection for the fonts):

```powershell
powershell -File scripts/render_og.ps1
```

## Design

The page follows the Massachusetts Data Hub theme: the official state colors (Bay
Blue, Berkshire Green, Cranberry) on a slate ground, with Halyard and IBM Plex
Mono. Yes/No runs from Cranberry (No) to Berkshire Green (Yes) rather than blue
and red, so the vote never reads as Democrat versus Republican next to the
party-enrollment maps. Both arms of that scale step through matching lightness.
