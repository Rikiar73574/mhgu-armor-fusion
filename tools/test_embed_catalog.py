from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest

from embed_catalog import embed_catalog


class EmbedCatalogTest(unittest.TestCase):
    def test_embeds_exact_bytes_deterministically(self):
        data = bytes(range(256))
        output = embed_catalog(data)
        self.assertEqual(output, embed_catalog(data))
        encoded = bytes(int(value, 16) for value in re.findall(r"0x([0-9a-f]{2})", output))
        self.assertEqual(encoded, data)
        self.assertIn("static const uint8_t fusion_catalog_bytes[]", output)
        self.assertIn("static const size_t fusion_catalog_size = sizeof fusion_catalog_bytes;", output)

    def test_empty_input_is_rejected(self):
        with self.assertRaises(ValueError):
            embed_catalog(b"")

    def test_cli_writes_include_from_input(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source.afus"
            output = Path(directory) / "catalog.inc"
            source.write_bytes(b"AFUS\x00\xff")
            subprocess.run([sys.executable, str(Path(__file__).with_name("embed_catalog.py")),
                            str(source), str(output)], check=True)
            self.assertEqual(output.read_text(), embed_catalog(source.read_bytes()))


if __name__ == "__main__":
    unittest.main()
