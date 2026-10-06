---
name: strict-schema-and-sorting
description: Use when parsing unstructured logs or text streams into structured JSON outputs with strict sorting and schema requirements.
---
1. Review output schema specifications carefully to include all mandated top-level keys, version numbers, and metadata identifiers.
2. Normalize entity identifiers and service names according to domain formatting rules (e.g., lowercasing and replacing hyphens with underscores).
3. Sort output lists and nested records using multi-level sorting keys (e.g., primary service name, secondary UTC timestamp) in ascending order.
4. Validate generated JSON structures against target schemas before finishing tasks.
