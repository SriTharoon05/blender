"""Delivery regressions for the wrong-voice correction, without network/GPU."""
from copy import deepcopy
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from ep009_verify_delivery import committed_source_matches, verify_peter_voice


class PeterDeliveryVoiceTests(unittest.TestCase):
    def fixture(self):
        identity = {"provider": "Gemini", "voice": "Charon", "gender": "male",
                    "locked": True, "allow_voice_fallback": False}
        project = {"peter_voice": "Charon"}
        cues = {"character_voices": {"Peter": deepcopy(identity)},
                "tts_provider": "Gemini", "tts_model": "example-tts-model",
                "peter_voice_catalog_evidence": {"voice": "Charon", "gender": "male",
                                                  "verified_live_catalog": True},
                "lines": [{"id": "L01", "speaker": "employee", "character": "Peter",
                           "voice": "Charon", "audio": "episode/L01_Dialogue.wav"},
                          {"id": "L02", "speaker": "host", "voice": "Puck"}]}
        defaults = {"tts_character_voices": {"Peter": identity}}
        generation = {"lines": [{"id": "L01", "speaker": "employee", "voice": "Charon",
                       "tts_model": "example-tts-model", "raw_audio": "episode/L01_Raw.wav",
                       "fitted_audio": "episode/L01_Dialogue.wav",
                       "raw_audio_sha256": "a" * 64, "fitted_audio_sha256": "b" * 64}]}
        hashes = {"episode/L01_Raw.wav": "a" * 64, "episode/L01_Dialogue.wav": "b" * 64}
        return project, cues, defaults, generation, hashes

    def test_correct_male_voice_and_real_source_hashes_pass(self):
        p, c, d, g, hashes = self.fixture()
        report = verify_peter_voice(p, c, d, g, hashes.__getitem__)
        self.assertTrue(report["all_voice_checks_passed"])
        self.assertEqual(report["employee_line_count"], 1)
        self.assertTrue(report["actual_generation_lines"][0]["audio_provenance"]["raw"]["actual_hash_matches"])

    def test_one_kore_employee_line_fails_even_with_charon_global_policy(self):
        p, c, d, g, hashes = self.fixture()
        c["lines"][0]["voice"] = "Kore"
        report = verify_peter_voice(p, c, d, g, hashes.__getitem__)
        self.assertFalse(report["all_voice_checks_passed"])
        self.assertTrue(any("L01" in error for error in report["errors"]))

    def test_wrong_project_voice_and_unlocked_policy_fail(self):
        p, c, d, g, hashes = self.fixture()
        p["peter_voice"] = "Kore"
        d["tts_character_voices"]["Peter"]["locked"] = False
        report = verify_peter_voice(p, c, d, g, hashes.__getitem__)
        self.assertFalse(report["all_voice_checks_passed"])
        self.assertTrue(any("project" in error for error in report["errors"]))
        self.assertTrue(any("locked" in error for error in report["errors"]))

    def test_tampered_raw_audio_rejected_despite_valid_voice_labels(self):
        p, c, d, g, hashes = self.fixture()
        hashes["episode/L01_Raw.wav"] = "c" * 64
        report = verify_peter_voice(p, c, d, g, hashes.__getitem__)
        self.assertFalse(report["all_voice_checks_passed"])
        self.assertTrue(any("raw audio hash" in error for error in report["errors"]))

    def test_versioned_generation_schema_with_separate_hash_evidence_passes(self):
        p, c, d, g, hashes = self.fixture()
        g["speech_audio_evidence"] = deepcopy(g["lines"])
        g["lines"] = [{"id": "L01", "speaker": "employee", "voice": "Charon"}]
        report = verify_peter_voice(p, c, d, g, hashes.__getitem__)
        self.assertTrue(report["all_voice_checks_passed"])

    def test_catalog_gender_requires_actual_verification(self):
        p, c, d, g, hashes = self.fixture()
        c["peter_voice_catalog_evidence"]["verified_live_catalog"] = False
        report = verify_peter_voice(p, c, d, g, hashes.__getitem__)
        self.assertFalse(report["all_voice_checks_passed"])
        self.assertFalse(report["live_catalog_matches_locked_male_voice"])

    def test_previous_text_permits_only_declared_line_ending_normalization(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "old_cues.json"
            original = b'{"voice":"Charon"}\n'
            path.write_bytes(b'{"voice":"Charon"}\r\n')
            self.assertTrue(committed_source_matches("old_cues.json", original, path))
            path.write_bytes(b'{"voice":"Kore"}\r\n')
            self.assertFalse(committed_source_matches("old_cues.json", original, path))

    def test_previous_binary_audio_requires_exact_bytes(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "old_audio.wav"
            path.write_bytes(b"RIFF\r\nDATA")
            self.assertFalse(committed_source_matches("old_audio.wav", b"RIFF\nDATA", path))


if __name__ == "__main__":
    unittest.main()
