# Archived Node.js Enforcement Prototype

This is the original temporary Node.js reference implementation of Revnara's enforcement logic, archived here (not deleted) as of Sprint 1's stack reset.

- `src/domain/capabilities.js` — canonical capability status / connector mode / risk tier enums.
- `src/enforcement/evaluateExternalAction.js` — the enforcement pipeline and approval-binding validation logic.
- `test/enforcement.test.js` — the test suite proving the above logic, including every approval-binding edge case.

**Why this exists:** this prototype is the working reference spec for `backend/app/policy_engine/`, `backend/app/risk_engine/`, and `backend/app/approvals/binding.py`, built in Sprint 10 of `docs/Revnara_Sprint_Development_Plan.md`. Sprint 10's task BE10.3 explicitly ports this file's logic to Python, and DQ10.1 ports `test/enforcement.test.js`'s test cases as the starting Python regression suite. Do not delete this directory until Sprint 10 is complete and its ported tests are passing.
