import os

from collections import namedtuple

struct_group = namedtuple('struct_group',
                          ['gr_name', 'gr_passwd', 'gr_gid', 'gr_mem'])


class MockGrp:
    def __init__(self, entries=None):
        if entries is None:
            entries = [
                ('sonar', 'x', 981, [])
            ]
        self.db = [struct_group(*entry) for entry in entries]

    def getgrgid(self, gid):
        for item in self.db:
            if item.gr_gid == gid:
                return item
        raise KeyError(f'getgrgid(): gid not found: {gid}')

    def getgrnam(self, name):
        for item in self.db:
            if item.gr_name == name:
                return item
        raise KeyError(f'getgrnam(): name not found: {name}')

    def getgrall(self):
        return self.db

    def groupadd(self, args):
        for arg in args:
            if not isinstance(arg, (str, bytes, os.PathLike)):
                raise TypeError(f"expected str, bytes or os.PathLike object, not {type(arg)}")

        if '--gid' in args:
            gid = int(args[3])
            name = args[4]
            if gid in [group.gr_gid for group in self.db]:
                raise ValueError(f"groupadd: GID '{gid}' already exists")
        else:
            name = args[2]
            gid = max([group.gr_gid for group in self.db]) + 1

        if name in [group.gr_name for group in self.db]:
            raise ValueError(f"groupadd: group '{name}' already exists")

        self.db.append(struct_group(name, 'x', int(gid), []))
