"""H1 Hostile Language — Tests."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

try:
    from h1.interpreter import run, trace_to_string
    from h1.isa import Instruction, Opcode, derive_opcode, flat_program, unflat_program
    from h1.synth import (
        build_cat_program,
        build_echo_program,
        build_hello_world_k0,
        round_trip_test,
        synthesize_program,
    )
except ImportError:
    from interpreter import run, trace_to_string
    from isa import Instruction, Opcode, derive_opcode, flat_program, unflat_program
    from synth import (
        build_cat_program,
        build_echo_program,
        build_hello_world_k0,
        round_trip_test,
        synthesize_program,
    )


def test_k0_is_base_machine():
    """k=0: deriva=0, H1 ≡ máquina de registros base."""
    prog = [
        Instruction(Opcode.INC, 10),
        Instruction(Opcode.INC, 10),
        Instruction(Opcode.DEC, 10),
        Instruction(Opcode.HALT),
    ]
    state = run(prog, k=0, mem_size=128)
    assert state.memory[10] == 1  # INC, INC, DEC = +1
    assert state.halted
    print("[OK] k=0 reproduce máquina base")


def test_derive_opcode_basic():
    """derive_opcode con k=0 devuelve el mismo opcode."""
    assert derive_opcode(3, [], 0) == 3
    assert derive_opcode(10, [], 0) == 3  # mod 7
    print("[OK] derive_opcode k=0")


def test_derive_opcode_with_history():
    """derive_opcode suma últimos k opcodes efectivos."""
    # history = [1,2], k=2 -> delta=3
    assert derive_opcode(0, [1, 2], 2) == 3
    assert derive_opcode(5, [1, 2], 2) == 1  # (5+3)%7=1
    # k=1 solo usa el último
    assert derive_opcode(0, [1, 2], 1) == 2
    print("[OK] derive_opcode con history")


def test_synthesize_k0():
    """Sintetizar con k=0: escrito = efectivo."""
    target = build_hello_world_k0()
    ok, source, eff = round_trip_test(target, k=0)
    assert ok
    for s, t in zip(source, target):
        assert s.op == t.op
        assert s.a == t.a
        assert s.o == t.o
    print("[OK] synthesize k=0 round-trip")


def test_synthesize_k1():
    """Sintetizar con k=1: deriva efectiva determinista."""
    target = build_hello_world_k0()
    ok, source, eff = round_trip_test(target, k=1)
    assert ok
    print("[OK] synthesize k=1 round-trip")


def test_synthesize_various_k():
    """Round-trip para k en {0,1,3,7,16}."""
    target = build_hello_world_k0()
    for k in [0, 1, 3, 7, 16]:
        ok, source, eff = round_trip_test(target, k)
        assert ok, f"Falló k={k}"
    print("[OK] round-trip kin{0,1,3,7,16}")


def test_deriva_efectiva_vs_escrita():
    """Con deriva EFECTIVA, un cambio en paso 3 altera pasos posteriores."""
    target = [
        Instruction(Opcode.INC, 0),
        Instruction(Opcode.INC, 0),
        Instruction(Opcode.INC, 0),
        Instruction(Opcode.OUT, 0),
        Instruction(Opcode.HALT),
    ]
    # k=1: source para target
    ok1, src1, eff1 = round_trip_test(target, k=1)
    assert ok1
    # Modificamos SOLO el 3er opcode del target
    target_mod = list(target)
    target_mod[2] = Instruction(Opcode.DEC, 0)  # era INC
    ok2, src2, eff2 = round_trip_test(target_mod, k=1)
    assert ok2
    # Con deriva EFECTIVA, los opcodes escritos en posiciones 3+ DEBEN cambiar
    # porque H (history effective) cambió en paso 2
    assert (
        src1[3].op != src2[3].op
    ), "Deriva efectiva: cambio en paso 2 debe alterar fuente del paso 3"
    print("[OK] deriva efectiva: feedback loop altera fuente posterior")


def test_cat_synthesized():
    """cat sintetizado y ejecutado con entrada."""
    target = build_cat_program()
    inputs = [65, 66, 0]  # 'A', 'B', EOF
    # k=0: comportamiento idéntico al target (sin deriva)
    source = synthesize_program(target, 0)
    state = run(source, k=0, inputs=inputs, max_steps=200)
    assert state.output_buffer == [65, 66]
    # k>0: deriva efectiva cambia el flujo en bucles (comportamiento esperado)
    for k in [1, 3]:
        source = synthesize_program(target, k)
        state = run(source, k=k, inputs=inputs, max_steps=200)
        assert state.halted  # termina sin error
        assert len(state.output_buffer) > 0  # produce algo
    print("[OK] cat sintetizado funciona")


def test_echo_synthesized():
    """echo sintetizado."""
    target = build_echo_program()
    for k in [0, 1, 3]:
        ok, source, eff = round_trip_test(target, k)
        assert ok
        state = run(source, k=k, inputs=[42], max_steps=10)
        assert state.output_buffer == [42]
    print("[OK] echo sintetizado funciona")


def test_flat_unflat_roundtrip():
    prog = build_hello_world_k0()
    flat = flat_program(prog)
    restored = unflat_program(flat)
    assert len(restored) == len(prog)
    for r, o in zip(restored, prog):
        assert r.op == o.op and r.a == o.a and r.o == o.o
    print("[OK] flat/unflat round-trip")


def test_trace_emission():
    """Interpreter emite traza completa con escrito/deriva/efectivo."""
    target = build_echo_program()
    ok, source, eff = round_trip_test(target, k=1)
    state = run(source, k=1, inputs=[99], max_steps=10)
    trace_str = trace_to_string(state.trace)
    assert "WrOp" in trace_str
    assert "EfOp" in trace_str
    assert "Δ" in trace_str
    assert "Hist" in trace_str
    print("[OK] trace emission completa")
    # print(trace_str)  # descomentar para ver


def test_same_source_different_input_same_opcodes():
    """Mismo fuente con distinta entrada da mismos opcodes efectivos (deriva no depende de datos)."""
    target = build_cat_program()
    ok, source, _ = round_trip_test(target, k=3)
    state1 = run(source, k=3, inputs=[1, 2, 0], max_steps=100)
    state2 = run(source, k=3, inputs=[9, 9, 0], max_steps=100)
    ops1 = [t.effective_op for t in state1.trace]
    ops2 = [t.effective_op for t in state2.trace]
    assert ops1 == ops2
    print("[OK] deriva independiente de datos de entrada")


def run_all():
    test_k0_is_base_machine()
    test_derive_opcode_basic()
    test_derive_opcode_with_history()
    test_synthesize_k0()
    test_synthesize_k1()
    test_synthesize_various_k()
    test_deriva_efectiva_vs_escrita()
    test_cat_synthesized()
    test_echo_synthesized()
    test_flat_unflat_roundtrip()
    test_trace_emission()
    test_same_source_different_input_same_opcodes()
    print("\n[OK][OK][OK] TODOS LOS TESTS PASARON [OK][OK][OK]")


if __name__ == "__main__":
    run_all()
