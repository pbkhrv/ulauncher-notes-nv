import os
from tempfile import TemporaryDirectory


def create_text_file(path, filename, text):
    full_path = os.path.join(path, filename)
    with open(full_path, "w") as f:
        print(text, file=f)
    return full_path


def with_temp_dir(filenames):
    def decorator(func):
        def wrapper(self):
            with TemporaryDirectory() as path:
                for fn in filenames:
                    create_text_file(path, fn, "")
                func(self, path)

        return wrapper

    return decorator
