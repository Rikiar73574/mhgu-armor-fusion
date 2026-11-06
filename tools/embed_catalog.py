"""Embed a locally generated AFUS catalog as a freestanding C include."""
import argparse
from pathlib import Path


def embed_catalog(data: bytes) -> str:
    if not data:
        raise ValueError("cannot embed an empty catalog")
    lines = ["/* Generated from the player's own dump. Do not commit. */",
             "static const uint8_t fusion_catalog_bytes[] = {"]
    lines.extend("    " + ", ".join(f"0x{value:02x}" for value in data[i:i + 12]) + ","
                 for i in range(0, len(data), 12))
    lines.extend(["};", "static const size_t fusion_catalog_size = sizeof fusion_catalog_bytes;", ""])
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("catalog", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    args.output.write_text(embed_catalog(args.catalog.read_bytes()))


if __name__ == "__main__":
    main()
