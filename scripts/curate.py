"""Curación manual de candidatos generados.

Abre cada imagen en el viewer del SO y te pregunta keep/skip. Las que kept se copian
a un directorio aparte (`outputs/canon/`) listo para ser dataset de training del LoRA.

Uso:
    python scripts/curate.py --input outputs/candidates --output outputs/canon --target 25

Acciones por imagen:
    [k] keep   — copiar a output dir
    [s] skip   — saltar (no copiar)
    [u] undo   — deshacer última decisión
    [q] quit   — salir y guardar progreso
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

IMG_EXTS = {".png", ".jpg", ".jpeg", ".webp"}


def open_in_viewer(path: Path) -> None:
    """Abre la imagen en el viewer default del SO. Cross-platform."""
    if sys.platform.startswith("win"):
        subprocess.Popen(["cmd", "/c", "start", "", str(path)], shell=False)
    elif sys.platform == "darwin":
        subprocess.Popen(["open", str(path)])
    else:
        subprocess.Popen(["xdg-open", str(path)])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", type=Path, required=True, help="Dir con candidatos generados")
    ap.add_argument("--output", type=Path, required=True, help="Dir donde se copian los kept")
    ap.add_argument("--target", type=int, default=25, help="Cuántos kept apuntás (informativo)")
    ap.add_argument("--state", type=Path, default=None, help="State file para retomar (default <output>/_curate_state.json)")
    args = ap.parse_args()

    args.output.mkdir(parents=True, exist_ok=True)
    state_file = args.state or (args.output / "_curate_state.json")

    state: dict = {"decided": {}}  # filename -> "keep" | "skip"
    if state_file.exists():
        state = json.loads(state_file.read_text())

    candidates = sorted(p for p in args.input.iterdir() if p.suffix.lower() in IMG_EXTS)
    if not candidates:
        print(f"No images found in {args.input}")
        return 1

    history: list[tuple[Path, str]] = []
    kept = sum(1 for v in state["decided"].values() if v == "keep")

    for img in candidates:
        if img.name in state["decided"]:
            continue

        print(f"\n[{kept}/{args.target} kept]  reviewing: {img.name}")
        open_in_viewer(img)
        while True:
            choice = input("  [k]eep / [s]kip / [u]ndo / [q]uit > ").strip().lower()
            if choice == "k":
                shutil.copy2(img, args.output / img.name)
                state["decided"][img.name] = "keep"
                history.append((img, "keep"))
                kept += 1
                break
            elif choice == "s":
                state["decided"][img.name] = "skip"
                history.append((img, "skip"))
                break
            elif choice == "u":
                if not history:
                    print("  (nothing to undo)")
                    continue
                last_img, last_action = history.pop()
                state["decided"].pop(last_img.name, None)
                if last_action == "keep":
                    target = args.output / last_img.name
                    if target.exists():
                        target.unlink()
                    kept -= 1
                print(f"  undone: {last_img.name}")
                break
            elif choice == "q":
                state_file.write_text(json.dumps(state, indent=2))
                print(f"\nSaved state. {kept} kept so far.")
                return 0
            else:
                print("  invalid input")

        state_file.write_text(json.dumps(state, indent=2))

    print(f"\nDone. {kept} images kept in {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
