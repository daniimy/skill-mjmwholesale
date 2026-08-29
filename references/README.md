# References for `mjm-battery-wholesale-sale`

Detailed knowledge extracted from the SKILL.md to keep it lean for triggering and decision flow.

- [`invoice-normalization.md`](invoice-normalization.md) — How to convert the user's invoice-shaped JSON into the form's expected shape, with a worked example. Load before Step 2 (Parse).
- [`invoice-json-schema.md`](invoice-json-schema.md) — Complete JSON schema spec for invoice data (supplier, customer, items, summary, signatures).
- [`extraction-prompt.md`](extraction-prompt.md) — Prompt template for extracting JSON from invoice images via vision_analyze. Give this to user when they send a photo of an invoice.
- [`prompt-for-external-ai.md`](prompt-for-external-ai.md) — Prompt for external AI tools (if using separate OCR pipeline).
- [`verified-page-state.md`](verified-page-state.md) — Form field reference, item/payment schemas, AJAX endpoints.
- [`direct-post-recipe.md`](direct-post-recipe.md) — Full annotated curl POST recipe for sale_save.php.
- [`cashback-handling.md`](cashback-handling.md) — How to absorb cashback/diskon into item prices instead of global_adjustments.
- [`product-code-map.md`](product-code-map.md) — Supplier invoice codes → admin panel allProducts[].code mapping.
- [`pitfalls.md`](pitfalls.md) — Production gotchas: ambiguous codes, customer fuzzy match, rounding, Origin header, session expiry, duplicate-submit.
- [`verified-runs.md`](verified-runs.md) — Every successful production POST with sale_ids for cross-reference.
- [`operational-notes.md`](operational-notes.md) — Idempotency state file path, skill revision workflow, user communication.
