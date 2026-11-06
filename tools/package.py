#!/usr/bin/env python3
"""Create a deterministic, allowlisted Armor Fusion mod archive."""
import argparse
import hashlib
from pathlib import Path
import struct
import zipfile

ROOT = Path(__file__).resolve().parents[1]
PLUGIN_PATH = "romfs/nativeNX/plugins/armor_fusion.nro"
PLUGIN_BUDGET = 12 * 1024 * 1024
LOADER_ALIGNMENT = 0x10000


def footprint(data):
    """Return aligned image+BSS, rejecting truncated or malformed NRO images."""
    if len(data) < 0x80 or data[0x10:0x14] != b"NRO0":
        raise ValueError("expected an NRO image")
    if struct.unpack_from("<I", data, 0x18)[0] != len(data):
        raise ValueError("NRO image size does not match its header")
    end = 0
    for offset in (0x20, 0x28, 0x30):
        start, size = struct.unpack_from("<II", data, offset)
        if start != end or size == 0 or start % 0x1000 or size % 0x1000:
            raise ValueError("NRO segments must be contiguous, nonempty and page aligned")
        end = start + size
    if end != len(data):
        raise ValueError("NRO segments do not cover the image")
    bss = struct.unpack_from("<I", data, 0x38)[0]
    return (len(data) + bss + LOADER_ALIGNMENT - 1) & ~(LOADER_ALIGNMENT - 1)


def package(nro, output, other_plugins=()):
    image = nro.read_bytes()
    used = footprint(image) + sum(footprint(path.read_bytes()) for path in other_plugins)
    # Recomp's loader also requires one 64 KiB margin beyond the next image.
    # This conservative bound is safe regardless of plugin enumeration order.
    if used + LOADER_ALIGNMENT > PLUGIN_BUDGET:
        raise ValueError("plugins plus loader headroom exceed the shared 12 MiB plugin region")
    files = {
        "README.md": (ROOT / "README.md").read_bytes(),
        "LICENSE": (ROOT / "LICENSE").read_bytes(),
        "LICENSE.forge-rs": (ROOT / "link/LICENSE.forge-rs").read_bytes(),
        PLUGIN_PATH: image,
    }
    files["SHA256SUMS"] = "".join(
        f"{hashlib.sha256(data).hexdigest()}  {name}\n" for name, data in files.items()
    ).encode()
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name, data in files.items():
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, data, compresslevel=9)
    return used


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--nro", type=Path, default=ROOT / "build/armor_fusion.nro")
    parser.add_argument("--output", type=Path, default=ROOT / "dist/native-armor-fusion.zip")
    parser.add_argument("--other-plugin", type=Path, action="append", default=[],
                        help="check combined memory use; never include this plugin in the archive")
    args = parser.parse_args()
    try:
        used = package(args.nro, args.output, args.other_plugin)
    except (OSError, ValueError) as error:
        parser.exit(1, f"package: {error}\n")
    print(f"{args.output}: {hashlib.sha256(args.output.read_bytes()).hexdigest()}")
    print(f"Aligned plugin memory: {used} bytes + {LOADER_ALIGNMENT} bytes loader headroom / {PLUGIN_BUDGET}")


if __name__ == "__main__":
    main()
