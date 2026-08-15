# H1 Design Document

## Overview

H1 (Hostile Language 1) is a non-Markovian programming language where the effective opcode at each step depends on the history of previously executed effective opcodes.

## Core Semantics

```
op_effective = (op_written + Σ_{i=1..k} op_effective_{t-i}) mod 7
```

Where:
- `op_written`: the opcode literally written in the program
- `k`: history length parameter (k ≥ 0)
- `H = [op_effective_{t-1}, ..., op_effective_{t-k}]`: history of effective opcodes

### k = 0 (Base Machine)
- No derivation: `op_effective = op_written`
- Pure register machine with 7 instructions

### k > 0 (Hostile Mode)
- Derivation with feedback loop
- History stores **effective** opcodes, not written ones
- Creates genuine non-Markovian behavior: a change at step t cascades to all subsequent steps

## ISA (HK-7)

| Opcode | Mnemonic | Arity | Semantics |
|--------|----------|-------|-----------|
| 0 | HALT | 0 | Stop execution |
| 1 | INC a | 1 | `mem[a] = (mem[a] + 1) mod 256` |
| 2 | DEC a | 1 | `mem[a] = (mem[a] - 1) mod 256` |
| 3 | JZ a o | 2 | `if mem[a] == 0: pc = o` |
| 4 | JNZ a o | 2 | `if mem[a] != 0: pc = o` |
| 5 | IN a | 1 | `mem[a] = input[ptr++]` (0 if EOF) |
| 6 | OUT a | 1 | `output.append(mem[a])` |

**Encoding**: Fixed 3 cells per instruction: `(op, a, o)`. Operands never derive.

## Memory Layout

```
[0..63]     Data memory (accessible by instructions)
[64..]      Program memory (read-only during execution)
```

Program offset = 64 cells. Prevents accidental self-modification.

## Synthesizer

Given target effective opcodes `[e₁, e₂, ..., eₙ]`, compute written opcodes:

```
w₁ = e₁                                    (H = [])
w₂ = (e₂ - w₁) mod 7                       (H = [e₁])
w₃ = (e₃ - (e₁ + e₂)) mod 7               (H = [e₁, e₂])
...
wᵢ = (eᵢ - Σ_{j=1..k} e_{i-j}) mod 7
```

Deterministic O(n). Unique solution per step because H is already fixed left-to-right.

## Why Effective History (Not Written)?

| Approach | Precomputable? | Cascading Changes? |
|----------|----------------|-------------------|
| Written history | Yes (static) | No |
| **Effective history** | **No** | **Yes** |

With effective history, the language is **genuinely non-Markovian** — not syntactic sugar over the base machine.

## Program Structure

- `.h1` files: space-separated integers (flat program: `op a o op a o ...`)
- Programs are pure code; data memory must be preloaded separately (e.g., hello world chars at cells 10-21)

## Testing Strategy

1. **k=0 identity**: H1(k=0) ≡ base register machine
2. **Round-trip**: synthesize(target, k) → execute → effective == target for k ∈ {0,1,3,7,16}
3. **Feedback loop**: modifying step 3 changes source at step 4+
4. **Data independence**: same source + different inputs → same effective opcodes
5. **Tracing**: every step emits written/history/delta/effective

## Examples

- `hello_k*.h1`: "Hello World\n" (requires memory preload at cells 10-21)
- `cat_k*.h1`: IN→OUT loop until EOF
- `echo_k*.h1`: IN→OUT→HALT

## Future Work (E25 Experiment)

- Hostility index quantification
- H(k) curve analysis
- Comparison with Malbolge
- Automatic synthesis from behavioral specs (BFS/DFS over source space)