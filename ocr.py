import pytesseract
from PIL import Image

# Set this path if needed (Windows)
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def extract_text(image_path):
    text = pytesseract.image_to_string(Image.open(image_path))
    return text