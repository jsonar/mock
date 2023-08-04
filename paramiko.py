import os
import shutil
from paramiko.sftp_attr import SFTPAttributes

class MockTransport:
    def __init__(self, *kargs):
        pass

    def start_client(self, **kargs):
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
    def from_transport_(cls, t, **kargs):
        return cls()

    def chdir(self, path):
        os.chdir(path)

    def mkdir(self, path):
        os.mkdir(path)

    def close(self):
        pass

    def _request(self, **kwargs):
        pass

    def stat(self, path):
        return os.stat(path)

    def unlink(self, path):
        os.unlink(path)

    def get(self, remote, local):
        shutil.copy(remote, local)

    def listdir(self, path):
        return os.listdir(path)

    def posix_rename(self, src, dst):
        return os.rename(src, dst)

    def listdir_attr(self, path="."):
        ret = []
        for filename in os.listdir(path):
            child = os.lstat(filename)
            ret.append(SFTPAttributes.from_stat(child, filename))
        return ret

    def rmdir(self, path):
        os.rmdir(path)

    def getcwd(self):
        return os.getcwd()

    def get_channel(self):
        return MockChannel()


class MockChannel:
    def getpeername(self):
        return ("127.0.0.1", None)
