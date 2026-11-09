import cv2, os
import numpy as np

MOVIE_PATH = r"C:\Users\user\我的雲端硬碟\Ai Code\10_科技競賽\115學年度\游智盃_南門河\南門河_MV製作\腳底下的小河冒險記_完整有聲微電影_1080p.mp4"
OUT_IMG = r"C:\Users\user\我的雲端硬碟\Ai Code\10_科技競賽\115學年度\游智盃_南門河\南門河_MV製作\movie_render_review.jpg"

# 10 個頁面的抽格秒數（抽在有台詞字幕出現的時間點）
SAMPLE_SECONDS = [
    25.0,   # P1: 小東趴在水溝蓋
    90.0,   # P2: 阿東伯與阿波
    195.0,  # P3: 阿束社自然原野
    280.0,  # P4: 船仔頭碼頭
    360.0,  # P5: 洗衫橋
    440.0,  # P6: 端午龍舟競渡
    530.0,  # P7: 藍蔭鼎與彩色噴泉
    630.0,  # P8: 水泥箱涵加蓋
    720.0,  # P9: 回到現代大石頭踏查
    820.0,  # P10: 電腦教室擊掌
]

cap = cv2.VideoCapture(MOVIE_PATH)
frames = []

for idx, sec in enumerate(SAMPLE_SECONDS, 1):
    cap.set(cv2.CAP_PROP_POS_MSEC, int(sec * 1000))
    ret, frame = cap.read()
    if ret:
        resized = cv2.resize(frame, (640, 360))
        # 標註頁碼與秒數
        cv2.putText(resized, f"Page {idx:02d} ({int(sec//60)}m{int(sec%60)}s)", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 255), 2)
        frames.append(resized)
    else:
        print(f"Failed to sample at {sec}s")

cap.release()

if len(frames) == 10:
    row1 = np.hstack(frames[:5])
    row2 = np.hstack(frames[5:])
    grid = np.vstack([row1, row2])
    
    cv2.imencode(".jpg", grid, [cv2.IMWRITE_JPEG_QUALITY, 92])[1].tofile(OUT_IMG)
    cv2.imencode(".jpg", grid, [cv2.IMWRITE_JPEG_QUALITY, 92])[1].tofile("scripts/movie_render_review.jpg")
    print(f"Review contact sheet saved: {OUT_IMG} ({grid.shape[1]}x{grid.shape[0]})")
