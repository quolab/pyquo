from .errors import AuthenticationError
from .session import AUTH_API


class Authenticator:
    """Authenticator parent class"""

    def __call__(self, session):
        self.authenticate(session)


class TokenAuthenticator(Authenticator):
    """Authenticate pyquo using a quolab Authenticator"""

    def __init__(self, token):
        self._token = token

    @classmethod
    def create_token(self, session, expires_in):
        """This method returns a session id"""

        info = {"expires-in": expires_in}
        res = session.http_post(AUTH_API, json=info).json()
        return res

    def authenticate(self, session):
        headers = {'Authorization': "Quoken {}".format(self._token)}

        if session.headers:
            session.headers.update(headers)
        else:
            session.headers = headers


class UserAuthenticator(Authenticator):
    """Authenticate pyquo using Basic Auth"""

    def __init__(self, username, password):
        self._username = username
        self._password = password

    def authenticate(self, session):
        data = {
            'username': self._username,
            'password': self._password
        }
        path = "/v1/auth/login"

        r = session.http_post(path, json=data)
        if r.status_code != 200:
            raise AuthenticationError(r.content)
