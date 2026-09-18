"""Verify data/ against the official AtliQ Mart dataset (Codebasics Challenge #2).

Compares each CSV to its official checksum (recorded 2026-08-25 from the
official Codebasics download: codebasics.io/challenges/codebasics-resume-project-
challenge/5 → login → Participate → Download Files → c2-input-for-participants-1.zip)
and checks expected row counts.

Note: the official dim_date.csv ships mmm_yy as Excel-converted dates like
"01-Apr-22" — that IS the official format (a GitHub mirror normalized it to
"Apr 22"; the official zip is authoritative).

Usage:  python analysis/verify_data.py
Exit code 0 = all good; 1 = something differs.
"""
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

# Official normalized MD5 (line endings converted to \n) + expected row count.
EXPECTED = {
    "dim_customers.csv":        ("e631b09ab07a36b81f703bdf3150fd26", 35),
    "dim_date.csv":             ("b52e245cb3f61a5eabe85a995169c199", 183),
    "dim_products.csv":         ("f61ea365549c80fe7d9510655a799c77", 18),
    "dim_targets_orders.csv":   ("10ff8c45bff88feb3de4dc7a1a41f8c6", 35),
    "fact_order_lines.csv":     ("2acfc36346ae7c23b6cc004d35de3d06", 57096),
    "fact_orders_aggregate.csv":("9565702a453fef9259ee73a259bd8676", 31729),
}


def norm_md5(path: Path) -> str:
    raw = path.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return hashlib.md5(raw).hexdigest()


def count_rows(path: Path) -> int:
    with open(path, "rb") as f:
        data = f.read().replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    # count lines minus header (last empty line from trailing newline excluded)
    lines = [ln for ln in data.split(b"\n") if ln.strip()]
    return len(lines) - 1


def main() -> int:
    failed = 0
    print(f"Verifying {DATA}")
    for name, (md5, rows) in EXPECTED.items():
        path = DATA / name
        if not path.exists():
            print(f"  MISSING  {name}")
            failed += 1
            continue
        ok_md5 = norm_md5(path) == md5
        ok_rows = count_rows(path) == rows
        status = "OK      " if (ok_md5 and ok_rows) else "FAIL    "
        if not (ok_md5 and ok_rows):
            failed += 1
        print(f"  {status}{name}  md5={'match' if ok_md5 else 'DIFFERS'}, "
              f"rows={count_rows(path)} (expect {rows})")
    print("RESULT:", "ALL 6 FILES CORRECT" if failed == 0 else f"{failed} file(s) differ")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())