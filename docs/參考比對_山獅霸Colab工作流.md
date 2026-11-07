# 山獅霸 Colab 工作流分析與待測清單

> **21:07 收工更新：audio.fixed 已有本環境成功樣本，並經老師同意接進正式流程。** 下文 17:48 的「待測」是當時分析；最新核查見文末〈Claude 測試結果複核〉。G4、Colab CLI 與完整饒舌範本仍未在我們環境實測。
- 紀錄時間：2026-10-31 17:48（Asia/Taipei），資訊組筆電／Codex。
- 使用者決定：先記錄，有空再測試；不啟動 Colab、不生成、不消耗運算單元。
- 狀態：已閱讀目錄、文件與主要程式；尚未在我們的環境實測，以下不得當成已驗證規則。
- 來源：https://github.com/mathruffian-dot/shanshiba-workflow-colab
- 分析版本：`63e7d97295a48c6cf81bbdabbb68f9fbcb46cdad`。下方來源固定到此版本，後續測試前再看上游差異。

## 判斷與專案定位

這是一套由 AI agent 操作的短片製作管線，包含一般劇情短片與饒舌對決範本；可只把 H3 交給 Colab，或全流程在雲端執行。對我們最有價值的是固定歌曲音軌對嘴與 Colab CLI 批次控制。建議先拆出單鏡測試，通過後才評估接進既有 MV 流程。

| 目錄 | 用途 |
|---|---|
| agent/ | 編劇、饒舌對決、Blender 預演技能 |
| cloud/ | Colab 開關機、安裝、批次、傳檔與本機／雲端混合佇列 |
| tools/ | H3、生圖、語音、歌曲、放大、檢查工具 |
| pipeline/ | template_local 一般短片、template_battle 饒舌對決與示例 |
| setup/ | 環境、模型清單與驗證 |
| docs/ | 架構、操作、踩坑、自審 |
| sfx/、templates/ | 音效、片尾與圖形素材 |

## 最值得試：audio.fixed 歌聲對嘴

已從程式確認：
- `pipeline/template_battle/make_battle.py` 分離歌曲人聲、對齊歌詞，依每鏡時間裁切人聲，寫入 `audio.fixed.file`。
- `tools/h3_shot.py` 的 fixed 分支會編碼音訊、設定零噪聲遮罩、合併影音 latent，並加入音訊 guide；輸出影片直接使用輸入音軌。
- 這條已讀取的分支沒有呼叫 T8 AudioLock；是用 ComfyUI 節點組合完成。不能因此推論它與 T8／ExactAudioLock 的結果完全相同。
- `audio.voice_ref` 是參考音色、讓 H3 自己念台詞，與 `audio.fixed` 固定歌曲音軌不同。
- 保留輸入音訊不等於嘴型準確。生成流程中的對嘴效果、最終編碼後音軌與我們中文歌曲的適用性，仍須實測。

## 作者驗證範圍（不是我們的實測）

| 項目 | 作者詳細紀錄 |
|---|---|
| 一般短片現行 h3_ref 模式 | 2026-10-24，RTX 5090 重跑 7 鏡、6 句台詞 |
| 饒舌本機版 | 2026-10-28～29，兩首 Suno 歌、49 鏡成片；其中 43 鏡 H3 |
| 饒舌 Colab 版 | 2026-10-29 跑通各階段，但實際首幀與 H3 僅生成 4 鏡，其餘用靜態圖／鏡號代替 |
| Colab 完整 49 鏡需 1.5–2 小時、15–18 單元 | 估算，不是全鏡實跑結果 |
| 付費生圖分支整套 Colab | 詳細說明記為尚未完整重跑 |

首頁「從頭實測通過」應搭配詳細測試範圍解讀；文件中也有舊的「尚未從頭實測」段落與後面的新驗證紀錄並存，採有日期、條件與範圍的紀錄。

## 與現有 MV 路線的關係

