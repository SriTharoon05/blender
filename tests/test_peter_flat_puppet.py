"""Check flat-style source and independent skeletal part contracts without bpy."""
from pathlib import Path
import sys
import unittest
import xml.etree.ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from peter_flat_puppet_tools import head_paths, load_flat_peter, part_paths


class FlatPeterTests(unittest.TestCase):
    def test_flat_style_has_one_skin_fill_and_no_shadow_regions(self):
        paths = head_paths()
        skin = {path["fill"] for path in paths if path["group"] in {"face", "ears"} and path["fill"]}
        self.assertEqual(skin, {"#FFC38A"})
        self.assertFalse(any("shadow" in path["id"] for path in paths))
        self.assertTrue(all(path["stroke"] in {None, "#111827"} for path in paths))

    def test_skeleton_parent_graph_is_complete_and_acyclic(self):
        source = load_flat_peter()
        self.assertEqual(len(source["parts"]), 15)
        for name in source["parts"]:
            seen = set()
            current = name
            while current != "root":
                self.assertNotIn(current, seen)
                seen.add(current)
                current = source["parts"][current]["parent"]

    def test_expressions_replace_parts_and_copies_are_independent(self):
        pose = head_paths(mouth="OH", blink=True)
        identifiers = {path["id"] for path in pose}
        self.assertIn("mouth_oh", identifiers)
        self.assertNotIn("mouth_rest", identifiers)
        self.assertIn("eye_left_closed", identifiers)
        self.assertNotIn("eye_left_white", identifiers)
        part = part_paths("head")
        part[0]["points"][0][0] = -123
        self.assertNotEqual(part_paths("head")[0]["points"][0][0], -123)

    def test_svg_is_vector_only_with_no_gradients(self):
        root = Path(__file__).resolve().parents[1]
        svg = ET.parse(root / "00_LIBRARY/Characters/Peter_2D/Peter_2D_Flat_Puppet_v002.svg")
        self.assertFalse(any("gradient" in node.tag.lower() or node.tag.endswith("image") for node in svg.iter()))
        ids = [node.attrib["id"] for node in svg.iter() if "id" in node.attrib]
        self.assertEqual(len(ids), len(set(ids)))


if __name__ == "__main__":
    unittest.main()
