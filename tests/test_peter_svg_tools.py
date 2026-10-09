"""Source identity and expression tests without bpy or rendering."""
from __future__ import annotations

from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from peter_svg_tools import load_peter, map_points, pose_paths


class PeterVectorTests(unittest.TestCase):
    def test_head_pose_preserves_identity_and_removes_costume(self):
        paths = pose_paths(include_body=False)
        self.assertNotIn("hoodie", {record["group"] for record in paths})
        self.assertNotIn("neck", {record["group"] for record in paths})
        self.assertIn("front_hair_silhouette", {record["id"] for record in paths})
        self.assertIn("cheek_mole", {record["id"] for record in paths})

    def test_expression_replacement_and_blink(self):
        paths = pose_paths(mouth="OH", blink=True)
        identifiers = {record["id"] for record in paths}
        self.assertIn("mouth_oh", identifiers)
        self.assertNotIn("mouth_smile", identifiers)
        self.assertIn("eye_left_closed", identifiers)
        self.assertNotIn("eye_left_white", identifiers)

    def test_pose_mutations_do_not_change_master_contours(self):
        master = load_peter()
        before = tuple(master["paths"][0]["points"][0])
        pose = pose_paths(gaze=(7, 7))
        pose[0]["points"][0][0] = -100
        self.assertEqual(tuple(master["paths"][0]["points"][0]), before)
        self.assertNotEqual(pose_paths()[0]["points"][0][0], -100)

    def test_coordinate_mapping_matches_anchor_and_vertical_flip(self):
        record = {"points": [[627, 495], [637, 505]]}
        self.assertEqual(map_points(record, target=(3, 4), scale=.1), [(3, 4), (4, 3)])


if __name__ == "__main__":
    unittest.main()
