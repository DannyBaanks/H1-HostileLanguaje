"""H1 CLI — Run .h1 programs."""

import argparse
import sys
from pathlib import Path

from h1 import (
    build_cat_program,
    build_echo_program,
    build_hello_world_k0,
    flat_program,
    run,
    synthesize_program,
    trace_to_string,
    unflat_program,
)


def load_program(path: Path) -> list:
    """Load .h1 file (space-separated ints) -> list[Instruction]."""
    text = path.read_text().strip()
    if not text:
        return []
    cells = [int(x) for x in text.split()]
    return unflat_program(cells)


def save_program(path: Path, prog: list):
    """Save list[Instruction] -> .h1 file."""
    flat = flat_program(prog)
    path.write_text(" ".join(str(x) for x in flat))


def cmd_run(args):
    prog = load_program(Path(args.program))
    state = run(prog, k=args.k, inputs=args.input, max_steps=args.steps)
    if args.trace:
        print(trace_to_string(state.trace))
    if state.output_buffer:
        print("OUTPUT:", " ".join(str(c) for c in state.output_buffer))
        if args.ascii:
            print("ASCII:", "".join(chr(c) for c in state.output_buffer))
    print(f"HALTED: {state.halted} | STEPS: {len(state.trace)}")


def cmd_synth(args):
    # built-in targets
    targets = {
        "hello": build_hello_world_k0(),
        "cat": build_cat_program(),
        "echo": build_echo_program(),
    }
    if args.target not in targets:
        print(f"Unknown target: {args.target}. Options: {list(targets.keys())}")
        sys.exit(1)
    target = targets[args.target]
    source = synthesize_program(target, args.k)
    save_program(Path(args.output), source)
    print(
        f"Synthesized {args.target} k={args.k} -> {args.output} ({len(flat_program(source))} cells)"
    )


def cmd_verify(args):
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
    state = run(source, k=args.k, inputs=args.input, max_steps=args.steps)
    print(f"OK: {args.target} k={args.k} halted={state.halted} steps={len(state.trace)}")
    if state.output_buffer:
        print("OUTPUT:", " ".join(str(c) for c in state.output_buffer))


def main():
    p = argparse.ArgumentParser(prog="h1", description="H1 Hostile Language (HK-7)")
    sub = p.add_subparsers(dest="cmd", required=True)

    p_run = sub.add_parser("run", help="Run a .h1 program")
    p_run.add_argument("program", type=Path, help="Path to .h1 file")
    p_run.add_argument("-k", type=int, default=0, help="History length (default 0)")
    p_run.add_argument("--input", type=int, nargs="*", default=[], help="Input bytes")
    p_run.add_argument("--steps", type=int, default=10000, help="Max steps")
    p_run.add_argument("--trace", action="store_true", help="Print full trace")
    p_run.add_argument("--ascii", action="store_true", help="Print output as ASCII")
    p_run.set_defaults(func=cmd_run)

    p_synth = sub.add_parser("synth", help="Synthesize source for a target program")
    p_synth.add_argument("target", choices=["hello", "cat", "echo"])
    p_synth.add_argument("output", type=Path, help="Output .h1 file")
    p_synth.add_argument("-k", type=int, default=0, help="History length")
    p_synth.set_defaults(func=cmd_synth)

    p_verify = sub.add_parser("verify", help="Synthesize + run + verify output")
    p_verify.add_argument("target", choices=["hello", "cat", "echo"])
    p_verify.add_argument("-k", type=int, default=0)
    p_verify.add_argument("--input", type=int, nargs="*", default=[])
    p_verify.add_argument("--steps", type=int, default=10000)
    p_verify.set_defaults(func=cmd_verify)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
