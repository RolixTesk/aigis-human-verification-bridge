from __future__ import annotations

from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Gt3Proof(StrictModel):
    version: Literal["gt3"]
    geetest_challenge: str = Field(min_length=1, max_length=16_384)
    geetest_validate: str = Field(min_length=1, max_length=16_384)
    geetest_seccode: str = Field(min_length=1, max_length=16_384)


class Gt4Proof(StrictModel):
    version: Literal["gt4"]
    lot_number: str = Field(min_length=1, max_length=16_384)
    captcha_output: str = Field(min_length=1, max_length=16_384)
    pass_token: str = Field(min_length=1, max_length=16_384)
    gen_time: str = Field(min_length=1, max_length=16_384)
    captcha_id: str = Field(min_length=1, max_length=16_384)
    sign_token: str | None = Field(default=None, min_length=1, max_length=16_384)


HumanVerificationProof = Annotated[Gt3Proof | Gt4Proof, Field(discriminator="version")]


class PublicChallenge(StrictModel):
    challenge_id: str
    version: Literal["gt3", "gt4"]
    captcha_id: str
    challenge: str | None = None
    success: int | None = None
    new_captcha: bool | None = None
    risk_type: str | None = None
    user_info: str | None = None
    expires_at: datetime


class DemoChallengeRequest(StrictModel):
    version: Literal["gt3", "gt4"]


class ProofAccepted(StrictModel):
    status: Literal["proof_ready"] = "proof_ready"
    encoded_length: int
    proof_sha256: str
    server_only: bool = True
