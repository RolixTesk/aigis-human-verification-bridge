from __future__ import annotations

import asyncio
import secrets
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

from aigis_bridge.protocol import AigisChallenge


@dataclass(slots=True)
class ChallengeTicket:
    challenge: AigisChallenge = field(repr=False)
    purpose: str
    context_digest: str = field(repr=False)
    round_number: int
    expires_at: datetime


class EphemeralChallengeStore:
    """Bound, bounded, in-memory challenge storage with one-time consumption."""

    def __init__(self, *, ttl: timedelta = timedelta(minutes=10), maximum: int = 20) -> None:
        self._ttl = ttl
        self._maximum = maximum
        self._items: dict[str, ChallengeTicket] = {}
        self._lock = asyncio.Lock()

    async def create(
        self,
        *,
        challenge: AigisChallenge,
        purpose: str,
        context_digest: str,
        round_number: int = 1,
    ) -> tuple[str, datetime]:
        async with self._lock:
            self._purge_locked()
            while len(self._items) >= self._maximum:
                self._items.pop(next(iter(self._items)))
            identifier = secrets.token_urlsafe(24)
            expires_at = datetime.now(timezone.utc) + self._ttl
            self._items[identifier] = ChallengeTicket(challenge, purpose, context_digest, round_number, expires_at)
            return identifier, expires_at

    async def consume(self, identifier: str, *, purpose: str, context_digest: str) -> ChallengeTicket:
        async with self._lock:
            self._purge_locked()
            value = self._items.get(identifier)
            if value is None or value.purpose != purpose or value.context_digest != context_digest:
                raise KeyError(identifier)
            del self._items[identifier]
            return value

    async def discard(self, identifier: str) -> None:
        async with self._lock:
            self._items.pop(identifier, None)

    async def clear(self) -> None:
        async with self._lock:
            self._items.clear()

    def _purge_locked(self) -> None:
        now = datetime.now(timezone.utc)
        for identifier in [key for key, value in self._items.items() if value.expires_at <= now]:
            del self._items[identifier]
