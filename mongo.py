import os.path
from datetime import datetime, timezone
from bson import ObjectId
from pymongo.errors import DuplicateKeyError, InvalidOperation, BulkWriteError


def match(doc, _filter):
    if _filter:
        return all([_match(doc, k, v) for k, v in _filter.items()])
    return True


def _match(doc, k, v):
    if (isinstance(v, dict)):
        for inner_k, inner_v in v.items():
            if (inner_k == "$exists"):
                return (k in doc) == inner_v
    return doc.get(k) == v


def update(doc, update):
    modified = 0
    if doc:
        for k, v in update.items():
            if k == '$set':
                doc.update(fix_date(v))
                modified = 1
            else:
                raise InvalidOperation
    return modified


def maybe_raise(func):
    def wrapper(self, *args, **kwargs):
        if self.raise_on_next_command is not None:
            e, self.raise_on_next_command = self.raise_on_next_command, None
            raise e
        return func(self, *args, **kwargs)
    return wrapper


class MockBase:
    def __init__(self):
        self.raise_on_next_command = None


class UpdateResult:
    def __init__(self, modified=0, matched=0):
        self.modified_count = modified
        self.matched_count = matched
        self.upserted_id = None

    @property
    def raw_result(self):
        return {
            'modified': self.modified_count,
            'matched': self.matched_count,
            'upserted_id': self.upserted_id
            }


class DeleteResult:
    def __init__(self, count):
        self.deleted_count = count


class InsertManyResult:
    def __init__(self, ids):
        self.inserted_ids = ids


class InsertOneResult:
    def __init__(self, inserted_id):
        self.inserted_id = inserted_id


class MockMongoClient:
    def __init__(self, uri):
        self.db = MockDatabase()
        self.uri = uri
        self.is_primary = True
        self.databases = {}

    def get_default_database(self):
        return self.db

    def __getitem__(self, key):
        if key not in self.databases:
            db = MockDatabase()
            self.databases[key] = db
        return self.databases[key]


def add_id(doc):
    doc['_id'] = doc.get('_id') or ObjectId()
    return doc


def equals(x, y):
    return x == y if x is None else \
        all([x[k] == y.get(k) for k in x.keys() if k != '_id']) \
        and all([y[k] == x.get(k) for k in y.keys() if k != '_id'])


def fix_date(doc):
    if isinstance(doc, dict):
        ret = dict()
        for k, v in doc.items():
            ret[k] = fix_date(v)
        return ret
    if isinstance(doc, datetime) and doc.tzinfo is not None:
        return doc.astimezone(tz=timezone.utc).replace(tzinfo=None)

    return doc


class MockCollection(MockBase):
    def __init__(self, data=None):
        self.db = None
        self.data = [add_id(d) for d in data or []]
        super().__init__()

    @maybe_raise
    def find_one(self, _filter=None):
        return next((e for e in self.data if match(e, _filter)), None)

    @maybe_raise
    def find(self, _filter=None):
        return [e for e in self.data if match(e, _filter)]

    def insert_one(self, doc):
        doc = add_id(fix_date(doc))
        self._check_duplicate(doc)
        self.data.append(doc)
        return InsertOneResult(doc['_id'])

    def update_one(self, _filter, update_doc):
        doc = self.find_one(_filter)
        matched = 0 if doc is None else 1
        modified = 0
        if doc:
            modified += update(doc, update_doc)
        else:
            modified = 0
        return UpdateResult(matched=matched, modified=modified)

    def update_many(self, _filter, update_doc):
        modified = 0
        matched = 0
        to_update = self.find(_filter)
        if to_update:
            for doc in to_update:
                if doc:
                    matched += 1
                    modified += update(doc, update_doc)
                else:
                    modified = 0
        return UpdateResult(matched=matched, modified=modified)

    @maybe_raise
    def insert_many(self, docs, **kwargs):
        docs_with_id = [add_id(fix_date(d)) for d in docs or []]
        ordered = kwargs['ordered'] if 'ordered' in kwargs else True
        success = True
        results = {
            'nInserted': 0,
            'nMatched': 0,
            'nModified': 0,
            'nRemoved': 0,
            'nUpserted': 0,
            'writeConcernErrors': [],
            'writeErrors': []
        }
        for doc in docs_with_id:
            try:
                self._check_duplicate(doc)
                self.data.append(doc)
                results['nInserted'] += 1
            except DuplicateKeyError:
                success = False
                if ordered:
                    raise BulkWriteError(results)
                else:
                    continue
        if success:
            return InsertManyResult([d['_id'] for d in docs_with_id])
        else:
            raise BulkWriteError(results)

    def bulk_write(self, cmds, ordered=False):
        for cmd in cmds:
            out = self.update_one(cmd._filter, cmd._doc)
            if not out.modified_count:
                self.insert_one(cmd._doc['$set'])

    def delete_one(self, _filter):
        e = self.find_one(_filter)
        if e:
            self.data.remove(e)
        return DeleteResult(1 if e else 0)

    def replace_one(self, old, new, upsert=False):
        ret = UpdateResult()
        o = self.find_one(old)
        ret.matched_count = 0 if o is None else 1
        if not equals(o, new):
            d = self.delete_one(old)
            ret.modified_count = d.deleted_count
            if d.deleted_count == 1 or upsert:
                doc = add_id(fix_date(new))
                self.insert_one(doc)
                ret.upserted_id = doc['_id']
        return ret

    def count(self, _filter=None):
        return len(self.find(_filter))

    def count_documents(self, _filter=None):
        return self.count(_filter=_filter)

    def _check_duplicate(self, doc):
        if self.find({'_id': doc['_id']}):
            raise DuplicateKeyError('mock duplicate id: %s' % doc['_id'])

    @maybe_raise
    def clear(self):
        self.data = []

    @maybe_raise
    def aggregate(self, pipeline):
        # only support a single aggregate for now
        assert pipeline == [{'$group': {
            '_id': None,
            'alldocs': {
                '$push': '$$CURRENT'
            }
        }}]
        return iter([{'_id': None, 'alldocs': self.find()}])

    @maybe_raise
    def drop(self):
        self.db.drop_collection(self)


