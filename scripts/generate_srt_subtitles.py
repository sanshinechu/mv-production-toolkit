"""南門河繪本微電影：依配音時間軸產生「短句」字幕（SRT 存檔＋ASS 燒錄用）。

2026-11-09 主機 1 改寫：原版一句台詞整句塞一格（最長 90 多字、四行、蓋掉半個畫面），
老師要求每段不要一次出現太多。現在：
- 每格最多 MAX_CHARS 字、單行，優先在標點切，切不開才硬切
- 該句的秒數依字數（＋標點停頓）比例分給各格
- 字級用 ASS 的像素單位（PlayResY=1080），不再走 SRT 的 288 換算
路徑從本檔位置往上推，不寫死碟號。
"""
import json, re, sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
AI_CODE = Path(__file__).resolve().parents[2]
AUDIO_DIR = AI_CODE / "10_科技競賽" / "115學年度" / "游智盃_南門河" / "繪本影片" / "音軌_v2"  # 11-09 旁白／阿波照定案重配
TIMELINE = AUDIO_DIR / "story_audio_timeline.json"
OUT_SRT = AUDIO_DIR / "nanmen_story_full.srt"
OUT_ASS = AUDIO_DIR / "nanmen_story_full.ass"

MAX_CHARS = 16          # 每格正文上限（不含角色標籤）
FONT_PX = 54            # 1080p 畫面上的字高
MARGIN_V = 48
END_P = "。！？；…"
MID_P = "，、：——～"
DROP_TAIL = "。，、；："   # 字幕格尾端的這些標點拿掉（！？…保留語氣）


def visible_len(s):
    return len(re.sub(r"[「」『』（）()]", "", s))


def split_pieces(text):
    """先切成「最小語塊」：在每個標點之後斷開。"""
    pieces, buf = [], ""
    i = 0
    while i < len(text):
        ch = text[i]
        buf += ch
        if ch in END_P + MID_P and not (i + 1 < len(text) and text[i + 1] in END_P + MID_P + "」』"):
            # 收尾引號跟著前面走
            pieces.append(buf); buf = ""
        elif ch in "」』" and buf and len(buf) > 1 and buf[-2] in END_P:
            pieces.append(buf); buf = ""
        i += 1
    if buf:
        pieces.append(buf)
    return [p for p in pieces if p.strip()]


def hard_split(p):
    """太長的語塊在「詞的邊界」上平均切開（jieba 斷詞；沒裝就退回平均切字）。"""
    n = -(-visible_len(p) // MAX_CHARS)
    try:
        import jieba
        jieba.setLogLevel(60)
        for w in ("羅東國小", "羅東", "南門河", "南門路", "南門港", "阿東伯", "羅小東", "羅絲", "阿波", "親水公園"):
            jieba.add_word(w, freq=10 ** 6)
        words = list(jieba.cut(p))
    except ImportError:
        words = list(p)
    target = len(p) / n
    out, cur = [], ""
    for w in words:
        if cur and len(out) < n - 1 and abs(len(cur) + len(w) - target) > abs(len(cur) - target):
            out.append(cur); cur = ""
        cur += w
    out.append(cur)
    return out


SHORT = 8   # 不到這個字數的句子，跟下一句併在同一格，避免只閃一秒


def chunk(text):
    out, cur = [], ""
    for p in split_pieces(text):
        parts = hard_split(p) if visible_len(p) > MAX_CHARS else [p]
        for q in parts:
            # 句號類結尾原則上換格（前一格太短就併）；否則能併就併
            ends = cur.rstrip("」』")[-1:] in END_P
            if cur and (visible_len(cur) + visible_len(q) > MAX_CHARS or (ends and visible_len(cur) >= SHORT)):
                out.append(cur); cur = ""
            cur += q
    if cur:
        out.append(cur)
    return out


def weight(s):
    w = visible_len(re.sub(r"[^\w]", "", s))
    w += sum(1.2 for c in s if c in END_P) + sum(0.6 for c in s if c in MID_P)
    return max(w, 1)


def clean(s):
    s = s.strip()
    while s and s[-1] in DROP_TAIL:
        s = s[:-1]
    # 引號被切到兩格時，各格自己補成對（否則會出現孤零零的「」」）
    for o, c in ("「」", "『』"):
        if s.count(c) > s.count(o):
            s = o + s
        elif s.count(o) > s.count(c):
            s = s + c
    return s


def ts_srt(t):
    ms = round(t * 1000)
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


def ts_ass(t):
    cs = round(t * 100)
    return f"{cs // 360000}:{cs // 6000 % 60:02d}:{cs // 100 % 60:02d}.{cs % 100:02d}"


def main():
    data = json.loads(TIMELINE.read_text(encoding="utf-8"))
    cues, t_page, longest = [], 0.0, 0
    for p in data:
        t = t_page
        for l in p["lines"]:
            parts = chunk(l["text"])
            ws = [weight(x) for x in parts]
            tot = sum(ws)
            if "start" in l:          # v2 時間軸有句間空檔，照每句實際起點
                t = t_page + l["start"]
            s = t
            for x, w in zip(parts, ws):
                e = s + l["duration"] * w / tot
                body = clean(x)
                cap = body if l["role"] == "旁白" else f"【{l['role']}】{body}"
                longest = max(longest, visible_len(body))
                cues.append((s, e, cap))
                s = e
            t += l["duration"]
        t_page += p["total_duration"]

    OUT_SRT.write_text("\n".join(f"{i}\n{ts_srt(s)} --> {ts_srt(e)}\n{c}\n" for i, (s, e, c) in enumerate(cues, 1)),
                       encoding="utf-8")
    head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Microsoft JhengHei,{FONT_PX},&H00FFFFFF,&H00FFFFFF,&H00000000,&H80000000,1,0,0,0,100,100,0,0,4,10,0,2,60,60,{MARGIN_V},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    OUT_ASS.write_text(head + "".join(f"Dialogue: 0,{ts_ass(s)},{ts_ass(e)},Default,,0,0,0,,{c}\n" for s, e, c in cues),
                       encoding="utf-8-sig")
    print(f"{len(cues)} 格字幕，正文最長 {longest} 字 → {OUT_SRT.name}、{OUT_ASS.name}")


if __name__ == "__main__":
    main()
