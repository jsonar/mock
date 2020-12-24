import json
import urllib3

crypto_url = 'https://localhost:27999/crypto/current-key'
connection_url = 'https://localhost:27902/jsonar/SonarConnections/1.0.0'
assets_url = connection_url + '/assets'
connections_url = connection_url + '/connections'


class MockAssetsServer:
    def __init__(self, data):
        self.db = MockedDB(data)

    def request(self, method, url, **kwargs):
        if method == 'GET':
            return self.get_endpoints(url, **kwargs)
        elif method == 'PUT':
            return self.put_endpoints(url, **kwargs)
        elif method == 'POST':
            pass
        elif method == 'DELETE':
            pass

    def get_endpoints(self, url, **kwargs):
        if url == crypto_url:
            return self.get_current_crypto
        elif assets_url in url:
            asset_id = url.rsplit('/', 1)[1]
            return self.get_asset(asset_id)
        elif connections_url in url:
            pass

        return MockResponse('Page not found', 404, 'NOT FOUND')

    def put_endpoints(self, url, **kwargs):
        if assets_url in url:
            asset = json.loads(kwargs['body'])
            return self.set_asset(asset)
        elif connections_url in url:
            connection = json.loads(kwargs['body'])
            return self.set_connection(connection)

        return MockResponse('Page not found', 404, 'NOT FOUND')

    def get_asset(self, asset_id):
        asset = self.db.get_asset(asset_id)
        if asset is not None:
            return MockResponse(json.dumps(asset), 200, 'OK')

        return MockResponse(f'Failed to get asset with asset_id: {asset_id} ',
                            404, 'NOT FOUND')

    def set_asset(self, asset):
        if asset and asset['asset_id'] != 'missing_mandatory_fields':
            self.db.set_asset(asset)
            return MockResponse(
                json.dumps({'url': f'{assets_url}/asset/{asset["asset_id"]}'}),
                201, 'CREATED')
        else:
            raise_max_retry_exception('400', '27902', 'set_asset')

    def set_connection(self, connection):
        self.db.set_connection(connection)
        return MockResponse(
            json.dumps({'url': f'{connections_url}/{connection["asset_id"]}'}),
            201, 'CREATED')

    @property
    def get_current_crypto(self):
        return MockResponse('THIS IS THE CRYPTO KEY', 200, 'OK')


class MockResponse:
    def __init__(self, data, status_code, reason):
        self.data = data.encode('utf-8')
        self.status = status_code
        self.reason = reason


class MockedDB:
    def __init__(self, data):
        self.name = 'lmrm__sonarg'
        self.asset = data['assets'].copy()
        self.connection = data['connections'].copy()

    def set_asset(self, asset):
        if asset and not self.get_asset(asset['asset_id']):
            self.asset.append(asset)
        else:
            raise_max_retry_exception('400', '27902', 'db/set_asset')

    def set_connection(self, connection):
        if connection and connection['asset_id'] != 'missing_mandatory_fields':
            self.connection.append(connection)
        else:
            raise_max_retry_exception('400', '27902', 'db/set_connection')

    def get_asset(self, asset_id):
        return item_by_asset_id(self.asset, asset_id)


def raise_max_retry_exception(code, port, func):
    raise urllib3.exceptions.MaxRetryError(
        pool=urllib3.HTTPSConnectionPool(host='localhost', port=port),
        url=f'localhost/{func}',
        reason=f'too many {code} error responses')


def item_by_asset_id(items, asset_id):
    for item in items:
        if item['asset_id'] == asset_id:
            return item
    return None
