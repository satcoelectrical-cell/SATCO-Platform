from pydantic import BaseModel, Field


class MfaStatusResponse(BaseModel):
    required: bool
    enrolled: bool
    active: bool


class TotpEnrollmentStartResponse(BaseModel):
    secret: str
    provisioning_uri: str


class TotpEnrollmentVerifyRequest(BaseModel):
    code: str = Field(min_length=6, max_length=6, pattern=r"^\d{6}$")


class TotpEnrollmentVerifyResponse(BaseModel):
    outcome: str = "success"
    recovery_codes: list[str]


class RecoveryCodeRequest(BaseModel):
    code: str = Field(min_length=16, max_length=128)


class RecoveryCodesResponse(BaseModel):
    outcome: str = "success"
    recovery_codes: list[str]


class StepUpRequest(BaseModel):
    password: str = Field(min_length=1, max_length=512)
    totp_code: str | None = Field(default=None, min_length=6, max_length=6, pattern=r"^\d{6}$")
