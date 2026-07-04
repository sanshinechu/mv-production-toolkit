---
name: 分鏡批次生圖
description: 讀取 MV 分鏡表/prompts 清單，用免費生圖管道批次產出分鏡圖（Cloudflare Workers AI 優先、Pollinations 備援），檔名前綴對齊組裝腳本。當使用者說「照分鏡生圖」「批次生成分鏡圖」「生 MV 素材圖」時使用
triggers: 批次生圖、分鏡生圖、MV 素材、shots、照腳本生圖
version: 1.0.0
author: 羅東國小資訊組長
---

## 🎨 功能說明

把分鏡表變成一整批可組裝的分鏡圖。內建免費生圖順序（draw_cf → draw-free 自動備援）、檔名規格對齊、斷點續跑（已存在自動跳過），以及免費模型的風格護欄。

---

## ⚠️ 風格鐵律（最重要，先讀這條）

**免費模型勿用寫實風格。** 免費模型畫寫實的三大死穴：人臉崩壞、跨張角色不一致、中文字亂碼。

- **優先**：抽象/風格化路線——蠟筆塗鴉、粉筆畫、剪影、水彩。筆觸不完美是風格加分，火柴人天然一致
- **寫實僅限**使用者明確要求，且人物一律剪影/背影/俯瞰，避開臉部特寫；黑板/招牌文字用「模糊質感」帶過，勿要求可讀中文
- 台灣場景務必在 prompt 加 Taiwanese（免費模型預設畫西方場景）

## 🔧 生圖管道順序

| 順位 | 管道 | 特性 |
|------|------|------|
| 1 | **draw_cf**（Cloudflare Workers AI, flux-1-schnell） | 預設。快（約 6 秒/張）、每天約 170 張免費、固定 1024x1024 方形 |
| 2 | **draw-free**（Pollinations.ai） | 備援。可指定 1920x1080 等尺寸、不用金鑰、會排隊 |
| 3 | **draw**（Vertex AI，付費） | 使用者明確要求高品質時才用 |

憑證：draw_cf 需 `%USERPROFILE%\.cloudflare_ai`（ACCOUNT_ID= 與 API_TOKEN= 兩行）。

## 🚀 執行流程

### Step 1：整理 prompts 清單

從分鏡表（mv-11 產出）萃取每個 cut 的畫面描述，寫成 `prompts.md`：
- 定義**統一風格基底**（所有 prompt 結尾都帶），這是跨張一致性的關鍵
- 檔名前綴規格：`cutNN_場景關鍵字`（例 `cut06_crayon_circle`），**必須與組裝腳本 STORYBOARD 清單對齊**
- draw_cf 出方形圖、組裝時置中裁 16:9——prompt 重點勿放畫面最上下緣

### Step 2：produce 批次腳本並執行

以本技能 `scripts/gen_shots_template.ps1` 為範本，填入 cuts 清單後執行。範本已內建：
- draw_cf 優先、失敗自動落 draw-free
- 已存在同前綴圖片自動跳過（**重生個別 cut：刪掉該前綴的圖再重跑即可**）
- 完成統計與失敗清單

```powershell
powershell -ExecutionPolicy Bypass -File gen_shots.ps1
```

**PowerShell 慣例**：腳本一律存 UTF-8 with BOM（PowerShell 5.1 讀無 BOM 中文會炸）。

### Step 3：抽查與交付

- 生成後用 2x3 或 3x4 拼圖（ffmpeg tile）抽查全批風格一致性
- 檢查跨張呼應設計（如首尾 cut 的同元素）
- 回報：成功張數、走備援的張數、建議重抽的 cut

## 📌 參考範例

`11_Opencode/`：`tools/gen_shots_v3.ps1`（實戰腳本）、`mv_project/prompts_v3.md`（塗鴉宇宙 prompt 表）、`mv_project/shots_v3/`（成品）。
