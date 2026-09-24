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
