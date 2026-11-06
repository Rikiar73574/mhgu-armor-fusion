"""Release archives contain only the mod and its notices, with real checksums."""
import hashlib
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools/package.py"
PLUGIN = "romfs/nativeNX/plugins/armor_fusion.nro"


def nro(bss=0):
    image = bytearray(0x3000)
    struct.pack_into("<I", image, 4, 0x80)
    image[0x10:0x14] = b"NRO0"
    struct.pack_into("<I", image, 0x18, len(image))
    for index in range(3):
        struct.pack_into("<II", image, 0x20 + index * 8, index * 0x1000, 0x1000)
    struct.pack_into("<I", image, 0x38, bss)
    image[0x80:0x84] = b"MOD0"
    return image


class PackageTests(unittest.TestCase):
    def run_package(self, directory, image, *extra):
        source = directory / "armor.nro"
        source.write_bytes(image)
        output = directory / "release.zip"
        result = subprocess.run(
            [sys.executable, str(TOOL), "--nro", str(source), "--output", str(output), *extra],
            capture_output=True, text=True,
        )
        return result, output

    def test_archive_is_reproducible_and_has_only_runtime_payload_and_notices(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            payload = nro()
            result, output = self.run_package(directory, payload)
            self.assertEqual(result.returncode, 0, result.stderr)
            first = output.read_bytes()
            with zipfile.ZipFile(output) as archive:
                self.assertEqual(set(archive.namelist()), {PLUGIN, "README.md", "LICENSE", "LICENSE.forge-rs", "SHA256SUMS"})
                self.assertEqual(archive.read(PLUGIN), payload)
                self.assertEqual(archive.read("README.md"), (ROOT / "README.md").read_bytes())
                self.assertEqual(archive.read("LICENSE"), (ROOT / "LICENSE").read_bytes())
                self.assertEqual(archive.read("LICENSE.forge-rs"), (ROOT / "link/LICENSE.forge-rs").read_bytes())
                entries = dict(line.split("  ", 1)[::-1] for line in archive.read("SHA256SUMS").decode().splitlines())
                self.assertEqual(set(entries), {PLUGIN, "README.md", "LICENSE", "LICENSE.forge-rs"})
                for name, digest in entries.items():
                    self.assertEqual(digest, hashlib.sha256(archive.read(name)).hexdigest())
            result, output = self.run_package(directory, payload)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(output.read_bytes(), first)

    def test_invalid_or_truncated_nro_is_rejected_without_output(self):
        for image in [b"not a plugin", nro()[:-1], nro()[:0x80]]:
            with self.subTest(size=len(image)), tempfile.TemporaryDirectory() as temporary:
                result, output = self.run_package(Path(temporary), image)
                self.assertNotEqual(result.returncode, 0)
                self.assertFalse(output.exists())
                self.assertIn("NRO", result.stderr)

    def test_shared_memory_check_counts_bss_other_plugins_and_loader_headroom(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            peer = directory / "compendium.nro"
            peer.write_bytes(nro(8 * 1024 * 1024))
            result, output = self.run_package(directory, nro(4 * 1024 * 1024), "--other-plugin", str(peer))
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse(output.exists())
            self.assertIn("12 MiB", result.stderr)
            result, output = self.run_package(directory, nro(), "--other-plugin", str(peer))
            self.assertEqual(result.returncode, 0, result.stderr)
            with zipfile.ZipFile(output) as archive:
                self.assertNotIn("compendium.nro", archive.namelist())


if __name__ == "__main__":
    unittest.main()
