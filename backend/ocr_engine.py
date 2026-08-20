import re
import cv2
import numpy as np
from PIL import Image

def perform_ocr(image_input):
    """
    Extracts raw text lines from image using EasyOCR, PyTesseract, or OpenCV text region scanner.
    """
    if isinstance(image_input, Image.Image):
        img_np = np.array(image_input)
    else:
        img_np = image_input

    raw_text = ""
    lines_with_boxes = []

    # Strategy 1: PyTesseract
    try:
        import pytesseract
        text = pytesseract.image_to_string(img_np)
        if text and len(text.strip()) > 20:
            raw_text = text
            data = pytesseract.image_to_data(img_np, output_type=pytesseract.Output.DICT)
            n_boxes = len(data['text'])
            for i in range(n_boxes):
                if int(data['conf'][i]) > 30 and data['text'][i].strip():
                    lines_with_boxes.append({
                        "text": data['text'][i],
                        "bbox": [data['left'][i], data['top'][i], data['width'][i], data['height'][i]],
                        "confidence": float(data['conf'][i])
                    })
            return raw_text, lines_with_boxes
    except Exception:
        pass

    # Strategy 2: EasyOCR
    try:
        import easyocr
        reader = easyocr.Reader(['en'], gpu=False)
        results = reader.readtext(img_np)
        text_lines = []
        for bbox, text, prob in results:
            text_lines.append(text)
            xs = [p[0] for p in bbox]
            ys = [p[1] for p in bbox]
            x, y, w, h = int(min(xs)), int(min(ys)), int(max(xs) - min(xs)), int(max(ys) - min(ys))
            lines_with_boxes.append({
                "text": text,
                "bbox": [x, y, w, h],
                "confidence": float(prob * 100)
            })
        raw_text = "\n".join(text_lines)
        if raw_text and len(raw_text.strip()) > 20:
            return raw_text, lines_with_boxes
    except Exception:
        pass

    return raw_text, lines_with_boxes

def parse_certificate_fields(raw_text, qr_payload=None):
    """
    Parses key academic fields from extracted raw OCR text using regex and heuristics,
    falling back to QR code payload values if OCR engine is in lightweight fallback mode.
    """
    fields = {
        "cert_id": None,
        "student_name": None,
        "reg_no": None,
        "institution": None,
        "course": None,
        "cgpa": None,
        "total_marks": None,
        "issue_date": None
    }

    if raw_text:
        # Certificate ID regex
        cert_match = re.search(r'(CERT[-\s]?\d{4}[-\s]?\d{4})', raw_text, re.IGNORECASE)
        if cert_match:
            fields["cert_id"] = cert_match.group(1).replace(" ", "")

        # Register Number regex
        reg_match = re.search(r'(?:Register|Reg)[^\d]*(\d{8,12})', raw_text, re.IGNORECASE)
        if reg_match:
            fields["reg_no"] = reg_match.group(1)
        else:
            digits_match = re.search(r'\b(312\d{7}|\d{10})\b', raw_text)
            if digits_match:
                fields["reg_no"] = digits_match.group(1)

        # Student Name regex
        name_match = re.search(r'(?:Student Name|Name|Name of Candidate)[^\w:]*([A-Za-z\s.]+)', raw_text, re.IGNORECASE)
        if name_match:
            candidate = name_match.group(1).split('\n')[0].strip()
            if len(candidate) > 3:
                fields["student_name"] = candidate

        # Institution
        for inst_kw in ["INSTITUTE OF TECHNOLOGY", "UNIVERSITY", "BITS PILANI"]:
            if inst_kw in raw_text.upper():
                lines = raw_text.split('\n')
                for line in lines:
                    if inst_kw in line.upper():
                        fields["institution"] = line.strip()
                        break

        # Course
        course_match = re.search(r'(BACHELOR OF TECHNOLOGY[^\n]*|B\.TECH[^\n]*)', raw_text, re.IGNORECASE)
        if course_match:
            fields["course"] = course_match.group(1).strip()

        # CGPA
        cgpa_match = re.search(r'CGPA[^\d]*(\d\.\d{1,2})', raw_text, re.IGNORECASE)
        if cgpa_match:
            try:
                fields["cgpa"] = float(cgpa_match.group(1))
            except ValueError:
                pass

        # Date
        date_match = re.search(r'(\d{2}[-/\.]\d{2}[-/\.]\d{4})', raw_text)
        if date_match:
            fields["issue_date"] = date_match.group(1)

    # Fallback to QR Payload fields if present
    if isinstance(qr_payload, dict):
        if not fields["cert_id"] and qr_payload.get("cert_id"):
            fields["cert_id"] = qr_payload["cert_id"]
        if not fields["student_name"] and qr_payload.get("name"):
            fields["student_name"] = qr_payload["name"]
        if not fields["reg_no"] and qr_payload.get("reg_no"):
            fields["reg_no"] = qr_payload["reg_no"]
        if not fields["cgpa"] and qr_payload.get("cgpa"):
            fields["cgpa"] = qr_payload["cgpa"]

    return fields
