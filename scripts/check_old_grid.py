import cv2, os, glob
import numpy as np

old_dir = r"C:\Users\user\我的雲端硬碟\Ai Code\10_科技競賽\115學年度\游智盃_南門河\南門河_MV製作\videos-raw\_old_mismatched"
imgs = []
for i in range(1, 11):
    f = os.path.join(old_dir, f"p{i:02d}_flow.mp4")
    if os.path.exists(f):
        cap = cv2.VideoCapture(f)
        cap.set(cv2.CAP_PROP_POS_MSEC, 3000)
        ret, frame = cap.read()
        cap.release()
        if ret:
            img = cv2.resize(frame, (480, 270))
            cv2.putText(img, f"old_p{i:02d}", (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 255), 3)
            imgs.append(img)
        else:
            print(f"Failed to read frame from {f}")

print(f"Read {len(imgs)} images")
if len(imgs) == 10:
    row1 = np.hstack(imgs[:5])
    row2 = np.hstack(imgs[5:])
    grid = np.vstack([row1, row2])
    out_file = r"scripts\all_old_previews.jpg"
    cv2.imencode(".jpg", grid)[1].tofile(out_file)
    print("Saved to scripts/all_old_previews.jpg")
