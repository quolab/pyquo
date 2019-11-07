# Exceptions
class FetchError(Exception):
    """Raised when an error occurs during fetching"""
    status_code = None

    def __init__(self, error_msg, status_code=None):
        super(Exception, self).__init__(error_msg)
        self.status_code = status_code


class SessionError(Exception):
    """Raised when no session could be found"""
    pass


class ResultNotFound(FetchError):
    """Raised when the requested object is not found"""
    pass


class ValidationError(Exception):
    """Raised when the input validation fails"""
    pass


class RequiredError(Exception):
    """Raised when a required field is missing"""
    pass


class AuthenticationError(Exception):
    """Raised when the authentication failed"""
    pass
