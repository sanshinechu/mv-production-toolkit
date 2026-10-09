#!/usr/bin/env bash
# 把 dotfiles 正本的 MV skill 同步到本專案的兩份副本
#
#   正本：$CHEZMOI_SRC/.skills/{MV_WORKFLOW_GUIDE,mv-01…mv-12}   （預設 ~/.local/share/chezmoi）
#   副本：.claude/skills/<名稱>/   給 Claude Code，內容與正本相同
#         .agents/skills/<名稱>/   給 Codex，*.md 裡的工具名 Claude 換成 Codex（大小寫有別，路徑 .claude 不動）
#
# 為什麼要有這支：2026-10-09 Codex 檢視發現專案兩份副本停在 7–8 月，
# 而且早在那之前就跟正本分岔（缺角色一致性參考詞）。Claude 與 Codex 會照不同 SOP 做事。
#
# 規則：
#   - 只改正本，不要直接改副本（下次同步會被蓋掉）
#   - 本腳本只覆蓋同名檔，不刪檔；副本裡多出來的檔案只列出來，自己判斷要不要清
#   - 本專案獨有的 skill（mv-production-packaging 等）不在同步範圍
#
# 用法（在 01_MV製作 底下）：
#   bash scripts/sync_mv_skills.sh           # 乾跑：列出哪些會變
#   bash scripts/sync_mv_skills.sh --apply   # 真的寫入

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRC="${CHEZMOI_SRC:-$HOME/.local/share/chezmoi}/.skills"
APPLY=0
[[ "${1:-}" == "--apply" ]] && APPLY=1

[[ -d "$SRC" ]] || { echo "找不到正本 $SRC（這台沒裝 chezmoi source？）" >&2; exit 1; }

SKILLS=(MV_WORKFLOW_GUIDE)
while IFS= read -r d; do SKILLS+=("$(basename "$d")"); done < <(find "$SRC" -maxdepth 1 -type d -name 'mv-[0-9][0-9]-*' | sort)
[[ ${#SKILLS[@]} -ge 13 ]] || { echo "正本只找到 ${#SKILLS[@]} 支，預期 13 支，先停下來檢查" >&2; exit 2; }

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
changed=0

for s in "${SKILLS[@]}"; do
    for target in claude agents; do
        dest="$ROOT/.$target/skills/$s"
        stage="$TMP/$target/$s"
        mkdir -p "$stage"
        cp -r "$SRC/$s/." "$stage/"
        if [[ $target == agents ]]; then
            find "$stage" -name '*.md' -print0 | xargs -0 sed -i 's/Claude/Codex/g'
        fi
        # 比對（忽略行尾差異，Drive 上的副本可能是 CRLF）
        if [[ -d "$dest" ]] && diff -rq --strip-trailing-cr "$stage" "$dest" >/dev/null 2>&1; then
            continue
        fi
        changed=$((changed + 1))
        echo "  ~ .$target/skills/$s"
        if [[ -d "$dest" ]]; then
            while IFS= read -r f; do
                rel="${f#"$dest"/}"
                [[ -e "$stage/$rel" ]] || echo "      ⚠️ 副本多出 $rel（正本沒有，不會刪，自己確認）"
            done < <(find "$dest" -type f)
        fi
        if [[ $APPLY -eq 1 ]]; then
            mkdir -p "$dest"
            cp -r "$stage/." "$dest/"
        fi
    done
done

if [[ $changed -eq 0 ]]; then
    echo "兩份副本都已是最新（${#SKILLS[@]} 支）"
elif [[ $APPLY -eq 1 ]]; then
    echo "已同步 $changed 份。.claude/skills 有進 git，記得 commit；.agents 被 .gitignore 排除，靠雲端硬碟同步。"
else
    echo "乾跑：$changed 份需要更新。確認後加 --apply。"
fi
