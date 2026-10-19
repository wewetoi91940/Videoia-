"""Grain de film fixe (512 px, répété) : casse les aplats et évite les bandes de compression. Graine fixe."""
from pathlib import Path

import numpy as np
from PIL import Image

rng = np.random.default_rng(17)
g = np.clip(128 + rng.normal(0, 46, (512, 512)), 0, 255).astype(np.uint8)
Image.fromarray(g, "L").save(Path(__file__).resolve().parent.parent / "assets" / "grain.png", optimize=True)
