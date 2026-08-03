"""
vertex_imagen.py 的設定解析測試（不生圖、不連網、不需要 google-genai）。

跑法：python scripts/test_vertex_imagen_config.py
只驗參數與環境變數怎麼被解析，所以在任何機器上都跑得動。
"""

import io
import os
import sys
import contextlib
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import vertex_imagen as vi  # noqa: E402

FAKE_KEY = Path(tempfile.gettempdir()) / "fake-sa-key.json"
FAKE_KEY.write_text("{}", encoding="utf-8")

VARS = [
    "GOOGLE_APPLICATION_CREDENTIALS",
    "GOOGLE_CLOUD_PROJECT",
    "GOOGLE_CLOUD_LOCATION",
    "VERTEX_IMAGE_MODEL",
    "VERTEX_IMAGEN_MODEL",
]

passed = failed = 0


def check(label: str, got, want) -> None:
    global passed, failed
    if got == want:
        passed += 1
        print(f"  [v] {label}")
    else:
        failed += 1
        print(f"  [X] {label}\n      得到 {got!r}，預期 {want!r}")


@contextlib.contextmanager
def env(**kwargs):
    """把相關環境變數清乾淨，只留這次要測的，避免讀到本機真的設定。"""
    saved = {k: os.environ.pop(k, None) for k in VARS}
    home = os.environ.get("USERPROFILE"), os.environ.get("HOME")
    empty = tempfile.mkdtemp()
    os.environ["USERPROFILE"] = os.environ["HOME"] = empty  # 讓 ~/.vertexai.env 讀不到
    os.environ.update({k: v for k, v in kwargs.items() if v is not None})
    try:
        yield
    finally:
        for k in VARS:
            os.environ.pop(k, None)
        for k, v in saved.items():
            if v is not None:
                os.environ[k] = v
        if home[0]:
            os.environ["USERPROFILE"] = home[0]
        if home[1]:
            os.environ["HOME"] = home[1]


def capture(fn):
    """跑一個會寫 stderr / 可能 sys.exit 的函式，回傳 (結果, stderr, exit 碼)。"""
    err = io.StringIO()
    code = None
    result = None
    with contextlib.redirect_stderr(err):
        try:
            result = fn()
        except SystemExit as e:
            code = e.code
    return result, err.getvalue(), code


print("1. 預設值（只給必填）")
with env(GOOGLE_APPLICATION_CREDENTIALS=str(FAKE_KEY), GOOGLE_CLOUD_PROJECT="proj-a"):
    cfg, err, _ = capture(vi.resolve_config)
    check("區域預設 global", cfg["location"], "global")
    check("模型預設 gemini-3.1-flash-image", cfg["model"], "gemini-3.1-flash-image")
    check("專案讀得到", cfg["project"], "proj-a")
    check("預設值不吐警告", err.strip(), "")

print("2. 命令列參數蓋過環境變數")
with env(GOOGLE_APPLICATION_CREDENTIALS=str(FAKE_KEY), GOOGLE_CLOUD_PROJECT="proj-env"):
    cfg, _, _ = capture(lambda: vi.resolve_config(project="proj-cli"))
    check("--project 優先", cfg["project"], "proj-cli")

print("3. 舊的 VERTEX_IMAGEN_MODEL 仍相容但會提醒")
with env(
    GOOGLE_APPLICATION_CREDENTIALS=str(FAKE_KEY),
    GOOGLE_CLOUD_PROJECT="proj-a",
    VERTEX_IMAGEN_MODEL="some-old-model",
):
    cfg, err, _ = capture(vi.resolve_config)
    check("舊名稱還是讀得到", cfg["model"], "some-old-model")
    check("有印棄用提醒", "已棄用" in err, True)

print("4. 新的 VERTEX_IMAGE_MODEL 優先於舊名稱")
with env(
    GOOGLE_APPLICATION_CREDENTIALS=str(FAKE_KEY),
    GOOGLE_CLOUD_PROJECT="proj-a",
    VERTEX_IMAGE_MODEL="new-model",
    VERTEX_IMAGEN_MODEL="old-model",
):
    cfg, _, _ = capture(vi.resolve_config)
    check("新名稱勝出", cfg["model"], "new-model")

print("5. 非 global 區域要警告（但不自動改）")
with env(
    GOOGLE_APPLICATION_CREDENTIALS=str(FAKE_KEY),
    GOOGLE_CLOUD_PROJECT="proj-a",
    GOOGLE_CLOUD_LOCATION="us-central1",
):
    cfg, err, _ = capture(vi.resolve_config)
    check("區域保持使用者指定的值", cfg["location"], "us-central1")
    check("有印區域警告", "只開在" in err, True)

print("6. 已停用的 Imagen 模型要警告")
with env(
    GOOGLE_APPLICATION_CREDENTIALS=str(FAKE_KEY),
    GOOGLE_CLOUD_PROJECT="proj-a",
    VERTEX_IMAGE_MODEL="imagen-3.0-generate-001",
):
    _, err, _ = capture(vi.resolve_config)
    check("有印停用警告", "已停用" in err, True)

print("7. 缺設定要中止並給指引")
with env():
    _, _, code = capture(vi.resolve_config)
    check("有 sys.exit", code is not None, True)
    check("錯誤訊息可讀", "缺少設定" in str(code), True)

print("8. 金鑰檔不存在要中止")
with env(GOOGLE_APPLICATION_CREDENTIALS="/definitely/not/here.json", GOOGLE_CLOUD_PROJECT="p"):
    _, _, code = capture(vi.resolve_config)
    check("有點出找不到金鑰", "找不到服務帳戶金鑰" in str(code), True)

print("9. 輸出檔名規則")
check("單張就用 --output", [p.name for p in vi.output_paths("out/cover.png", 1)], ["cover.png"])
check(
    "多張加序號",
    [p.name for p in vi.output_paths("out/cover.png", 3)],
    ["cover_1.png", "cover_2.png", "cover_3.png"],
)

print("─" * 48)
print(f"通過 {passed}、失敗 {failed}")
sys.exit(1 if failed else 0)
