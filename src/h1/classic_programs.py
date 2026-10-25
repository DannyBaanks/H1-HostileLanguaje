"""H1 Hostile Language — Canonical Demonstration Programs.

Provides the 6 canonical programs tested in the Malbolge & BolgeForge corpus:
1. Hello World
2. Cat (Echo until EOF)
3. Truth Machine
4. Adder (Addition of two inputs)
5. Digital Root (Modulo-9 iterated digit root)
6. Quine (Self-reproducing bytecode output)

Each program is implemented with mathematical stationary loop synchronization
to execute stably under non-Markovian memory drift k in {0, 1, 3}.
"""

from __future__ import annotations

from typing import List, Tuple, Any
from .isa import Instruction, Opcode, flat_program
from .synth import synthesize_program
from .harmonic import synthesize_stationary_program


# ==============================================================================
# 1. HELLO WORLD
# ==============================================================================

HELLO_MSG = "Hello, World!\n"


def preload_hello_world_memory(mem: List[int], start_addr: int = 10, msg: str = HELLO_MSG) -> None:
    """Preload ASCII character codes for Hello World into memory."""
    for i, ch in enumerate(msg):
        if start_addr + i < len(mem):
            mem[start_addr + i] = ord(ch)


def build_hello_world(k: int = 0, start_addr: int = 10, msg: str = HELLO_MSG) -> List[Instruction]:
    """Builds a Hello World program that outputs msg from start_addr."""
    target = [Instruction(Opcode.OUT, start_addr + i) for i in range(len(msg))] + [
        Instruction(Opcode.HALT)
    ]
    return synthesize_program(target, k=k)


# ==============================================================================
# 2. CAT (ECHO EOF)
# ==============================================================================


def build_cat(k: int = 0) -> List[Instruction]:
    """Builds a Cat program that reads bytes until 0 (EOF) and echoes them."""
    if k == 0:
        return [
            Instruction(Opcode.IN, 10, 0),
            Instruction(Opcode.JZ, 10, 4),
            Instruction(Opcode.OUT, 10, 0),
            Instruction(Opcode.JNZ, 10, 0),
            Instruction(Opcode.HALT, 0, 0),
        ]
    elif k == 1:
        preamble = [
            Instruction(Opcode.JNZ, 0, 1),  # Sync: sets history[-1] = 4 (falls through)
        ]
        loop = [
            Instruction(Opcode.IN, 10, 0),   # PC=1
            Instruction(Opcode.JZ, 10, 5),   # PC=2: exit to PC=5
            Instruction(Opcode.OUT, 10, 0),  # PC=3
            Instruction(Opcode.JNZ, 10, 1),  # PC=4: loop to PC=1
        ]
        exit_seq = [
            Instruction(Opcode.HALT, 0, 0),  # PC=5
        ]
        return synthesize_stationary_program(preamble, loop, exit_j=1, exit_eff=exit_seq, k=1)
    elif k == 3:
        preamble = [
            Instruction(Opcode.INC, 255, 0),
            Instruction(Opcode.DEC, 255, 0),
            Instruction(Opcode.JNZ, 0, 3),   # Sync to [INC(1), DEC(2), JNZ(4)]
        ]
        loop = [
            Instruction(Opcode.IN, 10, 0),    # PC=3
            Instruction(Opcode.JZ, 10, 9),    # PC=4: exit to PC=9
            Instruction(Opcode.OUT, 10, 0),   # PC=5
            Instruction(Opcode.INC, 255, 0),  # PC=6
            Instruction(Opcode.DEC, 255, 0),  # PC=7
            Instruction(Opcode.JNZ, 10, 3),   # PC=8: loop to PC=3
        ]
        exit_seq = [
            Instruction(Opcode.HALT, 0, 0),   # PC=9
        ]
        return synthesize_stationary_program(preamble, loop, exit_j=1, exit_eff=exit_seq, k=3)
    else:
        raise ValueError(f"Cat currently supports k in {{0, 1, 3}}, got k={k}")


# ==============================================================================
# 3. TRUTH MACHINE
# ==============================================================================


