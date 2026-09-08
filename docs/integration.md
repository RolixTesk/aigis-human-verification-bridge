# Integration guide

## 1. Protocol boundary

The host application owns the upstream HTTP request. When that upstream reports a human-verification condition and
returns `x-rpc-aigis`, pass only that header to `parse_aigis_challenge`:

```python
from aigis_bridge import parse_aigis_challenge

challenge = parse_aigis_challenge(upstream_response.headers.get("x-rpc-aigis"))
```

Do not log the header or the resulting object. `AigisChallenge.session_id` is excluded from its representation, but
that is only a guardrail, not a substitute for log discipline.

## 2. Bind the challenge

Hash the host's operation context and store the challenge on the server:

```python
import hashlib
from aigis_bridge import EphemeralChallengeStore

store = EphemeralChallengeStore()
context_digest = hashlib.sha256(b"sms-request\0opaque-account-context\0opaque-device-context").hexdigest()
challenge_id, expires_at = await store.create(
    challenge=challenge,
    purpose="sms-request",
    context_digest=context_digest,
    round_number=1,
)
```

Return an opaque `challenge_id`, public GeeTest initialization fields, and `expires_at` to the authenticated browser.
GT4 requires the short-lived `user_info` produced by the challenge; the browser must never be allowed to choose the
server-side session used for final encoding.

## 3. Render the browser component

Copy these files into the host React application:

- `frontend/src/HumanVerificationModal.tsx`
- `frontend/src/loadSdk.ts`
- `frontend/src/types.ts`
- the `.human-verification-*`, `.verification-status`, and `.geetest-mount` CSS rules
- `frontend/public/vendor/geetest/` plus its byte-preserving `.gitattributes` rule

Render the modal only after the user has authorized the operation and the upstream has returned a challenge. On
success, POST the strict GT3 or GT4 result together with the host's opaque challenge ID. On cancel, call the host's
discard endpoint.

## 4. Consume and retry once

On the server, recompute the same purpose and context digest, consume the challenge, and encode the browser proof:

```python
from aigis_bridge import encode_aigis_proof

ticket = await store.consume(
    submitted_challenge_id,
    purpose="sms-request",
    context_digest=context_digest,
)
browser_fields = proof.model_dump(exclude={"version"}, exclude_none=True)
aigis_value = encode_aigis_proof(ticket.challenge, proof.version, browser_fields)

upstream_response = await upstream_client.post(
    original_url,
    headers={**original_headers, "x-rpc-aigis": aigis_value},
    content=original_body,
)
```

The Aigis value stays server-side. Retry only the original operation with the same business and device context. If
the upstream returns another challenge, create at most one explicitly bounded second round; after that, stop and ask
the user to restart later. Never fall back automatically to another login protocol.

## 5. Host responsibilities

This repository deliberately does not implement authentication, CSRF, rate limiting, mobile-number validation,
upstream error-code mapping, or durable storage. The host must provide those controls. Challenge and proof values are
short-lived verification material and should never be persisted.

The production build uses official GeeTest bootstrap scripts, whose runtime requests require an appropriate CSP.
Observe the exact domains used by the deployed GT3/GT4 scenario and allow the smallest required `script-src`,
`connect-src`, `img-src`, and `frame-src` set.
