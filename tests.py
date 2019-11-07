import unittest
try:
    from unittest.mock import MagicMock
except ImportError:
    from mock import MagicMock
from pyquo.session import Session, Query
from pyquo.fields import Integer, String
from pyquo.models import Fact, Reference, File, URL, Contains
from pyquo.errors import ValidationError, RequiredError, SessionError
from pyquo.helper import _register_class
from pyquo.fields import (
    StringValidator, FloatValidator, DictValidator,
    IntegerValidator, ListValidator, ChoiceValidator
)


class TestFactModel(Fact):
    _type = 'testfact'

    id = String()
    name = String(required=True)
    description = String()
    number = Integer()


_register_class('testfact', TestFactModel)


class TestPyQuo(unittest.TestCase):
    fileObj = File(id='file_identifier')
    urlObj = URL(id='http://testbla.com')

    def testValidators(self):
        StringValidator()("no exception")

        with self.assertRaises(ValidationError):
            StringValidator()(123)

        FloatValidator()(1)
        with self.assertRaises(ValidationError):
            FloatValidator()("exception")

        DictValidator()({'foo': 'bar'})
        with self.assertRaises(ValidationError):
            DictValidator()("exception")

        IntegerValidator()(123)
        with self.assertRaises(ValidationError):
            IntegerValidator()("exception")

        ListValidator(type=int)([1, 2, 3])
        with self.assertRaises(ValidationError):
            ListValidator(type=int)(["string", 1, 2, 3])

        ChoiceValidator(['foo', 'bar'])('foo')
        with self.assertRaises(ValidationError):
            ChoiceValidator(['foo', 'bar'])('foo2')

    def testModelVarTypes(self):
        session = MagicMock()

        # wrong type in field id
        with self.assertRaises(ValidationError):
            TestFactModel(id=123)

        # superflous field passed
        data = dict(name="foobar", superflous=12)
        test = TestFactModel(id="123", document=data)
        self.assertEqual(test.superflous, 12)
        self.assertEqual(test.document['superflous'], 12)

        # check document is stored properly
        document = dict(name="bar")
        test = TestFactModel(id="id", document=document)
        self.assertEqual(test.document, document)

        # missing required field "name"
        with self.assertRaises(RequiredError):
            TestFactModel(id="identifier", session=session).save(
                session=session)

    def testFactAnnotations(self):
        session = MagicMock()
        TestFactModel(id="123", session=session).annotations()

    def testFactReferences(self):
        session = MagicMock()

        # set_global_session(session)
        session._query.return_value = [{
            'class': 'reference',
            'type': 'contains',
            'target': self.fileObj.serialize,
            'source': self.urlObj.serialize
        }, {
            'class': 'reference',
            'type': 'contains',
            'target': self.urlObj.serialize,
            'source': self.fileObj.serialize
        }]
        self.fileObj._session = session

        for incoming in (True, False):
            # test incoming / outgoing references
            references = self.fileObj.references(
                refs=Reference, session=session, limit=4)
            str(references)
            tuple(references)

            containsFile = Contains(target=self.fileObj, source=self.urlObj)
            containsURL = Contains(target=self.urlObj, source=self.fileObj)

            self.assertEqual(references[0], containsFile)
            self.assertEqual(references[1], containsURL)

        # test descendants
        descendants = self.fileObj.descendants(refs=Reference)
        self.assertEqual(descendants[0], self.fileObj)
        self.assertEqual(descendants[1], self.urlObj)

        ancestors = self.fileObj.ancestors(refs=Reference)
        self.assertEqual(ancestors[0], self.urlObj)
        self.assertEqual(ancestors[1], self.fileObj)

    def testFactEquals(self):
        self.assertEqual(URL(id='123'), URL(id='123'))
        self.assertNotEqual(File(id='foo'), URL(id='bar'))

    def testGettingAndSaving(self):
        session = MagicMock()
        session._import.return_value = {
            'fact': [
                {
                    'type': 'file',
                    'id': 'asdfasdf'
                }
            ]
        }

        fileObj = File(
            id='asdfasdf',
            session=session
        )
        fileObj.get()
        # XXX add mock checks

        fileObj.md5 = 'md5'
        fileObj.sha1 = 'sha1'
        fileObj.sha256 = 'sha256'
        fileObj.save(session)

        # XXX test here


