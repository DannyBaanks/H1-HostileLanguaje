# Contributing to H1 Hostile Language

Gracias por contribuir a H1.

## Desarrollo

```bash
# Entorno
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\Activate.ps1
pip install -e ".[dev]"

# Tests
pytest -v

# Lint
ruff check .
black --check .
mypy src/h1
```

## Estructura

```
src/h1/          # Paquete principal (isa, interpreter, synth)
tests/           # Tests unitarios
examples/        # Programas de ejemplo .h1 + build_examples.py
docs/            # Documentación adicional
```

## Guidelines

- **No romper k=0**: k=0 debe ser siempre la máquina base (7 instrucciones, sin deriva).
- **Deriva determinista**: con feedback loop efectivo, la síntesis es O(n) y única.
- **Tests obligatorios**: cada cambio debe pasar `pytest -v` y añadir tests para nueva funcionalidad.
- **Trazas completas**: el intérprete debe emitir `written_op`, `history`, `delta`, `effective_op` por paso.
- **Operandos no derivan**: solo el opcode (mod 7). Encoding fijo 3 celdas.

## Añadir lenguaje nuevo

Si extiendes la ISA:
1. Añade opcode en `isa.py::Opcode`
2. Actualiza `arity` property
3. Añade semántica en `interpreter.py::step()`
4. Tests de round-trip para k∈{0,1,3,7,16}

## Reportar issues

Incluye:
- k usado
- Programa fuente (o pasos para reproducir)
- Traza esperada vs obtenida
- `trace_to_string()` output

---

**Nota**: H1 es investigación (ISyCo experiment E25 base). No hay promesa de estabilidad API.