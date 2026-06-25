from __future__ import annotations
from copy import copy, deepcopy
from dataclasses import asdict, dataclass
from math import prod
from typing import Callable, Literal
from pretty_midi import PrettyMIDI, Instrument as PmInstrument, Note as PmNote
from beartype import beartype
from lark import Lark, Transformer, v_args
from ._exception import MusicScriptError



Number = float | int

class Notes(list):
    def __init__(self, notes, early = 0):
        self.extend(notes)
        self.early = early

@beartype
@dataclass
class Track:
    instr: int
    len: Number | None
    vel: int | None
    key: int | None
    hook: Callable[[Note], Notes[Note]] | None
    is_drum: bool

ENV = {'common': Track(0, 1, 100, 0, None, False)}

@beartype
@dataclass
class Note:
    start: Number
    lasting: Number
    base_pitch: int | Literal['B']
    offset: int
    vel: Number | None
    _hook: Callable[[Note], Notes[Note]] | None
    length: Number
    beats: Number | None = None
    scale: Number = 1
    @property
    def end(self):
        return self.length + self.start
    @property
    def pitch(self):
        return self.base_pitch + self.offset

@beartype
@dataclass
class Chord:
    notes: list[Note]
    hook: Callable[[list[Note]], Notes[Note]] | None

class Trans(Transformer):
    def start(self, args):
        return args
    def _(self, args):
        return str(args)
    TEXT1 = A = B = C = D = E = _
    @v_args(inline=True)
    def note(self, hook, vel, octave, s_or_f, pitch, length, lasting):
        if octave is None: octave = 0
        else: octave = len(octave) * 12 * (1 if octave[0] == "'" else -1)
        if s_or_f is None: s_or_f = 0
        else: s_or_f = (1 if s_or_f[0] == 's' else -1) * len(s_or_f)
        try:
            pitch = int(pitch)
        except: pass
        if length is None: length = 1
        else: length = 1 + len(length)
        lasting = 0 if lasting is None else len(lasting)
        return Note(0, length + lasting, pitch, octave + s_or_f, vel, eval(hook.code, globals=ENV) if hook is not None else None, length)
    def python(self, args):
        return Python(args[0])
    def chord(self, args):
        hook, *notes, length, lasting = args
        notes: list[Note]
        if any(i is not None for i in [length, lasting]):
            if length is None: length = 1
            else: length = 1 + len(length)
            lasting = 0 if lasting is None else len(lasting)
            for i in notes:
                i.lasting = length + lasting
                i.length = length
        return Chord(notes, eval(hook.code, globals=ENV) if hook is not None else None)
_parser = Lark('''
start: (note | chord)*

chord: [python] "[" note+ "]" [D] [E]

note: [python] ["(" INT ")"] [A] [B] C [D] [E]
A: "."+ | "'"+
B: "s"+ | "f"+
C: "1" | "2" | "3" | "4" | "5" | "6" | "7" | "0"
D: "-"+
E: "_"+
python: "`" TEXT1 "`"
TEXT1: /[^`]+/

%import common.INT
%import common.WS
%ignore WS
''', parser='lalr')

def _compile(notes: str, unit, vel, key, hook: Callable[[Note], list[Note]] | None, len) -> list[Note]:
    ret: list[Note | Chord] = Trans().transform(_parser.parse(notes.replace('|', ' ')))
    key_to_pitch = [60, 62, 64, 65, 67, 69, 71]
    key_to_pitch = [i + key for i in key_to_pitch]
    key_to_pitch = {i + 1: key_to_pitch[i] for i in range(key_to_pitch.__len__())}
    key_to_pitch[0] = 0
    propress_note_and_chord = []
    new_note = lambda i: Note(i.start * unit, i.lasting * unit, key_to_pitch[i.base_pitch], i.offset, i.vel if i.vel is not None else vel, i._hook, i.length * unit, len * i.length, unit)
    for i in ret:
        if isinstance(i, Note):
            propress_note_and_chord.append(i._hook(new_note(i)) if i._hook else (hook(new_note(i)) if hook else [new_note(i)]))
        elif isinstance(i, Chord):
            notes = [new_note(j) for j in i.notes]
            if not i.hook:
                propress_note_and_chord.append(notes)
            else:
                propress_note_and_chord.append(i.hook(notes))
        else:
            assert isinstance(i, (Note, Chord))
    propress_note_and_chord = [i for i in propress_note_and_chord if i]
    ret = [NotrackScore(i, 0 if not hasattr(i, 'early') else i.early) for i in propress_note_and_chord]
    if not ret:
        return []
    new_ret = ret[0]
    for i in ret[1:]:
        new_ret += i
    return new_ret.notes


@dataclass
class Python:
    code: str
