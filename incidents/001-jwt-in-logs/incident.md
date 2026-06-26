# JWT leaked into application logs

A bearer token was passed directly into a logger call, writing the raw JWT to
the centralized log store, where it was retained for 90 days and broadly
readable. Tokens in logs are credential exposure. The fix is to never log the
token value; log a non-sensitive identifier or nothing.
