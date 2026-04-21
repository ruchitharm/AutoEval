import os
import pytesseract
from PIL import Image, ImageOps, ImageFilter
from PyPDF2 import PdfReader

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


def preprocess_image(image_path):
    img = Image.open(image_path)

    width, height = img.size

    left = int(width * 0.08)
    top = int(height * 0.18)
    right = int(width * 0.92)
    bottom = int(height * 0.88)
    img = img.crop((left, top, right, bottom))

    img = img.resize((img.width * 2, img.height * 2))

    img = img.convert("L")
    img = ImageOps.autocontrast(img)
    img = img.filter(ImageFilter.MedianFilter())

    threshold = 170
    img = img.point(lambda p: 255 if p > threshold else 0)

    return img


def clean_extracted_text(text):
    lines = text.splitlines()
    cleaned_lines = []

    unwanted_words = [
        "search", "bing", "chatgpt", "github", "upload", "result",
        "dashboard", "history", "logout", "continue reading", "type here"
    ]

    for line in lines:
        line = line.strip()
        if not line:
            continue

        lower_line = line.lower()

        if any(word in lower_line for word in unwanted_words):
            continue

        if len(line) < 3:
            continue

        cleaned_lines.append(line)

    return " ".join(cleaned_lines).strip()


def extract_text(file_path):
    extension = os.path.splitext(file_path)[1].lower()

    if extension in [".png", ".jpg", ".jpeg", ".webp", ".bmp"]:
        processed_img = preprocess_image(file_path)
        config = r"--oem 3 --psm 6"
        text = pytesseract.image_to_string(processed_img, config=config)
        return clean_extracted_text(text)

    elif extension == ".pdf":
        text = ""
        reader = PdfReader(file_path)
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        return clean_extracted_text(text)

    return ""