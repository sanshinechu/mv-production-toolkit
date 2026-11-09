import re, json
from pathlib import Path

md_path = Path(r"C:\Users\user\我的雲端硬碟\Ai Code\10_科技競賽\115學年度\游智盃_南門河\南門河故事繪本_學生閱讀版.md")
text = md_path.read_text(encoding="utf-8")

# 分割各頁
pages_raw = re.split(r'## 第\s*(\d+)\s*頁[：:]?', text)

def parse_page_text(p_num, raw_text):
    # 清理小偵探筆記、圖片、水平線
    lines = []
    for l in raw_text.split('\n'):
        s = l.strip()
        if not s or s.startswith('>') or s.startswith('!') or s.startswith('*【') or s.startswith('---'):
            continue
        lines.append(s)
    
    # 移除頁標題
    title = lines[0] if lines else f"第{p_num}頁"
    body_lines = lines[1:]
    
    return title, body_lines

all_pages = {}
for i in range(1, len(pages_raw), 2):
    p_num = int(pages_raw[i])
    title, body = parse_page_text(p_num, pages_raw[i+1])
    all_pages[p_num] = {
        "title": title,
        "body": body
    }

print(f"Parsed {len(all_pages)} pages.")
out_file = Path(r"C:\Users\user\我的雲端硬碟\Ai Code\10_科技競賽\115學年度\游智盃_南門河\繪本影片\raw_pages_for_dialogue.json")
out_file.write_text(json.dumps(all_pages, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"Saved to {out_file}")
