from bson import ObjectId


def match(doc, _filter):
    if _filter:
        return all([doc.get(k) == v for k, v in _filter.items()])
    return True


class UpdateResult:
    def __init__(self, modified=0, matched=0):
        self.modified_count = modified
        self.matched_count = matched
        self.upserted_id = None


class DeleteResult:
    def __init__(self, count):
        self.deleted_count = count


class InsertManyResult:
    def __init__(self, ids):
        self.inserted_ids = ids


class MockMongoClient:
    def __init__(self, uri):
        self.db = MockDatabase()
        self.uri = uri
        self.is_primary = True

    def get_default_database(self):
        return self.db


class MockException(Exception):
    pass


class DuplicateKeyError(MockException):
    pass


def add_id(doc):
    doc['_id'] = doc.get('_id') or ObjectId()
    return doc


def equals(x, y):
    return x == y if x is None else \
        all([x[k] == y.get(k) for k in x.keys() if k != '_id']) \
        and all([y[k] == x.get(k) for k in y.keys() if k != '_id'])


class MockCollection:
    def __init__(self, data=None):
        self.data = [add_id(d) for d in data or []]

    def find_one(self, _filter=None):
        return next((e for e in self.data if match(e, _filter)), None)

    def find(self, _filter=None):
        return [e for e in self.data if match(e, _filter)]

    def insert_one(self, doc):
        doc_with_id = add_id(doc)
        self._check_duplicate(doc_with_id)
        self.data.append(doc_with_id)

    def insert_many(self, docs):
        docs_with_id = [add_id(d) for d in docs or []]
        for doc in docs_with_id:
            self._check_duplicate(doc)
        self.data.extend(docs_with_id)
        return InsertManyResult([d['_id'] for d in docs_with_id])

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
                add_id(new)
                self.insert_one(new)
                ret.upserted_id = new['_id']
        return ret

    def count(self, _filter=None):
        return len(self.find(_filter))

    def _check_duplicate(self, doc):
        if self.find({'_id': doc['_id']}):
            raise DuplicateKeyError


class MockSystemCollection(MockCollection):
    def __init__(self, data=None):
        super().__init__(data)
        self.views = MockCollection()
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


class MockDatabase:
    def __init__(self):
        self.gid = MockGidCollection()
        self.system = MockSystemCollection()
        self.collections = {}

    def __getitem__(self, key):
        if key not in self.collections:
            self.collections[key] = MockCollection()
        return self.collections[key]

    def __setitem__(self, key, value):
        self.collections[key] = value

    def __getattr__(self, name):
        ''' immitate pymongo magic for collection names as attribute '''
        return self.__getitem__(name)


class MockGidCollection(MockCollection):
    def __init__(self, data=None):
        super().__init__(data or [
            {'_id': 1, 'gid': 1, 'gmachine_id': '1', 'hostname': 'host1',
             'version': 9, 'current': 'True'},
            {'_id': 2, 'gid': 2, 'gmachine_id': '2', 'hostname': 'host2',
             'version': 9},
            {'_id': 3, 'gid': 3, 'gmachine_id': '2', 'hostname': 'host2',
             'version': 10, 'current': True},
            {'_id': 4, 'gid': 4, 'gmachine_id': '3', 'current': True},
            {'_id': 5, 'gid': 5, 'gmachine_id': '4', 'version': 10,
             'current': True}
        ])
