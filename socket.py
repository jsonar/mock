class MockSocket:
    AF_INET = 0
    SOCK_STREAM = 0

    def __init__(self, **kwargs):
        pass

    def socket(family, typ):
        del family
        del typ
        return MockSocket()

    def __enter__(self):
        return self

    def __exit__(self, _, value, traceback):
        return True

    def connect(self, **kwargs):
        pass

    def sendall(self, **kwargs):
        pass