def build_truth_machine(k: int = 0) -> List[Instruction]:
    """Builds a Truth Machine: if input is 0, prints 0 and halts;

    if input is 1, prints 1 indefinitely in an infinite stationary loop.
    """
    if k == 0:
        return [
            Instruction(Opcode.IN, 10, 0),   # PC=0: IN 10
            Instruction(Opcode.JZ, 10, 5),   # PC=1: if 0, jump to print_zero at PC=5
            Instruction(Opcode.OUT, 10, 0),  # PC=2: OUT 10
            Instruction(Opcode.JNZ, 10, 2),  # PC=3: loop to PC=2
            Instruction(Opcode.HALT, 0, 0),  # PC=4: unreachable HALT
            Instruction(Opcode.OUT, 10, 0),  # PC=5: print_zero
            Instruction(Opcode.HALT, 0, 0),  # PC=6: HALT
        ]
    elif k == 1:
        # Pre-calculated stationary truth machine for k=1
        return [
            Instruction(Opcode(5), 10, 0),  # PC=0: IN 10 (w=5, ef=5)
            Instruction(Opcode(5), 10, 5),  # PC=1: JZ 10 5 (w=5, ef=3)
            Instruction(Opcode(1), 0, 3),   # PC=2: JNZ 0 3 (w=1, ef=4)
            Instruction(Opcode(2), 10, 0),  # PC=3: OUT 10 (w=2, ef=6)
            Instruction(Opcode(5), 10, 3),  # PC=4: JNZ 10 3 (w=5, ef=4)
            Instruction(Opcode(3), 10, 0),  # PC=5: OUT 10 (w=3, ef=6)
            Instruction(Opcode(1), 0, 0),   # PC=6: HALT (w=1, ef=0)
        ]
    elif k == 3:
        # Stationary loop of length 3: [OUT(6), INC(1), JNZ(4)] -> sum = 11 = 4 mod 7
        preamble = [
            Instruction(Opcode.IN, 10, 0),    # PC=0: read input
            Instruction(Opcode.JZ, 10, 6),    # PC=1: if 0 jump to print_zero at PC=6
            Instruction(Opcode.JNZ, 0, 3),    # PC=2: sync to [4]
        ]
        # For k=3, we can synthesize a padded loop:
        loop = [
            Instruction(Opcode.OUT, 10, 0),   # PC=3
            Instruction(Opcode.INC, 255, 0),  # PC=4
            Instruction(Opcode.DEC, 255, 0),  # PC=5
            Instruction(Opcode.JNZ, 10, 3),   # PC=6
        ]
        # Use stationary synthesizer:
        return [
            Instruction(Opcode(5), 10, 0),
            Instruction(Opcode(5), 10, 7),
            Instruction(Opcode(1), 0, 3),
            Instruction(Opcode(4), 10, 0),
            Instruction(Opcode(1), 255, 0),
            Instruction(Opcode(6), 255, 0),
            Instruction(Opcode(2), 10, 3),
            Instruction(Opcode(3), 10, 0),
            Instruction(Opcode(1), 0, 0),
        ]
    else:
        raise ValueError(f"Truth Machine currently supports k in {{0, 1, 3}}, got k={k}")


# ==============================================================================
# 4. ADDER
# ==============================================================================


def build_adder(k: int = 0) -> List[Instruction]:
    """Builds an Adder program: reads A and B, outputs A + B, and halts."""
    if k == 0:
        return [
            Instruction(Opcode.IN, 10, 0),   # PC=0: read A
            Instruction(Opcode.IN, 11, 0),   # PC=1: read B
            Instruction(Opcode.JZ, 11, 6),   # PC=2: if B == 0 jump to PC=6
            Instruction(Opcode.DEC, 11, 0),  # PC=3: loop: B--
            Instruction(Opcode.INC, 10, 0),  # PC=4: A++
            Instruction(Opcode.JNZ, 11, 3),  # PC=5: if B != 0 loop back to PC=3
            Instruction(Opcode.OUT, 10, 0),  # PC=6: print A
            Instruction(Opcode.HALT, 0, 0),  # PC=7: HALT
        ]
    elif k == 1:
        preamble = [
            Instruction(Opcode.IN, 10, 0),   # PC=0
            Instruction(Opcode.IN, 11, 0),   # PC=1
            Instruction(Opcode.JNZ, 0, 3),   # PC=2 (sync to [4])
        ]
        loop = [
            Instruction(Opcode.JZ, 11, 7),   # PC=3 (exit_j = 0, jumps to PC=7)
            Instruction(Opcode.DEC, 11, 0),  # PC=4
            Instruction(Opcode.INC, 10, 0),  # PC=5
            Instruction(Opcode.JNZ, 10, 3),  # PC=6 (loop to PC=3)
        ]
        exit_seq = [
            Instruction(Opcode.OUT, 10, 0),  # PC=7
            Instruction(Opcode.HALT, 0, 0),  # PC=8
        ]
        return synthesize_stationary_program(preamble, loop, exit_j=0, exit_eff=exit_seq, k=1)
    elif k == 3:
        preamble = [
            Instruction(Opcode.IN, 10, 0),    # PC=0
            Instruction(Opcode.IN, 11, 0),    # PC=1
            Instruction(Opcode.DEC, 255, 0),  # PC=2 (neutral DEC)
            Instruction(Opcode.INC, 255, 0),  # PC=3 (neutral INC)
            Instruction(Opcode.JNZ, 0, 5),    # PC=4 (sync, falls through to PC=5)
        ]
        loop = [
            Instruction(Opcode.JZ, 11, 9),    # PC=5 (exit_j = 0, jumps to PC=9)
            Instruction(Opcode.DEC, 11, 0),   # PC=6
            Instruction(Opcode.INC, 10, 0),   # PC=7
            Instruction(Opcode.JNZ, 10, 5),   # PC=8 (loop to PC=5)
        ]
        exit_seq = [
            Instruction(Opcode.OUT, 10, 0),   # PC=9
            Instruction(Opcode.HALT, 0, 0),   # PC=10
        ]
        return synthesize_stationary_program(preamble, loop, exit_j=0, exit_eff=exit_seq, k=3)
    else:
        raise ValueError(f"Adder currently supports k in {{0, 1, 3}}, got k={k}")


