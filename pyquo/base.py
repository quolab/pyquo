# coding: utf8
from collections import Iterable

from .helper import (
    sessionize,
    TypeFactory, _register_class,
    FACT_CLASS, ANNOTATION_CLASS, SYSFACT_CLASS, REFERENCE_CLASS, SYSREF_CLASS
)
from .session import Filter
from .errors import ValidationError, RequiredError, ResultNotFound
from .fields import Field

from six import with_metaclass


class QuerySet(object):
    _parent = None

    def __init__(self, parent, refs=(), facts=(),
                 incoming=False, limit=None, session=None):
        self._parent = parent
        self._references = refs or (SysRef, Reference)
        self._facts = facts
        self._incoming = incoming
        self._limit = limit
        self._session = session

    def __call__(self, refs=(), facts=(), annotations=(),
                 incoming=None, limit=None, session=None):
        if not isinstance(facts, Iterable):
            facts = (facts,)
        self._facts = facts

        if not isinstance(refs, Iterable):
            refs = (refs,)
        self._references = refs or (SysRef, Reference)

        if incoming is not None:
            self._incoming = incoming

        if limit is not None:
            self._limit = limit

        if session is not None:
            self._session = session

        return self

    def query(self, key=None):
        results = self._parent._references(
            refs=self._references,
            facts=self._facts,
            incoming=self._incoming,
            limit=self._limit,
            session=self._session
        )

        return tuple(results)

    def __getitem__(self, key):
        results = self.query(key)
        return [self._target(result) for result in results][key]

    def __iter__(self):
        for item in self.query():
            yield self._target(item)

    def __len__(self):
        return len(self.query())

    def __repr__(self):
        result = list(self[:4])
        if len(result) > 3:
            result[3] = 'truncated...'
        return 'QuerySet{}'.format(str(result))


class ReferenceQuerySet(QuerySet):
    @property
    def facts(self):
        return FactQuerySet(
            parent=self._parent,
            refs=self._references,
            facts=self._facts,
            incoming=self._incoming,
            limit=self._limit,
            session=self._session
        )

    def _target(self, item):
        return item


class FactQuerySet(QuerySet):
    def _target(self, item):
        if self._incoming is False:
            return item.target
        else:
            return item.source


class AnnotationQuerySet(QuerySet):
    def _target(self, item):
        return item

    def __call__(self, annotations=(), limit=None, session=None):
        if not isinstance(annotations, Iterable):
            annotations = (annotations,)
        self._annotations = annotations

        if limit is not None:
            self._limit = limit

        if session is not None:
            self._session = session

        return self

    def query(self, key=None):
        return tuple(self._parent._annotations(
            limit=self._limit,
            annotations=self._annotations,
            session=self._session
        ))


class ModelMetaClass(type):
    """This class adds the '_fields' attribute which corresponds to a
    mapping of {"property name": <field instance>} and a _fieldmap
    corresponding to a mapping between the actual property name and the
    name of the expected field. E.g. {'created_at': 'created-at'}
    """
    def __new__(cls, name, bases, attrs):
        if attrs.get('_type'):
            _register_class(attrs['_type'], name)

        attrs['_fields'] = dict()
        attrs['_fieldmap'] = dict()

        for key, field in attrs.items():
            if not isinstance(field, Field):
                continue

            if field.field:
                attrs['_fieldmap'][field.field] = key

            attrs['_fields'][key] = field

        klass = super(ModelMetaClass, cls).__new__(cls, name, bases, attrs)
        klass._filter = Filter(klass)
        return klass


class Model(with_metaclass(ModelMetaClass)):
    """All Model types are derived from this class."""
    _class = None
    _type = None
    _session = None

    def __init__(self, document=None, session=None, **kwargs):
        self._data = dict()
        for key, val in kwargs.items():
            if key in self._fields:
                self._data[self._fields[key]] = val
        if session is not None:
            self._session = session
        self.document = document

    @sessionize
    def get(self, session=None):
        """This method gets the object from the api using the session param
        or using the session provided by the instance. If no session is
        available this method raises a SessionError"""

        query = self.serialize
        records = session._query(query)
        if not records:
            raise ResultNotFound('Result not found for {}'.format(self))

        self.document = records[0]['document']

        return self

    @sessionize
    def save(self, session=None):
        """This method stores the object to the api using the session param
        or using the session provided by the instance. If no session is
        available this method raises a SessionError"""

        for key, field in self._fields.items():
            if field.required and field not in self._data:
                raise RequiredError('Required field "{}" missing {}'.format(
                    key, self))

            if field.read_only:
                continue

            if field in self._data:
                self.document[key] = self._data[field]

        serialized = self.serialize_with_document
        cl = serialized.pop('class')
        query = {self._class: [self.serialize_with_document]}
        res = session._import(query)
        res = res.get(cl)[0]
        res.setdefault('class', cl)
        return TypeFactory.deserialize(res)

    @sessionize
    def update(self, session=None, **patchfields):
        query = self.serialize
        query['patch'] = patchfields
        return session._patch(query)

    @sessionize
    def delete(self, session=None):
        """This method deletes an object using the api"""
        return session.remove({'query': self.serialize})

    @classmethod
    @sessionize
    def filter(self, target=None, source=None, fact=None,
               document=None, session=None, **kwargs):
        return self._filter(target, source, fact, document, session, **kwargs)

    def resolve_name(self, key):
        """This method resolves field names. E.g.

        >>> name = String(field='mapped-name')
        """
        return self._fieldmap.get(key, key)

    @property
    def document(self):
        return self._document

    @document.setter
    def document(self, document):
        if document is None:
            document = {}
        self._document = document

        for key, value in document.items():
            name = self.resolve_name(key)

            if name not in self._fields:
                field = Field(value)
                self._fields[name] = field
                setattr(self, name, field)

            try:
                setattr(self, name, value)
            except ValidationError:
                raise ValidationError("{} has no field {}={}".format(
                    self._type, name, value))

    @classmethod
    def deserialize(self, payload):
        return TypeFactory.deserialize(payload)

    @property
    def serialize_with_document(self):
        result = self.serialize
        if self.document is None:
            raise Exception('Document not fetched')

        result['document'] = self.document
        return result


