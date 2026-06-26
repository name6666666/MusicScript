import sys as _sys
from ._music_script import compile as _compile
from ._exception import MusicScriptError
from ._preprocess import preprocess, PreprocessError

def compile(file: str, include_path: list[str] = None, py_import_path: str = '.', print_time = True):
    import time
    start = time.time()
    origin = _sys.path
    _sys.path = py_import_path
    ret = _compile(preprocess(file, include_path))
    _sys.path = origin
    if print_time: print(f'Completed with {time.time() - start:.2f}s')
    return ret
