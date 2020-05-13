# About

pyquo is a library which offers bindings for the quolab REST API in
python.

## Compatibility

pyquo is designed to be compatbile with both python2 and python3

## Installation

```shell
$ pip install pyquo
```

## Authentication

There are two ways of authenticating against Quolab's API. The first 
method is using the UserAuthenticator which uses  `BasicAuth`.

```python
from pyquo.authenticator import UserAuthenticator
auth = UserAuthenticator(username='user', password='pass')
```

However, the prefered way of authenticating would be by using the
`TokenAuthenticator`.

```python
from pyquo.authenticator import TokenAuthenticator

auth = TokenAuthenticator(token='your-token-here')
```

In order to generate a token the following pyquo code can be used:

```python
from pyquo.Session import Session
from pyquo.authenticator import UserAuthenticator, TokenAuthenticator

session = Session(
    base_url="https://qlab.quo/",
    global_session=True,
    auth=UserAuthenticator(username="<username>", password="<password>")
)

print(TokenAuthenticator.create_token(session, "1y"))
```

For more information on the `expires_in` (e.g. 1y = 1 year) field, please
consult the quolab REST API documentation

## Sessions

In order to interact with the quolab api, a `Session` instance is required. This
can be created as follows:

```python
from pyquo.session import Session

s = Session(base_url="https://<url>/", global_session=True, auth=auth, verify=False)
```

When interacting with a single quolab instance, it is recommended to set
`global_session` to `True`. When interacting with multiple sessions at once,
e.g. retreiving information mutliple nodes, you will be required to store the
session, and pass it around with your queries.

## Models

pyquo implements (sys-)facts, (sys-)references and annotations as pyquo.model
object instances. For example, a case model can be created as follows:

```python
[In:] from pyquo.models import Case
[In:] case = Case(id='2981693283194043a185c0cc9412ad83')
[Out:] case(2981693283194043a185c0cc9412ad83)
```

`case` is a 'handle' object for the case with the case id
'2981693283194043a185c0cc9412ad83'. This handle can now be used to perform
read/store/update/delete operations on the case. 

```python
[In:] case.get()
[In:] case.name
[Out:] "Fancy case name"
[In:] case.name = "Renamed case"
[In:] case.save()
[In:] case.get().name
[Out:] "Renamed case"
```

## Querysets

### References / Sysreferences

(Sys-)Facts can have incoming and outgoing (sys-)references, which can be
queried as follows:

```python
[In:] references = case.references()
[Out:] [case(2981693283194043a185c0cc9412ad83)→associated-with→user(test),
        case(2981693283194043a185c0cc9412ad83)→encases→ipynb(Untitled1.ipynb)]
```

This will show all outgoing references. In order to show incoming references,
the `incoming` parameter needs to be set to `True` (`case.references(incoming=True)`)

It is possible to filter for `sysrefs` using `fact.references(refs=SysRef)`.

Further the associated facts behind the references can be filtered (e.g. Files
and Mutexes only) using:

```python
[In:] fact.references(facts=(models.File, models.Mutex))
```

While the reference type can also be filtered using:

```python
[In:] fact.references[models.Contains](facts=(models.File, models.Mutex))
```

The obtained references have a `source` and a `target` property which resolves
to an instance of the related fact. E.g.

```python
[In:] reference
[Out:] case(2981693283194043a185c0cc9412ad83)→encases→ipynb(Untitled1.ipynb)
[In:] reference.source
[Out:] case(2981693283194043a185c0cc9412ad83)
[In:] reference.target
[Out:] ipynb(Untitled1.ipynb)
```

It is also possible to obtain the `source` and `target` facts directly, by
using the properties `fact.ancestors` and `fact.descendants`.

### Annotations

Fact annotations can be queries as follows:

```python
fact.annotations(annotations=pyquo.models.KnownAs, limit=3)
```

`annotations=<pyquo.Model>` allows serverside filtering for annotations of a
given type, while `limit=1` allows limiting the number of results returned by a
given query.


## Raw Queries

From time to time it can occur that pyquo is not flexible enough to cover each
and every usecase/api feature which is why raw queries have been made possible
in pyquo:

```python
from pyquo.session import Query

foo = {
    "class": "annotation",
    "type": "known-as",
    "aggregate": "first",
    "fact": {
        "type": "function",
        "id": [f.id for f in functions],
        "aggregate": "group" 
    }
}

for i in Query.generate(foo, session):
    print(i)

print(Query.execute(foo, session))
```

The `Query.generate(foo, session)` method will execute the given query and
return a deserialized pyquo object, while `result = Query.execute(foo, session)`
will return the raw query result as a dictionary.

## Examples

Furhter examples can be found here [Example.md](Examples.md)
