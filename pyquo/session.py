from requests import Session
import json

try:
    from urllib.parse import urljoin
except ImportError:
    from urlparse import urljoin

from .errors import FetchError
from .helper import TypeFactory

import logging

logger = logging.getLogger(__name__)


CATALOG_QUERY = "/v1/catalog/query"
CATALOG_IMPORT = "/v1/catalog/import"
AUTH_API = "/v1/auth/api"
AUTH_LOGIN = "/v1/auth/login"
FILE_UPLOAD = '/v1/file'
FILE_DOWNLOAD = FILE_UPLOAD + '/{}'


def expect(*codes):
    def wrap(func, *args, **kwargs):
        def wrapper(*args, **kwargs):
            res = func(*args, **kwargs)
            if res.status_code not in codes:
                raise FetchError("unexpected http code <{}> {}".format(
                    res.status_code, res.content), res.status_code)
            return res
        return wrapper
    return wrap


def logme(func):
    def wrap(self, path, *args, **kwargs):
        name = func.__code__.co_name.upper()
        logger.debug('%s %s data: %s', name.upper(), path, kwargs)
        res = func(self, path, *args, **kwargs)
        try:
            resp = res.json()
        except Exception:
            resp = res.content
        logger.debug('%d: Response %s', res.status_code, resp)
        return res
    return wrap


def set_global_session(session):
    from .base import Model
    Model._session = session


class Session(Session):
    """ This class maintains the session information for the current
        Connection with the QuoLab server.
        An Instance of this class is required when performing operations
        against the API

        >>> s = Session("http://qlab01-dev.app.quo:9090/v1/", None)
        >>> s.get(Case, "2ee9b31253f44e6cb1d40ff7af333b4f")

    """
    def __init__(self, base_url, auth=None, global_session=False,
                 *args, **kwargs):
        super(Session, self).__init__(*args, **kwargs)

        self.url = base_url
        if global_session is True:
            set_global_session(self)

        if auth:
            auth(self)

    @logme
    def http_post(self, path, data=None, json=None, headers={}):
        url = urljoin(self.url, path)
        res = self.post(url, data=data, json=json, headers=headers)
        return res

    @logme
    def http_patch(self, path, data=None, json=None, headers={}):
        url = urljoin(self.url, path)
        res = self.patch(url, data=data, json=json, headers=headers)
        return res

    @logme
    def http_delete(self, path, data=None, json=None, headers={}):
        url = urljoin(self.url, path)
        res = self.delete(url, data=data, json=json, headers=headers)
        return res

    @logme
    def http_get(self, path):
        url = urljoin(self.url, path)
        res = self.get(url)
        return res

    def remove(self, query):
        @expect(200)
        def q(self, query):
            return self.http_delete(CATALOG_QUERY, json=query)
        return q(self, query).json()

    def _query(self, query):
        @expect(200)
        def q(self, query):
            if isinstance(query, str):
                query = json.dumps(query)

            return self.http_post(CATALOG_QUERY, json=query)
        return q(self, query).json()['records']

    def _import(self, query):
        @expect(200)
        def q(self, query):
            return self.http_post(CATALOG_IMPORT, json=query)
        return q(self, query).json()

    def _patch(self, query):
        @expect(200)
        def q(self, query):
            return self.http_patch(CATALOG_QUERY, json=query)
        return q(self, query).json()

    @property
    def current_user(self):
        @expect(200)
        def q(self):
            return self.http_get(AUTH_LOGIN)
        return q(self).json()['user']['id']


class Filter():
    def __init__(self, parent):
        self._type = parent._type
        self._class = parent._class

    def __call__(self, target=None, source=None, fact=None,
                 document=None, session=None, **kwargs):
        if target:
            kwargs['target'] = target.serialize
        if source:
            kwargs['source'] = source.serialize
        if fact:
            kwargs['fact'] = [f.serialize for f in fact]

        results = self.query(
            session=session,
            _type=self._type,
            _class=self._class,
            document=document,
            **kwargs
        )

        return [TypeFactory.deserialize(r) for r in results]

    def query(self, session, _type, _class, document=None, **kwargs):
        query = dict(kwargs)
        query.update({
            'type': _type,
            'class': _class,
        })

        if isinstance(document, dict):
            query['document'] = document

        return session._query(query)


class Query():
    """This class allows issuing raw queries to the API"""
    @classmethod
    def generate(cls, query, session):
        """This method returns serialized pyquo objects"""
        for i in cls.execute(query, session):
            yield TypeFactory.deserialize(i)

    @classmethod
    def execute(cls, query, session):
        """This method returns the raw query request"""
        return session._query(query)
