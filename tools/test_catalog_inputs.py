"""An incremental build must never retain metadata from a different dump."""
import os
from pathlib import Path
import struct
import subprocess
import tempfile
import unittest

from test_fusion_materials import fixture

ROOT = Path(__file__).resolve().parents[1]


class CatalogInputsTest(unittest.TestCase):
    def write_dump(self, game, points=2):
        table = game / "romfs/nativeNX/table"
        table.mkdir(parents=True)
        data = fixture()
        item = bytearray(data["itemData.itm"])
        item[8 + 27] = points
        data["itemData.itm"] = item
        for name, contents in data.items():
            path = table / name
            path.write_bytes(contents)
            os.utime(path, (946684800, 946684800))  # Older than every build artifact.
        return table

    def build_catalog(self, game, build):
        return subprocess.run(
            ["make", "--no-print-directory", f"BUILD={build}", f"GAME_DIR={game}",
             str(build / "armor-fusion.afus")],
            cwd=ROOT, capture_output=True, text=True,
        )

    def material_points(self, artifact):
        data = artifact.read_bytes()
        count = struct.unpack_from("<I", data, 8)[0]
        return data[48 + count * 12 + 4]

    def test_changed_dump_path_and_contents_rebuild_even_with_old_table_timestamps(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            first, second, build = root / "first", root / "second", root / "build"
            self.write_dump(first)
            table = self.write_dump(second, points=3)
            artifact = build / "armor-fusion.afus"
            result = self.build_catalog(first, build)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(self.material_points(artifact), 2)
            modified = artifact.stat().st_mtime_ns
            result = self.build_catalog(first, build)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(artifact.stat().st_mtime_ns, modified)
            result = self.build_catalog(second, build)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(self.material_points(artifact), 3)
            item = table / "itemData.itm"
            data = bytearray(item.read_bytes()); data[8 + 27] = 4
            item.write_bytes(data)
            os.utime(item, (946684800, 946684800))
            result = self.build_catalog(second, build)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(self.material_points(artifact), 4)

    def test_missing_dump_cannot_reuse_a_successful_previous_catalog(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            game, build = root / "game", root / "build"
            self.write_dump(game)
            result = self.build_catalog(game, build)
            self.assertEqual(result.returncode, 0, result.stderr)
            previous = (build / "armor-fusion.afus").read_bytes()
            result = self.build_catalog(root / "missing", build)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual((build / "armor-fusion.afus").read_bytes(), previous)


if __name__ == "__main__":
    unittest.main()
