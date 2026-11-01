# Dreamina 影片提示詞寫作指南

Dreamina（Seedance 2.0）對**英文 cinematic 提示詞**效果最好。中文也行，但英文 + 電影術語會讓品質直接上一個檔次。

## 🎬 核心公式

一個好的提示詞 = **主體 + 動作 + 環境 + 鏡頭 + 光線 + 風格**

```
[Subject] + [Action] + [Environment] + [Camera movement] + [Lighting] + [Style]
```

### 範例對照

❌ 太簡單：
> A cat runs on the beach.
>（貓在沙灘跑）

✅ 高品質：
> A fluffy orange tabby cat runs joyfully along a golden sunset beach, 
> paws splashing through gentle waves, shot in cinematic slow motion with 
> a tracking shot from the side, warm golden hour lighting, shallow depth 
> of field, film grain, Wes Anderson color palette, 4K quality.

## 🎥 實用關鍵字清單

### 鏡頭運動（Camera movement）
- `tracking shot` — 跟拍
- `dolly in / dolly out` — 推軌／拉軌
- `aerial shot` / `drone shot` — 空拍
- `close-up` — 特寫
- `wide shot` / `establishing shot` — 廣角／定場
- `POV shot` — 主觀視角
- `handheld` — 手持晃動
- `slow motion` — 慢動作
- `time-lapse` — 縮時
- `360 rotation` — 環繞鏡頭

### 光線（Lighting）
- `golden hour` — 黃昏暖光
- `blue hour` — 黎明藍調
- `backlit` / `rim lighting` — 逆光／輪廓光
- `neon lighting` — 霓虹燈
- `soft natural lighting` — 自然柔光
- `dramatic side lighting` — 戲劇側光
- `volumetric lighting` — 體積光（光線有粒子感）

### 風格（Style）
- `cinematic` — 電影感（萬用必加）
- `photorealistic` — 寫實
- `anime style` — 動畫風
- `Studio Ghibli style` — 吉卜力風
- `film noir` — 黑色電影
- `documentary style` — 紀錄片感
- `cyberpunk` — 賽博龐克
- `shot on 35mm film` — 35mm 底片質感
- `IMAX quality` — IMAX 級質感

### 情緒與色調
- `warm color grading` / `cool color grading`
- `moody atmosphere`
- `vibrant colors`
- `desaturated`
- `high contrast`

## 📝 五個現成範本（可直接改寫）

### 1. 人物特寫
```
A young woman with long black hair stands in a Tokyo alley at night, 
rain falling gently, neon signs reflecting in puddles behind her, 
slow push-in close-up on her face, shallow depth of field, 
cinematic lighting, melancholic mood, shot on anamorphic lens.
```

### 2. 自然風景
```
Aerial drone shot flying over a misty mountain range at sunrise, 
clouds drifting between peaks, golden light breaking through, 
sweeping camera movement, National Geographic style, 4K, 
cinematic color grading.
```

### 3. 產品展示
```
A premium wristwatch rotates slowly on a black velvet surface, 
macro close-up, dramatic side lighting highlighting the gold details, 
shallow depth of field, commercial advertising style, 
ultra-sharp focus, luxury aesthetic.
```

### 4. 動物動作
```
A golden retriever leaps joyfully through a field of tall grass 
in slow motion, warm summer sunlight, grass blades flying in the air, 
tracking shot from the side, shallow depth of field, 
cinematic golden hour lighting, 120fps feel.
```

### 5. 教學場景（給老師參考）
```
A teacher stands in front of a bright classroom holding a tablet, 
students visible in soft focus background, warm natural lighting 
through large windows, slow dolly-in shot, documentary style, 
inspiring atmosphere.
```

## ⚠️ 寫 prompt 的五個禁忌

1. **不要用否定句**：「不要有貓」這種寫法通常沒用。要什麼就正面寫什麼。
2. **不要太多主體**：一個影片建議 1~2 個主體，多了 AI 會搞混。
3. **不要寫文字**：AI 生成的文字幾乎一定會錯（拼錯、亂碼），盡量避免招牌、看板等需要清楚文字的場景。
4. **不要指定人名**：「馬斯克在台上演講」不會生成真實的馬斯克，改寫成外觀描述。
5. **不要過長**：超過 500 字的 prompt 反而會讓 AI 抓不到重點，控制在 100~200 字最佳。

## 🎯 阿亮老師的中文→英文轉換建議

教學現場老師和學生通常用中文思考，Claude 應該幫忙做「語意擴寫」：

| 中文原意 | 直翻（不好） | 擴寫後（好） |
|---------|--------------|--------------|
| 貓在跑 | cat is running | A playful cat sprints across a sunlit garden, slow-motion tracking shot, golden hour lighting, cinematic |
| 下雨的街道 | rainy street | Empty city street at night during heavy rain, puddles reflecting neon signs, moody atmosphere, film noir style, handheld camera |
| 學生在讀書 | student reading book | A student sits by a large window reading a book, warm afternoon light streaming in, soft dust particles in the air, shallow depth of field, peaceful atmosphere |
