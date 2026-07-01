---
type: coding-guide
source: Engineering Handbook, section 4.3 "Logging"
---

# Logging sensitive data

Application logs are shipped to our central aggregator and retained for 90 days. They are visible to on-call engineers, the platform team, and anyone with read access to the observability stack. Treat every log line as if it will be read by someone outside your team, because it will be.

Never write secrets or personal data into a log. This includes authentication tokens, session identifiers, API keys, passwords, full card numbers, and anything that identifies a person such as an email, a phone number, or a national ID. The most common way this goes wrong is interpolating a variable straight into a log message while debugging and forgetting to remove it before merge. A line like `log.info(f"auth request token={token}")` looks harmless in review and leaks a live credential the moment it runs in production.

If you need to confirm a token is present, log its presence, not its value. Log that authentication was attempted, or log a short non-reversible fingerprint, never the token itself. The same rule applies to structured logging. Passing a secret as a field value is no safer than putting it in the message string.

We had a token reach the aggregator this way once and had to rotate credentials across three services. The rule is absolute: no secret and no personal identifier is ever passed to a logging call, in the message or in any argument.
