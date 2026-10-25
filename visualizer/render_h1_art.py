"""H1 Visual Art Engine — Non-Markovian Phase Space & Toroidal Geometries.

Renders:
1. 3D Torus of (Z/7Z)^k non-Markovian memory states (rotating particle swarm)
2. (PC, Delta) Phase Space limit cycles
3. FLOW cinematic & orbit profiles on H1 execution traces
4. Self-modifying Quine memory scan animation
"""

import sys
import math
import json
from pathlib import Path
from typing import List, Dict, Any, Tuple
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

FLOW_DIR = Path("/home/danny/Development/ISyCo Git/FLOW")
if str(FLOW_DIR) not in sys.path:
    sys.path.insert(0, str(FLOW_DIR))

from h1.isa import Instruction, Opcode, flat_program
from h1.interpreter import create_machine, step, StepTrace
from h1.classic_programs import (
    build_hello_world,
    build_cat,
    build_truth_machine,
    build_adder,
    build_quine,
    preload_hello_world_memory,
    preload_quine_memory,
)

# Colors for HK-7 opcodes (Futuristic Cyberpunk Palette)
OPCODE_COLORS = {
    0: (255, 60, 60),    # HALT: Crimson Red
    1: (60, 255, 120),   # INC: Neon Mint
    2: (255, 160, 40),   # DEC: Amber Orange
    3: (60, 220, 255),   # JZ: Electric Cyan
    4: (200, 80, 255),   # JNZ: Ultraviolet Purple
    5: (60, 120, 255),   # IN: Deep Sapphire
    6: (255, 235, 60),   # OUT: Radiant Gold
}

OPCODE_NAMES = {
    0: "HALT", 1: "INC", 2: "DEC", 3: "JZ", 4: "JNZ", 5: "IN", 6: "OUT"
}


# ==============================================================================
# 1. 3D TORUS OF NON-MARKOVIAN STATES: (Z/7Z)^k
# ==============================================================================

