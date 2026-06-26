import re
import sys
from jinja2 import Environment, FileSystemLoader
from pathlib import Path
from importlib import resources
from ast import literal_eval


class PreprocessError(Exception):
    pass

STD = str(resources.files('music_script') / 'include') if not getattr(sys, 'frozen', False) else str(Path(sys.executable).parent / 'include')

def _prep(file: str, include_path: list[str] = None):
    include = [str(Path(file).parent), STD] + (include_path if include_path is not None else [])
    def search(file):
        if file:
            for i in include:
                if Path(i).joinpath(file).is_file():
                    return str(Path(i) / file)
        raise PreprocessError(f'Can not find file {file}')
    code = Path(file).read_text('utf-8')
    while True:
        new = re.sub(r'\{\%\s*include\s*([^{}]+)\s*\%\}', lambda m: _prep(search(literal_eval(m.group(1))), include_path), code)
        if code == new:
            break
        code = new
    return code


def preprocess(file: str, include_path: list[str] = None):
    include = [str(Path(file).parent), STD] + (include_path if include_path is not None else [])
    code = _prep(file, include_path)
    code = re.sub(
        r'\$([A-Za-z_][0-9A-Za-z_]*)(\s*\([^\(\)]*\))?',
        lambda m: ' {{ ' + m.group(1) + ('(' + ', '.join(repr(i.strip()) for i in m.group(2).strip()[1:-1].split(',')) + ')' if m.group(2) else '()') + ' }}',
        code
    )
    env = Environment(loader=FileSystemLoader(include))
    env.globals.update({
        'int': int, 'float': float, 're': re
    })
    try:
        tmpl = env.from_string(code)
        return tmpl.render()
    except Exception as e:
        raise PreprocessError(e)
