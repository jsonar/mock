from test.mock import mongo
from test.mock.mongo import MockCollection


def test_match_nested_document_filter():
    mongo_mock_client = mongo.MockMongoClient(None)
    coll = MockCollection()
    coll.insert_one({'_id': 'a'})
    mongo_mock_client['db']['coll'] = coll

    assert coll.find({"something": {'$exists': True}}) == []


def test_match_filter_key_not_dict():
    mongo_mock_client = mongo.MockMongoClient(None)
    coll = MockCollection()
    coll.insert_one({'_id': 'a'})
    mongo_mock_client['db']['coll'] = coll

    assert coll.find({'_id': 'a'}) == [{'_id': 'a'}]
