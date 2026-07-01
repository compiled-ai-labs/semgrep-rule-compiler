---
type: incident
source: JIRA INC-1108
severity: SEV-2
---

# INC-1108: payments service unresponsive during upstream slowdown

## Summary

On 3 March the payments service stopped responding to health checks for roughly 40 minutes. Pods were not crashing but were not serving traffic. The trigger was a slowdown at the third-party payment provider, not a full outage. Their API was responding, just slowly.

## What happened

The service makes a synchronous call to the provider on the checkout path. That call was written as a plain `requests.get(provider_url)` with no timeout set. When the provider's latency climbed from about 200ms to 30 seconds and beyond, each request held its worker thread for the full duration. The thread pool drained, new requests queued, and the pod stopped answering. Kubernetes saw healthy pods because the liveness probe hit a different path that still worked, so it did not restart them.

## Root cause

Any outbound HTTP call without an explicit timeout will wait indefinitely by default. Under normal conditions this is invisible because responses are fast. Under partial degradation it converts a slow dependency into a full outage of the calling service.

## Prevention

Every outbound HTTP call must set an explicit timeout. This applies to all verbs, get, post, put, delete, and to any call made through the requests library or a thin wrapper around it. A call that omits the timeout argument is a defect regardless of whether it has caused a problem yet.
