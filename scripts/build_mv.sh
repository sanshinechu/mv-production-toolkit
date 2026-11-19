#!/usr/bin/env bash
# 一支 MV 從素材到成品的組裝：make_mv.py → post/overlays.py（有才跑）→ review_mv.py
#
# 用法（在 Git Bash，從哪裡執行都可以）：
#   bash scripts/build_mv.sh <MV資料夾> <版本>          例：bash scripts/build_mv.sh "F:/video/MV/怪獸申請住隔壁" v9
#   bash scripts/build_mv.sh <MV資料夾> <版本> --force  已有同版本成品時覆蓋
#
# 參數寫在 <MV資料夾>/build.conf（範例見 MV專案範本/build.conf），路徑一律相對於 MV 資料夾。
# 成品：<MV資料夾>/review/<片名>_後製_<版本>.mp4
# 2026-11-19 從《怪獸申請住隔壁》v8 那串指令整理出來。
set -euo pipefail

usage() { sed -n 2,9p "$0" | sed 's/^# \{0,1\}//'; exit 1; }
[ $# -ge 2 ] || usage
MV_ARG=$1; VER=$2; FORCE=${3:-}

TOOLKIT=$(cd "$(dirname "$0")/.." && pwd)
[ -d "$MV_ARG" ] || { echo "❌ 找不到 MV 資料夾：$MV_ARG"; exit 1; }
# 給 Windows 版 python／ffmpeg 用的路徑要是 F:/... 形式（Git Bash 的 pwd -W）；其他系統退回 pwd
MV=$(cd "$MV_ARG" && (pwd -W 2>/dev/null || pwd))
CONF="$MV/build.conf"
[ -f "$CONF" ] || { echo "❌ 缺 $CONF（從 MV專案範本/build.conf 複製一份來改）"; exit 1; }

# ---- 讀設定（每一項都有預設，conf 只要寫有用到的）----
NAME=""; STORYBOARD=""; MUSIC=""; SHOTS=""; VIDEOS="videos-raw"; SIZE="1920x1080"
STRETCH=""; FIT=""; PROLOGUE=""; EPILOGUE=""; AUDIO_CUES=""
SUB_LYRICS=""; LYRICS_OFFSET=""; SUB_DIALOG=""; SUB_MARGIN=""; COVER=""; COVER_SEC="3"
# shellcheck disable=SC1090
source "$CONF"
NAME=${NAME:-$(basename "$MV")}
[ -n "$STORYBOARD" ] || { echo "❌ build.conf 沒填 STORYBOARD"; exit 1; }
[ -n "$MUSIC" ] || { echo "❌ build.conf 沒填 MUSIC"; exit 1; }

# conf 裡寫的檔案先全部檢查一遍，免得跑了十分鐘才在半路缺檔
missing=0
for v in STORYBOARD MUSIC SHOTS VIDEOS AUDIO_CUES SUB_LYRICS SUB_DIALOG COVER; do
  p=${!v}; [ -z "$p" ] && continue
  [ -e "$MV/$p" ] || { echo "❌ $v 指到的檔不存在：$p"; missing=1; }
done
[ $missing -eq 0 ] || exit 1

OUT="$MV/review/${NAME}_後製_${VER}.mp4"
if [ -e "$OUT" ] && [ "$FORCE" != "--force" ]; then
  echo "❌ $OUT 已經存在。換個版本號，或加 --force 覆蓋"; exit 1
fi
mkdir -p "$MV/review"

# ---- 找 ffmpeg：PATH 沒有就去 WinGet 的安裝位置找（主機 1 的 ffmpeg 不在 PATH）----
if ! command -v ffmpeg >/dev/null 2>&1; then
  if [ -n "${LOCALAPPDATA:-}" ]; then
    WG=$(cygpath -u "$LOCALAPPDATA" 2>/dev/null || echo "$LOCALAPPDATA")/Microsoft/WinGet/Packages
    for d in "$WG"/Gyan.FFmpeg*/ffmpeg-*/bin; do
      [ -x "$d/ffmpeg.exe" ] && { export PATH="$d:$PATH"; break; }
    done
  fi
fi
command -v ffmpeg >/dev/null 2>&1 || { echo "❌ 找不到 ffmpeg（PATH 與 WinGet 都沒有）"; exit 1; }

PY=${PYTHON:-python}
export PYTHONIOENCODING=utf-8

# ---- 1. make_mv ----
args=(--storyboard "$MV/$STORYBOARD" --music "$MV/$MUSIC" --size "$SIZE")
[ -n "$VIDEOS" ]        && args+=(--videos "$MV/$VIDEOS")
[ -n "$SHOTS" ]         && args+=(--shots "$MV/$SHOTS")
[ -n "$STRETCH" ]       && args+=(--stretch "$STRETCH")
[ -n "$FIT" ]           && args+=(--fit "$FIT")
[ -n "$PROLOGUE" ]      && args+=(--prologue "$PROLOGUE")
[ -n "$EPILOGUE" ]      && args+=(--epilogue "$EPILOGUE")
[ -n "$AUDIO_CUES" ]    && args+=(--audio-cues "$MV/$AUDIO_CUES")
[ -n "$SUB_LYRICS" ]    && args+=(--sub-lyrics "$MV/$SUB_LYRICS")
[ -n "$LYRICS_OFFSET" ] && args+=(--lyrics-offset "$LYRICS_OFFSET")
[ -n "$SUB_DIALOG" ]    && args+=(--sub-dialog "$MV/$SUB_DIALOG")
[ -n "$SUB_MARGIN" ]    && args+=(--sub-margin "$SUB_MARGIN")
CS=0
if [ -n "$COVER" ]; then args+=(--cover "$MV/$COVER" --cover-sec "$COVER_SEC"); CS=$COVER_SEC; fi

OVERLAYS="$MV/post/overlays.py"
if [ -f "$OVERLAYS" ]; then BODY="$MV/review/_build_${VER}_無字卡.mp4"; else BODY="$OUT"; fi

echo "▶ 1/3 make_mv.py → $(basename "$BODY")"
"$PY" "$TOOLKIT/scripts/make_mv.py" "${args[@]}" --out "$BODY"
[ -s "$BODY" ] || { echo "❌ make_mv 沒產出 $BODY"; exit 1; }

# ---- 2. 後製字卡（這支 MV 有 post/overlays.py 才跑）----
if [ -f "$OVERLAYS" ]; then
  echo "▶ 2/3 post/overlays.py（--cover-sec $CS）"
  # overlays.py 會在自己的資料夾寫字卡 png，所以在 post/ 裡執行
  (cd "$MV/post" && "$PY" -X utf8 overlays.py "$BODY" "$OUT" --cover-sec "$CS")
  [ -s "$OUT" ] || { echo "❌ overlays 沒產出 $OUT（中間檔留著：$BODY）"; exit 1; }
  rm -f "$BODY"
else
  echo "▶ 2/3 沒有 post/overlays.py，略過後製字卡"
fi

# ---- 3. 自動檢查 ----
echo "▶ 3/3 review_mv.py"
rargs=(--music "$MV/$MUSIC" --storyboard "$MV/$STORYBOARD" --cover-sec "$CS")
[ -n "$AUDIO_CUES" ] && rargs+=(--audio-cues "$MV/$AUDIO_CUES")
[ -n "$PROLOGUE" ]   && rargs+=(--prologue "$PROLOGUE")
[ -n "$EPILOGUE" ]   && rargs+=(--epilogue "$EPILOGUE")
"$PY" "$TOOLKIT/scripts/review_mv.py" "$OUT" "${rargs[@]}" || echo "⚠ review_mv 回報有問題，看上面的訊息"

echo "✅ 成品：$OUT"
echo "   接下來照 README 第 11 步做三家抽幀，不要只看 review_mv 的結果就交件"
