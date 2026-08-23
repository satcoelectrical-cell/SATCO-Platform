"""Stable Supporting File domain failures."""


class SupportingFileError(ValueError):
    pass


class SupportingFileValidationError(SupportingFileError):
    pass


class SupportingFileInvalidTransition(SupportingFileError):
    pass


class SupportingFileVersionConflict(SupportingFileError):
    pass


class SupportingFileIntegrityError(SupportingFileError):
    pass


class SupportingFileScannerUnavailable(SupportingFileError):
    """Safety decision unavailable: asset remains quarantined, never available."""
    pass


class SupportingFileProtectedNotFound(SupportingFileError):
    pass
