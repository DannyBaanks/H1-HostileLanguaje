"""H1 Hostile Language — Programas de ejemplo sintetizados."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from isa import Instruction, Opcode, flat_program
from synth import (
    synthesize_program, build_hello_world_k0, build_cat_program, build_echo_program,
    preload_memory_for_hello
)
from interpreter import create_machine, step


def save_program(name: str, prog, k: int):
    """Guarda programa fuente como triplets plano."""
    flat = flat_program(prog)
    with open(f"{name}_k{k}.h1", "w") as f:
        f.write(" ".join(str(x) for x in flat))
    print(f"Saved {name}_k{k}.h1 ({len(flat)} cells)")


def demo():
    # Hello World
    target = build_hello_world_k0()
    for k in [0, 1, 3, 7, 16]:
        source = synthesize_program(target, k)
        save_program("hello", source, k)
        # Verify
        state = create_machine(source, mem_size=128)
        preload_memory_for_hello(state.memory)
        for _ in range(50):
            if not step(state, k):
                break
        output = ''.join(chr(c) for c in state.output_buffer)
        assert output == "Hello World\n", f"k={k} failed: {repr(output)}"
        print(f"  k={k} verified: {repr(output)}")

    # Cat
    target = build_cat_program()
    for k in [0, 1, 3]:
        source = synthesize_program(target, k)
        save_program("cat", source, k)
        print(f"  cat k={k} saved")

    # Echo
    target = build_echo_program()
    for k in [0, 1, 3]:
        source = synthesize_program(target, k)
        save_program("echo", source, k)
        print(f"  echo k={k} saved")

    print("\nAll programs synthesized and verified.")


if __name__ == "__main__":
    demo()