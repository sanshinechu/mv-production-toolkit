# -*- coding: utf-8 -*-
r"""從 MV專案範本/ 建一支新 MV 的專案資料夾 outputs/<MV名>/（brief、角色錨點、分鏡表、共審紀錄、shots、music、videos-raw、review、metadata）。

用法：python scripts/new_mv.py "<MV名>"
- 已存在就停下，不覆蓋（避免洗掉做到一半的專案）
- 範本裡的 {{MV名}}、{{建立日期}} 會換成實際值
- MV 名稱同時是 colab_mv/inputs|outputs/ 的資料夾名，避免空白以外的特殊符號
"""
import datetime as dt
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "MV專案範本"


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")   # sys.exit(訊息) 走 stderr，不設會亂碼
    if len(sys.argv) != 2 or sys.argv[1] in ("-h", "--help"):
        print(__doc__)
        sys.exit(0 if len(sys.argv) == 2 else 2)
    name = sys.argv[1].strip()
    if not name or any(c in name for c in '\\/:*?"<>|'):
        sys.exit(f"MV 名稱不能空白或含 \\ / : * ? \" < > |：{name!r}")
    dst = ROOT / "outputs" / name
    if dst.exists():
        sys.exit(f"{dst} 已經存在，不覆蓋")
    shutil.copytree(TEMPLATE, dst, ignore=shutil.ignore_patterns(".gitkeep", "desktop.ini"))
    today = dt.datetime.now().strftime("%Y-%m-%d")
    for f in dst.glob("*.md"):
        t = f.read_text(encoding="utf-8")
        f.write_text(t.replace("{{MV名}}", name).replace("{{建立日期}}", today), encoding="utf-8")
    print(f"已建立 {dst}")
    for p in sorted(dst.iterdir()):
        print("  ", p.name + ("/" if p.is_dir() else ""))
    print("下一步：填 brief.md，照 README.md 的進度檢核往下做。")


if __name__ == "__main__":
    main()