def render_torus_3d_gif(traces: List[StepTrace], out_path: Path, n_frames: int = 40):
    """Renders the execution path on the discrete 3-torus (Z/7Z)^3 with 3D rotation."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    width, height = 480, 480
    frames = []

    # Filter steps that have at least 3 history items
    points_3d = []
    opcodes = []
    for t in traces:
        h = t.history_snapshot
        if len(h) >= 3:
            h1, h2, h3 = h[-3], h[-2], h[-1]
        elif len(h) == 2:
            h1, h2, h3 = 0, h[-2], h[-1]
        elif len(h) == 1:
            h1, h2, h3 = 0, 0, h[-1]
        else:
            h1, h2, h3 = 0, 0, int(t.effective_op)

        # Toroidal angles on (Z/7Z)^3
        th1 = 2.0 * math.pi * h1 / 7.0
        th2 = 2.0 * math.pi * h2 / 7.0
        th3 = 2.0 * math.pi * h3 / 7.0

        R = 120.0
        r = 50.0
        r_inner = 18.0

        # Embedding in 3D
        x = (R + r * math.cos(th2) + r_inner * math.cos(th3)) * math.cos(th1)
        y = (R + r * math.cos(th2) + r_inner * math.cos(th3)) * math.sin(th1)
        z = r * math.sin(th2) + r_inner * math.sin(th3)

        points_3d.append((x, y, z))
        opcodes.append(int(t.effective_op))

    if not points_3d:
        return

    # Lattice vertices of the (Z/7Z)^3 torus
    lattice = []
    for i in range(7):
        for j in range(7):
            for m in [0, 3]:  # sample of 3rd dimension
                t1 = 2.0 * math.pi * i / 7.0
                t2 = 2.0 * math.pi * j / 7.0
                t3 = 2.0 * math.pi * m / 7.0
                R = 120.0
                r = 50.0
                r_inner = 18.0
                lx = (R + r * math.cos(t2) + r_inner * math.cos(t3)) * math.cos(t1)
                ly = (R + r * math.cos(t2) + r_inner * math.cos(t3)) * math.sin(t1)
                lz = r * math.sin(t2) + r_inner * math.sin(t3)
                lattice.append((lx, ly, lz))

    for f_idx in range(n_frames):
        img = Image.new("RGBA", (width, height), (10, 12, 22, 255))
        draw = ImageDraw.Draw(img)

        # Rotation angles
        angle_z = 2.0 * math.pi * f_idx / n_frames
        angle_x = 0.55 + 0.15 * math.sin(2.0 * math.pi * f_idx / n_frames)

        cos_z, sin_z = math.cos(angle_z), math.sin(angle_z)
        cos_x, sin_x = math.cos(angle_x), math.sin(angle_x)

        def project(pt):
            x, y, z = pt
            # Rotate around Z
            rx = cos_z * x - sin_z * y
            ry = sin_z * x + cos_z * y
            rz = z
            # Rotate around X
            px = rx
            py = cos_x * ry - sin_x * rz
            pz = sin_x * ry + cos_x * rz
            # Perspective projection
            fov = 380.0
            scale = fov / (fov + py + 180.0)
            sx = width / 2.0 + px * scale
            sy = height / 2.0 + pz * scale
            return sx, sy, scale

        # Draw discrete lattice nodes (faint guide)
        for pt in lattice:
            sx, sy, sc = project(pt)
            rad = max(1.0, 1.8 * sc)
            draw.ellipse([sx - rad, sy - rad, sx + rad, sy + rad], fill=(40, 55, 80, 120))

        # Draw trajectory up to current frame's progress
        step_progress = int((f_idx + 1) / n_frames * len(points_3d))
        prev_proj = None
        for i in range(max(0, step_progress - 25), step_progress):
            sx, sy, sc = project(points_3d[i])
            col = OPCODE_COLORS.get(opcodes[i], (200, 200, 200))
            fade = (i - max(0, step_progress - 25)) / 25.0
            r_col = int(col[0] * fade)
            g_col = int(col[1] * fade)
            b_col = int(col[2] * fade)

            if prev_proj is not None:
                draw.line([prev_proj[0], prev_proj[1], sx, sy], fill=(r_col, g_col, b_col, 200), width=max(1, int(2 * sc)))
            prev_proj = (sx, sy)

        # Draw current head particle
        if step_progress > 0 and step_progress <= len(points_3d):
            curr_idx = min(step_progress - 1, len(points_3d) - 1)
            sx, sy, sc = project(points_3d[curr_idx])
            col = OPCODE_COLORS.get(opcodes[curr_idx], (255, 255, 255))
            head_rad = max(3.0, 6.0 * sc)
            # Glow
            draw.ellipse([sx - head_rad * 1.8, sy - head_rad * 1.8, sx + head_rad * 1.8, sy + head_rad * 1.8], fill=(col[0], col[1], col[2], 70))
            draw.ellipse([sx - head_rad, sy - head_rad, sx + head_rad, sy + head_rad], fill=(col[0], col[1], col[2], 255))

        # HUD Overlay
        draw.text((15, 15), "H1 — (Z/7Z)^3 TOROIDAL PHASE STATE", fill=(220, 230, 255, 255))
        draw.text((15, 30), f"Attractor Cycle: k=3 Non-Markovian Drift | Frame {f_idx+1}/{n_frames}", fill=(120, 145, 190, 255))
        if step_progress > 0 and step_progress <= len(points_3d):
            curr_op = opcodes[min(step_progress - 1, len(points_3d) - 1)]
            draw.text((15, height - 25), f"Opcode: {OPCODE_NAMES.get(curr_op, '?')} (mod 7)", fill=OPCODE_COLORS.get(curr_op, (255, 255, 255)))

        frames.append(img.convert("P", palette=Image.ADAPTIVE))

    frames[0].save(out_path, save_all=True, append_images=frames[1:], duration=60, loop=0, optimize=True)
    print(f"  [RENDERED] 3D Torus GIF -> {out_path} ({out_path.stat().st_size // 1024} KB)")


# ==============================================================================
# 2. FLOW CINEMATIC & ORBIT ADAPTER
# ==============================================================================

def render_h1_with_flow(traces: List[StepTrace], out_dir: Path, name: str):
    """Adapts H1 step traces into a FLOW ExecutionTrace and renders with FLOW profiles."""
    from flow.render.profiles import render_profile
    from flow.render.spec import RenderSpec, RenderEntity

    out_dir.mkdir(parents=True, exist_ok=True)
    n_ticks = min(len(traces), 60)

    # Convert traces to FLOW particle events
    # We map (pc, delta) into a continuous canvas (800, 500)
    flow_trace: Dict[str, Any] = {
        "metadata": {
            "engine": "FLOW-H1-Bridge",
            "engine_version": "0.1.0",
            "seed": 42,
            "config": {"image_size": [600, 400]},
            "ticks": n_ticks,
            "particles_spawned": 1,
            "final_alive": 1
        },
        "ticks": [{"tick": t} for t in range(n_ticks)],
        "events": []
    }

    # Spawn main execution head
    t0 = traces[0]
    prev_x = 60.0 + (t0.pc % 12) * 45.0
    prev_y = 200.0 + (t0.derived_delta - 3) * 35.0
    flow_trace["events"].append({
        "tick": 0,
        "pid": 0,
        "type": "PARTICLE_SPAWN",
        "payload": {
            "x": prev_x,
            "y": prev_y
        }
    })

    for tick in range(1, n_ticks):
        t = traces[tick]
        px = 60.0 + (t.pc % 12) * 45.0
        py = 200.0 + (t.derived_delta - 3) * 35.0
        flow_trace["events"].append({
            "tick": tick,
            "pid": 0,
            "type": "PARTICLE_MOVE",
            "payload": {
                "x_from": prev_x,
                "y_from": prev_y,
                "x_to": px,
                "y_to": py
            }
        })
        prev_x, prev_y = px, py

    # Render Cinematic
    spec_cinematic = RenderSpec(
        profile="cinematic",
        scale=4,
        trail_length=12,
        entities=[RenderEntity(id="p0", label="H1-Head", pid=0)]
    )
    cinematic_gif = out_dir / f"{name}_flow_cinematic.gif"
    render_profile(flow_trace, cinematic_gif, spec_cinematic)
    print(f"  [RENDERED] FLOW Cinematic -> {cinematic_gif} ({cinematic_gif.stat().st_size // 1024} KB)")

    # Render Orbit
    spec_orbit = RenderSpec(
        profile="orbit",
        scale=4,
        trail_length=16,
        entities=[RenderEntity(id="p0", label="H1-Head", pid=0)]
    )
    orbit_gif = out_dir / f"{name}_flow_orbit.gif"
    render_profile(flow_trace, orbit_gif, spec_orbit)
    print(f"  [RENDERED] FLOW Orbit -> {orbit_gif} ({orbit_gif.stat().st_size // 1024} KB)")


# ==============================================================================
# 3. SELF-MODIFYING QUINE MEMORY SCAN ANIMATION
# ==============================================================================

def render_quine_memory_scan_gif(traces: List[StepTrace], mem_init: List[int], out_path: Path):
    """Renders the self-modifying pointer scanning memory cells and emitting itself."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    width, height = 520, 360
    frames = []

    # Take 30 representative steps
    steps = traces[:35]

    for f_idx, t in enumerate(steps):
        img = Image.new("RGB", (width, height), (12, 14, 24))
        draw = ImageDraw.Draw(img)

        # Title
        draw.text((15, 15), "H1 — QUINE SELF-MODIFYING MEMORY SCAN", fill=(255, 255, 255))
        draw.text((15, 32), f"Step {t.pc} | Opcode: {t.effective_op.name} | Active Cell: {t.effective_a}", fill=(130, 160, 210))

        # Memory Visualizer Grid (16 x 8 cells for 0..127)
        grid_x0, grid_y0 = 30, 70
        cell_w, cell_h = 28, 22

        for addr in range(128):
            row = addr // 16
            col = addr % 16
            x = grid_x0 + col * cell_w
            y = grid_y0 + row * cell_h

            val = t.mem_after[addr]
            is_active = (addr == t.effective_a)
            is_program = (addr >= 64 and addr < 64 + 18)

            # Base background
            if is_active:
                bg = (255, 230, 40)  # Bright gold cursor
                fg = (0, 0, 0)
            elif is_program:
                bg = (40, 60, 110)   # Code area
                fg = (180, 210, 255)
            elif val > 0:
                bg = (25, 45, 60)    # Data area
                fg = (120, 220, 180)
            else:
                bg = (18, 22, 34)    # Empty zero
                fg = (60, 70, 90)

            draw.rectangle([x, y, x + cell_w - 2, y + cell_h - 2], fill=bg)
            # Value text
            draw.text((x + 4, y + 4), f"{val:02x}" if val < 256 else "..", fill=fg)

        # Output tape at bottom
        draw.text((30, 275), "EMITTED BYTECODE STREAM:", fill=(180, 190, 210))
        emitted_str = " ".join(f"{b:02d}" for b in t.mem_after[10:10+len(t.mem_after[10:28])])
        draw.text((30, 295), emitted_str[:60] + "...", fill=(60, 255, 140))

        # Legend
        draw.rectangle([30, height - 25, 40, height - 15], fill=(40, 60, 110))
        draw.text((45, height - 25), "Program Code (64..81)", fill=(140, 160, 190))
        draw.rectangle([210, height - 25, 220, height - 15], fill=(255, 230, 40))
        draw.text((225, height - 25), "Self-Modifying Read Head", fill=(255, 230, 40))

        frames.append(img.convert("P", palette=Image.ADAPTIVE))

    frames[0].save(out_path, save_all=True, append_images=frames[1:], duration=100, loop=0, optimize=True)
    print(f"  [RENDERED] Quine Memory Scan GIF -> {out_path} ({out_path.stat().st_size // 1024} KB)")


