from __future__ import annotations

from datetime import timedelta

import pytest

from aigis_bridge.protocol import AigisChallenge
from aigis_bridge.store import EphemeralChallengeStore


@pytest.mark.asyncio
async def test_store_binds_purpose_context_and_consumes_once() -> None:
    store = EphemeralChallengeStore()
    identifier, _ = await store.create(
        challenge=AigisChallenge("secret", "gt4", "captcha"),
        purpose="sms-request",
        context_digest="context",
    )

    with pytest.raises(KeyError):
        await store.consume(identifier, purpose="other", context_digest="context")
    ticket = await store.consume(identifier, purpose="sms-request", context_digest="context")
    assert ticket.round_number == 1
    assert "secret" not in repr(ticket)
    with pytest.raises(KeyError):
        await store.consume(identifier, purpose="sms-request", context_digest="context")


@pytest.mark.asyncio
async def test_expired_and_cancelled_challenges_are_closed() -> None:
    expired = EphemeralChallengeStore(ttl=timedelta(microseconds=-1))
    expired_id, _ = await expired.create(challenge=AigisChallenge("secret", "gt4", "captcha"), purpose="p", context_digest="c")
    with pytest.raises(KeyError):
        await expired.consume(expired_id, purpose="p", context_digest="c")

    store = EphemeralChallengeStore()
    cancelled_id, _ = await store.create(challenge=AigisChallenge("secret", "gt4", "captcha"), purpose="p", context_digest="c")
    await store.discard(cancelled_id)
    with pytest.raises(KeyError):
        await store.consume(cancelled_id, purpose="p", context_digest="c")
