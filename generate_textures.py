"""
generate_textures.py
Generate a CS2-valid PBR texture set for CERN_ScienceGateway as a 2-region
ATLAS matching the build script's UVs:

    LEFT  half (U 0.0-0.5) : concrete / steel  (tubes, columns, walls, plaza)
    RIGHT half (U 0.5-1.0) : photovoltaic panel grid  (building roofs)

Outputs (2048x2048, PNG) next to this script:
  CERN_ScienceGateway_BaseColor.png    RGB diffuse, A = opacity (opaque)
  CERN_ScienceGateway_ControlMask.png  off
  CERN_ScienceGateway_MaskMap.png      R metallic, G coat, B 0, A smoothness
  CERN_ScienceGateway_Normal.png       OpenGL tangent-space normal
  CERN_ScienceGateway_Emissive.png     black

Run:  python3 generate_textures.py     (pure PIL + numpy)
"""
import os
import numpy as np
from PIL import Image

SIZE = 2048
HALF = SIZE // 2
NAME = "CERN_ScienceGateway"
OUT = os.path.dirname(os.path.abspath(__file__))
PANEL_CELLS = 21                       # ~2 m panels across a 43 m roof


def value_noise(size, cells, seed, octaves=4, persistence=0.5):
    rng = np.random.default_rng(seed)
    acc = np.zeros((size, size), np.float32)
    amp, tot, c = 1.0, 0.0, cells
    for _ in range(octaves):
        grid = rng.random((c + 1, c + 1)).astype(np.float32)
        img = np.asarray(Image.fromarray((grid * 255).astype(np.uint8))
                         .resize((size, size), Image.BICUBIC), np.float32) / 255.0
        acc += img * amp
        tot += amp
        amp *= persistence
        c *= 2
    return acc / tot


def to_u8(a):
    return np.clip(a * 255.0 + 0.5, 0, 255).astype(np.uint8)


def panel_masks():
    """Return (grid_line_mask, cell_jitter) for the RIGHT half (HALF x SIZE)."""
    xs = np.arange(HALF)                      # 0..1024 maps to U 0.5..1.0 (43 m)
    ys = np.arange(SIZE)                      # 0..2048 maps to V 0..1   (43 m)
    cw = HALF / PANEL_CELLS
    ch = SIZE / PANEL_CELLS
    fx = (xs % cw) / cw
    fy = (ys % ch) / ch
    line_w = 0.06
    lx = (fx < line_w) | (fx > 1 - line_w)
    ly = (fy < line_w) | (fy > 1 - line_w)
    grid = lx[None, :] | ly[:, None]         # (SIZE, HALF) bool
    cellx = (xs // cw).astype(int)
    celly = (ys // ch).astype(int)
    rng = np.random.default_rng(7)
    jit_table = rng.uniform(-0.04, 0.04, (PANEL_CELLS + 2, PANEL_CELLS + 2)).astype(np.float32)
    jit = jit_table[celly[:, None], cellx[None, :]]
    return grid, jit


def main():
    big = value_noise(SIZE, 6, 1)
    fine = value_noise(SIZE, 64, 2)
    grid, jit = panel_masks()

    # ---------------- BaseColor ----------------
    rgb = np.zeros((SIZE, SIZE, 3), np.float32)
    # left: concrete / silver-grey
    tone = 0.70 + (big - 0.5) * 0.10 + (fine - 0.5) * 0.05
    for k, m in enumerate((0.99, 1.0, 1.02)):
        rgb[:, :HALF, k] = tone[:, :HALF] * m
    # right: PV panels (deep blue cells, lighter frames)
    panel = np.empty((SIZE, HALF, 3), np.float32)
    panel[..., 0] = 0.09 + jit
    panel[..., 1] = 0.12 + jit
    panel[..., 2] = 0.20 + jit
    frame = np.array([0.30, 0.31, 0.34], np.float32)
    panel[grid] = frame
    rgb[:, HALF:, :] = np.clip(panel, 0, 1)
    a = np.ones((SIZE, SIZE), np.float32)
    Image.fromarray(np.dstack([to_u8(rgb), to_u8(a)]), "RGBA").save(
        os.path.join(OUT, f"{NAME}_BaseColor.png"))

    # ---------------- ControlMask (off) ----------------
    z = np.zeros((SIZE, SIZE), np.uint8)
    Image.fromarray(np.dstack([z, z, z, z]), "RGBA").save(
        os.path.join(OUT, f"{NAME}_ControlMask.png"))

    # ---------------- MaskMap (R metallic, G coat, B 0, A smooth) ----------------
    metal = np.zeros((SIZE, SIZE), np.float32)
    smooth = np.zeros((SIZE, SIZE), np.float32)
    metal[:, :HALF] = 0.20 + (fine[:, :HALF] - 0.5) * 0.1     # concrete/steel
    smooth[:, :HALF] = 0.34 + (big[:, :HALF] - 0.5) * 0.1
    mr = np.full((SIZE, HALF), 0.75, np.float32)             # glossy glass panels
    sr = np.full((SIZE, HALF), 0.85, np.float32)
    mr[grid] = 0.25
    sr[grid] = 0.35
    metal[:, HALF:] = mr
    smooth[:, HALF:] = sr
    coat = np.zeros((SIZE, SIZE), np.float32)
    blue = np.zeros((SIZE, SIZE), np.float32)
    Image.fromarray(np.dstack([to_u8(metal), to_u8(coat), to_u8(blue), to_u8(smooth)]),
                    "RGBA").save(os.path.join(OUT, f"{NAME}_MaskMap.png"))

    # ---------------- Normal (flat + faint panel frame relief) ----------------
    nx = np.full((SIZE, SIZE), 0.5, np.float32)
    ny = np.full((SIZE, SIZE), 0.5, np.float32)
    gx = np.gradient(fine, axis=1) * 5.0
    gy = np.gradient(fine, axis=0) * 5.0
    nx[:, :HALF] = np.clip(0.5 + gx[:, :HALF] * 0.5, 0, 1)
    ny[:, :HALF] = np.clip(0.5 + gy[:, :HALF] * 0.5, 0, 1)
    nz = np.ones((SIZE, SIZE), np.float32)
    Image.fromarray(np.dstack([to_u8(nx), to_u8(ny), to_u8(nz)]), "RGB").save(
        os.path.join(OUT, f"{NAME}_Normal.png"))

    # ---------------- Emissive (black) ----------------
    Image.fromarray(np.dstack([z, z, z]), "RGB").save(
        os.path.join(OUT, f"{NAME}_Emissive.png"))

    for f in ("BaseColor", "ControlMask", "MaskMap", "Normal", "Emissive"):
        p = os.path.join(OUT, f"{NAME}_{f}.png")
        print(f"  wrote {os.path.basename(p)}  ({os.path.getsize(p)//1024} KB)")


if __name__ == "__main__":
    main()
