"""H1 Hostile Language — Stationary Harmonic Loop Synthesizer.

Provides deterministic synthesis of programs with periodic loops under
non-Markovian drift k (HK-7 feedback loop):
    op_effective = (op_written + sum(history_effective[-k:])) mod 7

By solving the cyclic boundary conditions, loops become periodic attractors
that can execute an arbitrary number of iterations without phase drift.
"""

from __future__ import annotations

from typing import List, Tuple
from .isa import Instruction, Opcode, N_OPCODES


def synthesize_stationary_program(
    preamble_eff: List[Instruction],
    loop_eff: List[Instruction],
    exit_j: int,
    exit_eff: List[Instruction],
    k: int,
) -> List[Instruction]:
    """Synthesize a complete program: preamble -> stationary loop -> exit sequence.

    Args:
        preamble_eff: Initial instructions executed once before loop.
                      Must end with k instructions whose opcodes match the
                      tail of loop_eff (for k > 0) to seed the stationary history.
        loop_eff: The cyclic instructions of the loop in effective form.
        exit_j: The 0-based index in loop_eff where the branch condition exits.
        exit_eff: The instructions executed upon taking the branch.
        k: The non-Markovian memory window.

    Returns:
        A list of Instruction objects in written form (ready to execute).
    """
    if k == 0:
        return list(preamble_eff) + list(loop_eff) + list(exit_eff)

    # 1. Synthesize preamble (linear forward derivation)
    w_preamble: List[Instruction] = []
    hist: List[int] = []
    for inst in preamble_eff:
        delta = sum(hist[-k:]) if hist else 0
        w = (inst.op - delta) % N_OPCODES
        w_preamble.append(Instruction(Opcode(w), inst.a, inst.o))
        hist.append(int(inst.op))

    # 2. Synthesize loop (cyclic boundary conditions)
    L = len(loop_eff)
    w_loop: List[Instruction] = []
    for j in range(L):
        # Steady-state history is the last k instructions in cyclic order
        h_k = [int(loop_eff[(j - i) % L].op) for i in range(k, 0, -1)]
        delta = sum(h_k) % N_OPCODES
        w = (loop_eff[j].op - delta) % N_OPCODES
        w_loop.append(Instruction(Opcode(w), loop_eff[j].a, loop_eff[j].o))

    # 3. Synthesize exit sequence
    # At exit_j, the branch was taken immediately after executing loop_eff[exit_j].
    # So history at branch time is the last k opcodes ending at exit_j:
    h_exit = [int(loop_eff[(exit_j - i) % L].op) for i in range(k - 1, -1, -1)]
    w_exit: List[Instruction] = []
    hist_exit = list(h_exit)
    for inst in exit_eff:
        delta = sum(hist_exit[-k:]) % N_OPCODES
        w = (inst.op - delta) % N_OPCODES
        w_exit.append(Instruction(Opcode(w), inst.a, inst.o))
        hist_exit.append(int(inst.op))

    return w_preamble + w_loop + w_exit
