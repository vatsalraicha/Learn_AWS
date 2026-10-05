#!/usr/bin/env python3
"""Pre-process a markdown file: find every ```mermaid ... ``` block, render it to PNG
via the `mmdc` CLI, and replace the block with an image reference.

Output: a sibling .processed.md file alongside the original.
Rendered PNGs go into ./mermaid_images/.
"""
import hashlib
import re
import subprocess
import sys
from pathlib import Path

if len(sys.argv) != 3:
    print(f"usage: {sys.argv[0]} <input.md> <output.md>", file=sys.stderr)
    sys.exit(1)

src = Path(sys.argv[1])
dst = Path(sys.argv[2])
img_dir = dst.parent / "mermaid_images"
img_dir.mkdir(exist_ok=True)

content = src.read_text()
mermaid_pattern = re.compile(r"```mermaid\n(.*?)\n```", re.DOTALL)

blocks = mermaid_pattern.findall(content)
print(f"Found {len(blocks)} mermaid block(s) in {src.name}", file=sys.stderr)


def render_block(diagram_text: str, idx: int) -> str:
    """Render one mermaid diagram to PNG; return the image filename."""
    # Hash-based filename for deterministic / cache-friendly output
    h = hashlib.md5(diagram_text.encode()).hexdigest()[:10]
    out_name = f"diagram_{idx:03d}_{h}.png"
    out_path = img_dir / out_name
    if out_path.exists():
        return out_name

    mmd_in = img_dir / f"_tmp_{idx:03d}.mmd"
    mmd_in.write_text(diagram_text)
    try:
        result = subprocess.run(
            [
                "mmdc",
                "-i", str(mmd_in),
                "-o", str(out_path),
                "-t", "default",
                "-b", "white",
                "-w", "1400",
                "--quiet",
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode != 0:
            print(f"  WARN: mmdc failed on block {idx}: {result.stderr[:200]}", file=sys.stderr)
            return None
        return out_name
    except subprocess.TimeoutExpired:
        print(f"  WARN: mmdc timed out on block {idx}", file=sys.stderr)
        return None
    finally:
        if mmd_in.exists():
            mmd_in.unlink()


# Replace each block in order
def replace(match: re.Match) -> str:
    idx = replace.counter
    replace.counter += 1
    diagram = match.group(1)
    img_name = render_block(diagram, idx)
    if img_name is None:
        # Fallback: keep the mermaid code block
        return match.group(0)
    return f"![Diagram {idx}](mermaid_images/{img_name})"

replace.counter = 0
processed = mermaid_pattern.sub(replace, content)

dst.write_text(processed)
print(f"Wrote {dst} ({replace.counter} diagram(s) replaced)", file=sys.stderr)
