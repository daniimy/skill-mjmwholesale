# Operational Notes

## Idempotency State File
Path: `~/.hermes/state/mjm_processed_invoices.json`
Key: `user_invoice` (invoice number as given by customer).
Do not rely on server search to detect duplicates; it does not index user-provided invoice numbers.

## Skill Revision Workflow
If the skill logic, payload JSON, or product mapping changes:
1. Instruct user to clear the state file (or prune entries for the affected invoices).
2. Then re-run the batch.

## Customer Name Consistency
After `idempotency_check.check()`, compare `state_record.customer_name` (or `customer`) against the current invoice's customer. Mismatches (e.g. "KARISMA AKI" vs "KELVIN AKI", "IBRAHIM ACCU" vs "ISTANA AKI") indicate the previous run resolved a different name variant — likely a fuzzy match drift. Surface this to the user before re-processing so they can confirm or correct the customer identity.

## Grand Total Consistency
After `idempotency_check.check()`, also compare `state_record.grand_total` against the current invoice's `summary.grand_total`. Mismatches indicate the previous run used a different delta/adjustment strategy (e.g. structural omset removal vs. direct supplier total). Surface discrepancies to the user before re-processing so they can confirm whether to proceed with the current invoice values or re-use the prior computation.

## Combine Rule (same invoice# = 1 sale)
When the user provides multiple JSON objects sharing the same `invoice_no` AND customer name, merge all items into one sale POST. Carry forward any part-level delta (grand_total > items_subtotal) into the combined grand_total.

## No-Rounding Preference
User explicitly said "aku tidak mau ada pembulatan ya harus apa adanya" — no artificial "Penyesuaian pembulatan" adjustments. Small deltas (≤2 rupiah from harga×qty ≠ stated line_total) are ignored — use invoice grand_total as payment amount without global_adjustments. Structural deltas from omset_details (50k-125k) are legitimate and keep their adjustments.

## Anti-Forcing Rule
User said "jangan sok tau" — when data doesn't match (wrong product ID, customer mismatch, price gap), STOP and search/ask. Do NOT force-post with wrong IDs hoping it will work. If validation fails, surface the mismatch to the user and let them decide. User handles production cleanup manually (deleting wrong sales from admin panel).

## Code-Map Strictness
Treat code_map as the source of truth. If a product code isn't in code_map and not found in admin by_code → STOP, ask user for product ID. Update code_map when user provides the correct admin code.
