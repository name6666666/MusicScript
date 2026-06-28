import argparse
from music_script import compile, PreprocessError, preprocess as prep
from pathlib import Path
from traceback import print_exc



def main():
    parser = argparse.ArgumentParser(description='MusicScript compiler 1.36')
    parser.add_argument('input', help='Input .ms file')
    parser.add_argument('-o', '--output', help='Output .mid file')
    parser.add_argument('-i', '--include', action='append', default=[], help='Include paths')
    parser.add_argument('-p', '--py-path', default='.', help='Python import path')
    parser.add_argument('--preprocess', default=False, action='store_true', help='Only preprocessing')

    args = parser.parse_args()

    preprocess = args.preprocess
    input = args.input
    output = args.output if args.output is not None else Path(input).stem + ('.mid' if not preprocess else '-preprocess.ms')
    include = args.include
    py_path = args.py_path
    

    if Path(input) == Path(output):
        print('Input path and output path are same. Compilation terminated')
        return -1

    try:
        if preprocess:
            text = prep(input, include)
            Path(output).write_text(text, 'utf-8')
        else:
            midi = compile(input, include, py_path)
            midi.write(output)
    except PreprocessError as e:
        if len(e.args) > 1:
            print(f'Prepreprocess code:\n{e.args[1]}')
        print_exc()
        return 2
    except Exception:
        print_exc()
        return 1
    
    return 0

if __name__ == '__main__':
    import sys
    sys.exit(main())
