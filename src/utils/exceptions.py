class AgroClimateError(Exception):
    """Base exception for domain-specific pipeline failures."""


class APIConnectionError(AgroClimateError):
    """Raised when the weather API cannot be reached successfully."""


class DataValidationError(AgroClimateError):
    """Raised when data quality checks fail."""


class DataProcessingError(AgroClimateError):
    """Raised when a processing step fails."""


class DatabaseLoadError(AgroClimateError):
    """Raised when warehouse loading fails."""
