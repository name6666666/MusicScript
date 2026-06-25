from __future__ import annotations
from copy import copy
from importlib import resources, reload
from beartype import beartype
from lark import Lark, Transformer
from dataclasses import dataclass
from pretty_midi import PrettyMIDI
from ._exception import MusicScriptError



Number = int | float


@beartype
@dataclass
class Attr:
    key: str
    val: Val

@beartype
@dataclass
class Track:
    is_drum: bool
    name: str
    attr: dict[str, Val]

@beartype
@dataclass
class Score:
    name: str
    attr: dict[str, Val]
    text: str

@beartype
@dataclass
class Python:
    code: str

@beartype
@dataclass
class Template:
    early: bool
    name: str
    beats: int
    notes: int
    text: str

Val = Number | Python

class Trans(Transformer):
    def TEXT1(self, args):
        return str(args)

    def TEXT2(self, args):
        return str(args)
    
    def NAME(self, args):
        return str(args)

    def INT(self, args):
        return int(args)

    def FLOAT(self, args):
        return float(args)
    
    def attr(self, args):
        return Attr(args[0], args[1])

    def track(self, args):
        is_drum, name, *attr= args
        return Track(True if is_drum else False, name, {i.key: i.val for i in attr})
    
    def score(self, args):
        name, *attr, text = args
        return Score(name, {i.key: i.val for i in attr}, text)
    
    def python(self, args):
        return Python(args[0])

    def EARLY(self, args):
        return str(args)
    
    def template(self, args):
        early, name, *attr, text = args
        attr: tuple[Attr]
        attr = {i.key: i.val for i in attr}
        if any(i not in ['beats', 'notes'] for i in attr):
            raise MusicScriptError('Unknown template option')
        return Template(False if early is None else True, name, attr.get('beats', 4), attr.get('notes', 3), text)
    
    def start(self, args):
        return args


parser = Lark(resources.files('music_script').joinpath('grammer.lark').read_text(), parser='lalr', transformer=Trans())




def compile(code: str) -> PrettyMIDI:
    from . import _score
    locals()['_score'] = reload(_score)
    def getattr(dct: dict, default: dict):
        if any(i not in default for i in dct):
            raise MusicScriptError(f'There are unknown options in {', '.join(dct)}')
        ret = {**default, **dct}
        try:
            ret = {k: eval(v.code, globals=_score.ENV) if isinstance(v, Python) else v for k, v in ret.items()}
        except KeyError as e:
            raise MusicScriptError(f'Unknown variable {e.args[0]}')
        return ret
    lst = parser.parse(code)
    for stmt in lst:
        if isinstance(stmt, Track):
            _score.ENV[stmt.name] = _score.Track(**{
                'instr': 0,
                'key': None,
                **getattr(
                    stmt.attr,
                    ({'instr': 0, 'len': 1, 'vel': None, 'key': None, 'hook': None}
                    if not stmt.is_drum else
                    {'len': 1, 'vel': None, 'hook': None})
                ),
                'is_drum': stmt.is_drum
            })
        elif isinstance(stmt, Python):
            dct = {
                'NotrackScore': _score.NotrackScore,
                'Note': _score.Note,
                'Score': _score.Score,
                'Track': _score.Track,
                'copy': copy,
                'Notes': _score.Notes
            }
            dct.update(_score.ENV)
            exec(stmt.code, globals=dct)
            if '__export__' in dct:
                if not isinstance(dct['__export__'], list):
                    raise MusicScriptError('__export__ must be list')
                try:
                    _score.ENV.update({k: dct[k] for k in dct['__export__']})
                except KeyError as e:
                    raise MusicScriptError(f'Can not export {e.args[0]}, not found')
        elif isinstance(stmt, Score):
            attr = getattr(stmt.attr, {'unit': 1, 'vel': 100, 'key': 0, 'hook': None})
            _score.ENV[stmt.name] = _score.Score(_score._compile_score(stmt.text, **attr), stmt.text, **attr)
        elif isinstance(stmt, Template):
            if stmt.name not in _score.ENV:
                def get_tmpl(stmt):
                    def use_tmpl(n: list[_score.Note]):
                        index = round(n[0].beats)
                        try:
                            hook = use_tmpl.dct[index, len(n) - 1]
                        except KeyError:
                            raise MusicScriptError(f'Template {use_tmpl.name} can not match {n[0].beats}(rounded as {index}) beats and {len(n) - 1} notes, can match {', '.join(str(i) for i in use_tmpl.dct)}')
                        return hook(n)
                    use_tmpl.dct = {}
                    use_tmpl.name = stmt.name
                    return use_tmpl
                _score.ENV[stmt.name] = get_tmpl(stmt)
            _score.ENV[stmt.name].dct[stmt.beats, stmt.notes] = _score._compile_tmpl(stmt.text, stmt.beats if stmt.early else 0)
    try:
        main: _score.Score = _score.ENV['main']
    except KeyError:
        raise MusicScriptError('Main score not found')
    midi = main.to_pretty_midi()
    return midi