class Label(Transformer):
    def NAME(self, args): return str(args)
    def INT(self, args): return int(args)
    def FLOAT(self, args): return float(args)
    def attr(self, args): return args
    def label(self, args): return args
    def start(self, args): return args[0]
    def TEXT1(self, args): return str(args)
    def python(self, args): return Python(args[0])
label_parser = Lark('''
start: label
%import common.CNAME -> NAME
label: NAME attr*
attr: NAME "=" (INT | FLOAT | python)
python: "`" TEXT1 "`"
TEXT1: /[^`]+/
%import common.INT -> _INT
INT: "-"? _INT
%import common.FLOAT
%import common.WS
%ignore WS
''', parser='lalr', transformer=Label())
@beartype
def _compile_score(score: str, **kw) -> dict[str, list[Note]]:
    if not score.strip():
        raise MusicScriptError('There is space string on side of operator')
    if '+' in score:
        ret = [Score(_compile_score(i, **kw)) for i in score.split('+')]
        if not ret:
            return {}
        return sum(ret[1:], start=ret[0])._score
    if '*' in score:
        ret = [Score(_compile_score(i, **kw)) for i in score.split('*')]
        if not ret:
            return {}
        return prod(ret[1:], start=ret[0])._score
    if ':' not in score:
        try:
            score, *attr = label_parser.parse(score.strip())
        except:
            raise MusicScriptError(f"{repr(score)} be recognised as score calling, but the syntax is wrong")
        attr = {i[0]: i[1] if not isinstance(i[1], Python) else eval(i[1].code, globals=ENV) for i in attr}
        if score not in ENV:
            raise MusicScriptError(f'Variable {score} not found')
        if not isinstance(ENV[score], Score):
            raise MusicScriptError(f'{score} is not Score type')
        def getattr(dct: dict, default: dict):
            if any(i not in default for i in dct):
                raise MusicScriptError(f'There are unknown options in {', '.join(dct)}')
            ret = {**default, **dct}
            try:
                ret = {k: eval(v.code, globals=ENV) if isinstance(v, Python) else v for k, v in ret.items()}
            except KeyError as e:
                raise MusicScriptError(f'Unknown variable {e.args[0]}')
            return ret
        return Score(_compile_score(ENV[score]._code, **getattr(attr, ENV[score]._attr)))._score
    ret = {}
    label_and_code = score.strip().split(':', 1)
    track_name, *attr = label_parser.parse(label_and_code[0])
    attr = {i[0]: i[1] if not isinstance(i[1], Python) else eval(i[1].code, globals=ENV) for i in attr}
    track: Track = copy(ENV[track_name])
    for k in attr:
        if not hasattr(track, k):
            raise MusicScriptError(f'Track has no option {k}')
        setattr(track, k, attr[k])
    track_p = {k: v for k, v in asdict(track).items() if v is not None}
    track_p['key'] = track_p.get('key', 0) + kw['key'] if not track_p['is_drum'] else 0
    p = {**kw, **track_p}
    del p['instr']
    del p['is_drum']
    p['unit'] *= p['len']
    if track_name in ret:
        ret[track_name].extend(_compile(label_and_code[1], **p))
    else:
        ret[track_name] = _compile(label_and_code[1], **p)
    return ret


tmpl_parser = Lark('''
start: (note | chord)*

chord: [python] "[" note+ "]" [D] [E]

note: [python] ["(" INT ")"] [A] [B] C [D] [E]
A: "."+ | "'"+
B: "s"+ | "f"+
C: "1" | "2" | "3" | "4" | "5" | "6" | "7" | "0" | "B"
D: "-"+
E: "_"+
python: "`" TEXT1 "`"
TEXT1: /[^`]+/

%import common.INT
%import common.WS
%ignore WS
''', parser='lalr', transformer=Trans())
def _compile_取不出名(notes: str, unit, vel, key, hook: Callable[[Note], list[Note]] | None) -> list[Note]:
    ret: list[Note | Chord] = Trans().transform(tmpl_parser.parse(notes.replace('|', ' ')))
    key_to_pitch = [60, 62, 64, 65, 67, 69, 71]
    key_to_pitch = [i + key for i in key_to_pitch]
    key_to_pitch = {i + 1: key_to_pitch[i] for i in range(len(key_to_pitch))}
    key_to_pitch[0] = None
    propress_note_and_chord = []
    new_note = lambda i: Note(i.start * unit, i.lasting * unit, i.base_pitch, i.offset, i.vel if i.vel is not None else vel, i._hook, i.length * unit)
    for i in ret:
        if isinstance(i, Note):
            propress_note_and_chord.append(i._hook(new_note(i)) if i._hook else (hook(new_note(i)) if hook else [new_note(i)]))
        elif isinstance(i, Chord):
            notes = [new_note(j) for j in i.notes]
            if not i.hook:
                propress_note_and_chord.append(notes)
            else:
                propress_note_and_chord.append(i.hook(notes))
        else:
            assert isinstance(i, (Note, Chord))
    propress_note_and_chord = [i for i in propress_note_and_chord if i]
    ret = [NotrackScore(i, i.early if hasattr(i, 'early') else 0) for i in propress_note_and_chord]
    if not ret:
        return []
    new_ret = ret[0]
    for i in ret[1:]:
        new_ret += i
    return new_ret.notes
