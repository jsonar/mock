import os


class MockTransport:
    def __init__(self, *kargs):
        pass

    def start_client(self):
        pass

    def auth_publickey(self, *kargs):
        pass

    def auth_password(self, *kargs):
        pass

    def auth_none(self, _):
        pass

    def is_authenticated(self):
        return True

    def close(self):
        pass


class MockSFTPClient:

    @classmethod
    def from_transport(cls, _):
        return cls()

    def chdir(self, _):
        pass

    def mkdir(self, _):
        pass

    def close(self):
        pass

    def _request(self, **kwargs):
        pass

    def stat(self, path):
        return os.stat(path)