- 我們已使用 Colab A100、H3、DMAD 4 步及六段提示詞格式，不是從零建置。
- 我們透過 `scripts/colab_bridge.py` 操作瀏覽器 Colab，正式批次遵守 `h3_guard.py` 三合一守護規則；上游用 Colab CLI，不能直接混接或取代。
- 現有 H3 分鏡規格禁止 audio／dialogue。歌聲對嘴需獨立試驗，通過後才評估調整分鏡審核、拆檔與守護流程。
- 作者 G4 的 90 格測試約 42 秒，A100 約 210–270 秒，僅代表其特定設定。我們的模型版本、卡片供應、單元費率與速度要現場確認，不能直接拿來預算。

## 已發現的使用限制

- `cloud/colab_h3.py` 的增量上傳對部分 out/ 檔案只比較大小；同大小但改內容可能被跳過。
- 本機刪除輸出不會自動刪除 VM 檔案；重做要依範本的 seed／重做機制處理，驗證用到的是本輪成果。
- 作者自審仍要求人看成片；逐音素嘴型沒有量測。
- H3 官方授權有地區限制；作者記錄 G4 測試機房位於美國／歐盟。測試前確認執行地區與適用條款，不能只比較速度。
- Qwen-Image 2.1、Breeze TTS 2、YuE2 的限制需依選用模型各自確認，repo 的程式授權不代表全部模型同樣可用。

## 有空再測：最小單鏡實驗

- [ ] 老師決定開始，先確認可用環境、機房與運算單元，再啟動付費 GPU。
- [ ] 選一張已定案、臉清楚的單人首幀，加 5–8 秒有權使用的中文演唱。
- [ ] 使用獨立測試資料夾，保存歌曲原段、人聲分軌、首幀、spec、生成 workflow、版本與 log；jobs.json／spec 不只留暫存區。
- [ ] 先評估既有 A100 環境能否跑 fixed 分支，不必一開始就換整套 G4／Colab CLI。
- [ ] 依上游 audio.fixed 做單鏡，保留原歌曲供最終組裝；先不套完整饒舌特效。
- [ ] 驗嘴型的子音／母音與開口時序、臉與服裝、運鏡、手部、意外切鏡，抽幀加實際播放。
- [ ] 比對音訊時長、偏移與內容，區分生成引導人聲和最終歌曲；「最後貼回原音」不算證明嘴型正確。
- [ ] 記錄 GPU、模型／節點版本、seed、鏡長、生成與安裝時間、重抽次數及實際單元。
- [ ] 通過後再測不同歌速／景別，再決定接進現有工作流；G4、雙 ComfyUI、完整饒舌範本另行評估。

## 原始依據

固定版本根目錄：
https://github.com/mathruffian-dot/shanshiba-workflow-colab/tree/63e7d97295a48c6cf81bbdabbb68f9fbcb46cdad

優先讀取同版本的：
- `pipeline/template_battle/README.md`：測試範圍、輸入、各階段與重做方法。
- `pipeline/template_battle/make_battle.py`：`specs()` 與 audio.fixed。
- `tools/h3_shot.py`：`build_graph()` 的 fixed／voice_refs 分支。
- `cloud/README.md`、`cloud/colab_h3.py`：CLI 控制、傳檔與雲端執行。
- `pipeline/template_local/README.md`：一般短片驗證。
- `docs/04_自審清單.md`、`setup/custom_nodes.txt`、`THIRD_PARTY_NOTICES.md`。

H3 官方授權（分析時已讀；測試前重查）：
https://huggingface.co/MiniMaxAI/MiniMax-H3/blob/main/LICENSE

相關既有分析：[DSLab 研習比對](參考比對_DSLab研習.md)、[山獅霸工作流比對](參考比對_山獅霸工作流.md)。

## 2026-10-31 21:07 Claude 測試結果複核（Codex／資訊組筆電）

### 直接核對的證據

