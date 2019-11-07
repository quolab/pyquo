

# pyquo documentation

pyquo is a python library which wraps the quolab api into an easily usable
api for python.

## Authentication examples:

pyquo needs to authenticate to the Quolab backend using either Basic or Token
authentication.

```python
from pyquo import session
from pyquo.authenticator import TokenAuthenticator

session.Session(
    base_url="https://<quolab-instance>/",
    global_session=True,
    auth=TokenAuthenticator("my-secret-token-string")
)
```

or

```python
from pyquo import session
from pyquo.authenticator import UserAuthenticator
session.Session(
    base_url="https://<quolab-instance>/",
    global_session=True,
    auth=UserAuthenticator(username="user", password="password")
)
```

The parameter `global_session=True` will ensure that your session is attached
to pyquo so that the session information does not need to be passed upon each
request to quolab.

Each of the following examples will need to be prefixed with the abovementioned
code snippet to enable authentication.


## Inserting data

In this example a file is uploaded to quolab from the local machine and
associated with a new threat name, via the "identified-as" reference.

```python
from pyquo.models import Malware, File, IdentifiedAs

# Upload a file to quolab
with open('/tmp/file', 'rb') as f:
    f = File.upload(f)

# Create a threat name
malware = Malware('ThreatName')
malware.save()

# Associate the threat_name with the file
ident = IdentifiedAs(source=f, target=malware)
ident.save()

print('Created reference: {!r}'.format(ident))
```

output:
```bash
$ python examples.py 
Created reference: file(5da078777cda24e4df697e2928451723f2303bfdbb2ce9551c822188c7945d25)→identified-as→malware(ThreatName)
```

## Creating a case

The following, is an example of how to create a case in quolab using pyquo.
A file and two url entities are subsequently attached to the case.

```python
from pyquo.models import Case, Encases, URL

# create and store a case object
case = Case(name='generated case', description='long description').save()
print('Created case: {!r}'.format(case))

# create url objects and upload a file
url1 = URL('http://test.com/site/index.html').save()
url2 = URL('http://test2.com/site2/index2.html').save()
with open('/tmp/file', 'rb') as f:
    f = File.upload(f)

# associate the created objects with the case
for obj in [url1, url2, f]:
    encases = Encases(source=case, target=f).save()
    print(encases)
```

output:
```
Created case: case(acc206f5eaf641d8a196d2bbd53034e8)
case(acc206f5eaf641d8a196d2bbd53034e8)→encases→url(http://test.com/site/index.html)
case(acc206f5eaf641d8a196d2bbd53034e8)→encases→url(http://test2.com/site2/index2.html)
case(acc206f5eaf641d8a196d2bbd53034e8)→encases→file(5da078777cda24e4df697e2928451723f2303bfdbb2ce9551c822188c7945d25)
```

## Querying existing data

Information regarding a specific fact can be retrieved from quolab by querying
the incoming/outgoing references and/or resolving the facts behind each of these
references as such:

```python
file_ = File("5da078777cda24e4df697e2928451723f2303bfdbb2ce9551c822188c7945d25")
url1 = URL('http://test.com/site/index.html').save()
Contains(source=file_, target=url1).save()

for ref in file_.references():
    print('any {!r}'.format(ref))

# Only show references that point to specific fact types
for ref in file_.references(facts=(Malware, URL)):
    print('specific {!r}'.format(ref))
    print('target {!r}'.format(ref.target))
```

output:
```
any file(5da078777cda24e4df697e2928451723f2303bfdbb2ce9551c822188c7945d25)→observed-by→user(omni@quolab.internal)
any file(5da078777cda24e4df697e2928451723f2303bfdbb2ce9551c822188c7945d25)→scheduled→task(magic)
any file(5da078777cda24e4df697e2928451723f2303bfdbb2ce9551c822188c7945d25)→scheduled→task(tlsh)
any file(5da078777cda24e4df697e2928451723f2303bfdbb2ce9551c822188c7945d25)→contains→url(http://test.com/site/index.html)
any file(5da078777cda24e4df697e2928451723f2303bfdbb2ce9551c822188c7945d25)→identified-as→malware(Malicious_Name)
specific file(5da078777cda24e4df697e2928451723f2303bfdbb2ce9551c822188c7945d25)→identified-as→malware(Malicious_Name)
target malware(Malicious_Name)
```