# ==============================================================================
# MAIN PILOT RUNNER
# ==============================================================================

def main():
    art_dir = ROOT / "assets"
    art_dir.mkdir(parents=True, exist_ok=True)
    print("=" * 60)
    print("Generating H1 Visual Art Pilot (MalbolgArt for H1)")
    print("=" * 60)

    # 1. Cat with k=3 (generates a 3-torus limit cycle)
    print("\n[1] Running Cat k=3 for Toroidal Art...")
    prog_cat = build_cat(k=3)
    text = "H1_TORUS_LIMIT_CYCLE_FLOW_ENGINE!"
    state_cat = create_machine(prog_cat, mem_size=256, inputs=[ord(c) for c in text] + [0])
    while step(state_cat, k=3):
        pass
    print(f"Cat executed {len(state_cat.trace)} steps.")
    render_torus_3d_gif(state_cat.trace, art_dir / "h1_cat_torus_3d.gif", n_frames=45)
    render_h1_with_flow(state_cat.trace, art_dir, "h1_cat")

    # 2. Adder with k=3 (addition dynamics)
    print("\n[2] Running Adder k=3...")
    prog_adder = build_adder(k=3)
    state_adder = create_machine(prog_adder, mem_size=256, inputs=[25, 18])
    while step(state_adder, k=3):
        pass
    render_h1_with_flow(state_adder.trace, art_dir, "h1_adder")

    # 3. Quine with k=1 (self-modifying scan)
    print("\n[3] Running Quine k=1...")
    prog_quine = build_quine(k=1)
    flat = flat_program(prog_quine)
    state_quine = create_machine(prog_quine, mem_size=128)
    preload_quine_memory(state_quine.memory, flat)
    while step(state_quine, k=1):
        pass
    render_quine_memory_scan_gif(state_quine.trace, state_quine.memory, art_dir / "h1_quine_scan.gif")

    print("\n" + "=" * 60)
    print("H1 Visual Art Pilot Completed! Inspect artifacts in visualizer/art/")
    print("=" * 60)


if __name__ == "__main__":
    main()
