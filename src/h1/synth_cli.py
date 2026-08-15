"""H1 Synth CLI — Synthesize programs from effective opcodes."""

import argparse
import sys
from pathlib import Path

from h1 import (
    flat_program as _flat,
)
from h1 import (
    synthesize_from_effective,
    synthesize_program,
)


def cmd_from_effective(args):
    """Given effective opcodes, compute written opcodes."""
    if args.opcodes:
        effective = [int(x) for x in args.opcodes]
    else:
        # Read from file (one per line or space-separated)
        text = Path(args.file).read_text().strip()
        effective = [int(x) for x in text.split()]

    written = synthesize_from_effective(effective, args.k)
    if args.output:
        Path(args.output).write_text(" ".join(str(x) for x in written))
        print(f"Written opcodes saved to {args.output}")
    else:
        print(" ".join(str(x) for x in written))


def cmd_build(args):
    """Build a known program for given k."""
    from h1 import build_cat_program, build_echo_program, build_hello_world_k0

    targets = {
        "hello": build_hello_world_k0(),
        "cat": build_cat_program(),
        "echo": build_echo_program(),
    }
    if args.target not in targets:
        print(f"Unknown target: {args.target}")
        sys.exit(1)
    target = targets[args.target]
    source = synthesize_program(target, args.k)
    if args.output:
        Path(args.output).write_text(" ".join(str(x) for x in _flat(source)))
        print(f"Saved to {args.output}")
    else:
        print(" ".join(str(x) for x in _flat(source)))


def main():
    p = argparse.ArgumentParser(prog="h1-synth", description="H1 Synthesizer")
    sub = p.add_subparsers(dest="cmd", required=True)

    p_fe = sub.add_parser("from-effective", help="Compute written opcodes from effective")
    p_fe.add_argument("opcodes", nargs="*", type=str, help="Effective opcodes (space-separated)")
    p_fe.add_argument("-f", "--file", type=Path, help="Read effective opcodes from file")
    p_fe.add_argument("-k", type=int, default=0, help="History length")
    p_fe.add_argument("-o", "--output", type=Path, help="Output file")
    p_fe.set_defaults(func=cmd_from_effective)

    p_build = sub.add_parser("build", help="Build known program for k")
    p_build.add_argument("target", choices=["hello", "cat", "echo"])
    p_build.add_argument("-k", type=int, default=0)
    p_build.add_argument("-o", "--output", type=Path, help="Output .h1 file")
    p_build.set_defaults(func=cmd_build)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