## Data Representation

pyquo uses the REST api of quolab to send json serialized data back and forth.
A raw cURL request might look as follows:
```bash
$ curl -sd '{"class": "fact", "type": "file", "id": "5da078777cda24e4df697e2928451723f2303bfdbb2ce9551c822188c7945d25"}' -H "Authorization: ...." http://localhost/v1/catalog/query  | json_pp
```
```json
{
   "records" : [
      {
         "class" : "fact",
         "id" : "5da078777cda24e4df697e2928451723f2303bfdbb2ce9551c822188c7945d25",
         "type" : "file",
         "document" : {
            "sha256" : "5da078777cda24e4df697e2928451723f2303bfdbb2ce9551c822188c7945d25",
            "md5" : "2c79e1762978235e7b4a9ef595f6c029",
            "sha1" : "a75b61f12ff94fbe04d472967c83d4c6cef55802",
            "tlsh" : "9701dc87d83a92b386217a877bf5f012210463ce74949648f4ed720e730b81410c5577",
            "size" : 759
         }
      }
   ]
}
```

In pyquo model objects can be easily serialized/deserialized to and from json:

```python
import json

id = "5da078777cda24e4df697e2928451723f2303bfdbb2ce9551c822188c7945d25"
file_ = File(id).get()

print('object: "{!r}"'.format(file_))
print('serialized: {!s}'.format(
    json.dumps(file_.serialize_with_document, indent=2))
)

urlstr = {
    "class": "fact",
    "type": "url",
    "id": "http://strange.com/foo"
}
url = Model.deserialize(urlstr)
print('deserialized: '.format(url))
```

output:
```
object: "file(5da078777cda24e4df697e2928451723f2303bfdbb2ce9551c822188c7945d25)"
serialized: {
  "class": "fact",
  "type": "file",
  "id": "5da078777cda24e4df697e2928451723f2303bfdbb2ce9551c822188c7945d25",
  "document": {
    "md5": "2c79e1762978235e7b4a9ef595f6c029",
    "sha1": "a75b61f12ff94fbe04d472967c83d4c6cef55802",
    "sha256": "5da078777cda24e4df697e2928451723f2303bfdbb2ce9551c822188c7945d25",
    "tlsh": "9701dc87d83a92b386217a877bf5f012210463ce74949648f4ed720e730b81410c5577",
    "size": 759
  }
}
deserialized: url(http://strange.com/foo)
```


## Full example

pyquo is both python2 and python3 compatible. As such the following example can
be executed as follows:

```bash
$ python example.py
```

