"""Exception hierarchy for pyvworld."""


class VworldError(Exception):
    """Base class for all pyvworld exceptions."""


class VworldAuthError(VworldError):
    """Authentication or key-domain mismatch error."""


class VworldRateLimitError(VworldError):
    """Daily or service quota exceeded."""


class VworldInvalidParameterError(VworldError):
    """Invalid parameter detected before sending the HTTP request."""


class VworldNoDataError(VworldError):
    """Raised when strict no-data handling is enabled and VWorld returns NOT_FOUND."""


class VworldServerError(VworldError):
    """VWorld server, parse, or unexpected response error."""


class VworldNetworkError(VworldError):
    """Network timeout or connection error."""
