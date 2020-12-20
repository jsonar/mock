import json


crypto_url = 'https://localhost:27999/crypto/current-key'
connection_url = 'https://localhost:27902/jsonar/SonarConnections/1.0.0'
assets_url = connection_url + '/assets'
connections_url = connection_url + '/connections'


class MockAssetsServer:
    def __init__(self, data):
        self.db = MockedDB(data)

    def requests(self, method, url, **kwargs):
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
            asset_id = kwargs['fields']['asset_id']
            return self.get_connection(asset_id)
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
        if asset != 'NOT FOUND':
            return MockResponse(json.dumps(asset), 200, 'OK')

        return MockResponse(f'Failed to get asset with asset_id: {asset_id} ',
                            404, 'NOT FOUND')

    def get_connection(self, asset_id):
        asset = self.get_asset(asset_id)
        if asset.reason == 'OK':
            connection = self.db.get_connection(asset_id)
            if (connection == 'NOT FOUND' or
                    connection['asset_id'] == 'missing_mandatory_fields'):
                return MockResponse('No asset or missing mandatory fields',
                                    500, 'INTERNAL SERVER ERROR')
            return MockResponse(json.dumps([connection]), 200, 'OK')
        return MockResponse(json.dumps('NOT FOUND'), 200, 'OK')

    def set_asset(self, asset):
        if asset and asset['asset_id'] != 'missing_mandatory_fields':
            if self.db.set_asset(asset):
                return MockResponse(json.dumps({'url': f'{assets_url}/asset/{asset["asset_id"]}'}),
                                    201, 'CREATED')
            return MockResponse(json.dumps(f'An asset with id: {asset["asset_id"]} already exists'),
                                409, 'CONFLICT')
        else:
            return MockResponse(json.dumps('Bad Request'), 400, 'BAD REQUEST')

    def set_connection(self, connection):
        if self.db.set_connection(connection):
            return MockResponse(json.dumps({'url': f'{connections_url}/{connection["asset_id"]}'}),
                                201, 'CREATED')
        return MockResponse(json.dumps('Bad Request'), 400, 'BAD REQUEST')

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
        self.asset = data['assets']
        self.connection = data['connections']

    def set_asset(self, asset):
        success = False
        if asset and self.get_asset(asset['asset_id']) == 'NOT FOUND':
            self.asset.append(asset)
            success = True
        return success

    def set_connection(self, connection):
        if connection and connection['asset_id'] != 'missing_mandatory_fields':
            self.connection.append(connection)
            return True
        return False

    def get_asset(self, asset_id):
        return item_by_asset_id(self.asset, asset_id)

    def get_connection(self, asset_id):
        return item_by_asset_id(self.connection, asset_id)


def item_by_asset_id(items, asset_id):
    for item in items:
        if item['asset_id'] == asset_id:
            return item
    return 'NOT FOUND'
