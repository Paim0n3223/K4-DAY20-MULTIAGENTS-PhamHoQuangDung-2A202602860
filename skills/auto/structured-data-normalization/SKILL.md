---
name: structured-data-normalization
description: Use when cleaning tabular data, parsing multiple timestamp/format variants, and exporting JSON/CSV reports.
---
1. Inspect input files to account for duplicate rows, missing or sentinel values (e.g., `-999`), and inconsistent casing in categorical fields.
2. Standardize dates across multiple formats and convert all timestamps explicitly to UTC in ISO-8601 format (`YYYY-MM-DDTHH:MM:SSZ`).
3. Convert monetary values to integer cents (multiplying float amounts by 100 and rounding) when required by schema rules.
4. Populate metadata objects precisely, ensuring keys like source filename, input row counts, and processed row counts match actual data.
