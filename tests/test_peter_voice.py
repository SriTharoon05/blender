"""Permanent Peter voice and cache isolation regressions; no network/Blender."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import ep009_audio
from speech_api import SpeechAPIError


class PeterVoiceTests(unittest.TestCase):
    def identity(self, **changes):
        return {"provider": "Gemini", "voice": "Charon", "gender": "male", "locked": True,
                "allow_voice_fallback": False, **changes}

    def configured(self, **changes):
        return ep009_audio.configured_lines({"tts_character_voices": {"Peter": self.identity(**changes)}})

    def test_peter_uses_one_configured_male_voice_with_separate_puck_host(self):
        lines, identity = self.configured()
        self.assertEqual(identity["voice"], "Charon")
        self.assertEqual({row["voice"] for row in lines if row["speaker"] == "employee"}, {"Charon"})
        self.assertEqual({row["voice"] for row in lines if row["speaker"] == "host"}, {"Puck"})

    def test_female_and_unlocked_identity_are_rejected(self):
        for changes in ({"voice": "Kore", "gender": "female"}, {"locked": False}):
            with self.subTest(changes=changes), self.assertRaises(SpeechAPIError):
                self.configured(**changes)

    def test_voice_fallback_and_wrong_provider_are_rejected(self):
        for changes in ({"allow_voice_fallback": True}, {"provider": "Other"},
                        {"allow_voice_fallback": None}, {"provider": None}):
            with self.subTest(changes=changes), self.assertRaises(SpeechAPIError):
                self.configured(**changes)

    def test_missing_configured_voice_is_rejected(self):
        with self.assertRaises(SpeechAPIError):
            ep009_audio.configured_lines({})

    def test_every_speech_identity_dimension_invalidates_cache(self):
        spec = self.configured()[0][0]
        model = "gemini-3.8-flash-tts"
        original = ep009_audio.speech_signature(spec, model)
        for changes in ({"voice": "Kore"}, {"text": "Different spoken words."},
                        {"style": "Different delivery and pacing."}):
            with self.subTest(changes=changes):
                self.assertNotEqual(original, ep009_audio.speech_signature({**spec, **changes}, model))
        self.assertNotEqual(original, ep009_audio.speech_signature(spec, "different-model"))

    def test_employee_never_imports_old_female_cache(self):
        spec = self.configured()[0][0]
        with tempfile.TemporaryDirectory() as directory:
            self.assertFalse(ep009_audio.reuse_host_cache(Path(directory), spec, "gemini-3.8-flash-tts"))
            self.assertEqual(list(Path(directory).iterdir()), [])

    def make_host_fixture(self, episode, *, voice="Puck", changed_bytes=False):
        (episode / "audio").mkdir()
        (episode / "edit").mkdir()
        target = episode / "audio/v002"
        target.mkdir()
        spec = self.configured()[0][1]
        model = "gemini-3.8-flash-tts"
        (episode / "edit/speech_cues_v001.json").write_text(json.dumps({
            "tts_model": model, "lines": [{**spec, "voice": voice}]}))
        raw = b"unchanged-host-audio"
        (episode / "audio/L02_Gemini_Raw.wav").write_bytes(raw if not changed_bytes else b"damaged")
        (episode / "audio/L02_Dialogue.wav").write_bytes(b"unchanged-fitted-audio")
        (episode / "audio/L02_Groq_Whisper.json").write_text('{"words": []}')
        (episode / "audio/L02_generation.json").write_text(json.dumps({
            "tts_model": model, "voice": voice, "raw_sha256": hashlib.sha256(raw).hexdigest()}))
        return spec, model, target

    def test_unchanged_host_cache_is_copied_without_mutating_original(self):
        with tempfile.TemporaryDirectory() as directory:
            episode = Path(directory)
            spec, model, target = self.make_host_fixture(episode)
            original = (episode / "audio/L02_Gemini_Raw.wav").read_bytes()
            with patch.object(ep009_audio, "EPISODE", episode):
                self.assertTrue(ep009_audio.reuse_host_cache(target, spec, model))
            self.assertEqual((episode / "audio/L02_Gemini_Raw.wav").read_bytes(), original)
            self.assertEqual((target / "L02_Gemini_Raw.wav").read_bytes(), original)
            metadata = json.loads((target / "L02_generation.json").read_text())
            self.assertEqual(metadata["signature"], ep009_audio.speech_signature(spec, model))
            self.assertEqual(metadata["reused_from_audio_version"], "v001")

    def test_changed_voice_or_damaged_host_cache_is_not_reused(self):
        for changes in ({"voice": "Kore"}, {"changed_bytes": True}):
            with self.subTest(changes=changes), tempfile.TemporaryDirectory() as directory:
                episode = Path(directory)
                spec, model, target = self.make_host_fixture(episode, **changes)
                with patch.object(ep009_audio, "EPISODE", episode):
                    self.assertFalse(ep009_audio.reuse_host_cache(target, spec, model))
                self.assertEqual(list(target.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
