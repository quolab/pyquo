import six
from .helper import TypeFactory
from collections import defaultdict

from .errors import ValidationError


# Validators
class Validator(object):
    """Callable base class to validate a given value"""
    def __call__(self, value):
        self.validate(value)


class StringValidator(Validator):
    """Validate strings"""
    @classmethod
    def validate(cls, value):
        valid = isinstance(value, str)

        if six.PY2 is True:
            valid |= isinstance(value, unicode)  # noqa

        if valid is False:
            raise ValidationError('expected a string for "{}"'.format(value))


class FloatValidator(Validator):
    """Validate floats"""
    @classmethod
    def validate(cls, value):
        if not isinstance(value, float) and not isinstance(value, int):
            raise ValidationError('expected an int for "{}"'.format(value))


class DictValidator(Validator):
    """Validate dicts"""
    @classmethod
    def validate(cls, value):
        if not isinstance(value, dict):
            raise ValidationError('execpted a dict for "{}"'.format(value))


class IntegerValidator(Validator):
    """Validate integers"""
    @classmethod
    def validate(cls, value):
        if not isinstance(value, int):
            raise ValidationError('expected an int for {} ({})'.format(
                value, type(value)))


class ChoiceValidator(Validator):
    """Validate that a flavor is either 'hypothesis', 'case' or folder'"""

    def __init__(self, choices):
        self._choices = choices

    def validate(self, value):
        if value not in self._choices:
            raise ValidationError('expected "{}" to be one of {}'.format(
                value, self._choices))


class ListValidator(Validator):
    """Validate that field is a List. If a type is given the validator will
    validate that all elements of the list are of the given type"""
    def __init__(self, type):
        self.type = type

    def validate(self, value):
        if not isinstance(value, list):
            raise ValidationError('expected a list for {}'.format(value))

        if not self.type:
            return

        for element in value:
            if not isinstance(element, self.type):
                raise ValidationError(
                    'expected list element to be of type {}'.format(self.type))


# Fields
class Field(object):
    """The Field class is the class of which all other fields are derived.
    It implements the __get__ and __set__ methods to store and read value
    information to and from the parent._data and parent._fields
    properities.
    """
    _toResolve = defaultdict(list)

    def __init__(self, field=None, required=False,
                 read_only=False, nullable=False, validators=()):
        """
        Constructor of Field

        :param field: if set to non-None the field will be used as a name
            mapping
        :param read_only: if set to True, the field will be set to read_only
            and never be passed to the import endpoint when creating the object
        :param nullable: if set to True, this field ensures that the value of
            this field can be None
        :param validators: Tuple of validator classes

        :Example:

        >>> created_at = String(read_only=True, field="created-at")
        """
        self.validators = validators
        self.nullable = nullable
        self.field = field
        self.read_only = read_only

        self.required = required

    def __get__(self, parent, owner):
        """Get a property using lazy fetching of the entire object if a value
        of the requested property is not cached in the _data field of the model
        instance. Otherwise the cached value is returned from _data. If lazy a
        lazy fetch is performed all cached values will be overwritten"""

        if parent is None:
            return self

        """lazy fetching"""
        if self not in parent._data:
            if parent._session:
                parent.get()

        return parent._data.get(self, Unset)

    def __set__(self, parent, value):
        """Store value of a given property into the _data field of the model
        instance and trigger validators"""
        if value is None and self.nullable is True:
            parent._data[self] = None
            return

        self.validate(value)
        parent._data[self] = value

    @classmethod
    def _resolve(cls, glob):
        """Allow resolves of class names as string references. Fields
        must implement the _resolve method"""
        for typename, lst in cls._toResolve.items():
            for ob in lst:
                ob._resolve(glob[typename])

    def validate(self, value):
        """Iterate over all validators and trigger them"""
        for validator in self.validators:
            validator(value)


# Field Types
class Any(Field):
    """Any field"""


class Unset(Field):
    """Unset field"""


class Integer(Field):
    """Integer field"""
    def __init__(self, *args, **kwargs):
        super(Integer, self).__init__(
            validators=(IntegerValidator(),), *args, **kwargs)


class String(Field):
    """String field"""
    def __init__(self, *args, **kwargs):
        super(String, self).__init__(
            validators=(StringValidator(),), *args, **kwargs)


class Flavor(Field):
    """Flavor field"""
    def __init__(self, *args, **kwargs):
        super(Flavor, self).__init__(
            validators=(ChoiceValidator(['hypothesis', 'case', 'folder']),),
            *args, **kwargs)


class Float(Field):
    """Float field"""
    def __init__(self, *args, **kwargs):
        super(Float, self).__init__(
            validators=(FloatValidator(),), *args, **kwargs)


class Relation(Field):
    """Relation field"""
    def __init__(self, *args, **kwargs):
        super(Relation, self).__init__(
            validators=(DictValidator(),), *args, **kwargs)

    def __set__(self, parent, value):
        from .models import Model

        if isinstance(value, Model):
            value = TypeFactory._type_class(value['type'])(
                id=value['id'],
                session=parent._session,
                **value.get('document', {})
            )
        parent._data[self] = value


class List(Field):
    """List field. If Type is not None the list will validate that all
    elements of the list are of the given type"""
    def __init__(self, type=None, *args, **kwargs):
        self.type = type

        if isinstance(type, str):
            self._toResolve[type].append(self)
            return super(List, self).__init__(*args, **kwargs)

        super(List, self).__init__(
            validators=(ListValidator(type),), *args, **kwargs)

    def __set__(self, parent, value):
        if self.type:
            value = [self.type(parent._session, **v) for v in value]

        super(List, self).__set__(parent, value)

    def _resolve(self, typ):
        self.validators = (ListValidator(typ),)
        self.type = typ


class Dict(Field):
    """Dict field"""
    def __init__(self, *args, **kwargs):
        super(Dict, self).__init__(
            validators=(DictValidator(),), *args, **kwargs)


Field._resolve(globals())