- 已讀家裡用筆電同日每日筆記、DSLab 比對文件、分流策略與本次程式變更。
- 經專案 colab_mv.lnk 解析到本機可讀的共用資料夾，直接讀 outputs/_test_audiofixed、outputs/_test_sing/cut25、cut27 的 meta.json、workflow_api.json、shot.json 及批次 log。
- meta.json：cut05 測試 107 格／126.2 秒；cut25 90 格／109.4 秒；cut27 107 格／118.0 秒，皆是程序回報 ok。程序 ok 不等於畫面驗收合格。
- 直接抽看 cut25 原始 H3、cut27 原始 H3 與 FlashVSR 版，每隔 0.5 秒排圖。cut25 的抽樣畫面穩定、嘴巴有開合；cut27 約 1 秒起，臉部特寫與坐著拿發光車票的較遠構圖重疊。
- **cut27 疊影已存在於原始 H3，FlashVSR 不是此次疊影起因。** 首幀／文字構圖不一致是合理假說，尚未做對照試驗證實；不能斷言「裁切首幀必然失敗」。
- cut27 的 camera 寫肩膀以上特寫，setting 卻詳列座位、車內配置與發光車票，subjects 仍寫胸前識別證和車票。後續應統一鏡頭內可見內容與特寫需求；不在此次收工擅自修改既有規格。

### 結論的適用範圍

- 可確認：現有工具的 audio.fixed 分支已實際運作，有中文演唱中近景成功樣本；老師已在 Claude 對話同意接進正式唱歌鏡流程，採 FlashVSR 預設並逐鏡抽格。
- 中近景 2/2（cut05、cut25），集中同一角色與黏土風，僅是樣本紀錄，不是普遍成功率；特寫嘗試 0/1。
- Claude 記錄音軌相關 0.994／0 ms；組片後畫面誤差 0 格、音訊 +5 ms。**這次未重新計算這些數字**，亦未逐音素驗嘴型。這些指標支持音軌保留與組裝時間對齊，不證明每字嘴型準確。
- 56 鏡整片組裝是驗證新唱歌鏡能放回既有作品，並非 56 鏡都重新生成或都測過對嘴。
- ExactAudioLock 已試裝成功，但沒有用它生成；G4／CLI／完整饒舌範本仍未在我們環境驗證。

### 程式核查與待辦（未修）

1. **人聲快取會過期**：h3_batch.py ensure_guides() 只看 guide 是否存在；整首 vocals.wav 也只看存在與否。換原曲、改 song_start 或 duration 後可能沿用舊人聲。應以歌曲內容雜湊、切段起點與長度判斷是否重建，或明確強制重建。
2. **唱歌清單不能清空**：collect_videos.py 只有 sings 非空才寫 _sing_cuts.json；全部取消唱歌鏡後舊清單仍在。應每次更新完整清單（包括空集合），並確認與本輪素材一致。
3. make_mv.py 已擋唱歌鏡放入 --fit，也會覆蓋由 last-frame 觸發的加速，方向正確；正式重剪時仍要連同前述快取一致性驗證。
4. 背景 nohup 的守護無法直接 runtime.unassign()，Claude 已記錄並手動釋放。下一輪按既有文件在筆記本前景啟動，不把程序結束當成 GPU 已釋放。
5. demucs 的 pip --target 目前多抓相依套件，約 5 GB（**11-01 已改成一條 pip、只裝 CPU 版 torch，見分流策略 🅰**）；瘦身列後續，優先先處理內容正確性。

### 下次接續順序

- 先補人聲快取更新與空唱歌清單處理（屬開發工作，開始前照老師規範提出範圍確認）。
- 統一 cut27 特寫首幀與鏡頭可見描述，保留角色身份一致，經既有生圖／審核關卡後再重測；不要直接沿用「裁切是原因」的假說。
- 再增加不同角色、歌速與景別樣本。G4、完整饒舌與第三方 AudioLock 暫列後續。

Claude 原始詳錄在 Obsidian：每日筆記/2026-10-31-家裡用筆電.md；正式規則仍以 [影片分流策略](影片分流策略.md) 為準。

