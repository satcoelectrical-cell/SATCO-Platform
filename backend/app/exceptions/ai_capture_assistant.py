"""Private inward exceptions for PATCH-035 adapter translation."""


class AICaptureAssistantError(Exception):
    pass


class AICaptureSourceProtected(AICaptureAssistantError):
    pass


class AICaptureDependencyUnavailable(AICaptureAssistantError):
    pass


class AICaptureProviderUnavailable(AICaptureAssistantError):
    pass


class AICaptureInvalidProviderResponse(AICaptureAssistantError):
    pass
