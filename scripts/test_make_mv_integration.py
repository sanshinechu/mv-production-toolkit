"""以暫存的合成素材驗證 make_mv.py 微電影整合流程；不使用正式影音素材。"""
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
MAKE_MV = ROOT / "scripts" / "make_mv.py"


def run(command, cwd=None):
    return subprocess.run(
        command,
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


class MakeMvIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ffmpeg = shutil.which("ffmpeg")
        cls.ffprobe = shutil.which("ffprobe")
        if not cls.ffmpeg or not cls.ffprobe:
            raise unittest.SkipTest("此機器沒有 ffmpeg／ffprobe，略過整合測試")

    def make_color_clip(self, path, color):
        result = run([
            self.ffmpeg, "-y", "-f", "lavfi", "-i",
            f"color=c={color}:s=1280x720:r=24", "-t", "1.0", "-an",
            "-c:v", "libx264", "-pix_fmt", "yuv420p", str(path),
        ])
        self.assertEqual(result.returncode, 0, result.stderr[-1000:])

    def make_audio(self, path, duration, frequency=440):
        result = run([
            self.ffmpeg, "-y", "-f", "lavfi", "-i",
            f"sine=frequency={frequency}:sample_rate=48000", "-t", str(duration),
            "-ar", "48000", "-ac", "2", str(path),
        ])
        self.assertEqual(result.returncode, 0, result.stderr[-1000:])

    def test_valid_microfilm_pipeline_with_subtitles(self):
        # 此專案的受限執行環境不可寫系統 TEMP；測試資料仍會在結束時自動清除。
        with tempfile.TemporaryDirectory(prefix="make_mv_integration_", dir=ROOT) as temp:
            work = Path(temp)
            videos = work / "videos-raw"
            audio = work / "audio"
            videos.mkdir()
            audio.mkdir()
            self.make_color_clip(videos / "cut01_test.mp4", "navy")
            self.make_color_clip(videos / "cut02_test.mp4", "teal")
            self.make_audio(work / "music.wav", 2.0, 330)
            self.make_audio(audio / "vo.wav", 0.5, 660)
            self.make_audio(audio / "sfx.wav", 0.2, 220)

            (work / "storyboard.md").write_text(
                "| Cut | 時間 | 秒數 | 歌詞對應 | 畫面 | 動畫 | 進/出轉場 |\n"
                "| --- | --- | --- | --- | --- | --- | --- |\n"
                "| Cut 01 test | 0:00–0:01 | 1.0 | 測試 | 藍 | zoom_in | fadein/fade |\n"
                "| Cut 02 test | 0:01–0:02 | 1.0 | 測試 | 綠 | zoom_out | fade/fadeout |\n",
                encoding="utf-8",
            )
            (work / "lyrics.srt").write_text(
                "1\n00:00:00,550 --> 00:00:00,900\n重疊歌詞\n\n"
                "2\n00:00:01,200 --> 00:00:01,500\n保留歌詞\n",
                encoding="utf-8",
            )
            (work / "dialog.srt").write_text(
                "1\n00:00:00,550 --> 00:00:00,950\n測試對白\n",
                encoding="utf-8",
            )
            (work / "audio_cues.json").write_text(json.dumps({
                "vo": [{"file": "audio/vo.wav", "start": 0.5, "text": "測試對白"}],
                "sfx": [{"file": "audio/sfx.wav", "start": 1.4, "gain_db": -18}],
            }, ensure_ascii=False), encoding="utf-8")

            output = work / "microfilm.mp4"
            result = run([
                sys.executable, str(MAKE_MV),
                "--videos", str(videos),
                "--storyboard", str(work / "storyboard.md"),
                "--music", str(work / "music.wav"),
                "--audio-cues", str(work / "audio_cues.json"),
                "--sub-lyrics", str(work / "lyrics.srt"),
                "--sub-dialog", str(work / "dialog.srt"),
                "--out", str(output),
            ], cwd=ROOT)
            self.assertEqual(result.returncode, 0, result.stdout + "\n" + result.stderr)
            self.assertTrue(output.is_file())
            self.assertIn("與口白重疊拿掉 1 條", result.stdout)

            probe = run([
                self.ffprobe, "-v", "error", "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1", str(output),
            ])
            self.assertEqual(probe.returncode, 0, probe.stderr)
            self.assertAlmostEqual(float(probe.stdout.strip()), 2.0, delta=0.15)


if __name__ == "__main__":
    unittest.main()
