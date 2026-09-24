# Implementation status — 24 September 2026

The nine stages were implemented in sequence as a local prototype. External integrations remain explicitly configurable rather than represented as completed financial actions.

| Stage | Delivered |
|---|---|
| 1. Accurate demonstration | Kintsugi branding, simulated-finance warnings, honest approval previews, revised README and cleared stale notebook outputs. |
| 2. Functional correctness | Literal search, moratorium-aware optimization, input validation, infeasible-target status, consistent baseline EMI, no artificial interest-rate increases. |
| 3. Data contracts | Numeric normalization, missing/range/ID checks, observed/generated field documentation, explicit missing-path errors and visible fallback modes. |
| 4. Persistence and roles | SQLite borrowers/loans/users/sessions, hashed passwords, expiring sessions, login lockout, borrower/underwriter authorization and UI-facing services. |
| 5. Workflow | Immutable versioned drafts, affordability review, approval/rejection decisions, exact-term consent, transactional/idempotent local activation and audit events. |
| 6. Communications | Durable email/SMS outbox, separate worker, timezone window, retries, crash leases, stable idempotency keys, simulated receipts and configurable HTTPS gateway adapter. |
| 7. Model evidence | Separate holdout evaluation, rules comparison, optional temporal/outcome evaluation, retrained model/scaler, hashes and dependency/feature metadata. |
| 8. Usability | Borrower handoff to the demo simulator, full terms comparison in the saved workflow, schedule downloads, empty/error states, mobile CSS, visible keyboard focus and reduced-motion support. |
| 9. Verification and distribution | Regression/UI/permissions/queue tests, dependency lock, package resources and installed launcher, protected Streamlit configuration, JSON worker logs, health command and CI build checks. |

## Verification

- 42 tests passed on Python 3.14.7 in the final regression run.
- The exact dependency lock resolved successfully with pip in an isolated dry run.
- Critical syntax/undefined-name checks and unused-import/local-variable checks passed.
- Git whitespace validation passed (only Windows line-ending notices).
- Source distribution and wheel built successfully. Installed wheel loaded the dataset, logo and trained model outside the source checkout.
- Browser checked at desktop and mobile widths. The mobile page had no horizontal overflow. Keyboard Space toggled the demo consent checkbox, enabled the preview button, and Tab focused that button with a visible outline.
- Streamlit UI tests exercised actual stored draft approval, borrower consent and local activation using isolated temporary databases.
- Delivery tests used in-memory fake gateways; no email/SMS was sent. Demo accounts remain simulation-only even when webhook mode is configured.

Build/test logs are under the ignored `build/` directory. Distribution artifacts are under ignored `dist/`.

## Integration boundaries and remaining work

1. **External delivery:** provide a real email/SMS gateway, credentials, verified contacts and durable idempotency support. Gateway acceptance is tracked; end-user delivery callbacks are not implemented.
2. **Real evaluation:** supply representative borrower snapshots and observed outcomes with an established horizon. Current statistics do not validate prediction of default or recovery benefit.
3. **Servicing reconciliation:** payment records are receipts, not a full accounting ledger. Repeated restructures after activation/receipts are blocked rather than guessing outstanding balances. Dated installment allocation, fees and delinquency calculations require a servicing integration.
4. **Production operations:** remote hosting, HTTPS termination, database backup policy, centralized identity/MFA, password recovery, and a production security/legal review remain deployment work. No production accounts or default credentials were created.
5. **Compatibility:** runtime minimum is now Python 3.12 to match the pinned scientific stack; CI is configured for 3.12–3.14. Only 3.14 was executed locally.
6. **Known warning:** joblib 1.5.3 emits NumPy 2.5 shape-assignment deprecation warnings when loading artifacts. Tests and inference pass; this dependency warning is documented rather than hidden.
7. **Accessibility:** mobile layout and basic keyboard behavior were verified, not a full screen-reader/WCAG audit.

The original `PROJECT_ANALYSIS.md` is retained as the pre-change audit.
