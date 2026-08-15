"""H1 Hostile Language — ISA (HK-7)
7 instrucciones, encoding fijo 3 celdas: (op, a, o).
Solo el opcode deriva; operandos a,o son literales.
"""

from dataclasses import dataclass
from enum import IntEnum


class Opcode(IntEnum):
    HALT = 0
    INC = 1
    DEC = 2
    JZ = 3
    JNZ = 4
    IN = 5
    OUT = 6

    @property
    def arity(self) -> int:
        if self == Opcode.HALT:
            return 0
        if self in (Opcode.INC, Opcode.DEC, Opcode.IN, Opcode.OUT):
            return 1
        return 2  # JZ, JNZ


@dataclass(frozen=True)
class Instruction:
    op: Opcode
    a: int = 0
    o: int = 0

    def encode(self) -> tuple[int, int, int]:
        return (int(self.op), self.a, self.o)

    @staticmethod
    def decode(triplet: tuple[int, int, int]) -> "Instruction":
        op_raw, a, o = triplet
        try:
            op = Opcode(op_raw % 7)
        except ValueError:
            op = Opcode.HALT
        return Instruction(op, a, o)


N_OPCODES = 7
CELLS_PER_INSTR = 3


def derive_opcode(op_written: int, history: list[int], k: int) -> int:
    """op_efectivo = (op_escrito + sum(ultimos k opcodes_efectivos)) mod 7"""
    if k <= 0 or not history:
        return op_written % N_OPCODES
    relevant = history[-k:]
    return (op_written + sum(relevant)) % N_OPCODES


def program_from_triplets(triplets: list[tuple[int, int, int]]) -> list[Instruction]:
    return [Instruction.decode(t) for t in triplets]


def triplets_from_program(prog: list[Instruction]) -> list[tuple[int, int, int]]:
    return [instr.encode() for instr in prog]


def flat_program(prog: list[Instruction]) -> list[int]:
    out = []
    for instr in prog:
        out.extend(instr.encode())
    return out


def unflat_program(cells: list[int]) -> list[Instruction]:
    if len(cells) % CELLS_PER_INSTR != 0:
        raise ValueError(f"Longitud no múltiplo de {CELLS_PER_INSTR}")
    return [
        Instruction.decode((cells[i], cells[i + 1], cells[i + 2]))
        for i in range(0, len(cells), CELLS_PER_INSTR)
    ]
