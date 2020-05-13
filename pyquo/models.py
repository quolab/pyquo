import os.path

from .session import FILE_UPLOAD
from .helper import _resolve_classes, sessionize
from .fields import Dict, List, String, Float, Integer, Flavor
from .base import Reference, SysRef, Fact, SysFact, Annotation


# Facts
class Certificate(Fact):
    _type = 'certificate'


class Email(Fact):
    _type = 'email'


class Envelope(Fact):
    _type = 'envelope'


class ExportTable(Fact):
    _type = 'export-table'


class File(Fact):
    _type = 'file'

    # md5 = String()
    # sha256 = String()
    # sha1 = String()

    # # XXX old format
    # mime_type = String(field='mime-type')
    # language_name = String()
    # language_id = Integer()
    # language_country = String()
    # type_name = String()
    # type_id = Integer()
    # tlsh = String()
    # magic = Dict()

    @staticmethod
    def _extract_filename(file_obj):
        name = getattr(file_obj, 'name', None)

        return os.path.basename(name) if name else None

    @classmethod
    @sessionize
    def upload(cls, file_obj, filename=None, session=None):
        """ This function uploads a file_obj to quolab

        :param file_obj: can be a file-like object such as BytesIO
             or a string
        :param str filename: Name of the file, if not provided it will be
        guessed based on file_obj.name

        :returns: An instance of pyquo.models.File
        """
        try:
            content = file_obj.read()
        except AttributeError:
            content = file_obj

        headers = {'Content-Type': 'application/octet-stream'}
        data = session.http_post(FILE_UPLOAD, data=content, headers=headers)
        f = cls(id=data.json()['records'][0]['id']).get(session)

        if filename is None:
            filename = cls._extract_filename(file_obj)

        if filename:
            KnownAs(f, filename).save(session=session)

        return f

    @sessionize
    def download(self, session=None):
        url = '/v1/file/{}'.format(self.id)
        return session.http_get(url)


class Function(Fact):
    _type = 'function'

    @sessionize
    def similar(self, session=None):
        path = '/v1/function/{}/similar'.format(self.id)
        response = session.http_get(path).json()
        similars = response.get('records', [])

        return (
            Function(id=match['id'], session=session)
            for match in similars
        )


class Hostname(Fact):
    _type = 'hostname'


class ImportTable(Fact):
    _type = 'import-table'


class IpAddress(Fact):
    _type = 'ip-address'

    version = Integer()


class Ipynb(Fact):
    _type = 'ipynb'

    notebook = Dict()


class Malware(Fact):
    _type = 'malware'


class MispBlob(Fact):
    _type = 'misp-blob'


class MispEvent(Fact):
    _type = 'misp-event'


class TTP(Fact):
    _type = 'ttp'


class Mutex(Fact):
    _type = 'mutex'


class Organization(Fact):
    _type = 'organization'


class Persona(Fact):
    _type = 'persona'


class PGP(Fact):
    _type = 'persona'

    key_id = String(field='key-id')


class Process(Fact):
    _type = 'process'


class RegistryKey(Fact):
    _type = 'registry-key'


class URL(Fact):
    _type = "url"

    netloc = String(read_only=True)
    scheme = String(read_only=True)
    path = String(read_only=True)
    query = String(read_only=True)
    hostname = String(read_only=True)


class Wallet(Fact):
    _type = 'wallet'


class YaraRule(Fact):
    _type = 'yara-rule'


class AutonomousSystem(Fact):
    _type = 'autonomous_system'


class Region(Fact):
    _type = 'region'


class TorDescriptor(Fact):
    _type = 'tor-descriptor'


# System Facts
class Case(SysFact):
    _type = "case"

    name = String(required=True)
    description = String(required=True, nullable=True)
    priority = Float(nullable=True)
    flavor = Flavor()
    type = String(required=True)

    created_at = Float(read_only=True, field='created-at')
    created_by = String(read_only=True, nullable=True, field='created-by')
    updated_at = Float(read_only=True, field='updated-at')
    contributors = List(read_only=True, type='Contributor')

    def __init__(self, id=None, **kwargs):
        super().__init__(id, **kwargs)

    @property
    def id(self):
        if self._id is None:
            self._id = '__new__'

        return self._id

    @id.setter
    def id(self, value):
        self._id = value


class User(SysFact):
    _type = 'user'

    @classmethod
    @sessionize
    def current(cls, session=None):
        user_id = session.current_user
        return User(id=user_id)


class Tag(SysFact):
    _type = 'tag'

    name = String(required=True)
    taxonomy = String(required=True)

    def __repr__(self):
        return '{._type}({.name})'.format(self, self)


class Endpoint(SysFact):
    _type = 'endpoint'

    @property
    def connector(self):
        connector = self.descendants(facts=Connector)
        if connector:
            return connector[0]


class Connector(SysFact):
    _type = 'connector'

    @property
    def endpoints(self):
        return self.ancestors(facts=Endpoint)


class Regulator(SysFact):
    _type = 'regulator'


class Source(SysFact):
    _type = 'source'


class Sink(SysFact):
    _type = 'sink'


class Task(SysFact):
    _type = 'task'


# References
class Accesses(Reference):
    _type = 'accesses'


class RelatesTo(Reference):
    _type = 'relates-to'


class Contains(Reference):
    _type = "contains"


class Creates(Reference):
    _type = 'creates'


class Delivered(Reference):
    _type = 'delivered'


class IdentifiedAs(Reference):
    _type = 'identified-as'


class IdentifiedBy(Reference):
    _type = 'identified-by'


class Loads(Reference):
    _type = 'loads'


class ReferredBy(Reference):
    _type = 'referred-by'


class SignedBy(Reference):
    _type = 'signed-by'


class ResolvedTo(Reference):
    _type = 'resolved-to'


class CommentedBy(SysRef):
    _type = 'commented-by'

    body = String(field='body')
    created_at = Float(read_only=True, field='created-at')


# SysRefs
class Queued(SysRef):
    _type = 'queued'

    queued_at = Float(read_only=True, field='queued-at')


class Scheduled(SysRef):
    _type = 'scheduled'

    scheduled_at = Float(read_only=True, field='scheduled-at')


class Executed(SysRef):
    _type = 'executed'

    executed_at = Float(read_only=True, field='executed-at')


class Canceled(SysRef):
    _type = 'canceled'

    canceled_at = Float(read_only=True, field='canceled-at')


class Failed(SysRef):
    _type = 'failed'

    failed_at = Float(read_only=True, field='failed-at')


class ObservedBy(SysRef):
    _type = 'observed-by'


class AssociatedWith(SysRef):
    _type = 'associated-with'


class Encases(SysRef):
    _type = 'encases'


class Tagged(SysRef):
    _type = 'tagged'


class Uses(SysRef):
    _type = 'uses'


class Implies(SysRef):
    _type = 'implies'


# Annotations
class Attribute(Annotation):
    _type = 'attribute'


class PublicSubkey(Annotation):
    _type = 'public-subkey'


class SecretSubkey(Annotation):
    _type = 'secret-subkey'


class Text(Annotation):
    _type = 'text'


class InterpretedAs(Annotation):
    _type = 'interpreted-as'


class KnownAs(Annotation):
    _type = 'known-as'


class Report(Annotation):
    _type = 'report'


_resolve_classes(globals())
