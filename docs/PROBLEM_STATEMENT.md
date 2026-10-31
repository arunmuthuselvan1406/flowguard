# Problem statement

**Who has the problem:** operations and maintenance teams in discrete-manufacturing plants and fleets, typically running several sites.

**What goes wrong:**
1. **Unplanned downtime with no clear root cause.** Sensor data, maintenance logs and shift records live in different systems, so after a stoppage people argue about the cause instead of fixing it.
2. **Spare parts in the wrong place.** One site holds surplus bearings while another runs short, so a failure becomes a long stoppage.
3. **Quality problems found at the end of the line.** A defect that starts at one station is discovered several stations later, after more work has been wasted on it.
4. **Suppliers reporting in inconsistent formats.** Column names, date formats and currencies differ per supplier, so shipment data cannot be compared.

**Why it matters:** each problem has a direct cost (lost production hours, emergency freight, scrap and rework, manual spreadsheet cleanup),
and all four come from the same cause: operational data that arrives late, scattered and messy.

**Our approach:** keep raw data as it arrives (event time and arrival time), do all analysis as SQL inside Exasol,
and expose four small, explainable modules that each answer one operational question.
