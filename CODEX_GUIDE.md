# 🎨 Codex 執行指南 - MV 主角設計生圖

**交接時間**：2026-05-23 16:35 台北時間  
**交接自**：Claude Code  
**任務**：生成女男主角設計圖（Split Screen 肖像）  
**預計時間**：20-40 分鐘（包括驗證）

---

## 📋 快速檢查清單

- [ ] 打開 `HANDOFF.md` 作為參考文件
- [ ] 確認 API Key 已設定（FAL_KEY、Replicate、或其他）
- [ ] 準備 2 個生圖提示詞（見下方）
- [ ] 建立輸出目錄：`outputs/characters/`
- [ ] 開始生圖

---

## 🔑 API Key 選項

### 選項 1：FAL.ai（推薦）
```bash
export FAL_KEY="your_fal_api_key"
```
申請：https://www.fal.ai/

### 選項 2：Replicate
```bash
export REPLICATE_API_TOKEN="your_replicate_token"
```
申請：https://replicate.com/

### 選項 3：OpenAI DALL-E
```bash
export OPENAI_API_KEY="your_openai_key"
```
申請：https://platform.openai.com/

### 選項 4：手動生圖（無需 API）
使用 Midjourney Discord、Ideogram Web UI、或 Flux Web 等網頁工具

---

## 🎨 生圖任務

### 任務 1：女主角設計圖

**英文提示詞**（複製粘貼到生圖工具）：

```
Split screen portrait of an East Asian woman. Left side: close-up portrait, 
soft studio lighting, gentle eye contact, warm smile, serene and sweet expression. 
Right side: full-body shot in relaxed seated posture, sitting in a cozy coffee shop setting.

Character design: Long straight black hair with subtle waves, falling gently past shoulders, 
clean and fresh look; wearing a soft oversized cream-colored sweater, paired with a beige 
long-sleeved blouse underneath, creating a layered, cozy aesthetic. Warm earth-tone color 
palette with soft whites and warm taupes. Simple gold jewelry, delicate and elegant. 
Innocent yet mature charm, perfect for a first love story. Soft studio background, 
warm and inviting ambiance.
```

**生圖參數**：
- 模型：FLUX.1 Dev 或 Ideogram V3
- 解析度：1024×576（landscape_16_9）
- 數量：1 張
- 風格：Professional portrait photography, studio lighting

**輸出檔名**：`female_character.jpg`

---

### 任務 2：男主角設計圖

**英文提示詞**（複製粘貼到生圖工具）：

```
Split screen portrait of an East Asian man. Left side: close-up portrait, 
soft studio lighting, direct eye contact, warm and gentle smile, caring expression. 
Right side: full-body shot in relaxed casual posture, sitting in a cozy coffee shop setting.

Character design: Short dark brown hair with subtle layers and a natural tousled style, 
modern yet casual; wearing a warm caramel-colored crew neck sweater over a white t-shirt, 
creating a comfortable and approachable look. Warm neutral color palette with browns, 
whites, and taupes. Simple watch and subtle silver chain, understated elegance. 
Warm, caring and mature demeanor despite youthful appearance. The kind, protective energy 
of a young man in love. Soft studio background, warm and intimate ambiance.
```

**生圖參數**：
- 模型：FLUX.1 Dev 或 Ideogram V3
- 解析度：1024×576（landscape_16_9）
- 數量：1 張
- 風格：Professional portrait photography, studio lighting

**輸出檔名**：`male_character.jpg`

---

## 🚀 執行步驟

### 方法 A：使用 Python + FAL API

```bash
cd "<雲端硬碟根目錄>\claude and codex\MV製作"

python3 << 'PYTHON_SCRIPT'
import os
import requests
from datetime import datetime

fal_key = os.getenv('FAL_KEY')
headers = {"Authorization": f"Key {fal_key}", "Content-Type": "application/json"}

# 女主角
female_prompt = """[複製上方的英文提示詞]"""

# 男主角
male_prompt = """[複製上方的英文提示詞]"""

# 生圖函數
def generate_image(prompt, filename):
    print(f"Generating {filename}...")
    response = requests.post(
        "https://fal.run/fal-ai/flux/dev",
        headers=headers,
        json={"prompt": prompt, "image_size": "landscape_16_9", "num_images": 1}
    )
    
    if response.status_code == 200:
        url = response.json()['images'][0]['url']
        img = requests.get(url)
        with open(f"outputs/characters/{filename}", 'wb') as f:
            f.write(img.content)
        print(f"✓ {filename} saved successfully!")
    else:
        print(f"✗ Failed: {response.status_code}")

# 執行
os.makedirs("outputs/characters", exist_ok=True)
generate_image(female_prompt, "female_character.jpg")
generate_image(male_prompt, "male_character.jpg")

PYTHON_SCRIPT
```

