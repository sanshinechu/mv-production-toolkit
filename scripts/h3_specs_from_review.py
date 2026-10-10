# -*- coding: utf-8 -*-
r"""把三方審核定案的「H3 分鏡」拆成一鏡一個 cutNN.json，檢查過才放進 colab_mv（影片分流 🅰，見 docs/影片分流策略.md）。

用法：
  python scripts/h3_specs_from_review.py "<H3 分鏡那份共修的資料夾名或完整路徑>" --mv <MV名> --storyboard outputs/<MV名>/storyboard_vN.md
  加 --dry-run 只檢查不寫檔。

流程位置：影片提示詞「無意見」→ Claude 寫 H3 分鏡初稿 → cowrite --flow mv-h3 --from … --draft …（三方審核）
→「無意見」→ **本程式** → 列清單給老師 → 老師說「直接生影片」→ h3_batch.py。

檢查（任何一項失敗就不寫檔、exit 1，回 cowrite 再審）：
- 「H3 分鏡」階段必須已定案（approved）
- 每個 ### cutNN 後面的 ```json 區塊都是合法 JSON
- 欄位規則（照 15_ai共筆工作流/flows/specs/H3分鏡.md）：size 1344×768、duration ≤ 12、draft true、
  upscale rtx|flashvsr、music N/A、沒有 audio／dialogue、style 全片逐字相同
- 對分鏡表：cut 編號一致、duration = 分鏡秒數 + 0.5
- H3 官方六段格式 lint（colab_mv/tools/h3_shot.py 的 build_prompt＋lint）0 錯誤
"""
import argparse
import importlib.util
import json
import re
import sys
from pathlib import Path

sys.dont_write_bytecode = True   # 會從雲端 colab_mv/tools 載入 h3_shot.py，別在雲端留 __pycache__
HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
import storyboard_md  # noqa: E402
from collect_videos import colab_dir  # noqa: E402

RECORDS = ROOT.parents[1] / "工作筆記本" / "AI共修紀錄"   # <雲端硬碟>/Ai Code/01_MV製作 → <雲端硬碟>/工作筆記本（不寫死碟號）
STAGE = "H3 分鏡"
BLOCK = re.compile(r"^#{2,4}\s*(cut\d+)\b[^\n]*\n+```json\s*\n(.*?)\n```", re.M | re.S)


def load_h3(session):
    p = Path(session)
    if not p.is_absolute():
        p = RECORDS / p
    f = p / "session.json" if p.is_dir() else p
    s = json.loads(f.read_text(encoding="utf-8"))
    st = next((x for x in s["stages"] if x["name"] == STAGE), None)
    if not st:
        sys.exit(f"{f} 沒有「{STAGE}」階段（是 --flow mv-h3 開的那份嗎？）")
    if not st.get("approved"):
        sys.exit(f"「{STAGE}」還沒定案——三方審核「無意見」、主持人 ok 之後才能拆")
    return st["draft"]


def load_lint(tools):
    spec = importlib.util.spec_from_file_location("h3_shot", tools / "h3_shot.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("session", help="H3 分鏡那份共修的資料夾名（在 工作筆記本/AI共修紀錄/ 底下）或完整路徑")
    ap.add_argument("--mv", required=True, help="MV 名稱＝colab_mv/inputs/ 底下的資料夾名")
    ap.add_argument("--storyboard", required=True, help="mv-11 的 storyboard_vN.md")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    text = load_h3(a.session)
    sb = {p.split("_")[0]: d for p, _a, _i, _o, d in storyboard_md.load(a.storyboard)}
    colab = colab_dir()
    h3 = load_lint(colab / "tools")
    errs, specs, styles = [], {}, set()

    blocks = BLOCK.findall(text)
    if not blocks:
        sys.exit("定案稿裡找不到任何「### cutNN ＋ ```json」區塊")
    for cut, body in blocks:
        try:
            j = json.loads(body)
        except json.JSONDecodeError as e:
            errs.append(f"{cut}：JSON 格式錯（{e.msg}，第 {e.lineno} 行）")
            continue
        e = []
        if j.get("size") != [1344, 768]:
            e.append(f"size 是 {j.get('size')}，要 [1344, 768]")
        dur = j.get("duration")
        if not isinstance(dur, (int, float)) or dur > 12:
            e.append(f"duration {dur} 要是數字且 ≤ 12")
        elif cut in sb and abs(dur - (sb[cut] + 0.5)) > 0.05:
            e.append(f"duration {dur} ≠ 分鏡 {sb[cut]} + 0.5")
        if j.get("draft") is not True:
            e.append("draft 要是 true")
        if j.get("upscale") not in ("rtx", "flashvsr"):
            e.append(f"upscale 是 {j.get('upscale')!r}，要 rtx 或 flashvsr")
        if j.get("music") != "N/A":
            e.append("music 要是 \"N/A\"")
        for bad in ("audio", "dialogue"):
            if bad in j or any(bad in s for s in j.get("shots", [])):
                e.append(f"不能有 {bad}（MV 沒台詞，聲音組裝時換成歌）")
        if not j.get("first_frame"):
            e.append("缺 first_frame")
        styles.add(j.get("style"))
        try:
            E, W = h3.lint(h3.build_prompt(j), dur)
            e += [f"官方格式：{x}" for x in E]
        except Exception as ex:  # build_prompt 遇到缺欄位會直接拋例外
            e.append(f"組不出 H3 提示詞：{ex!r}")
        errs += [f"{cut}：{x}" for x in e]
        specs[cut] = j
    if len(styles) > 1:
        errs.append(f"style 全片要逐字相同，現在有 {len(styles)} 種")
    missing, extra = sorted(set(sb) - set(specs)), sorted(set(specs) - set(sb))
    if missing:
        errs.append(f"分鏡表有、H3 分鏡沒有：{missing}")
    if extra:
        errs.append(f"H3 分鏡有、分鏡表沒有：{extra}")

    if errs:
        print("❌ 沒通過，不寫檔；把下面的問題當主持人意見丟回 cowrite --resume 再審：")
        for x in errs:
            print("  -", x)
        sys.exit(1)

    dst = colab / "inputs" / a.mv
    print(f"✅ {len(specs)} 鏡全部通過檢查 → {dst}")
    total = sum(j["duration"] for j in specs.values())
    print(f"\n| cut | duration | 首幀 | 放大 | 首幀檔在嗎 |\n|---|---|---|---|---|")
    for cut, j in sorted(specs.items()):
        ok = (dst / j["first_frame"]).exists()
        print(f"| {cut} | {j['duration']} | {j['first_frame']} | {j['upscale']} | {'✓' if ok else '✗ 待放'} |")
    gen_min = total * 25 / 60   # 2026-10-10 實測：5 秒 123 秒 ≈ 每秒影片 25 秒（DMAD 4 步，A100）
    print(f"\n合計 {total:.1f} 秒影片；H3 生成估 {gen_min:.0f} 分鐘（不含 AI 放大，尚未實測）"
          f"；約 {gen_min / 60 * 6.77:.1f} 個運算單元起跳。老師說「直接生影片」才跑 h3_batch.py。")
    if a.dry_run:
        print("（--dry-run：沒寫檔）")
        return
    dst.mkdir(parents=True, exist_ok=True)
    for cut, j in specs.items():
        (dst / f"{cut}.json").write_text(json.dumps(j, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"已寫入 {len(specs)} 個 cutNN.json")


if __name__ == "__main__":
    main()
