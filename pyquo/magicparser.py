from .base import Model
from .helper import TypeFactory

MAGIC_PARSER_URL = "/v1/scan/text"


class MagicParser(object):
    @classmethod
    def parse(cls, text, session=None):
        session = session or Model._session

        payload = {'text': text}
        res = session.http_post(MAGIC_PARSER_URL, json=payload).json()

        for i in res['records']:
            yield TypeFactory.deserialize(i)