output:
```
Created reference: file(5da078777cda24e4df697e2928451723f2303bfdbb2ce9551c822188c7945d25)→identified-as→malware(ThreatName)
Created case: case(acc206f5eaf641d8a196d2bbd53034e8)
case(acc206f5eaf641d8a196d2bbd53034e8)→encases→url(http://test.com/site/index.html)
case(acc206f5eaf641d8a196d2bbd53034e8)→encases→url(http://test2.com/site2/index2.html)
case(acc206f5eaf641d8a196d2bbd53034e8)→encases→file(5da078777cda24e4df697e2928451723f2303bfdbb2ce9551c822188c7945d25)
any file(5da078777cda24e4df697e2928451723f2303bfdbb2ce9551c822188c7945d25)→executed→task(magic)
any file(5da078777cda24e4df697e2928451723f2303bfdbb2ce9551c822188c7945d25)→executed→task(tlsh)
any file(5da078777cda24e4df697e2928451723f2303bfdbb2ce9551c822188c7945d25)→observed-by→user(omni@quolab.internal)
any file(5da078777cda24e4df697e2928451723f2303bfdbb2ce9551c822188c7945d25)→contains→url(http://test.com/site/index.html)
any file(5da078777cda24e4df697e2928451723f2303bfdbb2ce9551c822188c7945d25)→identified-as→malware(Malicious_Name)
any file(5da078777cda24e4df697e2928451723f2303bfdbb2ce9551c822188c7945d25)→identified-as→malware(ThreatName)
specific file(5da078777cda24e4df697e2928451723f2303bfdbb2ce9551c822188c7945d25)→identified-as→malware(Malicious_Name)
target file(5da078777cda24e4df697e2928451723f2303bfdbb2ce9551c822188c7945d25)→identified-as→malware(Malicious_Name)
specific file(5da078777cda24e4df697e2928451723f2303bfdbb2ce9551c822188c7945d25)→identified-as→malware(ThreatName)
target file(5da078777cda24e4df697e2928451723f2303bfdbb2ce9551c822188c7945d25)→identified-as→malware(ThreatName)
specific file(5da078777cda24e4df697e2928451723f2303bfdbb2ce9551c822188c7945d25)→contains→url(http://test.com/site/index.html)
target file(5da078777cda24e4df697e2928451723f2303bfdbb2ce9551c822188c7945d25)→contains→url(http://test.com/site/index.html)
object: file(5da078777cda24e4df697e2928451723f2303bfdbb2ce9551c822188c7945d25)
serialized {
  "class": "fact",
  "type": "file",
  "id": "5da078777cda24e4df697e2928451723f2303bfdbb2ce9551c822188c7945d25",
  "document": {
    "md5": "2c79e1762978235e7b4a9ef595f6c029",
    "sha1": "a75b61f12ff94fbe04d472967c83d4c6cef55802",
    "sha256": "5da078777cda24e4df697e2928451723f2303bfdbb2ce9551c822188c7945d25",
    "tlsh": "9701dc87d83a92b386217a877bf5f012210463ce74949648f4ed720e730b81410c5577",
    "size": 759,
    "magic": {
      "mime": "text/plain",
      "text": "ASCII text"
    }
  }
}
url(http://strange.url/foo)
```

example.py:

```python
from pyquo import session
from pyquo.base import Model
from pyquo.authenticator import UserAuthenticator
from pyquo.models import Malware, File, IdentifiedAs, Contains
from pyquo.models import Case, Encases, URL

import json

session.Session(
    base_url="http://localhost",
    global_session=True,
    auth=UserAuthenticator(username="admin", password="XXX")
)

# Upload a file to quolab
with open('/tmp/file', 'rb') as f:
    f = File.upload(f)

# Create a threat name
malware = Malware('ThreatName')
malware.save()

# Associate the threat_name with the file
ident = IdentifiedAs(source=f, target=malware)
ident.save()

print('Created reference: {!r}'.format(ident))

# creating a case with associated file
case = Case(name='generated case', description='long description').save()
print('Created case: {!r}'.format(case))

# create url objects and upload a file
url1 = URL('http://test.com/site/index.html').save()
url2 = URL('http://test2.com/site2/index2.html').save()
with open('/tmp/file', 'rb') as f:
    f = File.upload(f)

# associate the created objects with the case
for obj in [url1, url2, f]:
    encases = Encases(source=case, target=obj).save()
    print(encases)


# get all references for an entity
file_ = File("5da078777cda24e4df697e2928451723f2303bfdbb2ce9551c822188c7945d25")
url1 = URL('http://test.com/site/index.html').save()
Contains(source=file_, target=url1).save()

for ref in file_.references():
    print('any {!r}'.format(ref))

# Only show references that point to specific fact types
for ref in file_.references(facts=(Malware, URL)):
    print('specific {!r}'.format(ref))
    print('target {!r}'.format(ref))

# data represenation
id = "5da078777cda24e4df697e2928451723f2303bfdbb2ce9551c822188c7945d25"
file_ = File(id).get()
print('object: {!r}'.format(file_))
print('serialized {!s}'.format(
    json.dumps(file_.serialize_with_document, indent=2)))

urlstr = {
    "class": "fact",
    "type": "url",
    "id": "http://strange.url/foo"
}
url = Model.deserialize(urlstr)
print(url)
```
