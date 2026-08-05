class CamaraError(Exception):
    """Base exception for CAMARA integration failures."""


class CamaraProviderUnavailableError(CamaraError):
    """Raised when the configured provider cannot serve requests."""


class CamaraTimeoutError(CamaraError):
    """Raised when provider request exceeds timeout budget."""


class CamaraInvalidResponseError(CamaraError):
    """Raised when provider returns malformed or incomplete data."""


class CamaraNetworkError(CamaraError):
    """Raised for transport/network failures communicating with CAMARA provider."""
