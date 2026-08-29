#!/usr/bin/env python3
"""
Idempotency guard for mjm-battery-wholesale-sale.

Prevents duplicate POSTs of the same supplier invoice number. The mjmbattery
server's `sales.php?search=` does NOT index the user-supplied invoice number
(only the server-generated `OUT-NNNN-NNNNN` and customer name), so the form
will happily create a duplicate sale if the same invoice is submitted twice.

Local state file: ~/.hermes/state/mjm_processed_invoices.json
Schema: array of {
    user_invoice, customer_name, grand_total,
    server_invoice, sale_id, processed_at
}

Public API:
    check(user_invoice) -> dict | None   # existing record or None
    append(record)      -> None         # write new record (file-locked)
    is_processed(user_invoice) -> bool   # convenience
    rotate(max_age_days=90) -> int       # drop old entries, return count removed

CLI:
    python3 scripts/idempotency_check.py check 063/PS-T/VI/26
    python3 scripts/idempotency_check.py append '{"user_invoice":"...","sale_id":...}'
    python3 scripts/idempotency_check.py rotate
"""

import argparse
import json
import os
import sys
import tempfile
import time
from pathlib import Path

STATE_PATH = Path(os.path.expanduser("~/.hermes/state/mjm_processed_invoices.json"))


def _ensure_state():
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not STATE_PATH.exists():
        STATE_PATH.write_text("[]")


def _read():
    _ensure_state()
    with open(STATE_PATH) as f:
        return json.load(f)


def _write_atomic(rows):
    _ensure_state()
    # atomic write: temp + rename, avoids corruption on crash mid-write
    fd, tmp = tempfile.mkstemp(dir=STATE_PATH.parent, prefix=".mjm_idem_")
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(rows, f, indent=2, ensure_ascii=False)
        os.replace(tmp, STATE_PATH)
    except Exception:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def check(user_invoice):
    """Return existing record for user_invoice, or None."""
    if not user_invoice:
        return None
    user_invoice = str(user_invoice).strip()
    for r in _read():
        if str(r.get("user_invoice", "")).strip() == user_invoice:
            return r
    return None


def is_processed(user_invoice):
    return check(user_invoice) is not None


def append(record):
    """Append a new record. Idempotent on (user_invoice) — re-appending the
    same key just updates the existing record's server_invoice/sale_id/grand_total
    if they were previously unknown."""
    if not record.get("user_invoice"):
        raise ValueError("record must include user_invoice")
    record.setdefault("processed_at", time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
    rows = _read()
    for i, r in enumerate(rows):
        if r.get("user_invoice") == record["user_invoice"]:
            rows[i] = {**r, **record}  # merge, prefer new fields
            _write_atomic(rows)
            return
    rows.append(record)
    _write_atomic(rows)


def rotate(max_age_days=90):
    """Drop entries older than max_age_days. Returns count removed."""
    cutoff = time.time() - (max_age_days * 86400)
    rows = _read()
    keep, drop = [], []
    for r in rows:
        ts = r.get("processed_at", "")
        try:
            t = time.mktime(time.strptime(ts[:19] + "Z", "%Y-%m-%dT%H:%M:%SZ"))
        except (ValueError, TypeError):
            t = 0
        (keep if t >= cutoff else drop).append(r)
    if drop:
        _write_atomic(keep)
    return len(drop)


def _cli():
    p = argparse.ArgumentParser(description="mjm-battery invoice idempotency")
    sub = p.add_subparsers(dest="cmd", required=True)

    pc = sub.add_parser("check", help="check if a user_invoice has been processed")
    pc.add_argument("user_invoice")

    pa = sub.add_parser("append", help="append a processed record (JSON on stdin)")
    pa.add_argument("json", nargs="?", help="JSON record; if omitted, read stdin")

    pr = sub.add_parser("rotate", help="drop entries older than N days")
    pr.add_argument("--max-age-days", type=int, default=90)

    args = p.parse_args()

    if args.cmd == "check":
        r = check(args.user_invoice)
        if r is None:
            print("NEW")
            return 0
        print(f"DUP {args.user_invoice} -> {r.get('server_invoice', '?')} id={r.get('sale_id', '?')}")
        return 1
    elif args.cmd == "append":
        rec = json.loads(args.json) if args.json else json.load(sys.stdin)
        append(rec)
        print(f"appended {rec.get('user_invoice')}")
        return 0
    elif args.cmd == "rotate":
        n = rotate(args.max_age_days)
        print(f"rotated {n} entries older than {args.max_age_days} days")
        return 0


if __name__ == "__main__":
    sys.exit(_cli())
