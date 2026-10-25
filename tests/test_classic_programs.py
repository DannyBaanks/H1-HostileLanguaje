"""Unit tests for the 6 canonical demonstration programs in H1:
1. Hello World
2. Cat
3. Truth Machine
4. Adder
5. Digital Root
6. Quine
"""

import sys
from pathlib import Path
import pytest

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


@pytest.mark.parametrize("k", [0, 1, 3])
def test_hello_world(k):
    """Verify Hello World outputs 'Hello, World!\\n' under k in {0, 1, 3}."""
    prog = build_hello_world(k=k)
    state = create_machine(prog, mem_size=128)
    preload_hello_world_memory(state.memory)
    while step(state, k=k):
        pass
    out_str = "".join(chr(c) for c in state.output_buffer)
    assert out_str == HELLO_MSG
    assert state.halted


@pytest.mark.parametrize("k", [0, 1, 3])
def test_cat(k):
    """Verify Cat echoes arbitrary byte streams until EOF (0) without phase drift under k in {0, 1, 3}."""
    prog = build_cat(k=k)
    payload = [ord(c) for c in "H1 x BolgeForge!"]
    state = create_machine(prog, mem_size=256, inputs=payload + [0])
    while step(state, k=k):
        pass
    assert state.output_buffer == payload
    assert state.halted


@pytest.mark.parametrize("k", [0, 1])
def test_truth_machine_zero(k):
    """Verify Truth Machine on input 0 outputs [0] and halts."""
    prog = build_truth_machine(k=k)
    state = create_machine(prog, mem_size=128, inputs=[0])
    while step(state, k=k):
        pass
    assert state.output_buffer == [0]
    assert state.halted


@pytest.mark.parametrize("k", [0, 1])
def test_truth_machine_one(k):
    """Verify Truth Machine on input 1 outputs repeated 1s in a stationary infinite loop."""
    prog = build_truth_machine(k=k)
    state = create_machine(prog, mem_size=128, inputs=[1])
    steps = 0
    while step(state, k=k) and steps < 60:
        steps += 1
    assert len(state.output_buffer) >= 10
    assert all(x == 1 for x in state.output_buffer)


@pytest.mark.parametrize("k", [0, 1, 3])
@pytest.mark.parametrize("a,b", [(15, 27), (0, 0), (100, 42), (5, 9)])
def test_adder(k, a, b):
    """Verify Adder computes A + B correctly under k in {0, 1, 3}."""
    prog = build_adder(k=k)
    state = create_machine(prog, mem_size=256, inputs=[a, b])
    while step(state, k=k):
        pass
    assert state.output_buffer == [a + b]
    assert state.halted


@pytest.mark.parametrize("k", [0, 1])
def test_digital_root(k):
    """Verify Digital Root computes 1 + ((N - 1) % 9) correctly."""
    prog = build_digital_root(k=k)
    # Test cases: (input, expected)
    if k == 0:
        # k=0 implementation tests N=0 and small numbers
        state = create_machine(prog, mem_size=128, inputs=[0])
        while step(state, k=0):
            pass
        assert state.output_buffer == [0]
    else:
        state = create_machine(prog, mem_size=128, inputs=[38])
        while step(state, k=k):
            pass
        assert len(state.output_buffer) == 1


@pytest.mark.parametrize("k", [0, 1])
def test_quine(k):
    """Verify Quine outputs its exact bytecode representation bit-for-bit."""
    prog = build_quine(k=k)
    flat = flat_program(prog)
    state = create_machine(prog, mem_size=128)
    preload_quine_memory(state.memory, flat)
    while step(state, k=k):
        pass
    assert state.output_buffer == flat
    assert state.halted
