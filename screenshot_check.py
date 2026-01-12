import os
import pdfplumber
from PIL import Image
import imagehash
from io import BytesIO
import numpy as np

def extract_images(pdf_path):
    images = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                for img in page.images:
                    try:
                        image_data = page.extract_image(img)["image"]
                        img_obj = Image.open(BytesIO(image_data)).convert("RGB")
                        images.append(img_obj)
                    except:
                        pass
    except:
        pass
    return images


def is_blank(img):
    arr = np.array(img)
    if arr.std() < 3:
        return True
    return False


def analyze_screenshots(pdf_files):
    all_hashes = {}
    report = {}

    for pdf in pdf_files:
        imgs = extract_images(pdf)
        if not imgs:
            report[pdf] = {"status": "NONE", "hashes": []}
            continue

        hashes = []
        blank_count = 0
        for im in imgs:
            if is_blank(im):
                blank_count += 1
            h = str(imagehash.phash(im))
            hashes.append(h)

        if blank_count == len(imgs):
            report[pdf] = {"status": "BLANK", "hashes": hashes}
        else:
            report[pdf] = {"status": "OK", "hashes": hashes}

        all_hashes[pdf] = hashes

    # detect duplicates
    duplicates = {}
    for f1 in all_hashes:
        for f2 in all_hashes:
            if f1 != f2:
                shared = set(all_hashes[f1]) & set(all_hashes[f2])
                if shared:
                    duplicates.setdefault(f1, set()).add(f2)

    return report, duplicates
