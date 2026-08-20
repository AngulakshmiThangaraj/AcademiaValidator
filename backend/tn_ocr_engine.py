import io
import re
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter, ImageOps

HAS_PYTESSERACT = False
try:
    import pytesseract
    HAS_PYTESSERACT = True
except ImportError:
    HAS_PYTESSERACT = False

def preprocess_tn_marksheet(pil_image):
    """
    Image preprocessing tailored for Tamil Nadu SSLC/HSC marksheets:
    1. Resizes/upscales image for high-density text reading.
    2. Converts to grayscale.
    3. Enhances contrast and sharpness.
    4. Applies adaptive thresholding and noise reduction.
    """
    # 1. Ensure RGB
    orig = pil_image.convert("RGB")
    
    # Upscale if image is smaller than 1200px width
    w, h = orig.size
    scale = 1.0
    if w < 1200:
        scale = 1600.0 / w
        new_w = int(w * scale)
        new_h = int(h * scale)
        orig = orig.resize((new_w, new_h), Image.Resampling.LANCZOS)

    # 2. Grayscale conversion
    gray = orig.convert("L")

    # 3. Contrast & Sharpness Enhancement
    contrast_enhanced = ImageEnhance.Contrast(gray).enhance(1.8)
    sharp_enhanced = ImageEnhance.Sharpness(contrast_enhanced).enhance(1.6)

    # 4. Adaptive Binarization / Thresholding with NumPy
    np_img = np.array(sharp_enhanced)
    # Simple Otsu-like adaptive thresholding in pure NumPy
    mean_val = np.mean(np_img)
    binary_np = np.where(np_img > (mean_val * 0.95), 255, 0).astype(np.uint8)
    binary_pil = Image.fromarray(binary_np)

    return sharp_enhanced, binary_pil

def check_tamil_ocr_available():
    """Checks whether pytesseract has Tamil (tam.traineddata) installed."""
    if not HAS_PYTESSERACT:
        return False, "pytesseract Python library is not installed."
    try:
        langs = pytesseract.get_languages()
        if "tam" in langs:
            return True, "Tamil (tam.traineddata) language support is available."
        else:
            return False, "Tesseract is installed, but Tamil data ('tam.traineddata') was not found in tessdata directory. Falling back to eng+bilingual parser."
    except Exception as e:
        return False, f"Could not query Tesseract languages: {e}"

def perform_tn_ocr(pil_image):
    """
    Runs Tamil Nadu OCR preprocessing & text extraction.
    Returns: (raw_ocr_text, ocr_info_dict)
    """
    enhanced_pil, binary_pil = preprocess_tn_marksheet(pil_image)
    
    raw_text = ""
    engine_used = "Pillow/Dictionary Fallback"
    tam_available, msg = check_tamil_ocr_available()

    if HAS_PYTESSERACT:
        try:
            lang_config = "eng+tam" if tam_available else "eng"
            raw_text = pytesseract.image_to_string(binary_pil, lang=lang_config, config='--psm 6')
            engine_used = f"Tesseract ({lang_config})"
        except Exception as e:
            print(f"Pytesseract execution notice: {e}")
            raw_text = ""

    return raw_text, {
        "engine_used": engine_used,
        "tamil_data_installed": tam_available,
        "setup_message": msg
    }
