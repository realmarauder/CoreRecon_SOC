"""Custom exception classes."""


class CoreReconException(Exception):
    """Base exception for CoreRecon SOC."""

    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class AuthenticationError(CoreReconException):
    """Authentication failed."""

    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, status_code=401)


class AuthorizationError(CoreReconException):
    """Authorization failed - insufficient permissions."""

    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(message, status_code=403)


class ResourceNotFoundError(CoreReconException):
    """Requested resource not found."""

    def __init__(self, resource: str, identifier: str):
        message = f"{resource} with identifier '{identifier}' not found"
        super().__init__(message, status_code=404)


class ValidationError(CoreReconException):
    """Data validation failed."""

    def __init__(self, message: str):
        super().__init__(message, status_code=422)


class AlertNotFoundError(ResourceNotFoundError):
    """Alert not found."""

    def __init__(self, alert_id: str):
        super().__init__("Alert", alert_id)


class IncidentNotFoundError(ResourceNotFoundError):
    """Incident not found."""

    def __init__(self, incident_id: str):
        super().__init__("Incident", incident_id)


class DatabaseError(CoreReconException):
    """Database operation failed."""

    def __init__(self, message: str = "Database operation failed"):
        super().__init__(message, status_code=500)


class ExternalServiceError(CoreReconException):
    """External service request failed."""

    def __init__(self, service: str, message: str):
        full_message = f"External service '{service}' error: {message}"
        super().__init__(full_message, status_code=502)