class MockSystemCollection(MockCollection):
    def __init__(self, db, data=None):
        super().__init__(data)
        self.db = db
        self.views = MockCollection()
        self.views.db = db
        self.ingest = MockCollection([
            {
                '_id': 'instance',
                'allow_duplicate_ids': True,
                'buffer_size': 1 << 30
            },
            {
                '_id': 'exception',
                'allow_duplicate_ids': True,
                'buffer_size': 1 << 30
            },
            {
                '_id': 'full_sql',
                'allow_duplicate_ids': True,
                'buffer_size': 8 << 30
            }
        ])
        self.ingest.db = db


class MockDatabase(MockBase):
    def __init__(self):
        self.gid = MockGidCollection(self)
        self.system = MockSystemCollection(self)
        self.collections = {}
        self.return_from_next_command = None
        self.name = 'mock_db'
        super().__init__()

    def __getitem__(self, key):
        if key not in self.collections:
            c = MockCollection()
            c.db = self
            self.collections[key] = c
        return self.collections[key]

    def __setitem__(self, key, value):
        value.db = self
        self.collections[key] = value

    def __getattr__(self, name):
        ''' immitate pymongo magic for collection names as attribute '''
        return self.__getitem__(name)

    def collection_names(self):
        return self.collections.keys()

    def list_collection_names(self):
        return self.collection_names()

    def drop_collection(self, collection):
        name = None
        for name, c in self.collections.items():
            if collection is c:
                break
        if name:
            del self.collections[name]

    @maybe_raise
    def command(self, cmd):
        ret = None
        it = iter(cmd)
        sonar_command = next(it)
        if sonar_command == 'merge_part':
            assert cmd[sonar_command] == 1, f'cmd[{sonar_command}] must be 1'
            assert 'source' in cmd, f'source must be in {cmd}'
            source = cmd['source']
            assert os.path.exists(source), f'{source} must exist'
            assert os.path.isdir(source), f'{source} must be a directory'
            database = os.path.join(source, 'database')
            assert os.path.exists(database), f'{database} must exist'
            assert os.path.isfile(database), f'{database} must be a file'
        elif sonar_command == 'allow_duplicate_ids':
            assert isinstance(cmd[sonar_command], dict)
            for key, val in cmd[sonar_command].items():
                assert isinstance(key, str)
                assert isinstance(val, bool)
        elif sonar_command == 'getParameter':
            assert cmd[sonar_command] == 1
            param = next(it)
            assert cmd[param] == 1
            ret = {'ok': 1, param: 0}

        if ret is None:
            ret = self.return_from_next_command
            self.return_from_next_command = None

        return ret


class MockGidCollection(MockCollection):
    def __init__(self, db, data=None):
        super().__init__(data or [
            {'_id': 1, 'gid': 1, 'gmachine_id': '1', 'hostname': 'host1',
             'version': 9, 'current': True},
            {'_id': 2, 'gid': 2, 'gmachine_id': '2', 'hostname': 'host2',
             'version': 9, 'current': True},
            {'_id': 3, 'gid': 3, 'gmachine_id': '3', 'hostname': 'host3',
             'version': 10, 'current': True},
            {'_id': 4, 'gid': 4, 'gmachine_id': '3', 'hostname': 'host4',
             'current': False},
            {'_id': 5, 'gid': 5, 'gmachine_id': '5', 'hostname': 'host5',
             'version': 10, 'current': True}
        ])
        self.db = db
