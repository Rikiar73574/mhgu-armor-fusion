"""Record dump identity and content; preserve the stamp when nothing changed."""
import argparse
import hashlib
import json
from pathlib import Path

from fusion_materials import FORMATS


def verify_inputs(table_dir: Path, output: Path) -> None:
    source = table_dir.resolve()
    state = {
        "table_dir": str(source),
        "source_sha256": {
            name: hashlib.sha256((source / name).read_bytes()).hexdigest()
            for name in sorted(FORMATS)
        },
    }
    data = (json.dumps(state, indent=2) + "\n").encode()
    if not output.exists() or output.read_bytes() != data:
        output.write_bytes(data)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("table_dir", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    try:
        verify_inputs(args.table_dir, args.output)
    except OSError as error:
        parser.exit(1, f"catalog inputs: {error}\n")


if __name__ == "__main__":
    main()
