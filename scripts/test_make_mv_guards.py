"""不需 ffmpeg 或影音素材的 make_mv.py 微電影防呆測試。"""
import importlib.util
import io
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch


MODULE_PATH = Path(__file__).with_name("make_mv.py")
SPEC = importlib.util.spec_from_file_location("make_mv", MODULE_PATH)
make_mv = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(make_mv)


class MixTimelineGuardTests(unittest.TestCase):
    def test_valid_timeline_returns_song_window(self):
        cues = {
            "vo": [{"start": 1.0, "dur": 2.0}],
            "sfx": [{"start": 8.0, "dur": 1.5}],
        }
        self.assertEqual(make_mv.validate_mix_timeline(cues, 12.0, 1.0, 1.0), 10.0)

    def test_rejects_negative_or_songless_timeline(self):
        with redirect_stdout(io.StringIO()):
            with patch("sys.exit", side_effect=SystemExit) as exit_mock:
                with self.assertRaises(SystemExit):
                    make_mv.validate_mix_timeline({}, 10.0, -1.0, 11.0)
        exit_mock.assert_called_once_with(1)

    def test_rejects_song_window_under_half_second(self):
        with redirect_stdout(io.StringIO()):
            with self.assertRaises(SystemExit):
                make_mv.validate_mix_timeline({}, 10.0, 9.51, 0.0)

    def test_rejects_cue_past_end_of_movie(self):
        cues = {"vo": [{"start": 9.0, "dur": 2.0}]}
        with redirect_stdout(io.StringIO()):
            with self.assertRaises(SystemExit):
                make_mv.validate_mix_timeline(cues, 10.0, 0.0, 0.0)

    def test_rejects_negative_voiceover_or_sfx_start(self):
        cues = {
            "vo": [{"start": -0.01, "dur": 0.5}],
            "sfx": [{"start": -0.01, "dur": 0.2}],
        }
        with redirect_stdout(io.StringIO()):
            with self.assertRaises(SystemExit):
                make_mv.validate_mix_timeline(cues, 10.0, 0.0, 0.0)

    def test_rejects_sfx_past_end_of_movie(self):
        cues = {"sfx": [{"start": 9.9, "dur": 0.2}]}
        with redirect_stdout(io.StringIO()):
            with self.assertRaises(SystemExit):
                make_mv.validate_mix_timeline(cues, 10.0, 0.0, 0.0)


class DialogSubtitleGuardTests(unittest.TestCase):
    def test_accepts_dialog_within_voiceover(self):
        make_mv.validate_dialog_srt([(1.05, 2.95, "台詞")], [(1.0, 3.0)])

    def test_rejects_dialog_outside_voiceover(self):
        with redirect_stdout(io.StringIO()):
            with self.assertRaises(SystemExit):
                make_mv.validate_dialog_srt([(0.5, 2.0, "台詞")], [(1.0, 3.0)])

    def test_rejects_dialog_without_voiceover(self):
        with redirect_stdout(io.StringIO()):
            with self.assertRaises(SystemExit):
                make_mv.validate_dialog_srt([(1.0, 2.0, "台詞")], [])

    def test_accepts_multiple_dialogs_in_separate_voiceovers(self):
        entries = [(1.1, 1.8, "第一句"), (4.1, 4.8, "第二句")]
        make_mv.validate_dialog_srt(entries, [(1.0, 2.0), (4.0, 5.0)])


class ShortCutFadeTests(unittest.TestCase):
    def test_fadeout_never_starts_before_zero(self):
        filter_text = make_mv.build_fade_filter("fade", "fadeout", 1.0, 24)
        self.assertIn("fade=t=out:st=0.0:d=1.0", filter_text)
        self.assertNotIn("st=-", filter_text)

    def test_whiteflash_never_starts_before_zero(self):
        filter_text = make_mv.build_fade_filter("whiteflash", "whiteflash", 0.2, 24)
        self.assertIn("fade=t=out:st=0.0:d=0.2:color=white", filter_text)
        self.assertNotIn("st=-", filter_text)


if __name__ == "__main__":
    unittest.main()
