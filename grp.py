import os

from collections import namedtuple

struct_group = namedtuple('struct_group',
                          ['gr_name', 'gr_passwd', 'gr_gid', 'gr_mem'])
groupadd_cmd = namedtuple('groupadd_cmd',
                          ['command', 'sys_flag', 'gid_flag', 'gid', 'name'])


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
        cmd = self._groupadd_cmd(args)
        for group in self.db:
            if cmd.gid_flag and cmd.gid == group.gr_gid:
                raise ValueError(f"groupadd: GID '{cmd.gid}' already exists")
            if cmd.name == group.gr_name:
                raise ValueError(f"groupadd: group '{cmd.name}' already exists")

        self.db.append(struct_group(cmd.name, 'x', cmd.gid, []))

    def _groupadd_cmd(self, args):
        for arg in args:
            if not isinstance(arg, (str, bytes, os.PathLike)):
                raise TypeError(f"expected str, bytes or os.PathLike object, not {type(arg)}")

        if '--gid' in args:
            args[3] = int(args[3])
        else:
            args.insert(2, False)
            args.insert(3, max([group.gr_gid for group in self.db]) + 1)

        cmd = groupadd_cmd(*args)
        return cmd
