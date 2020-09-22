from collections import namedtuple

struct_passwd = namedtuple('struct_passwd',
                           ['pw_name', 'pw_passwd', 'pw_uid',
                            'pw_gid', 'pw_gecos', 'pw_dir', 'pw_shell'])


class MockPwd:
    def __init__(self, entries=None):
        if entries is None:
            entries = [
                ('sonarw', 'x', 981, 981, 'jsonar system user',
                 '/home/sonarw', '/bin/bash'),
                ('sonargd', 'x', 980, 981, 'jSonar system user',
                 '/home/sonargd', '/bin/bash'),
            ]
        self.db = [struct_passwd(*entry) for entry in entries]

    def getpwuid(self, uid):
        for item in self.db:
            if item.pw_uid == uid:
                return item
        raise(KeyError(f'getpwuid(): uid not found {uid}'))

    def getpwnam(self, name):
        for item in self.db:
            if item.pw_name == name:
                return item
        raise(KeyError(f'getpwnam(): name not found {name}'))

    def get_pwall(self):
        return self.db
