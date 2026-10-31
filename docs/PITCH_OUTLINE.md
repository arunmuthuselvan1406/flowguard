# Pitch deck outline (export as PDF or PPT, 8 slides)

1. **Title:** FlowGuard, operations intelligence on Exasol. Track 03. Solo participant.
2. **Problem:** the four pains (downtime, parts, quality, supplier data) and who has them. Use `PROBLEM_STATEMENT.md`.
3. **Insight:** all four come from late, scattered, messy data, so fix it in one analytics layer.
4. **Solution:** the four modules, one question each (table from the README).
5. **Architecture:** sources → pyexasol → Exasol (raw, core, SQL views) → FastAPI → dashboard. Stress: compute stays in the database.
6. **Why Exasol:** window and join heavy analytics in SQL, event vs arrival time, one platform for all four modules. Show the RootCause SQL.
7. **Demo screenshots:** one per module, with the headline result (for example "Bearing temperature +4.8σ, lot L-4471").
8. **Impact and next steps:** hours saved, avoided transfers, earlier defect catch; next: real connectors, an LLM for supplier mapping, alerting.
