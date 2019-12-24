from test.mock import mongo
from test.mock.mongo import MockCollection

sample_list = [{'_id': 1, 'something': 'something'}, {'_id': 2, 'something_else': 'something_else'}]


def test_one_matched_none_modified():
    mongo_mock_client = mongo.MockMongoClient(None)
    coll = MockCollection()
    coll.insert_many(sample_list)
    mongo_mock_client['db']['coll'] = coll

    update_result = coll.update_one({"something": {'$exists': True}}, {'$set': {'something': 'something2'}})
    assert update_result.matched_count == 1
    assert update_result.modified_count == 1
    assert mongo_mock_client['db']['coll'].find() == [{'_id': 1, 'something': 'something2'},
                                                      {'_id': 2, 'something_else': 'something_else'}]


def test_none_matched_none_modified():
    mongo_mock_client = mongo.MockMongoClient(None)
    coll = MockCollection()
    coll.insert_many(sample_list)
    mongo_mock_client['db']['coll'] = coll

    update_result = coll.update_one({"something_": {'$exists': True}}, {'$set': {'something': 'something2'}})
    assert update_result.matched_count == 0
    assert update_result.modified_count == 0
    assert mongo_mock_client['db']['coll'].find() == sample_list


def test_update_many():
    mongo_mock_client = mongo.MockMongoClient(None)
    coll = MockCollection()
    coll.insert_many([{'_id': 1, 'something': 'something'}, {'_id': 2, 'something': 'something'}])
    mongo_mock_client['db']['coll'] = coll

    update_result = coll.update_many({"something": {'$exists': True}}, {'$set': {'something': 'something2'}})
    assert update_result.matched_count == 2
    assert update_result.modified_count == 2
    assert mongo_mock_client['db']['coll'].find() == [{'_id': 1, 'something': 'something2'},
                                                      {'_id': 2, 'something': 'something2'}]
