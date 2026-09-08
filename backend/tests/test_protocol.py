from __future__ import annotations

import base64
import json

import pytest

from aigis_bridge.protocol import HumanVerificationError, encode_aigis_proof, parse_aigis_challenge


def envelope(data: dict[str, object]) -> str:
    return json.dumps({"session_id": "private-session", "data": json.dumps(data)})


def test_parse_and_encode_gt3_without_repr_leak() -> None:
    challenge = parse_aigis_challenge(envelope({"gt": "gt-id", "challenge": "challenge", "success": 1, "new_captcha": 1}))
    encoded = encode_aigis_proof(challenge, "gt3", {
        "geetest_challenge": "browser-challenge",
        "geetest_validate": "validate",
        "geetest_seccode": "seccode",
    })
    prefix, payload = encoded.split(";", 1)

    assert challenge.version == "gt3"
    assert "private-session" not in repr(challenge)
    assert prefix == "private-session"
    assert json.loads(base64.b64decode(payload)) == {
        "geetest_challenge": "browser-challenge",
        "geetest_validate": "validate",
        "geetest_seccode": "seccode",
    }


def test_parse_and_encode_gt4() -> None:
    challenge = parse_aigis_challenge(envelope({"gt": "captcha-id", "risk_type": "slide"}))
    encoded = encode_aigis_proof(challenge, "gt4", {
        "lot_number": "lot",
        "captcha_output": "output",
        "pass_token": "pass",
        "gen_time": "123",
        "captcha_id": "captcha-id",
    })

    assert challenge.version == "gt4"
    assert challenge.user_info == '{"session_id":"private-session"}'
    assert encoded.startswith("private-session;")


@pytest.mark.parametrize("raw", [None, "", "[]", '{"session_id":"x","data":"bad"}'])
def test_bad_challenge_is_rejected(raw: str | None) -> None:
    with pytest.raises(HumanVerificationError):
        parse_aigis_challenge(raw)


def test_version_mismatch_and_extra_fields_are_rejected() -> None:
    challenge = parse_aigis_challenge(envelope({"gt": "captcha-id", "risk_type": "slide"}))
    with pytest.raises(HumanVerificationError):
        encode_aigis_proof(challenge, "gt3", {})
    with pytest.raises(HumanVerificationError):
        encode_aigis_proof(challenge, "gt4", {
            "lot_number": "lot",
            "captcha_output": "output",
            "pass_token": "pass",
            "gen_time": "123",
            "captcha_id": "captcha-id",
            "unexpected": "value",
        })
