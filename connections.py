import json

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
            return self.post_endpoints(url, **kwargs)
        elif method == 'DELETE':
            return self.delete_endpoints(url, **kwargs)

    def get_endpoints(self, url, **kwargs):
        if url == crypto_url:
            return self.get_current_crypto
        elif assets_url in url:
            asset_id = url.rsplit('/', 1)[1]
            return self.get_asset(asset_id)
        elif connections_url in url:
            asset_id = kwargs['fields']['asset_id']
            return self.get_connections(asset_id)
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

    def post_endpoints(self, url, **kwargs):
        if assets_url in url:
            asset_id = url.rsplit('/', 1)[1]
            asset = json.loads(kwargs['body'])
            return self.update_asset(asset_id, asset)
        elif connections_url in url:
            _id = url.rsplit('/', 1)[1]
            connection = json.loads(kwargs['body'])
            return self.update_connection(_id, connection)

        return MockResponse('Page not found', 404, 'NOT FOUND')

    def delete_endpoints(self, url, **kwargs):
        if assets_url in url:
            pass
        elif connections_url in url:
            _id = url.rsplit('/', 1)[1]
            return self.delete_connection(_id)

        return MockResponse('Page not found', 404, 'NOT FOUND')

    def get_asset(self, asset_id):
        asset = self.db.get_asset(asset_id)
        if asset is not None:
            return MockResponse(json.dumps(asset), 200, 'OK')

        return MockResponse(f'Failed to get asset with asset_id: {asset_id} ',
                            404, 'NOT FOUND')

    def get_connections(self, asset_id):
        connections = self.db.get_connections(asset_id)
        if connections:
            return MockResponse(json.dumps(connections), 200, 'OK')

        return MockResponse(f'Failed to get connections with asset_id: {asset_id} ',
                            404, 'NOT FOUND')

    def set_asset(self, asset):
        if asset and asset['asset_id'] != 'missing_mandatory_fields':
            if self.db.set_asset(asset):
                return MockResponse(
                    json.dumps({'url': f'{assets_url}/asset/{asset["asset_id"]}'}),
                    201, 'CREATED')
            else:
                return MockResponse('Asset exists', 409, 'CONFLICT')
        else:
            return MockResponse('Missing mandatory fields', 400,
                                'BAD REQUEST')

    def set_connection(self, connection):
        response = self.db.set_connection(connection)
        if response['success']:
            return MockResponse(
                json.dumps(
                    {'url': f'{connections_url}/{connection["asset_id"]}'}
                ), 201, 'CREATED')
        else:
            return MockResponse(response['message'], 400,
                                'BAD REQUEST')

    def update_asset(self, asset_id, asset):
        if self.db.update_asset(asset_id, asset):
            return MockResponse(json.dumps(asset), 200, 'OK')

        return MockResponse(f'No asset with asset_id: {asset_id} ',
                            404, 'NOT FOUND')

    def update_connection(self, _id, connection):
        if self.db.update_connection(_id, connection):
            return MockResponse(json.dumps(connection), 200, 'OK')

        return MockResponse(f'No conection with asset_id: {_id} ',
                            404, 'NOT FOUND')

    def delete_connection(self, _id):
        for connection in self.db.connection:
            if connection['_id'] == _id:
                self.db.connection.remove(connection)
                return MockResponse(json.dumps(connection), 200, 'OK')

        return MockResponse(f'No resource found to update: {_id} ',
                            500, 'NOT FOUND')

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
        if not self.get_asset(asset['asset_id']):
            self.asset.append(asset)
            return True
        else:
            return False

    def set_connection(self, connection):
        if connection['asset_id'] == 'missing_mandatory_fields':
            response = {'success': False, 'message': 'missing_mandatory_fields'}
        elif connection in self.connection:
            response = {'success': False, 'message': f'Attempted to insert duplicate ID: {connection["_id"]}'}
        else:
            self.connection.append(connection)
            response = {'success': True, 'message': 'Success'}
        return response

    def get_asset(self, asset_id):
        return item_by_asset_id(self.asset, asset_id)

    def get_connections(self, asset_id):
        return items_by_asset_id(self.connection, asset_id)

    def update_asset(self, asset_id, asset):
        for i, item in enumerate(self.asset):
            if item['asset_id'] == asset_id:
                self.asset[i] = {**item, **asset}
                return True
        return False

    def update_connection(self, _id, connection):
        success = False
        for i, item in enumerate(self.connection):
            if item['_id'] == _id:
                self.connection[i] = {**item, **connection}
                success = True
        return success


def item_by_asset_id(items, asset_id):
    for item in items:
        if item['asset_id'] == asset_id:
            return item
    return None


def items_by_asset_id(items, asset_id):
    results = []
    for item in items:
        if item['asset_id'] == asset_id:
            results.append(item)
    return results
