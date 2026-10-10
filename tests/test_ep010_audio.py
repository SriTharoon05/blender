"""EP010 speech identity and late-episode timing regressions; offline/stdlib."""
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import ep010_audio
from speech_api import SpeechAPIError


class EP010SpeechTests(unittest.TestCase):
    def defaults(self):
        return json.loads((ROOT / "config/production_defaults.json").read_text())

    def test_inner_thought_is_peter_not_a_second_voice(self):
        lines, identity = ep010_audio.configured_lines(self.defaults())
        peter = [line for line in lines if line["speaker"] in ("peter", "inner")]
        self.assertEqual(len(peter), 9)
        self.assertEqual({line["voice"] for line in peter}, {identity["voice"]})
        self.assertEqual({line["character"] for line in peter}, {"Peter"})
        self.assertEqual(identity["voice"], "Charon")

    def test_voice_lock_cannot_be_relaxed_for_inner_lines(self):
        defaults = self.defaults()
        defaults["tts_character_voices"]["Peter"]["allow_voice_fallback"] = True
        with self.assertRaises(SpeechAPIError):
            ep010_audio.configured_lines(defaults)

    def test_button_timestamps_extend_beyond_the_old_18_second_episode(self):
        response = {"words": [{"word": "Worth", "start": .02, "end": .35},
                              {"word": "it.", "start": .35, "end": .6}]}
        words = ep010_audio.authoritative_words("Worth it.", response, 20, .65)
        self.assertGreater(words[0]["start_frame"], 432)
        self.assertLessEqual(words[-1]["end_frame"], 516)
        self.assertEqual(ep010_audio.FRAME_END, 528)
        self.assertLessEqual(ep010_audio.LINES[-1]["end"], 21.5)

    def test_wrong_actual_words_do_not_get_fabricated_captions(self):
        response = {"words": [{"word": "Not", "start": .02, "end": .35},
                              {"word": "it.", "start": .35, "end": .6}]}
        with self.assertRaises(ValueError):
            ep010_audio.authoritative_words("Worth it.", response, 20, .65)


if __name__ == "__main__":
    unittest.main()
