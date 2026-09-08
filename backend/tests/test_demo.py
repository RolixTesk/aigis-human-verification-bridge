from __future__ import annotations

import httpx
import pytest

from aigis_bridge.demo import create_demo_app


@pytest.mark.asyncio
async def test_demo_gt4_completion_is_one_time_and_server_only() -> None:
    app = create_demo_app(mount_frontend=False)
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        created = await client.post("/api/demo/challenges", json={"version": "gt4"})
        challenge = created.json()
        proof = {
            "version": "gt4",
            "lot_number": "lot",
            "captcha_output": "output",
            "pass_token": "pass",
            "gen_time": "123",
            "captcha_id": challenge["captcha_id"],
        }
        accepted = await client.post(f"/api/demo/challenges/{challenge['challenge_id']}/complete", json=proof)
        replayed = await client.post(f"/api/demo/challenges/{challenge['challenge_id']}/complete", json=proof)

    assert created.status_code == 200
    assert accepted.status_code == 200
    assert accepted.json()["server_only"] is True
    assert "private" not in accepted.text
    assert replayed.status_code == 409


@pytest.mark.asyncio
async def test_demo_cancel_closes_challenge() -> None:
    app = create_demo_app(mount_frontend=False)
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        created = await client.post("/api/demo/challenges", json={"version": "gt3"})
        identifier = created.json()["challenge_id"]
        cancelled = await client.delete(f"/api/demo/challenges/{identifier}")
        closed = await client.post(f"/api/demo/challenges/{identifier}/complete", json={
            "version": "gt3",
            "geetest_challenge": "challenge",
            "geetest_validate": "validate",
            "geetest_seccode": "seccode",
        })

    assert cancelled.status_code == 204
    assert closed.status_code == 409
