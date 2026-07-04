---
name: 空拍圖與運鏡生成
description: 生成無人機視角的空拍圖，並提供多種專業運鏡指令（Orbit、Push In、Pull Out 等）
triggers: 空拍、無人機、運鏡、Orbit、航拍、鳥瞰
version: 1.0.0
author: 羅東國小資訊組長
---

## 🚁 功能說明

作為資深的 MV 導演，我將根據你上傳的原始圖片，生成壯闊的**無人機空拍視角**。同時，我會根據你的需求提供五種不同的專業運鏡方式，讓你選擇最適合的動態效果。

---

## 🎥 五種運鏡方式

### 1. Orbit（環繞運鏡）
**效果**：以恆定的高度繞著中心主體進行 360 度平穩環繞飛行

**特點**：
- 保持主體位於畫面中心
- 全方位展現細節和周圍環境
- 製造雄偉、全景的感覺

**適用場景**：
- 突出建築或地標
- 展現壯闊的自然景觀
- 在 MV 中製造視覺的「轉體感」

**運鏡描述範例**：
```
FPV drone shot performing smooth 360-degree orbit around central subject at 
constant altitude, subject remains in frame center, cinematic 4k, motion blur effect.
```

---

### 2. Push In（推鏡/聚焦）
**效果**：無人機緩慢筆直地向前飛向主要主體，逐漸縮小視野

**特點**：
- 從寬廣視野逐漸靠近細節
- 將觀眾的注意力引導至場景的具體細節
- 製造「發現」或「揭曉」的感覺

**適用場景**：
- 從遠景逐漸聚焦到主角
- 強調重點人物或物體
- 營造懸念和期待感

**運鏡描述範例**：
```
FPV drone steadily pushing forward toward main subject, gradually narrowing 
field of view, pulling viewer attention to specific details, cinematic 4k, 
smooth and intentional movement.
```

---

### 3. Pull Out（拉鏡/揭曉）
**效果**：從主體的特寫開始，無人機向後並向上移動

**特點**：
- 揭示周圍的地景和環境
- 建立環境的宏觀視覺與規模感
- 從細節逐漸擴展到全景

**適用場景**：
- 展現人物在廣闊環境中的位置
- 製造「孤獨感」或「渺小感」
- 結尾揭曉全景的故事背景

**運鏡描述範例**：
```
FPV drone pulling back and upward from subject close-up, gradually revealing 
surrounding landscape and environment, establishing macro visual scale, 
cinematic 4k, smooth ascending movement.
```

---

### 4. 圖幀轉影片（Frame to Film）
**效果**：執行流暢的搖臂式動作，將初始幀與最終幀連結

**特點**：
- 從靜態照片轉換為動態影片
- 單一連續路徑中上升並拉遠
- 保持地點與主體的一致性，同時揭示更廣闊的環境

**適用場景**：
- 將靜態的 MV 截圖轉換為動態開場
- 製造「相片活躍」的魔幻效果
- 過場轉場動畫

**運鏡描述範例**：
```
Smooth crane movement transitioning from static frame to cinematic drone shot, 
camera rises and pulls back in single continuous path, maintaining location 
and subject consistency while revealing broader environment, magical photo-to-film 
effect, cinematic 4k.
```

---

### 5. FPV 概念指令（高級運用）
**效果**：沉浸式的第一人稱無人機飛行視角

**特點**：
- 近距離飛行，貼近主體
- 高速或靈活的動作
- 製造刺激和動感

**適用場景**：
- 高能量的動作片段
- 穿越障礙物
- 緊張懸念的場景

**運鏡模板**：
```
FPV drone shot, [環境描述], [速度與動作描述], proximity flying, 
[燈光/風格], cinematic 4k, motion blur.
```

---

## 🚀 使用方法

### 第一步：上傳原始圖片

提供以下資訊：
- 上傳想要轉換為空拍視角的圖片
- 描述圖片中的主體和周圍環境
- 提供 MV 主題或故事背景（可選但建議）

### 第二步：選擇運鏡方式

告訴我你想要：

**選項 1：單一運鏡**
- 選擇上述 5 種方式之一
- 我會提供該運鏡的詳細提示詞

**選項 2：組合運鏡**
- 結合多種運鏡方式
- 例：先 Push In，再轉 Orbit，最後 Pull Out