# Base Models
class BaseFact(Model):
    """All Fact derived classes must have a unique id field and can load and
    save the field values to and from the api"""

    _id = None

    def __init__(self, id, document=None, session=None, **kwargs):
        super(BaseFact, self).__init__(
            session=session, document=document, **kwargs)

        self.id = id
        self.__references = ReferenceQuerySet(
            self, session=session or self._session)

    def get_references(self, ref, facts, incoming=True, session=None):
        """This function retrieves references"""

        query = {"class": ref._class}

        key, ikey = 'target', 'source'
        if not incoming:
            key, ikey = 'source', 'target'

        query[key] = self.serialize

        if ref._type:
            query['type'] = ref._type

        if facts:
            query[ikey] = []
            for fact in facts:
                q = {'class': fact._class, 'type': fact._type}
                query[ikey].append(q)

            if len(query[ikey]) == 1:
                query[ikey] = q

        return session._query(query)

    @sessionize
    def _references(self, limit, refs=(), facts=(),
                    incoming=False, session=None):
        for ref in refs:
            references = self.get_references(
                ref=ref, facts=facts, incoming=incoming, session=session)

            base = Fact if ref == Reference else SysFact

            for item in references:
                # XXX remove once this has been implementd serverside
                item['target'].setdefault('class', base._class)
                item['source'].setdefault('class', base._class)

                yield TypeFactory.deserialize(item)

    @property
    def references(self):
        return self.__references

    @property
    def descendants(self):
        return self.__references(incoming=False).facts

    @property
    def ancestors(self):
        return self.__references(incoming=True).facts

    @property
    def serialize(self):
        result = {
            'class': self._class,
            'type': self._type
        }

        if self.id:
            result['id'] = self.id

        return result

    @property
    def id(self):
        return self._id

    @id.setter
    def id(self, value):
        self._id = value

    def __repr__(self):
        return '{._type}({.id})'.format(self, self)

    def __eq__(self, obj):
        return self.id == obj.id and \
                self._type == obj._type and \
                self._class == obj._class

    def __hash__(self):
        return hash(self.id) ^ hash(self._type) ^ hash(self._class)


class BaseReference(Model):
    def __init__(self, target, source, document=None, session=None):
        super(BaseReference, self).__init__(session=session, document=document)

        target._session = session or self._session
        source._session = session or self._session

        self.target = target
        self.source = source

    @property
    def serialize(self):
        return {
            'class': self._class,
            'type': self._type,
            'target': self.target.serialize,
            'source': self.source.serialize
        }

    def __repr__(self):
        return "{.source}→{._type}→{.target}".format(self, self, self)

    def __eq__(self, obj):
        try:
            # XXX check indexed field?
            return self.target == obj.target and \
                   self.source == obj.source
        except AttributeError:
            return False

    def __hash__(self):
        return hash(self.source) ^ hash(self.target) ^ \
               hash(self._type) ^ hash(self._class)


class Fact(BaseFact):
    """Fact Model"""
    _class = FACT_CLASS

    def __init__(self, id, document=None, session=None, **kwargs):
        super(Fact, self).__init__(
            id, session=session, document=document, **kwargs)

        self.__annotations = AnnotationQuerySet(
            self, session=session or self._session)

    @property
    def annotations(self):
        return self.__annotations

    @sessionize
    def _annotations(self, annotations, limit, session=None):
        queries = []
        query = {"query": queries}

        if annotations:
            for annotation in annotations:
                queries.append({
                    "class": "annotation",
                    "type": annotation._type,
                    "fact": self.serialize
                })

        if limit is not None:
            query['limit'] = limit

        for item in session._query(query):
            yield TypeFactory.deserialize(item)

    def __repr__(self):
        return '{._type}({.id})'.format(self, self)


class Annotation(Model):
    """Annotation Model"""
    _class = ANNOTATION_CLASS

    @property
    def serialize(self):
        result = {
            'type': self._type,
            'class': self._class,
            'label': self.label
        }
        if self.fact:
            result['fact'] = self.fact.serialize

        return result

    def __init__(self, fact, label, document=None, session=None):
        super(Annotation, self).__init__(session=session, document=document)

        self.label = label
        self.fact = fact

    def __repr__(self):
        return "{.fact}♪{._type}({.label})".format(self, self, self)


class SysFact(BaseFact):
    """SysFact Model"""
    _class = SYSFACT_CLASS


class Reference(BaseReference):
    """Reference Model"""
    _class = REFERENCE_CLASS


class SysRef(BaseReference):
    """SysRef Model"""
    _class = SYSREF_CLASS
