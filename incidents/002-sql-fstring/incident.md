# SQL built with an f-string passed to execute

A query was assembled with an f-string interpolating a request parameter and
passed straight to `cursor.execute` — a classic SQL injection. The fix is a
parameterized query: pass the SQL with placeholders and the values as the
second argument to `execute`.
