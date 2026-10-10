"""EP010 delivery guard regressions; no network, Blender or GPU required."""
from copy import deepcopy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from ep010_verify_delivery import EXPECTED_LINES, verify_caption_metadata, verify_peter_voice


class EP010DeliveryTests(unittest.TestCase):
    def voice_fixture(self):
        identity = {"provider": "Gemini", "voice": "Charon", "gender": "male",
                    "locked": True, "allow_voice_fallback": False}
        cues = {"tts_provider": "Gemini", "tts_model": "test-model", "character_voices": {"Peter": deepcopy(identity)},
                "peter_voice_catalog_evidence": {"voice": "Charon", "gender": "male", "verified_live_catalog": True},
                "lines": [{"id": "L01", "speaker": "peter", "character": "Peter", "voice": "Charon", "audio": "peter.wav"},
                          {"id": "L02", "speaker": "inner", "character": "Peter", "voice": "Charon", "audio": "inner.wav"}]}
        generation = {"lines": [{"id": line["id"], "speaker": line["speaker"], "voice": "Charon", "tts_model": "test-model",
                                 "fitted_audio": line["audio"], "raw_audio": line["id"] + "_raw.wav",
                                 "raw_audio_sha256": "a" * 64, "fitted_audio_sha256": "b" * 64} for line in cues["lines"]]}
        hashes = {name: digest for row in generation["lines"] for name, digest in
                  ((row["raw_audio"], row["raw_audio_sha256"]), (row["fitted_audio"], row["fitted_audio_sha256"]))}
        return {"peter_voice": "Charon"}, cues, {"tts_character_voices": {"Peter": identity}}, generation, hashes

    def caption_fixture(self):
        words, lines, records = [], [], []
        for identifier, speaker, text in EXPECTED_LINES:
            line_words = []
            for word in text.split():
                start = len(words) * 2 + 1
                row = {"word": word, "speaker": speaker, "start_frame": start, "end_frame": start + 1}
                words.append(row)
                line_words.append(row)
                records.append({**row, "max_bounds_px": [140, 1360, 830, 1450]})
            lines.append({"id": identifier, "speaker": speaker, "text": text, "words": line_words})
        cues = {"lines": lines, "words": words, "mouth_frames": [{"frame": frame} for frame in range(1, 529)],
                "timing_source": "Test fixture representing measured source"}
        project = {"spoken_caption_records": records, "caption_shake_fixed": True,
                   "title_records": [{"text": "BINGE WATCHING", "interval": [1, 516], "bounds_px": [110, 310, 900, 470]},
                                     {"text": "POV: ONE EPISODE TURNED\nINTO THE WHOLE SEASON.", "interval": [517, 528],
                                      "bounds_px": [110, 310, 900, 470]}]}
        return project, cues

    def test_same_voice_and_real_audio_hashes_cover_inner_thoughts(self):
        project, cues, defaults, generation, hashes = self.voice_fixture()
        report = verify_peter_voice(project, cues, defaults, generation, hashes.__getitem__)
        self.assertTrue(report["all_voice_checks_passed"])
        self.assertEqual(report["inner_line_count"], 1)

    def test_inner_thought_cannot_use_another_voice(self):
        project, cues, defaults, generation, hashes = self.voice_fixture()
        cues["lines"][1]["voice"] = "Puck"
        report = verify_peter_voice(project, cues, defaults, generation, hashes.__getitem__)
        self.assertFalse(report["all_voice_checks_passed"])
        self.assertTrue(any("L02" in error for error in report["errors"]))

    def test_inner_audio_tampering_fails_despite_correct_labels(self):
        project, cues, defaults, generation, hashes = self.voice_fixture()
        hashes["inner.wav"] = "c" * 64
        report = verify_peter_voice(project, cues, defaults, generation, hashes.__getitem__)
        self.assertFalse(report["all_voice_checks_passed"])
        self.assertTrue(any("fitted audio hash" in error for error in report["errors"]))

    def test_complete_nonoverlapping_safe_captions_pass(self):
        project, cues = self.caption_fixture()
        self.assertEqual(verify_caption_metadata(project, cues)["errors"], [])

    def test_popped_caption_outside_phone_safe_band_fails(self):
        project, cues = self.caption_fixture()
        project["spoken_caption_records"][0]["max_bounds_px"][2] = 920
        report = verify_caption_metadata(project, cues)
        self.assertTrue(any("safe band" in error for error in report["errors"]))

    def test_final_title_cannot_cover_spoken_button_or_miss_final_hold(self):
        project, cues = self.caption_fixture()
        project["title_records"][-1]["interval"] = [505, 528]
        report = verify_caption_metadata(project, cues)
        self.assertTrue(any("517..528" in error for error in report["errors"]))

    def test_missing_late_lip_sync_rows_is_not_an_18_second_success(self):
        project, cues = self.caption_fixture()
        cues["mouth_frames"] = cues["mouth_frames"][:432]
        report = verify_caption_metadata(project, cues)
        self.assertTrue(any("528" in error for error in report["errors"]))


if __name__ == "__main__":
    unittest.main()
