import logging

from .errors import SessionError

logger = logging.getLogger(__name__)

class_registry = {}

SYSREF_CLASS = "sysref"
SYSFACT_CLASS = "sysfact"
FACT_CLASS = "fact"
ANNOTATION_CLASS = "annotation"
REFERENCE_CLASS = "reference"


def sessionize(func):
    def wrapper(self, *args, **kwargs):
        session = None
        if func.__code__.co_argcount == 2:
            if len(args) == 1:
                session = args[0]
                args = ()
            else:
                session = kwargs.get('session')

        kwargs.setdefault('session', session or self._session)

        if kwargs.get('session') is None:
            raise SessionError("No session provided")

        return func(self, *args, **kwargs)
    return wrapper


def _register_class(key, value):
    class_registry[key] = value


def _resolve_classes(glob):
    for k, v in class_registry.items():
        class_registry[k] = glob[v]


def ClassFactory(name, argnames, baseClass):
    from .base import Fact, SysFact, Reference, SysRef

    class_map = {
        SYSREF_CLASS: SysRef,
        REFERENCE_CLASS: Reference,
        FACT_CLASS: Fact,
        SYSFACT_CLASS: SysFact
    }

    def __init__(self, *args, **kwargs):
        for key, value in kwargs.items():
            if key not in argnames:
                raise TypeError("Argument %s not valid for %s"
                                % (key, self.__class__.__name__))
        baseClass.__init__(self, *args, **kwargs)

    def get_class_name(name):
        return "".join([i.capitalize() for i in name.split('-')])

    baseClass = class_map[baseClass]
    newclass = type(get_class_name(name), (baseClass,), {"__init__": __init__})
    newclass._type = name
    newclass._phantom = True

    return newclass


class TypeFactory():
    """This class generates pyquo model objects from json"""
    class_argnames = {
        REFERENCE_CLASS: ('target', 'source', 'document', 'session'),
        SYSREF_CLASS: ('target', 'source', 'document', 'session'),
        FACT_CLASS: ('id', 'document', 'session'),
        SYSFACT_CLASS: ('id', 'document', 'session'),
        ANNOTATION_CLASS: ('fact', 'label', 'document', 'session')
    }

    @classmethod
    def _type_class(cls, type, argnames, baseClass):
        klass = class_registry.get(type)
        if klass is None:
            logger.warning('class %s not implemented', type)
            return ClassFactory(
                name=type,
                argnames=argnames,
                baseClass=baseClass
            )

        return klass

    @classmethod
    def _create_object(cls, type, baseClass):
        """This function allows generating unknown model classes on-the-fly.
        The class_argnames variable holds the definition of the constructor
        parameters for each model parent class type"""

        argnames = cls.class_argnames[baseClass]

        return cls._type_class(
            type=type,
            argnames=argnames,
            baseClass=baseClass
        )

    @classmethod
    def create_fact(cls, serialized):
        baseClass = serialized['class']

        factType = cls._create_object(serialized['type'], baseClass)
        obj = factType(id=serialized['id'])

        if 'document' in serialized:
            obj.document = serialized['document']

        return obj

    @classmethod
    def create_reference(cls, serialized):
        baseClass = serialized['class']
        target = serialized['target']
        source = serialized['source']

        # XXX remove once this is implemented serverside
        if target.get('class') is None:
            target['class'] = FACT_CLASS
        if source.get('class') is None:
            source['class'] = FACT_CLASS

        target = cls.create_fact(target)
        source = cls.create_fact(source)

        refType = cls._create_object(serialized['type'], baseClass)
        obj = refType(target=target, source=source)

        if 'document' in serialized:
            obj.document = serialized['document']

        if "index" in serialized:
            obj.index = serialized["index"]

        return obj

    @classmethod
    def create_annotation(cls, serialized):
        baseClass = serialized['class']

        # XXX remove once this is implemented serverside
        serialized['fact']['class'] = FACT_CLASS

        fact = cls.create_fact(serialized['fact'])
        annoType = cls._create_object(serialized['type'], baseClass)
        obj = annoType(fact=fact, label=serialized['label'])

        if 'document' in serialized:
            obj.document = serialized['document']

        return obj

    @classmethod
    def deserialize(cls, serialized):
        """This method deserializes a dictionary and returns a pyquo object"""
        baseClass = serialized.get('class', 'fact')

        if baseClass in (SYSREF_CLASS, REFERENCE_CLASS):
            return cls.create_reference(serialized)

        if baseClass in (SYSFACT_CLASS, FACT_CLASS):
            return cls.create_fact(serialized)

        if baseClass == ANNOTATION_CLASS:
            return cls.create_annotation(serialized)

        raise Exception('unknown base class %s', baseClass)
