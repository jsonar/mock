def maybe_raise(func):
    def wrapper(self, *args, **kwargs):
        if self.raise_on_next_command is not None:
            e, self.raise_on_next_command = self.raise_on_next_command, None
            raise e
        return func(self, *args, **kwargs)
    return wrapper


class MockSocket:
    AF_INET = 0
    SOCK_STREAM = 0
    raise_on_next_command = None

    def __init__(self, **kwargs):
        pass

    def socket(family, typ):
        del family
        del typ
        return MockSocket()

    def __enter__(self):
        return self

    def __exit__(self, _, value, traceback):
        return traceback is None

    @maybe_raise
    def connect(self, address, **kwargs):
        pass

    @staticmethod
    def sendall(self, **kwargs):
        pass
