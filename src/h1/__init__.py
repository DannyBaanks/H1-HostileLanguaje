"""H1 Hostile Language — Non-Markovian Hostile Language (HK-7).

A programming language where execution depends on the last k previous states.
The effective opcode at each step derives from the written opcode plus the
sum of the last k effective opcodes (mod 7).

    op_effective = (op_written + sum(last_k_effective)) % 7

With k=0: base register machine (7 instructions, no derivation)
With k>0: non-Markovian derivation with feedback loop.
"""

from .interpreter import (
    PROGRAM_OFFSET,
    MachineState,
    StepTrace,
    create_machine,
    run,
    step,
    trace_to_string,
)
from .isa import (
    CELLS_PER_INSTR,
    N_OPCODES,
    Instruction,
    Opcode,
    derive_opcode,
    flat_program,
    program_from_triplets,
    unflat_program,
)
from .synth import (
    build_cat_program,
    build_echo_program,
    build_hello_world_k0,
    preload_memory_for_hello,
    round_trip_test,
    synthesize_from_effective,
    synthesize_program,
)

__version__ = "0.1.0"
__all__ = [
    "Instruction",
    "Opcode",
    "N_OPCODES",
    "CELLS_PER_INSTR",
    "derive_opcode",
    "flat_program",
    "unflat_program",
    "program_from_triplets",
    "MachineState",
    "StepTrace",
    "create_machine",
    "step",
    "run",
    "trace_to_string",
    "PROGRAM_OFFSET",
    "synthesize_from_effective",
    "synthesize_program",
    "round_trip_test",
    "build_hello_world_k0",
    "build_cat_program",
    "build_echo_program",
    "preload_memory_for_hello",
]
