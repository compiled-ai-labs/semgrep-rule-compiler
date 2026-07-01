---
type: incident
source: JIRA INC-0997
severity: SEV-1
---

# INC-0997: SQL injection in reporting endpoint

## Summary

A penetration test found that the reporting endpoint was vulnerable to SQL injection. A crafted value in the `region` query parameter let an attacker read rows from tables the endpoint should never touch. This was a SEV-1 because the affected database held customer records.

## What happened

The query was assembled by formatting user input directly into the SQL string. The offending code built the statement with an f-string, roughly `cursor.execute(f"SELECT * FROM sales WHERE region = '{region}'")`, and passed the result to the driver. Because `region` came straight from the request, an attacker could close the quote and append their own clause.

## Root cause

User-controlled input was placed into a SQL statement by string building instead of being passed as a bound parameter. The driver already supports parameterised queries. The second argument to `execute` exists precisely so that values never touch the SQL text. The f-string bypassed that mechanism entirely.

## Prevention

SQL statements must not be built by string formatting or concatenation. Use bound parameters: pass the SQL with placeholders and supply the values as the parameter argument. Any `execute` call whose SQL string is produced by an f-string, by `.format`, or by `+` concatenation is a defect, whether or not the value is currently reachable from input.
