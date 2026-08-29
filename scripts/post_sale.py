#!/usr/bin/env python3
"""
Direct POST helper for mjmbattery.com /admin/sale_save.php.

Bundles the proven recipe:
  1. harvest CSRF from /admin/sale_custom_wholesale.php?branch=<branch>
  2. build items_json with full prices (cashback → separate expense)
  3. POST with Origin: https://mjmbattery.com (required, else 403)
  4. parse redirect -> (sale_id, server_invoice) or raise

NEW (browserless) functions — no byob needed:
    login()              — POST to login.php, return PHPSESSID
    search_customers()   — GET search_customers.php, return candidates
    get_page_data()      — return (csrf, allProducts) from sale page
    post_expense()       — POST cashback as Biaya Marketing expense

Public API:
    post_sale(phpsessid, invoice, products_by_code, branch='OUT_OF_TOWN',
              csrf=None, base_url='https://mjmbattery.com',
              cashback_mode='expense', post_expense_after=False) -> dict
        invoice:            parsed JSON invoice (the dict from the user)
        products_by_code:   dict mapping user product_code -> {id, name, price_wholesale}
                            (the resolved OUT_OF_TOWN allProducts entry, possibly
                             with code-map applied)
        cashback_mode:      'expense' (default) — items at full price, cashback separate
                            'absorb' (legacy) — cashback absorbed into item prices
        post_expense_after: if True and cashback_mode='expense', auto-post expense entry
                            for the cashback amount after sale succeeds
        Returns: {sale_id, server_invoice, items_subtotal, delta, payment_status,
                  global_adjustments, payments, cashback_amount, expense_id, request_url}

Idempotency is NOT the concern of this script — call scripts/idempotency_check.py
BEFORE post_sale() to short-circuit known duplicates.
"""

import json
import os
import re
import ssl
import sys
import urllib.parse
import urllib.request

CUSTOMER_CACHE_PATH = os.path.expanduser("~/.hermes/state/mjm_customers.json")

# ── Customer cache ──

def _load_customer_cache():
    os.makedirs(os.path.dirname(CUSTOMER_CACHE_PATH), exist_ok=True)
    if not os.path.exists(CUSTOMER_CACHE_PATH):
        with open(CUSTOMER_CACHE_PATH, "w") as f:
            json.dump({}, f)
        return {}
    with open(CUSTOMER_CACHE_PATH) as f:
        return json.load(f)


def _save_customer_cache(cache):
    with open(CUSTOMER_CACHE_PATH, "w") as f:
        json.dump(cache, f, indent=2, ensure_ascii=False)


def lookup_customer_id(name):
    """Check customer cache for a matching name. Returns id or None."""
    cache = _load_customer_cache()
    if not name or not cache:
        return None
    name_lower = name.lower().strip()
    # Exact match
    if name_lower in cache:
        return cache[name_lower]
    # Prefix match — "hs aki sidoarjo" matches cached "hs aki"
    for cached_name, cid in cache.items():
        if name_lower.startswith(cached_name) or cached_name.startswith(name_lower):
            return cid
    return None


def cache_customer_id(name, customer_id):
    """Save a customer name -> id mapping."""
    if not name or not customer_id:
        return
    cache = _load_customer_cache()
    cache[name.lower().strip()] = int(customer_id)
    _save_customer_cache(cache)


CREDS_PATH = os.path.expanduser("~/.hermes/state/mjm_credentials.json")

def _load_dotenv():
    """Load .env from repo/skill root or cwd if present — stdlib only, no dep."""
    import pathlib as _pl
    for base in [ _pl.Path(__file__).resolve().parents[1], _pl.Path.cwd() ]:
        for name in (".env",):
            f = base / name
            if f.exists():
                try:
                    for line in f.read_text().splitlines():
                        line=line.strip()
                        if not line or line.startswith("#") or "=" not in line:
                            continue
                        k,v=line.split("=",1)
                        k=k.strip(); v=v.strip().strip('"').strip("'")
                        if k and v and k not in __import__("os").environ:
                            __import__("os").environ[k]=v
                except Exception:
                    pass
                return

# auto-load .env on import (cheap, no-op if missing)
try:
    _load_dotenv()
except Exception:
    pass

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
)


# ── Shared HTTP helpers ──

def _ctx():
    c = ssl.create_default_context()
    c.check_hostname = False
    c.verify_mode = ssl.CERT_NONE
    return c