**選項 3：讓我推薦**
- 根據圖片內容和主題推薦最適合的運鏡

### 第三步：我會生成

輸出內容包含：
1. ✅ **詳細的空拍視角圖片提示詞**
2. ✅ **選定運鏡的完整英文指令**
3. ✅ **運鏡的中文解析說明**
4. ✅ **技術建議**（速度、時長、特效等）

---

## 📚 範例

### 範例 1：Orbit 環繞運鏡

**輸入**：
```
圖片：主角站在城市廣場中央
運鏡：Orbit（環繞）
主題：展現人物的孤獨與城市的宏大
```

**輸出提示詞**：
```
中文提示詞：
無人機從較高的俯視角度捕捉位於城市廣場中央的主角，執行平穩的 360 度環繞運鏡。
攝影機保持恆定的高度，維持主角在畫面中心，緩慢旋轉繞行。
隨著無人機環繞，周圍的城市建築、街道、人群逐漸進入和退出畫面，
展現城市的壯闊與主角身在其中的位置對比。
光線為自然日光或金色時刻，增強電影感。
整個動作平穩無抖動，時長約 10-15 秒。
```

**英文指令**：
```
FPV drone shot performing smooth 360-degree orbit around central character 
in urban plaza at constant altitude, character remains centered in frame, 
surrounding cityscape rotates, establishes environmental scale and subject isolation, 
cinematic 4k, natural golden hour lighting, no camera shake, 15-second duration.
```

---

### 範例 2：組合運鏡 - Push In 到 Orbit

**輸入**：
```
圖片：山頂上的主角
運鏡：先 Push In 靠近，再轉 Orbit 環繞
主題：從遠距離發現主角，再展現周圍的山景
```

**運鏡流程**：
```
0-5 秒：Push In（推鏡）
- 無人機從距離較遠的上空位置開始
- 平穩地向前推進，逐漸靠近山頂
- 觀眾的視野從廣闊的山脈全景逐漸聚焦到主角

5-15 秒：Orbit（環繞）
- 靠近主角後，切換為環繞運鏡
- 無人機以主角為中心，平穩地 360 度旋轉
- 逐漸展現壯闊的山景和主角在其中的位置
```

---

## 💡 最佳實踐

✅ **選擇合適的運鏡方式**
- 溫柔敘事的 MV：Push In 或 Pull Out
- 全景展現的 MV：Orbit 或 Wide Aerial
- 動感激昂的 MV：FPV 高速飛行
- 引導觀眾視線：Pull Out → Orbit → Push In

✅ **考慮音樂節奏**
- 運鏡速度應該與音樂的節奏相匹配
- 快節奏的歌配快速運鏡，慢歌配緩慢運鏡

✅ **保持視覺一致性**
- 無人機的高度、速度、方向應該邏輯連貫
- 避免生硬的切割或不自然的跳轉

✅ **光影和色調**
- 描述天時（早晨、黃金時刻、傍晚、夜晚）
- 這會大幅影響最終的視覺效果

✅ **時長控制**
- 單一運鏡 10-30 秒效果最佳
- 組合運鏡的各段可以 5-10 秒為單位

---

## 🎯 常見問題

**Q: Push In 和 Dolly Shot 有什麼區別？**
A: 兩者都是靠近主體的運鏡，但 Push In 用於無人機，Dolly 用於地面攝影機。

**Q: 可以在運鏡中加入旋轉嗎？**
A: 可以。例如 Push In 同時輕微旋轉，製造螺旋上升的效果。

**Q: FPV 飛行適合 MV 的什麼時刻？**
A: 適合高能量的片段、突破的時刻或製造驚喜感的時刻。

**Q: 運鏡的時長可以自訂嗎？**
A: 可以。根據音樂的節奏和故事節奏進行調整。

**Q: 多個無人機視角可以怎麼組合？**
A: 可以用不同的運鏡方式連接，製造流暢的多視角敘事。

---

## 📞 後續步驟

空拍圖和運鏡指令完成後，建議：

1. **ai-media-generator** → 根據提示詞生成空拍影片
2. **MV_06 影片提示詞生成** → 加入進一步的動態效果
3. **MV_09 Google Flow 微電影製作** → 製作完整的微電影

---

準備好製作你的空拍鏡頭了嗎？上傳圖片並選擇運鏡方式！🚁✨