## 2026-11-08 上游差異（63e7d97→b7a65d4，31 個 commit）

- 紀錄：2026-11-08，Claude。只讀 GitHub 差異，沒有開 Colab、沒有生成。
- 固定版本：https://github.com/mathruffian-dot/shanshiba-workflow-colab/tree/b7a65d4ecf746e9ceba513cd6994b1a614aedc0a
- 以下是作者在他的環境裡的紀錄，**我們還沒實測**。

### 跟 🅰 唱歌鏡最有關

1. **嘴不動**（rap-battle `references/video-spec.md`）：首幀閉嘴又加上尾幀＝首幀，嘴型會被鎖住；寫 quietly／low voice／stays still 嘴也會變小。作者的做法：先用同場驗證過的首幀，action 寫 `his mouth opens visibly on every syllable`、換 seed，交片前量所有演唱鏡嘴部的逐格變化，挑出最低的幾支。這可能就是我們特寫 0/2 的一部分原因，下次重測可以拿來當對照組。
2. **H3 會自己切鏡**（1–2.4 秒，沒台詞的短反應鏡最常發生）：新增 `tools/clipcheck.py`，逐鏡跟首幀算相關係數，低於 0.7 就標 CHECK。`review_mv.py` 目前沒有這項。
3. **新增 H3 規則**（`docs/03_規則與踩坑.md`、video-spec）：soundscape／setting 不寫 crowd、chatter（會畫出路人）；近景背後要貼牆、門或櫃子，不留空地；慢推最多約 5%；人不要「拿著東西走出畫面」（會變殘影）；只拍手的插入鏡要明寫「只有手和前臂」；限制句加 no flags, banners；H3 念的台詞開頭不放「……」，稱呼後面不標逗號。
4. **Veda 閃屏**：Veda 稀疏注意力會讓整個畫面在第 51／119／187 格閃一下，上游已改成預設關閉。我們的 `colab_mv/tools/h3_shot.py` 只在 spec 明寫 `sparse` 時才開，`colab_mv/inputs/` 也沒有任何 spec 寫了 → 沒中。
5. **控制字元檢查**：上游 h3_shot 會擋 prompt 裡的控制字元（作者因為 regex 替換壞掉，23 行台詞變成亂語）。**11-08 已移植**到 `colab_mv/tools/h3_shot.py` 的 `lint()`（備份 `h3_shot.py.bak-20261108`），本機用假 prompt 驗過：含 `` 的會擋下，正常的照常通過。

### 次要、先記著

- 審片工具：`framecheck.py`（每秒一格總表）、`flashcheck.py`（抓閃屏）。
- 真人感首幀的固定段落（`docs/07` §3b）：只在 Image 2.5 測過；我們多半是黏土／卡通風，參考價值普通。
- Suno 經驗（rap-battle `songs.md`）：長的風格描述標籤幾乎沒用；短標籤 `[Breakdown]`、`[Build-up]` 大約四分之一的版本有效，要多抽；每場換人聲類型。要補進 mv-01 的話，改 dotfiles 正本。
- `poly_check.py`（用教育部辭典查破音字）、`vc_swap.py`（念錯的字局部換聲，用到 MMS_FA，屬 CC BY-NC）：微電影對白可能用得到。
- `colab_plan.py`（估算要開幾台）、同帳號開兩台 G4：都靠 Colab CLI＋G4，我們走瀏覽器＋A100，暫時用不到。

### 還沒做

- ~~把 1、3 寫進規則~~ **11-08 已完成**：寫進 H3 分鏡規格正本 `15_ai共筆工作流/flows/specs/H3分鏡.md`（分流策略 🅰 第 1 步本來就指向它，不重抄）。三方共審第 4 輪全部無意見；三家補的重點是「影片提示詞本來就有人群的鏡頭照寫不刪、在總表加註」，避免跟忠實規則衝突。
- clipcheck 要併進 `review_mv.py` 還是單獨用，等下一支 MV 實際跑過再決定。
