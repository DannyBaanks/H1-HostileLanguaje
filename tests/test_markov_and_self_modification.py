"""Tests for Markovian State-Space Lifting, History Bifurcation, Harmonic Loop Stability,
and Von Neumann Self-Modifying Code in H1 Hostile Language.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

import pytest
from h1.isa import Instruction, Opcode
from h1.interpreter import create_machine, step, run, PROGRAM_OFFSET
from h1.classic_programs import build_cat, build_adder


def test_history_bifurcation_same_pc_and_memory():
    """Falsación empírica de la markovianidad clásica:
    Dos máquinas con IDÉNTICO PC=0, IDÉNTICA memoria y el MISMO programa,
    pero con historiales distintos, ejecutan instrucciones efectivas distintas.
    """
    prog = [Instruction(Opcode.HALT, 10, 0)]  # written instruction is HALT

    # Machine A: history [0] -> delta = 0 -> effective = (0 + 0) % 7 = 0 (HALT)
    mA = create_machine(prog)
    mA.history_effective = [0]
    mA.memory[10] = 42

    # Machine B: history [1] -> delta = 1 -> effective = (0 + 1) % 7 = 1 (INC)
    mB = create_machine(prog)
    mB.history_effective = [1]
    mB.memory[10] = 42

    # Verification of identical pre-step state on (PC, Memory)
    assert mA.pc == mB.pc == 0
    assert mA.memory == mB.memory

    step(mA, k=1)
    step(mB, k=1)

    # Post-step divergence
    assert mA.halted is True
    assert mA.trace[-1].effective_op == Opcode.HALT
    assert mA.memory[10] == 42

    assert mB.halted is False
    assert mB.trace[-1].effective_op == Opcode.INC
    assert mB.memory[10] == 43  # mutated by INC!


def test_markovian_lifting_determinism():
    """Demuestra que sobre el espacio de estados ampliado S* = (PC, Memoria, h_k),
    el operador de transición es estrictamente determinista y markoviano de orden 1.
    """
    prog = [Instruction(Opcode.INC, 10, 0), Instruction(Opcode.HALT, 0, 0)]

    # Two machines with identical extended state (PC, Mem, History)
    m1 = create_machine(prog)
    m1.history_effective = [2, 3]
    m1.memory[10] = 100

    m2 = create_machine(prog)
    m2.history_effective = [2, 3]
    m2.memory[10] = 100

    step(m1, k=2)
    step(m2, k=2)

    assert m1.pc == m2.pc
    assert m1.memory == m2.memory
    assert m1.history_effective == m2.history_effective
    assert m1.trace[-1].effective_op == m2.trace[-1].effective_op


def test_harmonic_loop_stability_cat_10k_iterations():
    """Verifica que los bucles armónicos estacionarios sobreviven a miles de iteraciones
    sin deriva de fase ni colapso de estado.
    """
    n_iterations = 10000
    inputs = [((i % 250) + 1) for i in range(n_iterations)] + [0]  # EOF=0
    cat_k1 = build_cat(k=1)
    m = create_machine(cat_k1, inputs=inputs)

    steps = 0
    phases = []
    while step(m, k=1):
        steps += 1
        phases.append(m.trace[-1].derived_delta)

    # Verificación de salida bit a bit exacta
    assert len(m.output_buffer) == n_iterations
    assert m.output_buffer == inputs[:-1]

    # Verificación de estacionariedad armónica: ciclo límite estricto de período 4
    # En el bucle de Cat k=1, la secuencia de deltas periódicos es [4, 5, 3, 6]
    loop_phases = phases[1 : 1 + n_iterations * 4]
    assert len(loop_phases) == n_iterations * 4

    for i in range(0, len(loop_phases), 4):
        chunk = loop_phases[i : i + 4]
        assert chunk == [4, 5, 3, 6], f"Harmonic phase drift at iteration {i // 4}: got {chunk}"


def test_harmonic_loop_stability_cat_k3():
    """Verifica la estabilidad del bucle armónico para k=3 sobre 2,000 iteraciones."""
    n_iterations = 2000
    inputs = [((i % 250) + 1) for i in range(n_iterations)] + [0]
    cat_k3 = build_cat(k=3)
    m = create_machine(cat_k3, inputs=inputs)

    while step(m, k=3):
        pass

    assert m.output_buffer == inputs[:-1]


def test_von_neumann_self_modifying_code():
    """Demuestra que la memoria de programa en H1 es modificable en tiempo de ejecución
    (Von Neumann puro), permitiendo que una instrucción altere el código de otra.
    """
    prog = [
        Instruction(Opcode.INC, 67, 0),   # PC=0: incrementa mem[67] (opcode de PC=1)
        Instruction(Opcode.HALT, 10, 0),  # PC=1: escrito como HALT!
        Instruction(Opcode.OUT, 10, 0),   # PC=2: OUT 10
        Instruction(Opcode.HALT, 0, 0),   # PC=3: HALT
    ]
    m = create_machine(prog)
    m.memory[10] = 50

    # Estado inicial en mem[67] es 0 (HALT)
    assert m.memory[67] == Opcode.HALT.value

    # Paso 0: ejecuta INC 67
    step(m, k=0)
    # mem[67] fue mutado a 1 (INC)
    assert m.memory[67] == Opcode.INC.value

    # Paso 1: ejecuta PC=1 que AHORA es INC 10 0 (en vez de HALT)
    step(m, k=0)
    assert m.halted is False
    assert m.memory[10] == 51

    # Paso 2: ejecuta OUT
    step(m, k=0)
    assert m.output_buffer == [51]


def test_self_modifying_dynamic_pointer():
    """Demuestra cómo la automodificación del operando `a` en el código sustituye
    la ausencia de direccionamiento indirecto para iterar sobre un buffer en memoria.
    """
    # Llenamos un buffer en mem[20..24] con valores [10, 20, 30, 40, 50]
    buffer_vals = [10, 20, 30, 40, 50]
    # Programa:
    # PC=0: OUT 20 (mem[65] es el operando 20)
    # PC=1: INC 65 (incrementa el operando a del OUT para apuntar a la siguiente celda)
    # PC=2: DEC 15 (contador en mem[15])
    # PC=3: JNZ 15 0 (bucle a PC=0)
    # PC=4: HALT
    prog = [
        Instruction(Opcode.OUT, 20, 0),
        Instruction(Opcode.INC, 65, 0),
        Instruction(Opcode.DEC, 15, 0),
        Instruction(Opcode.JNZ, 15, 0),
        Instruction(Opcode.HALT, 0, 0),
    ]
    m = create_machine(prog)
    for i, v in enumerate(buffer_vals):
        m.memory[20 + i] = v
    m.memory[15] = len(buffer_vals)

    while step(m, k=0):
        pass

    # El programa recorrió el array completo mediante automodificación del operando de OUT
    assert m.output_buffer == buffer_vals
