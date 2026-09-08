from __future__ import annotations

import base64
import json
from dataclasses import dataclass, field
from typing import Literal, Mapping


AigisVersion = Literal["gt3", "gt4"]
MAX_AIGIS_HEADER_BYTES = 32_768
MAX_AIGIS_VALUE_LENGTH = 16_384


class HumanVerificationError(ValueError):
    """The upstream Aigis challenge or browser proof is not usable."""


@dataclass(frozen=True, slots=True)
class AigisChallenge:
    session_id: str = field(repr=False)
    version: AigisVersion
    captcha_id: str
    challenge: str | None = None
    success: int | None = None
    new_captcha: bool | None = None
    risk_type: str | None = None

    @property
    def user_info(self) -> str | None:
        if self.version != "gt4":
            return None
        return json.dumps({"session_id": self.session_id}, separators=(",", ":"))


def parse_aigis_challenge(raw: str | None) -> AigisChallenge:
    if not raw or len(raw.encode("utf-8")) > MAX_AIGIS_HEADER_BYTES:
        raise HumanVerificationError("missing or oversized Aigis header")
    try:
        envelope = json.loads(raw)
    except (TypeError, ValueError, json.JSONDecodeError) as exc:
        raise HumanVerificationError("invalid Aigis envelope") from exc
    if not isinstance(envelope, dict):
        raise HumanVerificationError("invalid Aigis envelope")

    session_id = _required_string(envelope.get("session_id"), maximum=512)
    raw_data = envelope.get("data")
    if isinstance(raw_data, str):
        if len(raw_data.encode("utf-8")) > MAX_AIGIS_HEADER_BYTES:
            raise HumanVerificationError("oversized Aigis data")
        try:
            data = json.loads(raw_data)
        except (TypeError, ValueError, json.JSONDecodeError) as exc:
            raise HumanVerificationError("invalid Aigis data") from exc
    else:
        data = raw_data
    if not isinstance(data, dict):
        raise HumanVerificationError("invalid Aigis data")

    captcha_id = _required_string(data.get("gt") or data.get("captcha_id"), maximum=512)
    raw_challenge = data.get("challenge")
    if raw_challenge is not None:
        challenge = _required_string(raw_challenge, maximum=2_048)
        version: AigisVersion = "gt3"
    else:
        challenge = None
        version = "gt4"

    success = data.get("success")
    if isinstance(success, bool):
        success = int(success)
    if success is not None and not isinstance(success, int):
        raise HumanVerificationError("invalid Aigis success flag")

    new_captcha = data.get("new_captcha")
    if isinstance(new_captcha, int) and new_captcha in (0, 1):
        new_captcha = bool(new_captcha)
    if new_captcha is not None and not isinstance(new_captcha, bool):
        raise HumanVerificationError("invalid Aigis captcha flag")

    risk_type = data.get("risk_type")
    if risk_type is not None:
        risk_type = _required_string(risk_type, maximum=128)

    return AigisChallenge(
        session_id=session_id,
        version=version,
        captcha_id=captcha_id,
        challenge=challenge,
        success=success,
        new_captcha=new_captcha,
        risk_type=risk_type,
    )


def encode_aigis_proof(challenge: AigisChallenge, version: AigisVersion, result: Mapping[str, str]) -> str:
    if version != challenge.version:
        raise HumanVerificationError("captcha version mismatch")
    required_by_version = {
        "gt3": {"geetest_challenge", "geetest_validate", "geetest_seccode"},
        "gt4": {"lot_number", "captcha_output", "pass_token", "gen_time", "captcha_id"},
    }
    required = required_by_version[version]
    optional = {"sign_token"} if version == "gt4" else set()
    if set(result) - required - optional or not required.issubset(result):
        raise HumanVerificationError("unexpected captcha proof fields")

    normalized = {name: _required_string(value, maximum=MAX_AIGIS_VALUE_LENGTH) for name, value in result.items()}
    raw = json.dumps(normalized, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    if len(raw) > MAX_AIGIS_HEADER_BYTES:
        raise HumanVerificationError("oversized captcha proof")
    return f"{challenge.session_id};{base64.b64encode(raw).decode('ascii')}"


def _required_string(value: object, *, maximum: int) -> str:
    if not isinstance(value, str) or not value or len(value) > maximum:
        raise HumanVerificationError("invalid Aigis string")
    return value
