#!/usr/bin/env python3
"""
vertex_imagen.py 的生圖流程測試。

預設離線：用 mock 取代 Gemini client，驗證整條產圖流程（張數迴圈、檔名、存檔、
錯誤處理），不連網、不花錢、不需要憑證。

  python scripts/test_vertex_imagen.py            # 離線 mock 測試
  python scripts/test_vertex_imagen.py --live     # 真的生 1 張 1K 圖（會計費）

--live 只生 1 張、固定 1K，避免測試時意外燒錢。
"""

import argparse
import base64
import io
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import vertex_imagen as vi  # noqa: E402

passed = failed = 0


def check(label: str, got, want) -> None:
    global passed, failed
    if got == want:
        passed += 1
        print(f"  [v] {label}")
    else:
        failed += 1
        print(f"  [X] {label}\n      得到 {got!r}，預期 {want!r}")


# ── mock：假的 Gemini 回應 ────────────────────────────────

class FakeImage:
    """模擬 SDK 回傳的圖片物件，save() 寫出一個最小的 PNG。"""

    PNG_1PX = base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
    )

    def save(self, path):
        Path(path).write_bytes(self.PNG_1PX)


class FakePart:
    def __init__(self, image):
        self._image = image

    def as_image(self):
        return self._image


class FakeResponse:
    def __init__(self, image):
        self.parts = [FakePart(image)]


class FakeModels:
    def __init__(self, image, recorder):
        self._image = image
        self._recorder = recorder

    def generate_content(self, model, contents, config):
        self._recorder.append({"model": model, "prompt": contents})
        return FakeResponse(self._image)


class FakeClient:
    def __init__(self, image, recorder):
        self.models = FakeModels(image, recorder)


def install_mock(monkey_calls, image=None):
    """把 build_client / resolve_config 換掉，讓 render() 完全離線。"""
    vi.build_client = lambda project, location: FakeClient(
        image if image is not None else FakeImage(), monkey_calls
    )
    vi.resolve_config = lambda *a, **k: {
        "key_path": "fake.json",
        "project": "fake-project",
        "location": vi.DEFAULT_LOCATION,
        "model": k.get("model") or (a[3] if len(a) > 3 and a[3] else vi.DEFAULT_MODEL),
    }
    vi.build_image_config = lambda aspect, size: {"aspect": aspect, "size": size}
    vi.build_generate_config = lambda image_config: {"image_config": image_config}


def run_offline_tests() -> None:
    calls: list[dict] = []
    install_mock(calls)
    tmp = Path(tempfile.mkdtemp())

    print("1. render() 依目標路徑產圖")
    targets = [tmp / "a.png", tmp / "b.png"]
    saved = vi.render("a cat", targets, "16:9")
    check("回傳張數正確", len(saved), 2)
    check("檔案真的寫出來", all(p.exists() for p in targets), True)
    check("呼叫次數等於張數", len(calls), 2)
    check("用預設模型", calls[0]["model"], vi.DEFAULT_MODEL)
    check("prompt 有傳進去", calls[0]["prompt"], "a cat")

    print("2. generate_to_dir() 的時間戳命名")
    calls.clear()
    out = tmp / "scenes"
    saved = vi.generate_to_dir("a dog", out, prefix="scene_01", count=3)
    check("張數正確", len(saved), 3)
    check("全部落在指定資料夾", all(p.parent == out for p in saved), True)
    check("檔名有序號 _01", saved[0].name.endswith("_01.png"), True)
    check("檔名有前綴", saved[0].name.startswith("scene_01_"), True)

    print("3. generate_image() 維持原本 CLI 行為")
    calls.clear()
    single = vi.generate_image("a bird", str(tmp / "cover.png"))
    check("單張就用 --output 的檔名", Path(single[0]).name, "cover.png")
    multi = vi.generate_image("a bird", str(tmp / "cover.png"), sample_count=2)
    check("多張加序號", [Path(p).name for p in multi], ["cover_1.png", "cover_2.png"])

    print("4. 不支援的長寬比要擋下來")
    try:
        vi.render("x", [tmp / "z.png"], "21:9")
        check("有擋下 21:9", False, True)
    except SystemExit as e:
        check("有擋下 21:9", "不支援的長寬比" in str(e), True)

    print("5. 回應沒夾帶圖片時要報錯")
    calls.clear()
    vi.build_client = lambda project, location: FakeClient(None, calls)
    try:
        vi.render("x", [tmp / "none.png"])
        check("有報錯", False, True)
    except SystemExit as e:
        check("有報錯", "沒有夾帶圖片" in str(e), True)


def run_live_test() -> None:
    """真的呼叫 API：只生 1 張、固定 1K。"""
    out_dir = Path(__file__).resolve().parent.parent / "outputs" / "vertex_test"
    print(f"\n[live] 真實生圖測試（1 張、1K）→ {out_dir}")
    paths = vi.generate_to_dir(
        prompt="a simple red apple on a white table, product photo",
        out_dir=out_dir,
        prefix="smoke_test",
        count=1,
        aspect_ratio="1:1",
        image_size=vi.DEFAULT_IMAGE_SIZE,
    )
    size_kb = paths[0].stat().st_size / 1024
    check("有產出檔案", paths[0].exists(), True)
    check("檔案看起來是張圖（>10KB）", size_kb > 10, True)
    print(f"  產出：{paths[0]}（{size_kb:.0f} KB）")


if __name__ == "__main__":
    if sys.platform == "win32":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(description="vertex_imagen 生圖流程測試")
    parser.add_argument("--live", action="store_true",
                        help="真的呼叫 API 生 1 張 1K 圖（會計費），不加就是離線 mock")
    args = parser.parse_args()

    if args.live:
        run_live_test()
    else:
        run_offline_tests()

    print("─" * 48)
    print(f"通過 {passed}、失敗 {failed}")
    sys.exit(1 if failed else 0)
