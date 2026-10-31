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
  upscale 收 flashvsr 或 lanczos（rtx 在 A100 上會 code -14 失敗，直接退回）、music N/A、style 全片逐字相同
- 非唱歌鏡不能有 audio／dialogue；唱歌鏡（2026-10-31）要符合規格〈唱歌鏡〉：audio.fixed.file＝cutNN_guide.wav、
  單人、一句 dialogue 跟分鏡表歌詞一字不差、沒有 last_frame、soundscape 是規定那句、歌詞欄是真的在唱
- 對分鏡表：cut 編號一致、duration = 分鏡秒數 + 0.5
- H3 官方六段格式 lint（colab_mv/tools/h3_shot.py 的 build_prompt＋lint）0 錯誤

唱歌鏡另外會寫進 cutNN.json（不用寫稿的人填）：
- audio.fixed.song_start：這鏡在**歌曲**裡從第幾秒開始＝分鏡表累加秒數 − 片頭前導秒數（--prologue，
  沒給就讀分鏡表旁的 audio_cues.json 的 prologue_sec，再沒有就 0）。h3_batch.py 靠它從原曲切出人聲 guide。
- constraints 補一句「在唱、不是在講話」（沒有這句時，模型會把歌詞當台詞念的口型）。
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
# A100 上能跑的放大方式（rtx 會 NvVFX_Load failed code -14）。
# flashvsr＝AI 放大、會多畫細節；lanczos＝不改畫面但較糊，對嘴／特寫鏡要保真時選。
# 老師在「給老師看的清單」那一步逐鏡選，見 docs/影片分流策略.md 🅰 第 4、7 步。
UPSCALE_OK = ("flashvsr", "lanczos")
BLOCK = re.compile(r"^#{2,4}\s*(cut\d+)\b[^\n]*\n+```json\s*\n(.*?)\n```", re.M | re.S)
# 唱歌鏡（規格〈唱歌鏡〉）：2026-10-31〈半張車票〉cut05 實測時用的寫法
SING_SOUNDSCAPE = "Only the solo singing voice of <Audio 1>; no other sounds."
SING_CONSTRAINT = ("The singer is singing, not talking: the mouth opens and closes in time with each sung syllable "
                   "of <Audio 1>, and the lips stay closed before the first syllable.")


def lyric_key(s):
    """比對歌詞用：拿掉括號和聲、方括號標籤、空白與標點。"""
    s = re.sub(r"[（(][^）)]*[）)]|\[[^\]]*\]", "", s or "")
    return re.sub(r"[\s\W_]+", "", s)


def is_sung(lyric):
    """分鏡表歌詞欄是不是真的在唱：[Prologue 口白]、（鋼琴間奏）這類去掉後就沒東西了。"""
    return bool(lyric_key(lyric)) and not re.match(r"\s*\[[^\]]*(口白|prologue|epilogue|interlude)", lyric or "", re.I)


def find_prologue(storyboard, given):
    if given is not None:
        return given, "--prologue"
    cues = Path(storyboard).resolve().parent / "audio_cues.json"
    if cues.exists():
        v = json.loads(cues.read_text(encoding="utf-8")).get("prologue_sec")
        if v is not None:
            return float(v), str(cues.name)
    return 0.0, "預設（沒有片頭戲）"


def check_sing(cut, j, row):
    """唱歌鏡的規則；回傳錯誤清單。"""
    e = []
    if j.get("audio") != {"fixed": {"file": f"{cut}_guide.wav"}}:
        e.append(f"唱歌鏡的 audio 要剛好是 {{\"fixed\": {{\"file\": \"{cut}_guide.wav\"}}}}，現在是 {j.get('audio')!r}")
    if j.get("last_frame"):
        e.append("唱歌鏡不能有 last_frame（組片時首尾幀會加速，一加速嘴就對不上歌）")
    subs = j.get("subjects") or []
    if len(subs) != 1:
        e.append(f"唱歌鏡只能有一個角色，現在 subjects 有 {len(subs)} 筆")
    lines = [d for s in j.get("shots", []) for d in s.get("dialogue", [])]
    if len(lines) != 1:
        e.append(f"唱歌鏡的 dialogue 只能一筆，現在有 {len(lines)} 筆")
    else:
        d = lines[0]
        if subs and d.get("subject") != subs[0].get("key"):
            e.append(f"dialogue 的 subject {d.get('subject')!r} 不是畫面上那個角色 {subs[0].get('key')!r}")
        lyric = (row or {}).get("lyric", "")
        if not is_sung(lyric):
            e.append(f"分鏡表這鏡的歌詞欄不是在唱的歌詞（{lyric!r}），不能當唱歌鏡")
        elif lyric_key(d.get("line")) != lyric_key(lyric):
            e.append(f"dialogue 的 line {d.get('line')!r} 跟分鏡表歌詞 {lyric!r} 不一樣（括號和聲可以拿掉，其他要一字不差）")
    if j.get("soundscape") != SING_SOUNDSCAPE:
        e.append(f"唱歌鏡的 soundscape 要逐字是 {SING_SOUNDSCAPE!r}")
    if "constraints" in j:
        e.append("不要寫 constraints（唱歌句由本程式補）")
    return e