### 方法 B：使用 curl + FAL API

```bash
# 女主角
curl -X POST "https://fal.run/fal-ai/flux/dev" \
  -H "Authorization: Key $FAL_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "[複製上方的英文提示詞]",
    "image_size": "landscape_16_9",
    "num_images": 1
  }' | tee female_response.json

# 從 JSON 提取圖片 URL 並下載
# curl -o outputs/characters/female_character.jpg "[圖片URL]"

# 男主角（同樣步驟）
```

### 方法 C：手動網頁生圖

1. **打開 Ideogram**（https://ideogram.ai/）或 **FLUX Web UI**
2. 複製提示詞到輸入框
3. 生圖設定：
   - 風格：Portrait / Photography
   - 寬高比：16:9 或 Custom 1024×576
4. 生成並下載為 `female_character.jpg` 和 `male_character.jpg`
5. 儲存到 `outputs/characters/` 資料夾

---

## ✅ 驗證檢查清單

生成圖片後，檢查以下項目：

### 女主角檢查
- [ ] Split Screen 格式正確（左臉特寫、右全身）
- [ ] 長直黑髮，髮尾帶微波浪
- [ ] 穿著米色毛衣 + 米白襯衫
- [ ] 溫柔甜蜜的表情，眼神溫柔
- [ ] 簡單金色飾品
- [ ] 咖啡廳柔和背景
- [ ] 色彩：暖色調（米色、棕色調）

### 男主角檢查
- [ ] Split Screen 格式正確（左臉特寫、右全身）
- [ ] 短棕髮，自然蓬鬆感
- [ ] 穿著焦糖色毛衣 + 白 T 恤
- [ ] 溫暖體貼的表情，眼神關懷
- [ ] 手錶和銀色項鍊
- [ ] 咖啡廳柔和背景
- [ ] 色彩：暖棕色調（焦糖、白色、卡其）

### 整體配對檢查
- [ ] 兩人色彩搭配協調（米色 + 焦糖色）
- [ ] 兩人穿著風格相搭（都是毛衣 + 打底）
- [ ] 年齡感相近（初戀學生）
- [ ] 燈光和背景風格一致

---

## 📥 輸出檔案位置

生成的圖片應儲存到：

```
outputs/
└── characters/
    ├── female_character.jpg       (1024×576)
    └── male_character.jpg         (1024×576)
```

如果目錄不存在，先建立：

```bash
mkdir -p outputs/characters
```

---

## 📝 更新 HANDOFF.md

生圖完成後，請更新 `HANDOFF.md`：

1. 開啟 `HANDOFF.md`
2. 找到「MV_02 - 主角設計」部分
3. 更新狀態：
   ```markdown
   ### ✓ MV_02 - 主角設計  
   - **狀態**：✅ 設計完成，✅ 圖片已生成
   ```

4. 添加驗證結果：
   ```markdown
   - **驗證**：✅ 女主角圖片已驗證
   - **驗證**：✅ 男主角圖片已驗證
   - **色彩搭配**：✅ 整體協調
   ```

5. 更新進度欄：
   ```
   進度：27%（3/11 步驟完成）
   ```

---

## 🔄 完成後交接回 Claude Code

圖片生成並驗證完成後：

1. 確保 `outputs/characters/` 目錄中有 2 張 JPG 圖片
2. 更新 `HANDOFF.md` 記錄進度
3. 準備回傳信息：
   - ✅ 女主角圖片狀態
   - ✅ 男主角圖片狀態
   - ✅ 驗證結果
   - 💾 圖片儲存位置

4. 通知 Claude Code 已準備好進行 **MV_03（場景提示詞）**

---

## 💡 常見問題

**Q：圖片色彩不符預期？**
A：調整提示詞中的色彩描述，例如將「cream-colored」改為「light peach」

**Q：人物比例不對？**
A：加入「professional headshot proportions」到提示詞

**Q：背景不像咖啡廳？**
A：確保提示詞包含「cozy coffee shop setting」並且使用高品質模型

**Q：Split Screen 格式不對？**
A：確保提示詞明確寫「Split screen portrait」且包含「Left side」和「Right side」的描述

**Q：生圖費用多少？**
A：FAL FLUX.1 Dev 約 $0.025/張，2 張約 $0.05

---

## 🎯 完成指標

✅ 生圖完成時的目標狀態：

```
✓ female_character.jpg 已生成（1024×576）
✓ male_character.jpg 已生成（1024×576）
✓ 兩張圖片已驗證
✓ HANDOFF.md 已更新
✓ 準備交接回 Claude Code
```

---

**準備好開始生圖了嗎？** 🎨

提示：複製上方的英文提示詞（在「任務 1」和「任務 2」中），貼到你選擇的生圖工具中！