class FileUploadTestCase(unittest.TestCase):
    class FakeFile:
        def __init__(self, content, name=None):
            self.name = name
            self.content = content

        def read(self):
            return self.content

    def setUp(self):
        self.session = MagicMock(spec=Session)
        self.content = 'testcontent'
        self.filename = 'testname'

    # def tearDown(self):
    #     base.Model._session = None

    def testUploadWithGivenNameShouldSaveAnnotation(self):
        self.session._import.return_value = {
            "annotation": [{
                "type": "known-as",
                "label": self.filename,
                "fact": File(id='foo').serialize
            }]
        }
        File.upload(self.content, filename=self.filename, session=self.session)

        self.session.http_post.assert_called_once_with(
            '/v1/file', data=self.content,
            headers={'Content-Type': 'application/octet-stream'})
        self.assertEqual(self.session.http_post.call_count, 1)

        label = self.session._import.call_args[0][0]['annotation'][0]['label']
        # print('jjjjjjjj', annot)
        self.assertEqual(label, self.filename)

    def testCallWithoutNameShouldNotSaveAnnotation(self):
        self.session.http_post.json.return_value = {'records': [{'id': '123'}]}
        File.upload(self.content, session=self.session)

        self.session.http_post.assert_called_once_with(
            '/v1/file', data=self.content,
            headers={'Content-Type': 'application/octet-stream'})
        self.session._import.assert_not_called()

    def testSaveWithFileLikeOjectShouldTryToExtractFilename(self):
        self.session._import.return_value = {
            "fact": [{"type": "file", "id": "foo"}],
            "annotation": [{
                "type": "known-as",
                "label": self.filename,
                "fact": File(id='foo').serialize
            }]
        }
        File.upload(
            self.FakeFile(self.content, self.filename),
            session=self.session
        )

        self.session.http_post.assert_called_once_with(
            '/v1/file', data=self.content,
            headers={'Content-Type': 'application/octet-stream'})
        self.assertEqual(self.session._import.call_count, 1)

        label = self.session._import.call_args[0][0]['annotation'][0]['label']
        self.assertEqual(label, self.filename)

    def testSaveWithFileLikeOjectShouldBePossibleToOverrideFilename(self):
        self.session._import.return_value = {
            "annotation": [{
                "type": "known-as",
                "label": self.filename,
                "fact": File(id='foo').serialize
            }]
        }
        FILENAME = 'anotherfilename'
        File.upload(
            self.FakeFile(self.content, self.filename), filename=FILENAME,
            session=self.session
        )

        self.session.http_post.assert_called_once_with(
            '/v1/file', data=self.content,
            headers={'Content-Type': 'application/octet-stream'})

        label = self.session._import.call_args[0][0]['annotation'][0]['label']
        self.assertEqual(label, FILENAME)

    def testWithoutprovidingSessionRaisesException(self):
        session = MagicMock()
        session._import.return_value = {
            "annotation": [{
                "type": "known-as",
                "label": "foo",
                "fact": File(id='foo').serialize
            }]
        }
        with self.assertRaises(SessionError):
            File.upload(self.FakeFile(self.content, self.filename))

        session._import.return_value = {
            "fact": [{
                'type': 'file',
                'id': '123'
            }],
            "annotation": [{
                "type": "known-as",
                "label": self.filename,
                "fact": File(id='foo').serialize
            }]
        }
        File.upload(self.FakeFile(self.content, self.filename),
                    session=session)


class ModelFilter(unittest.TestCase):
    def testFilter(self):
        session = MagicMock(spec=Session)
        session._query.return_value = [
            {
                'class': 'fact',
                'type': 'testfact',
                'id': 'myfact',
                'document': {'reliability': 'A'}
            }
        ]
        for i in TestFactModel.filter(name='foo', stuff=2, session=session):
            self.assertIsInstance(i, TestFactModel)


class RawQuery(unittest.TestCase):
    def testRawQuery(self):
        response = {"class": "fact", "type": "file", "id": "123"}

        session = MagicMock()
        session._query.return_value = [dict(response)]

        query = {'class': 'fact', 'limit': 1}
        res = Query.execute(query, session)
        self.assertDictEqual(res[0], response)

        res = list(Query.generate(query, session))
        self.assertEqual(res[0], File(id="123"))


if __name__ == '__main__':
    unittest.main()
