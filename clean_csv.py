import re
import csv
import io
from collections import Counter

SRC = 'us_stock_valuation.csv'
DST = 'us_stock_valuation_clean.csv'

def normalize_line(line: str):
    """
    Fix rows that start with an extra leading double-quote:
      - remove outer quotes
      - collapse doubled quotes "" -> "
    """
    if line.startswith('"'):
        line = line[1:]
        line = re.sub(r'"(\r?\n)?$', r'\1', line)
        line = line.replace('""', '"')
        return line, True
    return line, False

# 1) Read raw file and normalize glitched lines
glitch_flags = []
norm_lines = []
with open(SRC, 'r', encoding='utf-8') as f:
    for raw in f:
        fixed, glitched = normalize_line(raw)
        norm_lines.append(fixed)
        glitch_flags.append(glitched)

# 2) Parse safely
rows = list(csv.reader(io.StringIO(''.join(norm_lines))))
if not rows:
    raise SystemExit("No rows found in source file")

# 3) Expected column width (modal)
width_counts = Counter(len(r) for r in rows)
expected_cols, _ = max(width_counts.items(), key=lambda kv: kv[1])

# 4) Enforce width, remove stray quotes, and sanitize Company Name (col 1)
fixed_rows = []
trimmed = 0
padded = 0
COMPANY_COL = 1  # Ticker is col 0, Company Name is col 1

for i, r in enumerate(rows):
    # Remove stray quotes everywhere and trim spaces
    r = [field.replace('"', '').strip() for field in r]

    # If glitched rows have extra trailing field(s), drop from the end
    if glitch_flags[i] and len(r) > expected_cols:
        r = r[:expected_cols]
        trimmed += 1

    # Enforce width for any other anomalies
    if len(r) > expected_cols:
        r = r[:expected_cols]
        trimmed += 1
    elif len(r) < expected_cols:
        r = r + [''] * (expected_cols - len(r))
        padded += 1

    # Sanitize Company Name: remove commas so the CSV writer won't re-quote it
    if len(r) > COMPANY_COL:
        company = r[COMPANY_COL]
        # Remove any commas inside the name and normalize spaces
        company = re.sub(r'\s*,\s*', ' ', company)
        company = re.sub(r'\s+', ' ', company).strip()
        r[COMPANY_COL] = company

    fixed_rows.append(r)

# 5) Write clean CSV
with open(DST, 'w', encoding='utf-8', newline='') as f:
    writer = csv.writer(f, quoting=csv.QUOTE_MINIMAL)
    writer.writerows(fixed_rows)

print("File cleaned successfully!")
print(f"- Expected columns: {expected_cols}")
print(f"- Rows trimmed: {trimmed}")
print(f"- Rows padded: {padded}")

# 6) Quick verification
with open(DST, 'r', encoding='utf-8') as f:
    for i, line in enumerate(f):
        if i < 5:
            print(line.strip())
        else:
            break