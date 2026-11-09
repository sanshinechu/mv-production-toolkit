import cv2, os
import numpy as np
from PIL import Image, ImageDraw, ImageFont

VIDEO_DIR = r"C:\Users\user\我的雲端硬碟\Ai Code\10_科技競賽\115學年度\游智盃_南門河\南門河_MV製作\videos-raw"
OUT_IMG = os.path.join(VIDEO_DIR, "all_shots_review_10.jpg")

TITLES = [
    ("p01", "水溝好奇 (尋聲)"),
    ("p02", "船仔頭老爺與精靈"),
    ("p03", "阿束社自然溪流"),
    ("p04", "木造碼頭林業貨運"),
    ("p05", "洗衣埠生活常民"),
    ("p06", "端午龍舟競渡盛況"),
    ("p07", "翻閱南門河老畫冊"),
    ("p08", "水泥箱涵加蓋封存"),
    ("p09", "解開被封印的秘密"),
    ("p10", "電腦教室寫下新篇"),
]

def make_review_grid():
    frames = []
    # 嘗試找中文字型
    font_path = "C:/Windows/Fonts/msjhbd.ttc"  # 微軟正黑體粗體
    if not os.path.exists(font_path):
        font_path = "C:/Windows/Fonts/msjh.ttc"

    for i in range(1, 11):
        vpath = os.path.join(VIDEO_DIR, f"p{i:02d}_flow.mp4")
        cap = cv2.VideoCapture(vpath)
        # 抽第 4 秒
        cap.set(cv2.CAP_PROP_POS_MSEC, 4000)
        ret, frame = cap.read()
        cap.release()
        if not ret:
            print(f"Error reading p{i:02d}")
            continue

        # 縮放到 640x360
        resized = cv2.resize(frame, (640, 360))
        # 轉 RGB 使用 PIL 繪製中文
        rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(rgb)
        draw = ImageDraw.Draw(pil_img)
        
        font = ImageFont.truetype(font_path, 26)
        label_text = f"p{i:02d} | {TITLES[i-1][1]}"
        
        # 繪製陰影背景框
        bbox = draw.textbbox((15, 15), label_text, font=font)
        draw.rectangle([bbox[0]-5, bbox[1]-3, bbox[2]+5, bbox[3]+3], fill=(0, 0, 0, 180))
        draw.text((15, 15), label_text, fill=(255, 255, 0), font=font)
        
        bgr_res = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
        frames.append(bgr_res)

    row1 = np.hstack(frames[:5])
    row2 = np.hstack(frames[5:])
    grid = np.vstack([row1, row2])
    
    # 寫入 OUT_IMG
    cv2.imencode(".jpg", grid, [cv2.IMWRITE_JPEG_QUALITY, 95])[1].tofile(OUT_IMG)
    # 同步複製一份到 scripts 目錄方便直接檢視
    cv2.imencode(".jpg", grid, [cv2.IMWRITE_JPEG_QUALITY, 95])[1].tofile("scripts/all_shots_review_10.jpg")
    print(f"Saved review grid: {OUT_IMG} and scripts/all_shots_review_10.jpg ({grid.shape[1]}x{grid.shape[0]})")

if __name__ == "__main__":
    make_review_grid()