def load_h3(session):
    p = Path(session)
    if not p.is_absolute():
        p = RECORDS / p
    f = p / "session.json" if p.is_dir() else p
    if not f.is_file():
        sys.exit(f"[ERR] 找不到共修紀錄：{f}（給資料夾名就到 {RECORDS} 底下找）")
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
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser()
    ap.add_argument("session", help="H3 分鏡那份共修的資料夾名（在 工作筆記本/AI共修紀錄/ 底下）或完整路徑")
    ap.add_argument("--mv", required=True, help="MV 名稱＝colab_mv/inputs/ 底下的資料夾名")
    ap.add_argument("--storyboard", required=True, help="mv-11 的 storyboard_vN.md")
    ap.add_argument("--prologue", type=float, default=None,
                    help="片頭前導秒數（歌曲從成片第幾秒開始）；沒給就讀分鏡表旁的 audio_cues.json，再沒有就 0")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    text = load_h3(a.session)
    sb = {p.split("_")[0]: d for p, _a, _i, _o, d in storyboard_md.load_or_exit(a.storyboard)}
    tl = storyboard_md.timeline(a.storyboard)
    prologue, prologue_src = find_prologue(a.storyboard, a.prologue)
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
        if j.get("upscale") == "rtx":
            e.append("upscale 不能用 rtx：A100 上 RTX VSR 會 NvVFX_Load failed (code -14) 整鏡失敗，"
                     "改用 \"flashvsr\" 或 \"lanczos\"")
        elif j.get("upscale") not in UPSCALE_OK:
            e.append(f"upscale 是 {j.get('upscale')!r}，要 \"flashvsr\"（AI 放大，會多畫細節）"
                     "或 \"lanczos\"（不改畫面但較糊，對嘴／特寫鏡要保真時用）")
        if j.get("music") != "N/A":
            e.append("music 要是 \"N/A\"")
        sing = "audio" in j or any("dialogue" in s for s in j.get("shots", []))
        if sing:
            e += check_sing(cut, j, tl.get(cut))
            if not e and cut in tl:
                start = round(tl[cut]["start"] - prologue, 3)
                if start < 0:
                    e.append(f"算出來的歌曲起點是 {start} 秒（成片 {tl[cut]['start']} − 前導 {prologue}），這鏡在歌曲開始之前")
                j["audio"]["fixed"]["song_start"] = start
                j["constraints"] = [SING_CONSTRAINT]
        elif "dialogue" in j:
            e.append("不能有 dialogue（只有唱歌鏡可以，而且要寫在 shots 裡）")
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
    sings = {c: j for c, j in specs.items() if j.get("audio")}
    print(f"\n| cut | duration | 首幀 | 放大 | 唱歌（歌曲秒數） | 首幀檔在嗎 |\n|---|---|---|---|---|---|")
    for cut, j in sorted(specs.items()):
        ok = (dst / j["first_frame"]).exists()
        s = j["audio"]["fixed"]["song_start"] if cut in sings else None
        sing = f"✓ {s:.2f}～{s + h3.frames_for(j['duration']) / 24:.2f}" if s is not None else ""
        up = j["upscale"] + ("（要逐鏡抽格看嘴）" if cut in sings and j["upscale"] == "flashvsr" else "")
        print(f"| {cut} | {j['duration']} | {j['first_frame']} | {up} | {sing} | {'✓' if ok else '✗ 待放'} |")
    if sings:
        song = sorted(dst.glob("song.*"))
        print(f"\n唱歌鏡 {len(sings)} 鏡：歌曲起點＝成片秒數 − 前導 {prologue} 秒（{prologue_src}）。"
              f"老師在這一步勾掉的唱歌鏡要回 cowrite 改成一般鏡（加閉嘴、拿掉 audio／dialogue）再拆。")
        print("  原曲：" + (f"{song[0].name} ✓" if song else f"✗ 還沒放——把原曲複製成 {dst / 'song.mp3'}，h3_batch.py 才切得出人聲"))
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
