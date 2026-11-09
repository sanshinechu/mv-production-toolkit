import re, json
from pathlib import Path

path = Path(r"C:\Users\user\我的雲端硬碟\Ai Code\10_科技競賽\115學年度\游智盃_南門河\南門河故事繪本_學生閱讀版.md")
text = path.read_text(encoding="utf-8")

# 移除檔案開頭標題，以 "## 第 X 頁" 分割
pages_raw = re.split(r'## 第\s*(\d+)\s*頁[：:]?', text)

pages_data = []
for i in range(1, len(pages_raw), 2):
    p_num = int(pages_raw[i])
    content = pages_raw[i+1].strip()
    
    # 提取頁標題
    first_line = content.split('\n')[0].strip()
    
    # 過濾掉小偵探筆記（> 開頭）與圖片說明（! 開頭 或 *【 開頭）
    lines = []
    for line in content.split('\n'):
        line_s = line.strip()
        if not line_s:
            continue
        if line_s.startswith('>') or line_s.startswith('!') or line_s.startswith('*【') or line_s.startswith('---'):
            continue
        lines.append(line_s)
        
    pages_data.append({
        "page": p_num,
        "title": first_line,
        "raw_lines": lines
    })

print(f"Parsed {len(pages_data)} pages.")
out_json = Path(r"C:\Users\user\我的雲端硬碟\Ai Code\10_科技競賽\115學年度\游智盃_南門河\繪本影片\pages_parsed.json")
out_json.write_text(json.dumps(pages_data, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"Saved to {out_json}")