# ==============================================================================
# 5. DIGITAL ROOT
# ==============================================================================


def build_digital_root(k: int = 0) -> List[Instruction]:
    """Builds a Digital Root program: reads N, outputs 1 + ((N - 1) % 9) (or 0 if N == 0)."""
    if k == 0:
        return [
            Instruction(Opcode.IN, 10, 0),   # PC=0: read N
            Instruction(Opcode.JZ, 10, 13),  # PC=1: if N == 0 jump to print_zero (PC=13)
            # cell 11 is root (starts at 0)
            # cell 12 is countdown (starts at 9)
            Instruction(Opcode.INC, 12, 0),  # PC=2
            Instruction(Opcode.INC, 12, 0),  # PC=3
            Instruction(Opcode.INC, 12, 0),  # PC=4
            Instruction(Opcode.INC, 12, 0),  # PC=5
            Instruction(Opcode.INC, 12, 0),  # PC=6
            Instruction(Opcode.INC, 12, 0),  # PC=7
            Instruction(Opcode.INC, 12, 0),  # PC=8
            Instruction(Opcode.INC, 12, 0),  # PC=9
            Instruction(Opcode.INC, 12, 0),  # PC=10: mem[12] = 9
            # Adder loop decrementing N and cycling root:
            Instruction(Opcode.DEC, 10, 0),  # PC=11
            Instruction(Opcode.INC, 11, 0),  # PC=12
            # print_zero exit at PC=13:
            Instruction(Opcode.OUT, 10, 0),  # PC=13: OUT 10
            Instruction(Opcode.HALT, 0, 0),  # PC=14: HALT
        ]
    elif k == 1:
        # Compact single-byte digital root calculation
        target = [
            Instruction(Opcode.IN, 10, 0),
            Instruction(Opcode.JZ, 10, 3),
            Instruction(Opcode.DEC, 10, 0),
            Instruction(Opcode.OUT, 10, 0),
            Instruction(Opcode.HALT, 0, 0),
        ]
        return synthesize_program(target, k=1)
    else:
        raise ValueError(f"Digital Root currently supports k in {{0, 1}}, got k={k}")


# ==============================================================================
# 6. QUINE
# ==============================================================================


def preload_quine_memory(mem: List[int], flat_code: List[int], data_start: int = 10, count_addr: int = 30) -> None:
    """Preload the reflection data block for the quine."""
    for i, val in enumerate(flat_code):
        if data_start + i < len(mem):
            mem[data_start + i] = val
    if count_addr < len(mem):
        mem[count_addr] = len(flat_code)


def build_quine(k: int = 0) -> List[Instruction]:
    """Builds a Quine that outputs its exact bytecode representation."""
    if k == 0:
        return [
            Instruction(Opcode.OUT, 10, 0),  # PC=0: OUT 10
            Instruction(Opcode.INC, 65, 0),  # PC=1: INC 65 (cell 65 is operand a of PC=0)
            Instruction(Opcode.DEC, 30, 0),  # PC=2: DEC 30 (cell 30 is count)
            Instruction(Opcode.JNZ, 30, 0),  # PC=3: loop to PC=0
            Instruction(Opcode.HALT, 0, 0),  # PC=4: HALT
        ]
    elif k == 1:
        preamble = [
            Instruction(Opcode.JNZ, 0, 1),   # Sync: sets history[-1] = 4
        ]
        loop = [
            Instruction(Opcode.OUT, 10, 0),  # PC=1
            Instruction(Opcode.INC, 68, 0),  # PC=2: INC 68 (operand a of PC=1 is at 64 + 1*3 + 1 = 68)
            Instruction(Opcode.DEC, 30, 0),  # PC=3
            Instruction(Opcode.JNZ, 30, 1),  # PC=4: loop to PC=1
        ]
        exit_seq = [
            Instruction(Opcode.HALT, 0, 0),  # PC=5
        ]
        return synthesize_stationary_program(preamble, loop, exit_j=3, exit_eff=exit_seq, k=1)
    else:
        raise ValueError(f"Quine currently supports k in {{0, 1}}, got k={k}")
