# Outbound HTTP request without a timeout hung a worker

A `requests.get` call with no timeout blocked a worker thread indefinitely when
the upstream stalled, cascading into pool exhaustion and an outage. Every
outbound HTTP call must pass an explicit `timeout`. The fix is to add a
`timeout` keyword argument to the call.
