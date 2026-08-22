"""H1 Hostile Language — Sintetizador.
Invierte la deriva: dado opcodes EFECTIVOS deseados, computa la fuente.
Con deriva EFECTIVA (feedback loop), cada paso tiene solución única determinista:
    op_escrito = (op_deseado - Σ H) mod 7
donde H = últimos k opcodes EFECTIVOS ya fijados.
"""

from .isa import N_OPCODES, Instruction, Opcode


def synthesize_from_effective(effective_ops: list[int], k: int) -> list[int]:
    """
    Dada lista de opcodes EFECTIVOS deseados, devuelve lista de opcodes ESCRITOS.
    Determinista O(n) con deriva efectiva.
    """
    if k <= 0:
        return [op % N_OPCODES for op in effective_ops]

    written = []
    history = []
    for op_eff in effective_ops:
        delta = sum(history[-k:])
        op_written = (op_eff - delta) % N_OPCODES
        written.append(op_written)
        history.append(op_eff)
    return written


def synthesize_program(target_instructions: list[Instruction], k: int) -> list[Instruction]:
    """
    Dado programa objetivo (opcodes EFECTIVOS), genera programa fuente.
    Los operandos a,o se copian tal cual — no derivan.
    """
    effective_ops = [instr.op for instr in target_instructions]
    written_ops = synthesize_from_effective(effective_ops, k)

    source = []
    for i, op_written in enumerate(written_ops):
        target = target_instructions[i]
        source.append(Instruction(Opcode(op_written), target.a, target.o))
    return source


def round_trip_test(
    target: list[Instruction], k: int, inputs: list[int] = None, max_trace_len: int = None
) -> tuple[bool, list[Instruction], list[Instruction]]:
    """
    Sintetiza -> ejecuta -> verifica que los opcodes efectivos coinciden con el target
    para los primeros len(target) pasos ejecutados (o max_trace_len si se especifica).
    Returns: (ok, source_program, effective_program_from_trace)
    """
    from .interpreter import run

    source = synthesize_program(target, k)
    state = run(source, k=k, inputs=inputs, max_steps=10000)
    effective_ops = [t.effective_op for t in state.trace]
    limit = max_trace_len if max_trace_len is not None else len(target)
    effective_ops_limited = effective_ops[:limit]
    effective_prog = [
        Instruction(op, target[i].a, target[i].o) for i, op in enumerate(effective_ops_limited)
    ]
    ok = all(e == t.op for e, t in zip(effective_ops_limited, target[:limit]))
    return ok, source, effective_prog


def build_hello_world_k0() -> list[Instruction]:
    """Hello World para máquina base (k=0)."""
    # OUT 72='H', OUT 101='e', OUT 108='l', OUT 108='l', OUT 111='o', OUT 32=' ', OUT 87='W', OUT 111='o', OUT 114='r', OUT 108='l', OUT 100='d', OUT 10='\n', HALT
    # Usamos IN/OUT con memoria pre-cargada o IN directo.
    # Simplificado: asumimos memoria ya tiene los chars en celdas 10..21, OUT desde ahí.
    # Para k=0, construimos secuencia directa de OUT desde celdas pre-cargadas.
    return [
        Instruction(Opcode.OUT, 10),  # H
        Instruction(Opcode.OUT, 11),  # e
        Instruction(Opcode.OUT, 12),  # l
        Instruction(Opcode.OUT, 13),  # l
        Instruction(Opcode.OUT, 14),  # o
        Instruction(Opcode.OUT, 15),  # space
        Instruction(Opcode.OUT, 16),  # W
        Instruction(Opcode.OUT, 17),  # o
        Instruction(Opcode.OUT, 18),  # r
        Instruction(Opcode.OUT, 19),  # l
        Instruction(Opcode.OUT, 20),  # d
        Instruction(Opcode.OUT, 21),  # newline
        Instruction(Opcode.HALT),
    ]


def build_cat_program() -> list[Instruction]:
    """cat: IN -> OUT loop hasta EOF (0). Usa dirección 10 para datos."""
    # IN 10; JZ 10 end; OUT 10; JNZ 10 loop; HALT
    # Instrucciones: 0=IN, 1=JZ->4, 2=OUT, 3=JNZ->0, 4=HALT
    return [
        Instruction(Opcode.IN, 10),  # IN 10 (idx 0)
        Instruction(Opcode.JZ, 10, 4),  # JZ 10 -> HALT (idx 4)
        Instruction(Opcode.OUT, 10),  # OUT 10 (idx 2)
        Instruction(Opcode.JNZ, 10, 0),  # JNZ 10 -> loop (idx 0)
        Instruction(Opcode.HALT),  # idx 4
    ]


def build_echo_program() -> list[Instruction]:
    """echo: IN a, OUT a, HALT"""
    return [
        Instruction(Opcode.IN, 0),
        Instruction(Opcode.OUT, 0),
        Instruction(Opcode.HALT),
    ]


def preload_memory_for_hello(mem: list[int]):
    """Carga 'Hello World\\n' en celdas 10-21."""
    hello = [72, 101, 108, 108, 111, 32, 87, 111, 114, 108, 100, 10]
    for i, val in enumerate(hello):
        if 10 + i < len(mem):
            mem[10 + i] = val
