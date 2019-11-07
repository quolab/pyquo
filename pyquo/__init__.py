from . import models         # noqa
from . import session        # noqa
from . import authenticator  # noqa

try:
    import os
    token = os.environ.get('QUOLAB_API_TOKEN')
    base_url = os.environ.get('QUOLAB_BASE_URL')

    if token and base_url:
        from . import base
        base.Model._session = session.Session(
            base_url=base_url,
            auth=authenticator.TokenAuthenticator(token)
        )
except KeyError:
    pass
