import os


class MockEnt:

    @staticmethod
    def validate_strings(*args):
        for arg in args:
            if arg is not None and not isinstance(arg, (str, bytes, os.PathLike)):
                raise TypeError(f"expected str, bytes or os.PathLike object, not {type(arg)}")
