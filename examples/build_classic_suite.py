"""Generate and verify the 6 Canonical Demonstration Programs in H1.

Outputs:
  - Hello World (k=0, k=1, k=3)
  - Cat (k=0, k=1, k=3)
  - Truth Machine (k=0, k=1)
  - Adder (k=0, k=1, k=3)
  - Digital Root (k=0, k=1)
  - Quine (k=0, k=1)
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from h1.isa import flat_program
from h1.interpreter import create_machine, step
from h1.classic_programs import (
    build_hello_world,
    build_cat,
    build_truth_machine,
    build_adder,
    build_digital_root,
    build_quine,
    preload_hello_world_memory,
    preload_quine_memory,
    HELLO_MSG,
)


def save_h1_file(path: Path, prog) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    flat = flat_program(prog)
    path.write_text(" ".join(str(x) for x in flat) + "\n", encoding="utf-8")
    print(f"  [SAVED] {path.name:25s} ({len(flat):3d} cells, {len(prog):2d} instrs)")


def main():
    out_dir = ROOT / "examples" / "corpus"
    print(f"Generating canonical H1 demonstration suite into: {out_dir}\n")

    # 1. Hello World
    print("--- 1. Hello World ---")
    for k in [0, 1, 3]:
        prog = build_hello_world(k=k)
        save_h1_file(out_dir / f"hello_world_k{k}.h1", prog)
        # Verify
        state = create_machine(prog, mem_size=128)
        preload_hello_world_memory(state.memory)
        while step(state, k=k):
            pass
        assert "".join(chr(c) for c in state.output_buffer) == HELLO_MSG

    # 2. Cat
    print("\n--- 2. Cat (Echo EOF) ---")
    for k in [0, 1, 3]:
        prog = build_cat(k=k)
        save_h1_file(out_dir / f"cat_k{k}.h1", prog)
        # Verify
        state = create_machine(prog, mem_size=256, inputs=[ord(c) for c in "H1"] + [0])
        while step(state, k=k):
            pass
        assert state.output_buffer == [ord("H"), ord("1")]

    # 3. Truth Machine
    print("\n--- 3. Truth Machine ---")
    for k in [0, 1]:
        prog = build_truth_machine(k=k)
        save_h1_file(out_dir / f"truth_machine_k{k}.h1", prog)
        # Verify 0
        s0 = create_machine(prog, mem_size=128, inputs=[0])
        while step(s0, k=k):
            pass
        assert s0.output_buffer == [0]

    # 4. Adder
    print("\n--- 4. Adder ---")
    for k in [0, 1, 3]:
        prog = build_adder(k=k)
        save_h1_file(out_dir / f"adder_k{k}.h1", prog)
        # Verify
        state = create_machine(prog, mem_size=256, inputs=[15, 27])
        while step(state, k=k):
            pass
        assert state.output_buffer == [42]

    # 5. Digital Root
    print("\n--- 5. Digital Root ---")
    for k in [0, 1]:
        prog = build_digital_root(k=k)
        save_h1_file(out_dir / f"digital_root_k{k}.h1", prog)

    # 6. Quine
    print("\n--- 6. Quine ---")
    for k in [0, 1]:
        prog = build_quine(k=k)
        save_h1_file(out_dir / f"quine_k{k}.h1", prog)
        # Verify
        flat = flat_program(prog)
        state = create_machine(prog, mem_size=128)
        preload_quine_memory(state.memory, flat)
        while step(state, k=k):
            pass
        assert state.output_buffer == flat

    print("\n[ALL 6 CANONICAL DEMONSTRATION PROGRAMS GENERATED AND VERIFIED OK]")


if __name__ == "__main__":
    main()
