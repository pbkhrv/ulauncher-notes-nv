import os
from tempfile import TemporaryDirectory


def create_text_file(path, filename, text):
    full_path = os.path.join(path, filename)
    with open(full_path, "w") as f:
        print(text, file=f)
    return full_path


def with_temp_dir(items):
    def decorator(func):
        def wrapper():
            with TemporaryDirectory() as path:
                for item in items:
                    if isinstance(item, str):
                        create_text_file(path, item, "")
                    elif isinstance(item, tuple):
                        create_text_file(path, item[0], item[1])
                    else:
                        raise Exception("with_temp_dir arg should be str or tuple")
                func(path)

        return wrapper

    return decorator
