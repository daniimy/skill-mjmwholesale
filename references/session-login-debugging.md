# Session/login debugging

Observed workflow:

1. Direct POST to `/admin/login_process.php` without a fresh token returns HTTP 403 with body `CSRF token tidak valid. Refresh halaman dan coba lagi.`
2. GET `/admin/login.php` yields a hidden `csrf_token` and a `PHPSESSID` cookie.
3. POST username, password, and token using the same cookie jar returns HTTP 302 to `index.php`; credentials are valid.
4. A later request that omits the returned PHPSESSID is unauthenticated. The server may still return HTTP 200, but the body is the login page and product extraction returns `allProducts=[]`.

Verification gates before posting:

- Login response: expected 302 redirect to `index.php`.
- Sale form response: must not contain `Login Admin` or the login form.
- Product catalogue: `allProducts` must parse and contain at least one product.
- If any gate fails, stop before customer/product resolution or POST; re-login and propagate the same session ID through all HTTP helpers.

Implementation note: `login()` may use a private cookie jar for GET+POST, but downstream helpers receive the resulting PHPSESSID explicitly and must send `Cookie: PHPSESSID=<id>` on every authenticated request.