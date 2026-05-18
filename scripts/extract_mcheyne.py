"""
One-off script to extract the M'Cheyne reading plan from the canonical PDF
hosted at https://www.mcheyne.info/calendar.pdf into two reading files
(family and private) consumable by this project.

Run:
    curl -s -A "Mozilla/5.0" https://www.mcheyne.info/calendar.pdf -o /tmp/mcheyne.pdf
    pdftotext -layout /tmp/mcheyne.pdf /tmp/mcheyne.txt
    python scripts/extract_mcheyne.py /tmp/mcheyne.txt
"""
import re
import sys
from pathlib import Path

from bible_reading_plan.utils.bible_books import BIBLE_BOOKS

# The PDF uses a Psalms typo and a few short forms; normalize to canonical names.
BOOK_ALIASES = {
    "Phillipians": "Philippians",
    "Song": "Song of Solomon",
    "Psalms": "Psalms",  # left as-is; downstream parser already handles "Psalms"
}

# Build the list of names the parser should look for. Longest-first matters so
# "1 Samuel" beats "1 ", "Song of Solomon" beats "Song", etc.
_KNOWN_BOOKS = sorted(
    set(BIBLE_BOOKS) | {"Psalms"} | set(BOOK_ALIASES),
    key=lambda n: -len(n),
)


MONTH_HEADERS = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]


def _find_books_in_line(line):
    """Return list of (start, end, canonical_name) for every book in the line, in order."""
    matches = []
    occupied = [False] * len(line)
    for name in _KNOWN_BOOKS:
        for m in re.finditer(re.escape(name), line):
            s, e = m.span()
            if any(occupied[s:e]):
                continue
            for i in range(s, e):
                occupied[i] = True
            matches.append((s, e, BOOK_ALIASES.get(name, name)))
    matches.sort(key=lambda t: t[0])
    return matches


def _clean_chapter_spec(raw):
    """Collapse whitespace and tidy '9 , 10' -> '9, 10'."""
    s = re.sub(r"\s+", " ", raw).strip()
    s = re.sub(r"\s*,\s*", ", ", s)
    return s


def _parse_line(line):
    """Parse one data row into (family_ot, family_nt, secret_ot, secret_nt) Reading strings.

    Returns None if the row is not a data row.
    """
    books = _find_books_in_line(line)
    if len(books) != 4:
        return None

    (s1, e1, b1), (s2, e2, b2), (s3, e3, b3), (s4, e4, b4) = books

    seg1 = line[e1:s2]                     # chapter1
    seg2 = line[e2:s3]                     # chapter2 + date
    seg3 = line[e3:s4]                     # chapter3
    seg4 = line[e4:]                       # chapter4 (to end of line)

    # seg2 has the day-of-month tacked on after a wide gap. Split on the last
    # wide gap to peel the date off.
    m = re.match(r"(.+?)\s{3,}(\d{1,2})\s*$", seg2.rstrip())
    if not m:
        return None
    chapter2 = m.group(1)

    return (
        f"{b1} {_clean_chapter_spec(seg1)}",
        f"{b2} {_clean_chapter_spec(chapter2)}",
        f"{b3} {_clean_chapter_spec(seg3)}",
        f"{b4} {_clean_chapter_spec(seg4)}",
    )


def parse_pdf_text(text):
    """Yield (family_ot, family_nt, secret_ot, secret_nt) tuples in day order."""
    for line in text.splitlines():
        if not line.strip():
            continue
        # Skip headers/title rows containing the word "Book" repeatedly or month names.
        if "Book" in line and "Chapter" in line:
            continue
        if any(month in line for month in MONTH_HEADERS) and "M'Cheyne" in line:
            continue
        # Skip the directions page and front matter.
        if line.lstrip().startswith(("http://", "Page ", "Robert Murray", "M'Cheyne")):
            continue

        parsed = _parse_line(line)
        if parsed is None:
            continue
        yield parsed


def main():
    if len(sys.argv) != 2:
        print("Usage: extract_mcheyne.py <pdftotext-output.txt>", file=sys.stderr)
        sys.exit(2)

    text = Path(sys.argv[1]).read_text()
    rows = list(parse_pdf_text(text))

    if len(rows) != 365:
        print(f"WARNING: expected 365 rows, got {len(rows)}", file=sys.stderr)

    plans_dir = Path("plans")
    plans_dir.mkdir(exist_ok=True)
    family_path = plans_dir / "mcheyne-family.txt"
    private_path = plans_dir / "mcheyne-private.txt"

    with family_path.open("w") as f:
        for fot, fnt, _, _ in rows:
            f.write(f"{fot}; {fnt}\n")

    with private_path.open("w") as f:
        for _, _, sot, snt in rows:
            f.write(f"{sot}; {snt}\n")

    print(f"Wrote {len(rows)} rows to {family_path} and {private_path}")


if __name__ == "__main__":
    main()
