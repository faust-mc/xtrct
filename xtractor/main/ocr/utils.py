import cv2
import pytesseract
import numpy as np
from PIL import Image

# Set your Tesseract path (you already did this)
pytesseract.pytesseract.tesseract_cmd = r"C:\Users\SERVICE UNIT\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"

def extract_table_cells(uploaded_file):
    file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
    img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)


    gry = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blr = cv2.GaussianBlur(gry, (3, 3), 0)
    thr = cv2.threshold(blr, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
    (h_thr, w_thr) = thr.shape[:2]
    s_idx = 0
    e_idx = int(h_thr / 2)

    for _ in range(0, 2):
        crp = thr[s_idx:e_idx, 0:w_thr]
        (h_crp, w_crp) = crp.shape[:2]
        crp = cv2.resize(crp, (w_crp * 2, h_crp * 2))
        crp = cv2.erode(crp, None, iterations=1)
        s_idx = e_idx
        e_idx = s_idx + int(h_thr / 2)
        txt = pytesseract.image_to_string(crp)
        print(txt)
        cv2.imshow("crp", crp)
        cv2.waitKey(0)