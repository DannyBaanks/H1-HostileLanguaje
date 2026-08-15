"""H1 Hostile Language — Interpreter con deriva no-markoviana.
Cada paso registra: escrito -> H -> deriva -> efectivo.
"""

from dataclasses import dataclass, field

from .isa import (
    CELLS_PER_INSTR,
    N_OPCODES,
    Instruction,
    Opcode,
)


@dataclass
class StepTrace:
    pc: int
    written_op: int
    written_a: int
    written_o: int
    history_snapshot: list[int]
    derived_delta: int
    effective_op: Opcode
    effective_a: int
    effective_o: int
    mem_before: list[int]
    mem_after: list[int]
    pc_next: int
    halted: bool
    output: int | None = None
    input_consumed: int | None = None


@dataclass
class MachineState:
    memory: list[int]
    pc: int = 0
    halted: bool = False
    output_buffer: list[int] = field(default_factory=list)
    input_buffer: list[int] = field(default_factory=list)
    input_ptr: int = 0
    trace: list[StepTrace] = field(default_factory=list)
    history_effective: list[int] = field(default_factory=list)


def create_machine(
    program: list[Instruction],
    mem_size: int = 256,
    inputs: list[int] = None,
    program_offset: int = 64,
) -> MachineState:
    mem = [0] * mem_size
    for i, instr in enumerate(program):
        base = program_offset + i * CELLS_PER_INSTR
        if base + 2 < mem_size:
            mem[base], mem[base + 1], mem[base + 2] = instr.encode()
    return MachineState(
        memory=mem,
        pc=0,
        input_buffer=inputs or [],
        input_ptr=0,
    )


PROGRAM_OFFSET = 64


def step(state: MachineState, k: int) -> bool:
    """Ejecuta un paso. Returns True si continúa, False si HALT."""
    if state.halted or PROGRAM_OFFSET + state.pc * CELLS_PER_INSTR + 2 >= len(state.memory):
        state.halted = True
        return False

    pc_cells = PROGRAM_OFFSET + state.pc * CELLS_PER_INSTR
    op_written = state.memory[pc_cells]
    a_written = state.memory[pc_cells + 1]
    o_written = state.memory[pc_cells + 2]

    derived_delta = sum(state.history_effective[-k:]) if k > 0 else 0
    effective_op_val = (op_written + derived_delta) % N_OPCODES
    effective_op = Opcode(effective_op_val)
    effective_a = a_written
    effective_o = o_written

    mem_before = state.memory.copy()
    output_val = None
    input_val = None
    pc_next = state.pc + 1

    if effective_op == Opcode.HALT:
        state.halted = True
    elif effective_op == Opcode.INC:
        state.memory[effective_a] = (state.memory[effective_a] + 1) % 256
    elif effective_op == Opcode.DEC:
        state.memory[effective_a] = (state.memory[effective_a] - 1) % 256
    elif effective_op == Opcode.JZ:
        if state.memory[effective_a] == 0:
            pc_next = effective_o
    elif effective_op == Opcode.JNZ:
        if state.memory[effective_a] != 0:
            pc_next = effective_o
    elif effective_op == Opcode.IN:
        if state.input_ptr < len(state.input_buffer):
            state.memory[effective_a] = state.input_buffer[state.input_ptr]
            input_val = state.input_buffer[state.input_ptr]
            state.input_ptr += 1
        else:
            state.memory[effective_a] = 0
    elif effective_op == Opcode.OUT:
        output_val = state.memory[effective_a]
        state.output_buffer.append(output_val)

    mem_after = state.memory.copy()
    state.history_effective.append(effective_op_val)
    state.pc = pc_next

    state.trace.append(
        StepTrace(
            pc=state.pc - 1,
            written_op=op_written,
            written_a=a_written,
            written_o=o_written,
            history_snapshot=state.history_effective[-k - 1 : -1] if k > 0 else [],
            derived_delta=derived_delta,
            effective_op=effective_op,
            effective_a=effective_a,
            effective_o=effective_o,
            mem_before=mem_before,
            mem_after=mem_after,
            pc_next=pc_next,
            halted=state.halted,
            output=output_val,
            input_consumed=input_val,
        )
    )

    return not state.halted


def run(
    program: list[Instruction],
    k: int = 0,
    mem_size: int = 256,
    inputs: list[int] = None,
    max_steps: int = 10000,
) -> MachineState:
    state = create_machine(program, mem_size, inputs)
    steps = 0
    while step(state, k) and steps < max_steps:
        steps += 1
    if steps >= max_steps:
        state.halted = True
    return state


def trace_to_string(trace: list[StepTrace]) -> str:
    lines = ["PC | WrOp | Hist | Δ | EfOp |  a  |  o  | Out | In | PC' | Halt"]
    lines.append("-" * 70)
    for t in trace:
        hist_str = "".join(str(x) for x in t.history_snapshot[-3:]) if t.history_snapshot else "-"
        out_str = str(t.output) if t.output is not None else "-"
        in_str = str(t.input_consumed) if t.input_consumed is not None else "-"
        lines.append(
            f"{t.pc:2d} | {t.written_op:4d} | {hist_str:>4} | {t.derived_delta:2d} | "
            f"{t.effective_op.name:4s} | {t.effective_a:3d} | {t.effective_o:3d} | "
            f"{out_str:>3} | {in_str:>2} | {t.pc_next:3d} | {t.halted}"
        )
    return "\n".join(lines)
