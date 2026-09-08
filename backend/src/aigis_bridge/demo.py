from __future__ import annotations

import hashlib
import json
import secrets
from pathlib import Path

from fastapi import FastAPI, HTTPException, Response, status
from fastapi.staticfiles import StaticFiles

from aigis_bridge.models import DemoChallengeRequest, HumanVerificationProof, ProofAccepted, PublicChallenge
from aigis_bridge.protocol import HumanVerificationError, encode_aigis_proof, parse_aigis_challenge
from aigis_bridge.store import EphemeralChallengeStore


DEMO_PURPOSE = "standalone-demo"
DEMO_CONTEXT = hashlib.sha256(b"standalone-demo-context").hexdigest()


def create_demo_app(*, store: EphemeralChallengeStore | None = None, mount_frontend: bool = True) -> FastAPI:
    app = FastAPI(title="Aigis human-verification bridge demo")
    challenge_store = store or EphemeralChallengeStore()
    app.state.challenge_store = challenge_store

    @app.get("/api/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/api/demo/challenges", response_model=PublicChallenge)
    async def create_challenge(body: DemoChallengeRequest) -> PublicChallenge:
        challenge = parse_aigis_challenge(_mock_aigis_header(body.version))
        identifier, expires_at = await challenge_store.create(
            challenge=challenge,
            purpose=DEMO_PURPOSE,
            context_digest=DEMO_CONTEXT,
        )
        return PublicChallenge(
            challenge_id=identifier,
            version=challenge.version,
            captcha_id=challenge.captcha_id,
            challenge=challenge.challenge,
            success=challenge.success,
            new_captcha=challenge.new_captcha,
            risk_type=challenge.risk_type,
            user_info=challenge.user_info,
            expires_at=expires_at,
        )

    @app.post("/api/demo/challenges/{challenge_id}/complete", response_model=ProofAccepted)
    async def complete_challenge(challenge_id: str, body: HumanVerificationProof) -> ProofAccepted:
        try:
            ticket = await challenge_store.consume(
                challenge_id,
                purpose=DEMO_PURPOSE,
                context_digest=DEMO_CONTEXT,
            )
            fields = body.model_dump(exclude={"version"}, exclude_none=True)
            encoded = encode_aigis_proof(ticket.challenge, body.version, fields)
        except (KeyError, HumanVerificationError) as exc:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Challenge expired, already used, or mismatched.",
            ) from exc
        return ProofAccepted(
            encoded_length=len(encoded),
            proof_sha256=hashlib.sha256(encoded.encode("utf-8")).hexdigest(),
        )

    @app.delete("/api/demo/challenges/{challenge_id}", status_code=status.HTTP_204_NO_CONTENT)
    async def cancel_challenge(challenge_id: str) -> Response:
        await challenge_store.discard(challenge_id)
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    frontend = Path(__file__).resolve().parents[3] / "frontend" / "dist"
    if mount_frontend and frontend.is_dir():
        app.mount("/", StaticFiles(directory=frontend, html=True), name="frontend")
    return app


def _mock_aigis_header(version: str) -> str:
    data: dict[str, object]
    if version == "gt3":
        data = {
            "gt": "standalone-demo-gt3",
            "challenge": "standalone-demo-challenge",
            "success": 1,
            "new_captcha": True,
        }
    else:
        data = {
            "gt": "standalone-demo-gt4",
            "risk_type": "slide",
            "success": 1,
            "use_v4": True,
        }
    return json.dumps(
        {"session_id": secrets.token_urlsafe(18), "mmt_type": 1, "data": json.dumps(data, separators=(",", ":"))},
        separators=(",", ":"),
    )


app = create_demo_app()
