import unittest
from pathlib import Path

import sadasend


class TestPackaging(unittest.TestCase):
    def test_version_matches(self):
        self.assertEqual(sadasend.__version__, "0.1.2")
        self.assertEqual(sadasend.VERSION, "0.1.2")

    def test_all_exports_exist(self):
        for name in sadasend.__all__:
            self.assertTrue(
                hasattr(sadasend, name),
                f"Exported attribute '{name}' listed in __all__ does not exist in sadasend",
            )

    def test_pep_561_py_typed_marker_exists(self):
        pkg_dir = Path(sadasend.__file__).resolve().parent
        py_typed = pkg_dir / "py.typed"
        self.assertTrue(py_typed.exists(), "PEP 561 marker 'sadasend/py.typed' is required for IDE/mypy support")

    def test_zero_runtime_dependencies(self):
        pyproject_path = Path(__file__).resolve().parent.parent / "pyproject.toml"
        content = pyproject_path.read_text(encoding="utf-8")
        self.assertIn("dependencies = []", content, "SDK must maintain zero runtime dependencies")

    def test_all_resources_annotated_on_sadasend(self):
        annotations = sadasend.SadaSend.__annotations__
        for res_name in sadasend._generated.RESOURCES:
            self.assertIn(
                res_name,
                annotations,
                f"Resource '{res_name}' from RESOURCES must be annotated on SadaSend class",
            )
        self.assertIn("support", annotations)

    def test_client_has_all_resources_at_runtime(self):
        client = sadasend.SadaSend("sada_live_sk_test")
        for res_name in sadasend._generated.RESOURCES:
            self.assertTrue(
                hasattr(client, res_name),
                f"Client missing runtime resource attribute '{res_name}'",
            )
        self.assertTrue(hasattr(client, "support"))


if __name__ == "__main__":
    unittest.main()