def _get(url, phpsessid=None, referer=None):
    headers = {
        "User-Agent": USER_AGENT,
        "Origin": "https://mjmbattery.com",
    }
    if phpsessid:
        headers["Cookie"] = f"PHPSESSID={phpsessid}"
    if referer:
        headers["Referer"] = referer
    req = urllib.request.Request(url, headers=headers)
    opener = urllib.request.build_opener(urllib.request.HTTPSHandler(context=_ctx()))
    return opener.open(req, timeout=20)


def _post(url, data, phpsessid=None, referer=None):
    headers = {
        "User-Agent": USER_AGENT,
        "Origin": "https://mjmbattery.com",
        "X-Requested-With": "XMLHttpRequest",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    if phpsessid:
        headers["Cookie"] = f"PHPSESSID={phpsessid}"
    if referer:
        headers["Referer"] = referer
    payload = urllib.parse.urlencode(data).encode() if isinstance(data, dict) else data
    req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
    opener = urllib.request.build_opener(urllib.request.HTTPSHandler(context=_ctx()))
    return opener.open(req, timeout=20)


# ── Browserless helpers ──

def load_creds(path=None):
    """Resolve credentials: env vars (.env) > state file > error."""
    # 1. env vars (also populated from .env above)
    env_user = __import__("os").environ.get("MJM_USERNAME")
    env_pass = __import__("os").environ.get("MJM_PASSWORD")
    env_url  = __import__("os").environ.get("MJM_BASE_URL")
    if env_user and env_pass:
        return {"username": env_user, "password": env_pass, "base_url": env_url or "https://mjmbattery.com"}
    # 2. legacy state file (Hermes compat)
    path = path or CREDS_PATH
    if __import__("os").path.exists(path):
        with open(path) as f:
            return json.load(f)
    raise FileNotFoundError(
        f"No credentials found. Set MJM_USERNAME/MJM_PASSWORD env vars, "
        f"or create .env from .env.example, or provide {CREDS_PATH}. "
        f"CLI override: post_sale.py login --username X --password Y"
    )


def login(base_url="https://mjmbattery.com", username=None, password=None):
    """Login to admin panel, return PHPSESSID string.

    If username/password omitted, reads from creds file.
    """
    if not username or not password:
        creds = load_creds()
        username = creds["username"]
        password = creds["password"]
        base_url = creds.get("base_url", base_url)

    # Login requires a fresh CSRF token and the same session cookie.
    from http.cookiejar import CookieJar
    login_jar = CookieJar()
    login_opener = urllib.request.build_opener(
        urllib.request.HTTPSHandler(context=_ctx()),
        urllib.request.HTTPCookieProcessor(login_jar),
    )
    login_url = f"{base_url}/admin/login.php"
    page_req = urllib.request.Request(
        login_url,
        headers={"User-Agent": USER_AGENT, "Origin": base_url},
        method="GET",
    )
    page_resp = login_opener.open(page_req, timeout=20)
    page_html = page_resp.read().decode("utf-8", errors="replace")
    token_match = re.search(
        r'name=["\']csrf_token["\'][^>]*value=["\']([^"\']+)', page_html,
        re.I,
    )
    if not token_match:
        raise RuntimeError("CSRF token tidak ditemukan di halaman login")

    data = urllib.parse.urlencode({
        "username": username,
        "password": password,
        "csrf_token": token_match.group(1),
    }).encode()
    req = urllib.request.Request(
        f"{base_url}/admin/login_process.php", data=data, method="POST",
        headers={
            "User-Agent": USER_AGENT,
            "Content-Type": "application/x-www-form-urlencoded",
            "Origin": base_url,
        },
    )
    # Use a redirect-handler that doesn't follow (so we can grab the Set-Cookie)
    from urllib.request import HTTPRedirectHandler, build_opener, install_opener
    class NoRedirect(HTTPRedirectHandler):
        def http_error_302(self, req, fp, code, msg, hdrs):
            return fp
        http_error_301 = http_error_302
        http_error_303 = http_error_302
        http_error_307 = http_error_302
        http_error_308 = http_error_302

    resp = login_opener.open(req, timeout=20)

    cookie_header = resp.headers.get("Set-Cookie", "")
    m = re.search(r"PHPSESSID=([^;]+)", cookie_header)
    if m:
        return m.group(1)
    for cookie in login_jar:
        if cookie.name == "PHPSESSID":
            return cookie.value

    # Fallback: try a direct GET to a page that needs session
    resp2 = _get(f"{base_url}/admin/index.php")
    cookie2 = resp2.headers.get("Set-Cookie", "")
    m = re.search(r"PHPSESSID=([^;]+)", cookie2)
    if m:
        return m.group(1)

    raise RuntimeError(
        f"Login failed — no PHPSESSID. HTTP {resp.status}. "
        f"Check credentials in {CREDS_PATH}"
    )


def search_customers(base_url, phpsessid, query):
    """Search customers via autocomplete endpoint.

    Returns list of {id, label, value, type, phone, address}.
    Auto-fixes '+' encoding to match browser behaviour.
    """
    qs = urllib.parse.urlencode({"q": query}).replace("%20", "+")
    url = f"{base_url}/admin/ajax/search_customers.php?{qs}"
    referer = f"{base_url}/admin/sale_custom_wholesale.php"
    resp = _get(url, phpsessid=phpsessid, referer=referer)
    data = resp.read().decode("utf-8", errors="replace")
    return json.loads(data)


def get_page_data(base_url, phpsessid, branch="Kiriman Luar Kota"):
    """Fetch sale page and extract (csrf_token, allProducts[ ]).

    allProducts is the product catalogue for the given branch.
    """
    url = f"{base_url}/admin/sale_custom_wholesale.php?branch={urllib.parse.quote(branch)}"
    resp = _get(url, phpsessid=phpsessid)
    body = resp.read().decode("utf-8", errors="replace")

    m = re.search(r'name="csrf_token"\s+value="([^"]+)"', body)
    if not m:
        raise RuntimeError("csrf_token not found in form page — session may have expired")
    csrf = m.group(1)

    pm = re.search(r"allProducts\s*=\s*(\[[\s\S]*?\]);", body)
    all_products = json.loads(pm.group(1)) if pm else []
    # Index by code for fast lookup
    by_code = {}
    for p in all_products:
        by_code[p["code"]] = p
        # Also index by name_only if code has variants
        label_key = p.get("name_only", "")
        if label_key and label_key != p["code"]:
            by_code.setdefault(label_key, p)
    return csrf, all_products, by_code


def resolve_customer(invoice, base_url, phpsessid):
    """Resolve customer ID from invoice data.

    Priority:
    1. invoice['customer']['id'] — use verbatim, cache it
    2. Customer cache (local file) — auto-resolve known names
    3. Search autocomplete, pick first Grosir candidate — auto-cache
    4. If ambiguous, raise ValueError with candidates for user to pick

    Returns dict with at least {'id': ..., 'value': ...} or raises ValueError.
    """
    cust = invoice.get("customer", {})
    if isinstance(cust, dict) and cust.get("id"):
        # Cache it for future lookups
        name = cust.get("name")
        if name:
            cache_customer_id(name, cust["id"])
        return {"id": cust["id"], "value": cust.get("name", str(cust["id"]))}

    name = cust.get("name") if isinstance(cust, dict) else cust
    if not name:
        raise ValueError("customer.name missing in invoice — cannot resolve")

    # Check local cache first
    cached_id = lookup_customer_id(name)
    if cached_id:
        return {"id": cached_id, "value": name}

    candidates = search_customers(base_url, phpsessid, name.split()[0] if " " in name else name)
    if not candidates:
        raise ValueError(f"No customer found for '{name}' — create in /admin/customers.php first")

    # Grosir first
    grosir = [c for c in candidates if c.get("type") == "Grosir"]
    if len(grosir) == 1:
        cache_customer_id(name, grosir[0]["id"])
        return {"id": grosir[0]["id"], "value": grosir[0]["value"]}
    elif len(grosir) > 1:
        # Exact name match first
        exact = [c for c in grosir if c.get("value", "").lower() == name.lower()]
        if exact:
            cache_customer_id(name, exact[0]["id"])
            return {"id": exact[0]["id"], "value": exact[0]["value"]}
        raise ValueError(
            f"Multiple Grosir candidates for '{name}': "
            + json.dumps([{"id": c["id"], "name": c["value"]} for c in grosir])
        )

    # No Grosir — surface all candidates
    raise ValueError(
        f"No Grosir customer for '{name}'. Candidates: "
        + json.dumps([{"id": c["id"], "name": c["value"], "type": c.get("type")} for c in candidates])
    )


def filter_tagihan_items(items):
    """Remove items that are pending bills (tagihan nota), not actual products.

    Kata kunci di product_code atau product_name: TAGIHAN, ITAGIHAN, PIUTANG.
    Sales udah terjadi, tagihan gak perlu diproses ulang.
    """
    keywords = ["TAGIHAN", "ITAGIHAN", "PIUTANG"]
    filtered = []
    skipped = 0
    for it in items:
        code = (it.get("product_code") or it.get("code") or "").upper()
        name = (it.get("product_name") or it.get("name") or "").upper()
        if any(kw in code or kw in name for kw in keywords):
            skipped += 1
            continue
        filtered.append(it)
    if skipped:
        print(f"  ⚠️ Skipped {skipped} tagihan nota item(s)")
    return filtered


def resolve_products(items, products_by_code, code_map=None):
    """Match invoice items to products_by_code dict.

    Returns list of {'code': ..., 'product': ..., 'qty': ..., 'price': ...}
    Raises KeyError if a code can't be resolved — ASK USER for product ID, don't guess.
    """
    code_map = code_map or {}
    resolved = []
    for it in items:
        code = it.get("product_code") or it.get("code") or ""
        # Apply code-map (supplier code → admin code)
        mapped = code_map.get(code, code)
        if mapped not in products_by_code:
            # Don't guess — ask user for the admin product ID
            similar = [k for k in sorted(products_by_code.keys())
                       if code.replace("-","") in k.replace("-","")
                       or k.replace("-","") in code.replace("-","")][:8]
            raise KeyError(
                f"Product code '{code}' (mapped: '{mapped}') not found in admin.\n"
                f"Please provide the correct admin product code or product ID.\n"
                f"Similar codes: {similar if similar else '(none)'}"
            )
        prod = products_by_code[mapped]
        resolved.append({
            "code": code,
            "mapped_code": mapped,
            "product": prod,
            "qty": int(it.get("qty") or it.get("quantity") or 1),
            "price": int(it.get("unit_price") or it.get("price") or prod.get("price_wholesale", 0)),
            "name": it.get("product_name") or it.get("name") or prod.get("name_only", prod["code"]),
        })
    return resolved


# ── Cashback extraction ──

def _extract_cashback(invoice, items_subtotal=None):
    """Extract total cashback amount from invoice JSON.

    Checks several possible locations (in order):
    1. summary.cashback
    2. cashbacks[] array (sum of amounts)
    3. subtotal vs grand_total difference (if grand_total < subtotal)

    Returns int (0 if none found).
    """
    # 1. summary.cashback
    cashback = invoice.get("summary", {}).get("cashback")
    if cashback is not None:
        return int(cashback)

    # 2. cashbacks[] array (Variant B)
    cashbacks = invoice.get("cashbacks", [])
    if cashbacks:
        return sum(int(cb.get("amount", 0)) for cb in cashbacks)

    # 3. subtotal vs grand_total / total difference
    summary = invoice.get("summary", {})
    subtotal = summary.get("subtotal") or invoice.get("subtotal")
    grand = (summary.get("grand_total") or summary.get("total_amount")
             or invoice.get("total"))
    if subtotal and grand:
        diff = int(subtotal) - int(grand)
        if diff > 0:
            return diff

    # 4. items_sum vs grand_total (only if caller provided items_subtotal)
    if items_subtotal is not None:
        grand = (invoice.get("summary", {}).get("grand_total")
                 or invoice.get("summary", {}).get("total_amount")
                 or invoice.get("total"))
        if grand:
            diff = items_subtotal - int(grand)
            if diff > 0:
                return diff

    return 0


# ── Expense POST (cashback as Biaya Marketing) ──

def post_expense(phpsessid, base_url, expense_date, amount, description,
                  category_id="13", payment_source="Bank Transfer",
                  vendor_name="", branch_name="Kiriman Luar Kota",
                  tax_type="None", csrf=None):
    """Record a marketing expense (cashback) at /admin/expenses/expense_save.php.

    If csrf is None, auto-harvests from expense_new.php (same session).
    Returns {'expense_id': int, 'status': str} or raises RuntimeError.

    category_id=13 = Biaya Marketing (auto-approved, no limit).
    """
    if not csrf:
        url = f"{base_url}/admin/expenses/expense_new.php"
        resp = _get(url, phpsessid=phpsessid, referer=url)
        body = resp.read().decode("utf-8", errors="replace")
        m = re.search(r'name="csrf_token"\s+value="([^"]+)"', body)
        if not m:
            raise RuntimeError("CSRF not found on expense_new.php — session may be expired")
        csrf = m.group(1)

    payload = {
        "csrf_token": csrf,
        "expense_date": expense_date,
        "category_id": str(category_id),
        "payment_source": payment_source,
        "amount": str(int(amount)),
        "description": str(description)[:500],
        "vendor_name": str(vendor_name)[:200],
        "branch_name": branch_name,
        "tax_type": tax_type,
    }

    url = f"{base_url}/admin/expenses/expense_save.php"
    data = urllib.parse.urlencode(payload).encode()
    req = urllib.request.Request(
        url, data=data, method="POST",
        headers={
            "User-Agent": USER_AGENT,
            "Cookie": f"PHPSESSID={phpsessid}",
            "Origin": base_url,
            "Content-Type": "application/x-www-form-urlencoded",
            "X-Requested-With": "XMLHttpRequest",
            "Referer": f"{base_url}/admin/expenses/expense_new.php",
        })

    class _NoRedirect(urllib.request.HTTPRedirectHandler):
        def http_error_302(self, req, fp, code, msg, hdrs): return fp
        http_error_301 = http_error_302; http_error_303 = http_error_302
        http_error_307 = http_error_302; http_error_308 = http_error_302

    ctx2 = _ctx()
    opener = urllib.request.build_opener(_NoRedirect, urllib.request.HTTPSHandler(context=ctx2))
    resp = opener.open(req, timeout=20)
    body_r = resp.read().decode("utf-8", errors="replace")

    loc = resp.headers.get("Location", "")
    m = re.search(r"id=(\d+)", loc)
    if m:
        status_m = re.search(r"status=([^&]+)", loc)
        return {
            "expense_id": int(m.group(1)),
            "status": status_m.group(1) if status_m else "approved",
        }

    if "alert-danger" in body_r:
        err = re.search(r'alert-danger[^>]*>([^<]+)', body_r)
        raise RuntimeError(f"Expense POST failed: {err.group(1).strip() if err else 'unknown'}")
    raise RuntimeError(
        f"Expense POST returned HTTP {resp.status}. "
        f"Location={loc!r} Body[:200]={body_r[:200]!r}"
    )


# ── Sale payload builder ──

def harvest_csrf(base_url, phpsessid, branch):
    url = f"{base_url}/admin/sale_custom_wholesale.php?branch={urllib.parse.quote(branch)}"
    req = urllib.request.Request(url, headers={
        "Cookie": f"PHPSESSID={phpsessid}",
        "User-Agent": USER_AGENT,
    })
    body = urllib.request.urlopen(req, timeout=20, context=_ctx()).read().decode("utf-8", errors="replace")
    m = re.search(r'name="csrf_token"\s+value="([^"]+)"', body)
    if not m:
        raise RuntimeError("csrf_token not found in form page — session may have expired")
    return m.group(1)


def build_payload(invoice, products_by_code, csrf, branch="Kiriman Luar Kota",
                  cashback_mode="expense"):
    """Build the form payload for sale_save.php.

    cashback_mode:
      'expense' (default) — items at FULL price, grand_total = items_subtotal.
                             Cashback is NOT absorbed — caller handles via post_expense().
      'absorb' (legacy) — cashback absorbed into item prices so items_sum == grand_total.
    """
    items_in = invoice["items"]
    items_in = filter_tagihan_items(items_in)
    items = []
    for it in items_in:
        if "id" in it:
            items.append({
                "id": str(it["id"]),
                "name": it.get("product_name") or it.get("name") or str(it["id"]),
                "price": int(it.get("unit_price") or it.get("price") or 0),
                "base_price": int(it.get("unit_price") or it.get("price") or 0),
                "quantity": int(it.get("qty") or it.get("quantity") or 1),
                "price_type": "CustomGrosir",
            })
            continue
        code = it.get("product_code") or it.get("code")
        if code not in products_by_code:
            raise KeyError(
                f"product_code {code!r} not resolved. "
                f"Run product resolution / code-map first; known codes: "
                f"{sorted(products_by_code.keys())[:5]}…"
            )
        prod = products_by_code[code]
        price = int(it.get("unit_price") or it.get("price") or prod["price_wholesale"])
        qty = int(it.get("qty") or it.get("quantity") or 1)
        items.append({
            "id": str(prod["id"]),
            "name": prod.get("name") or it.get("product_name") or code,
            "price": price,
            "base_price": price,
            "quantity": qty,
            "price_type": "CustomGrosir",
        })

    items_subtotal = sum(i["price"] * i["quantity"] for i in items)
    cashback_amount = _extract_cashback(invoice, items_subtotal)

    if cashback_mode == "expense":
        # Full price — no absorption. grand = items_subtotal.
        grand = items_subtotal
        delta = 0
    else:
        # Legacy: absorb cashback into items
        grand = int(invoice.get("summary", {}).get("grand_total")
                    or invoice.get("summary", {}).get("total_amount")
                    or items_subtotal)
        delta = grand - items_subtotal

    # Per user preference: NO auto-generated global_adjustments.
    global_adjustments = list(invoice.get("global_adjustments") or [])

    inv = invoice.get("invoice", {})
    inv_number = inv.get("invoice_number") or invoice.get("invoice_number") or ""
    customer = invoice.get("customer", {})
    cust_name = customer.get("name") if isinstance(customer, dict) else customer
    cust_id = customer.get("id") if isinstance(customer, dict) else None
    if not cust_id:
        raise ValueError(
            "customer.id missing. Resolve customer (auto-pick Grosir, or user-supplied) "
            "and inject into invoice['customer']['id'] before calling post_sale()."
        )
    if not cust_name or not str(cust_name).strip():
        raise ValueError(
            "customer.name is EMPTY. Refusing to post a sale with blank customer name. "
            "Resolve the customer (resolve_customer / cache) so invoice['customer'] has a "
            "non-empty 'name', or ask the user for the correct customer before posting. "
            "Never post with a None/empty Pelanggan."
        )

    # Determine payment status from due_date
    due_date = inv.get("due_date") or invoice.get("due_date")
    is_tempo = bool(due_date)

    payments = invoice.get("payments")
    if not payments:
        if is_tempo:
            payments = [{
                "method": invoice.get("payment", {}).get("method", "Transfer"),
                "amount": 0,
                "notes": f"Invoice {inv_number}" if inv_number else "",
            }]
        else:
            payments = [{
                "method": invoice.get("payment", {}).get("method", "Transfer"),
                "amount": grand,
                "notes": f"Invoice {inv_number}" if inv_number else "",
            }]

    payload = {
        "csrf_token": csrf,
        "price_type": "CustomGrosir",
        "sale_type": "Grosir",
        "branch": branch,
        "branch_name": branch,
        "customer_id": str(cust_id),
        "customer_name": cust_name,
        "custom_sale_date": inv.get("invoice_date") or invoice.get("invoice_date") or invoice.get("date") or "",
        "items_json": json.dumps(items),
        "payment_method": payments[0].get("method", "Transfer"),
        "payment_status": "Tempo" if is_tempo else "Lunas",
        "payment_status_radio": "Tempo" if is_tempo else "Lunas",
        "payments": json.dumps(payments),
        "global_adjustments": json.dumps(global_adjustments),
        "excess_handling": "cash",
        "excessHandling": "cash",
        "adjType": "percent",
        "priceMode": "custom",
    }
    if is_tempo:
        payload["due_date"] = due_date

    return payload, items_subtotal, delta, global_adjustments, payments, is_tempo, cashback_amount


def post_sale(phpsessid, invoice, products_by_code, branch="Kiriman Luar Kota",
              csrf=None, base_url="https://mjmbattery.com",
              cashback_mode="expense", post_expense_after=False):
    """Post a sale to sale_save.php.

    Returns dict with sale result, cashback info, and optionally expense_id.
    """
    csrf = csrf or harvest_csrf(base_url, phpsessid, branch)
    payload, items_subtotal, delta, global_adjustments, payments, is_tempo, cashback_amount = \
        build_payload(invoice, products_by_code, csrf, branch, cashback_mode)

    data = urllib.parse.urlencode(payload).encode()
    url = f"{base_url}/admin/sale_save.php"
    req = urllib.request.Request(
        url, data=data, method="POST",
        headers={
            "Cookie": f"PHPSESSID={phpsessid}",
            "Content-Type": "application/x-www-form-urlencoded",
            "Referer": f"{base_url}/admin/sale_custom_wholesale.php?branch={urllib.parse.quote(branch)}",
            "Origin": base_url,
            "X-Requested-With": "XMLHttpRequest",
            "User-Agent": USER_AGENT,
        }
    )

    class _NoRedirect(urllib.request.HTTPRedirectHandler):
        def http_error_302(self, req, fp, code, msg, hdrs):
            return fp  # return raw response instead of raising
        http_error_301 = http_error_302
        http_error_303 = http_error_302
        http_error_307 = http_error_302
        http_error_308 = http_error_302

    ctx2 = _ctx()
    opener = urllib.request.build_opener(_NoRedirect, urllib.request.HTTPSHandler(context=ctx2))
    resp = opener.open(req, timeout=30)
    body = resp.read().decode("utf-8", errors="replace")

    # Success: redirect with Location -> sales.php?status=success&invoice=OUT-...&id=...
    loc = resp.headers.get("Location", "")
    m = re.search(r"invoice=([^&]+)", loc)
    sale_id_m = re.search(r"id=(\d+)", loc)
    if m and sale_id_m:
        result = {
            "sale_id": sale_id_m.group(1),
            "server_invoice": m.group(1),
            "items_subtotal": items_subtotal,
            "delta": delta,
            "payment_status": "Tempo" if is_tempo else "Lunas",
            "global_adjustments": global_adjustments,
            "payments": payments,
            "cashback_amount": cashback_amount,
            "expense_id": None,
            "request_url": loc,
        }

        # Auto-post expense if requested and cashback exists
        if post_expense_after and cashback_amount and cashback_mode == "expense":
            inv = invoice.get("invoice", {})
            inv_number = inv.get("invoice_number") or invoice.get("invoice_number") or ""
            cust = invoice.get("customer", {})
            cust_name = cust.get("name") if isinstance(cust, dict) else str(cust)
            sale_date = inv.get("invoice_date") or invoice.get("date") or ""

            try:
                exp = post_expense(
                    phpsessid=phpsessid,
                    base_url=base_url,
                    expense_date=sale_date,
                    amount=cashback_amount,
                    description=f"Cashback penjualan {cust_name} - {inv_number}",
                    vendor_name=cust_name,
                )
                result["expense_id"] = exp["expense_id"]
                result["expense_status"] = exp["status"]
            except RuntimeError as e:
                result["expense_error"] = str(e)
                result["expense_id"] = None

        return result

    # Failure: check body for error
    if "alert-danger" in body:
        err = re.search(r'alert-danger[^>]*>([^<]+)', body)
        err_msg = err.group(1).strip() if err else "unknown error (alert-danger)"
        raise RuntimeError(f"Sale POST failed: {err_msg}\nBody: {body[:500]}")
    if "CSRF token" in body:
        raise RuntimeError("CSRF token invalid — re-harvest from the page")
    if "Stock tidak cukup" in body:
        raise RuntimeError("Stock tidak cukup — was a real branch used instead of Kiriman Luar Kota?")
    if resp.status == 403:
        raise RuntimeError("HTTP 403 — missing Origin header or session expired")

    raise RuntimeError(
        f"Sale POST returned HTTP {resp.status}. Location={loc!r} "
        f"Body[:300]={body[:300]!r}"
    )


# ── CLI ──

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="MJM Wholesale — browserless sale poster")
    sub = p.add_subparsers(dest="cmd", required=True)

    # login
    lp = sub.add_parser("login", help="login and print PHPSESSID")
    lp.add_argument("--username")
    lp.add_argument("--password")
    lp.add_argument("--base-url", default="https://mjmbattery.com")

    # search customers
    sc = sub.add_parser("search", help="search customers")
    sc.add_argument("phpsessid")
    sc.add_argument("query")
    sc.add_argument("--base-url", default="https://mjmbattery.com")

    # post sale (full flow)
    pp = sub.add_parser("post", help="post a sale (reads JSON from stdin or file)")
    pp.add_argument("--phpsessid", help="session id; if omitted, auto-login")
    pp.add_argument("--branch", default="Kiriman Luar Kota")
    pp.add_argument("--csrf", help="optional pre-harvested csrf token")
    pp.add_argument("--json", help="path to invoice JSON file (default: stdin)")
    pp.add_argument("--code-map", help="path to code-map JSON {supplier_code: admin_code}")
    pp.add_argument("--no-idempotency", action="store_true",
                    help="skip idempotency check (use for retry)")
    pp.add_argument("--expense", action="store_true",
                    help="auto-post cashback as Biaya Marketing expense after sale")
    pp.add_argument("--cashback-mode", default="expense", choices=["expense", "absorb"],
                    help="'expense' (default): full price, cashback → expense. "
                         "'absorb': old behavior, cashback absorbed into items.")

    # expense subcommand (standalone)
    ep = sub.add_parser("expense", help="post a single expense entry (for manual cashback)")
    ep.add_argument("--phpsessid", help="session id; if omitted, auto-login")
    ep.add_argument("--date", required=True, help="expense date YYYY-MM-DD")
    ep.add_argument("--amount", required=True, type=int, help="amount in rupiah")
    ep.add_argument("--description", required=True, help="description")
    ep.add_argument("--vendor", default="", help="vendor/penerima name")
    ep.add_argument("--branch", default="Kiriman Luar Kota")
    ep.add_argument("--category", default="13", help="category_id (default: 13 = Biaya Marketing)")
    ep.add_argument("--source", default="Bank Transfer", choices=["Cash", "Bank Transfer"],
                    help="payment source")

    args = p.parse_args()

    if args.cmd == "login":
        sid = login(args.base_url, args.username, args.password)
        print(sid)

    elif args.cmd == "search":
        candidates = search_customers(args.base_url, args.phpsessid, args.query)
        print(json.dumps(candidates, indent=2, ensure_ascii=False))

    elif args.cmd == "expense":
        sid = args.phpsessid or login()
        base_url = "https://mjmbattery.com"
        result = post_expense(
            phpsessid=sid,
            base_url=base_url,
            expense_date=args.date,
            amount=args.amount,
            description=args.description,
            vendor_name=args.vendor,
            branch_name=args.branch,
            category_id=args.category,
            payment_source=args.source,
        )
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif args.cmd == "post":
        sid = args.phpsessid or login()
        base_url = "https://mjmbattery.com"

        # Read invoice JSON
        if args.json:
            with open(args.json) as f:
                invoice = json.load(f)
        else:
            invoice = json.load(sys.stdin)
        # Auto-filter tagihan nota items
        invoice.setdefault("items", [])
        invoice["items"] = filter_tagihan_items(invoice["items"])

        # Code map
        code_map = {}
        if args.code_map:
            with open(args.code_map) as f:
                code_map = json.load(f)

        # Get page data
        csrf, all_products, by_code = get_page_data(base_url, sid, args.branch)

        # Resolve customer
        customer = resolve_customer(invoice, base_url, sid)
        invoice.setdefault("customer", {})
        if isinstance(invoice["customer"], dict):
            invoice["customer"]["id"] = customer["id"]
            invoice["customer"]["name"] = customer["value"]
        else:
            invoice["customer"] = {"name": customer["value"], "id": customer["id"]}

        # Resolve products
        for item in invoice.get("items", []):
            if item.get("product_code") == "S35":
                item["product_code"] = "SEKEN NS40Z"
                code_map["S35"] = "SEKEN NS40Z"
            elif item.get("product_code") == "S60":
                item["product_code"] = "SEKEN N50Z"
                code_map["S60"] = "SEKEN N50Z"
        resolved = resolve_products(invoice.get("items", []), by_code, code_map)
        # Convert to products_by_code dict for post_sale()
        products_by_code = {}
        for r in resolved:
            prod = r["product"]
            products_by_code[r["mapped_code"]] = prod
            if r["code"] != r["mapped_code"]:
                products_by_code[r["code"]] = prod
        # Ensure items have 'id' field for build_payload
        for item, r in zip(invoice.get("items", []), resolved):
            item["id"] = r["product"]["id"]
            item["unit_price"] = item.get("unit_price") or item.get("price") or r["price"]
            item["qty"] = item.get("qty") or item.get("quantity") or r["qty"]
            item["product_code"] = r["mapped_code"]

        # Idempotency check
        if not args.no_idempotency:
            inv_num = invoice.get("invoice", {}).get("invoice_number") or invoice.get("invoice_number", "")
            if inv_num:
                sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
                from idempotency_check import check
                dup = check(inv_num)
                if dup:
                    print(f"DUPLICATE: {inv_num} → {dup.get('server_invoice','?')} id={dup.get('sale_id','?')}")
                    sys.exit(1)

        # Post sale (with optional expense)
        result = post_sale(
            sid, invoice, products_by_code,
            branch=args.branch, csrf=csrf, base_url=base_url,
            cashback_mode=args.cashback_mode, post_expense_after=args.expense,
        )

        # Record idempotency
        if not args.no_idempotency:
            inv_num = invoice.get("invoice", {}).get("invoice_number") or invoice.get("invoice_number", "")
            if inv_num:
                sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
                from idempotency_check import append as idem_append
                idem_append({
                    "user_invoice": inv_num,
                    "customer_name": customer["value"],
                    "grand_total": int(invoice.get("summary", {}).get("grand_total", 0)),
                    "server_invoice": result["server_invoice"],
                    "sale_id": result["sale_id"],
                })

        print(json.dumps(result, indent=2, ensure_ascii=False))