@beartype
def _compile_tmpl_(score: str, **kw) -> dict[str, list[Note]]:
    if not score.strip():
        raise MusicScriptError('There is space string on side of operator')
    if '+' in score:
        ret = [Score(_compile_score(i, **kw)) for i in score.split('+')]
        if not ret:
            return {}
        return sum(ret[1:], start=ret[0])._score
    if '*' in score:
        ret = [Score(_compile_score(i, **kw)) for i in score.split('*')]
        if not ret:
            return {}
        return prod(ret[1:], start=ret[0])._score
    ret = {}
    label_and_code = score.strip().split(':', 1)
    track_name, *attr = label_parser.parse(label_and_code[0])
    attr = {i[0]: i[1] if not isinstance(i[1], Python) else eval(i[1].code, globals=ENV) for i in attr}
    track: Track = copy(ENV[track_name])
    for k in attr:
        if not hasattr(track, k):
            raise MusicScriptError(f'Track has no option {k}')
        setattr(track, k, attr[k])
    p = {**kw, **{k: v for k, v in asdict(track).items() if v is not None}}
    del p['instr']
    p['unit'] *= p['len']
    del p['len']
    del p['is_drum']
    if track_name in ret:
        ret[track_name].extend(_compile_取不出名(label_and_code[1], **p))
    else:
        ret[track_name] = _compile_取不出名(label_and_code[1], **p)
    return ret
def _compile_tmpl(tmpl, early):
    notes = sum(_compile_tmpl_(tmpl, **{'unit': 1, 'vel': 100, 'key': 0, 'hook': None}).values(), [])
    def inner(n: list[Note]):
        new_notes: list[Note] = deepcopy(notes)
        for i in new_notes:
            if i.base_pitch == "B":
                target = n[0]
                i.base_pitch = target.base_pitch
                i.offset += target.offset
                i.length *= target.scale
                i.start *= target.scale
                i.vel = target.vel
            elif i.base_pitch == 0:
                i.base_pitch = 0
            else:
                target = n[({1: 1, 3: 2, 5: 3, 7: 4, 2: 5, 4: 6, 6: 7}[i.base_pitch] - 1) % len(n) + 1]
                i.base_pitch = target.base_pitch
                i.offset += target.offset
                i.length *= target.scale
                i.start *= target.scale
                i.vel = target.vel
        return Notes(new_notes, early)
    return inner

class Score:
    def __init__(self, score: dict[str, list[Note]] = None, code: str = None, early = 0, **kw):
        self._score = score if score is not None else {}
        self._attr = kw
        self._code = code
        self._early = early
        
    def to_pretty_midi(self):
        ret = PrettyMIDI()
        for k, v in self._score.items():
            track = ENV[k]
            pm_instr = PmInstrument(track.instr, name=k, is_drum=track.is_drum)
            pm_instr.notes.extend(PmNote(i.vel, i.pitch, i.start, i.start + i.lasting) for i in v if i.base_pitch != 0)
            ret.instruments.append(pm_instr)
            if any(i.start < 0 for i in pm_instr.notes):
                raise MusicScriptError('There is a note which start before zero')
        return ret
    
    def __repr__(self):
        return f'Score({self._score})'
    
    def __add__(self, other: Score):
        self_len = max(max(j.end for j in i) for i in self._score.values())
        other_sc = Score()
        for k, v in other._score.items():
            new_v = []
            for n in v:
                new_n = copy(n)
                new_n.start += self_len - other._early
                new_v.append(new_n)
            other_sc._score[k] = new_v
        return self * other_sc
    
    def __mul__(self, other: Score):
        ret = Score()
        for k in set(list(self._score) + list(other._score)):
            ret._score[k] = self._score.get(k, []) + other._score.get(k, [])
        return ret

class NotrackScore(Score):
    def __init__(self, score: list[Note] = None, early = 0):
        super().__init__({'no-track': score if score is not None else []}, early=early)
    
    def to_pretty_midi(self):
        raise NotImplementedError
    
    def to_track_score(self, track):
        return Score({track: self.notes})
    
    @property
    def notes(self):
        return self._score['no-track']
    @notes.setter
    def notes(self, value):
        self._score['no-track'] = value
    
    def __add__(self, other: Score):
        ret = super().__add__(other)
        return NotrackScore(ret._score['no-track'])
    
    def __mul__(self, other: Score):
        ret = super().__mul__(other)
        return NotrackScore(ret._score['no-track'])
    
    def __repr__(self):
        return f'NoTrackScore({self.notes})'
