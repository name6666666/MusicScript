import re
import sys
from jinja_script_block import ScriptBlockExtension
from jinja2 import Environment, FileSystemLoader
from pathlib import Path
from importlib import resources
from ast import literal_eval
from dataclasses import dataclass
from lark import Lark, Transformer


class PreprocessError(Exception):
    pass

STD = str(resources.files('music_script') / 'include') if not getattr(sys, 'frozen', False) else str(Path(sys.executable).parent / 'include')

def prepreprocess_include(file: str, include_path: list[str] = None):
    include = [str(Path(file).parent), STD] + (include_path if include_path is not None else [])
    def search(file):
        if file:
            for i in include:
                if Path(i).joinpath(file).is_file():
                    return str(Path(i) / file)
        raise PreprocessError(f'Can not find file {file}')
    code = Path(file).read_text('utf-8')
    while True:
        new = re.sub(r'\{\%\s*include\s*([^{}]+)\s*\%\}', lambda m: prepreprocess_include(search(literal_eval(m.group(1))), include_path), code)
        if code == new:
            break
        code = new
    return code

def prepreprocess_macro(string):
    @dataclass
    class Macro:
        name: str
        params: 'list[list[str | Macro]]'

    grammer = r'''
    start: (TEXT | macro)*

    param: (/(?:[^$(),]|\s)+/ | macro)*
    TEXT: /(?:[^$]|\s)+/
    macro: "$" CNAME macro_params?
    macro_params.2: "(" _WS? (param [_WS? "," _WS? param]* _WS?)? ")"

    %import common.CNAME
    %import common.WS -> _WS
    '''

    class Trans(Transformer):
        def param(self, args):
            return [i if isinstance(i, Macro) else str(i) for i in args]
        def macro_params(self, args):
            return [i for i in args if i is not None]
        def start(self, args):
            return args
        def TEXT(self, args):
            return str(args)
        def CNAME(self, args):
            return str(args)
        def macro(self, args):
            match args:
                case name, param:
                    return Macro(name, param)
                case name,:
                    return Macro(name, [])

    parser = Lark(grammer, parser='earley', propagate_positions=True)

    def p_to_str(p: list[str | Macro]):
        ret = '""'
        for i in p:
            if isinstance(i, Macro):
                ret += f'+str({i.name}({','.join(p_to_str(j) for j in i.params)}))'
            else:
                ret += f'+{repr(i)}'
        return ret

    def lst_to_str(lst: list[str | Macro]):
        ret = ''
        for i in lst:
            if isinstance(i, Macro):
                ret += f" {{{{ {i.name}({','.join(p_to_str(p) for p in i.params)}) }}}} "
            else:
                ret += i
        return ret

    lst = Trans().transform(parser.parse(string))
    string = lst_to_str(lst)
    return string

def preprocess(file: str, include_path: list[str] = None):
    include = [str(Path(file).parent), STD] + (include_path if include_path is not None else [])
    code = prepreprocess_include(file, include_path)
    code = prepreprocess_macro(code)
    env = Environment(
        loader=FileSystemLoader(include),
        extensions=[ScriptBlockExtension],
        line_statement_prefix='%'
    )
    env.globals.update({
        'int': int, 'float': float, 're': re, 'str': str
    })
    try:
        tmpl = env.from_string(code)
        return tmpl.render()
    except Exception as e:
        raise PreprocessError(e)
