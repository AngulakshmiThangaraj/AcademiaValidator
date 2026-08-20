import hashlib
import json
import io
import cv2
import numpy as np
from PIL import Image
import qrcode
from database import get_certificate_by_id

def compute_image_sha256(image_bytes):
    """Generates SHA-256 fingerprint of the image bytes."""
    return hashlib.sha256(image_bytes).hexdigest()

def decode_qr_code(image_input):
    """
    Decodes QR code from PIL Image or numpy array using OpenCV QRCodeDetector with pyzbar fallback.
    """
    if isinstance(image_input, Image.Image):
        img_np = np.array(image_input)
    else:
        img_np = image_input

    if len(img_np.shape) == 3 and img_np.shape[2] == 3:
        gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)
    else:
        gray = img_np

    # OpenCV QR Detector
    detector = cv2.QRCodeDetector()
    data, bbox, _ = detector.detectAndDecode(gray)
    if data:
        return data

    # Fallback to pyzbar if available
    try:
        from pyzbar.pyzbar import decode
        decoded = decode(gray)
        if decoded:
            return decoded[0].data.decode("utf-8")
    except Exception:
        pass

    return None

def verify_qr_and_id(qr_data_str, cert_id_from_ocr=None):
    """
    Validates decoded QR code data payload against database registry.
    Returns: (is_valid, decoded_payload, match_details)
    """
    if not qr_data_str:
        return False, None, "No QR Code detected on document"

    try:
        payload = json.loads(qr_data_str)
    except json.JSONDecodeError:
        return False, {"raw_qr": qr_data_str}, "QR code contains unparseable or corrupted payload"

    cert_id = payload.get("cert_id") or cert_id_from_ocr
    if not cert_id:
        return False, payload, "Certificate ID missing from QR payload"

    db_cert = get_certificate_by_id(cert_id)
    if not db_cert:
        return False, payload, f"Certificate ID '{cert_id}' not found in official University Registry"

    # Compare payload details with DB record
    mismatches = []
    if "reg_no" in payload and str(payload["reg_no"]) != str(db_cert["reg_no"]):
        mismatches.append(f"Reg No mismatch (QR: {payload['reg_no']}, DB: {db_cert['reg_no']})")

    if "name" in payload and payload["name"].lower() != db_cert["student_name"].lower():
        mismatches.append(f"Name mismatch (QR: {payload['name']}, DB: {db_cert['student_name']})")

    if "cgpa" in payload and float(payload["cgpa"]) != float(db_cert["cgpa"]):
        mismatches.append(f"CGPA mismatch (QR: {payload['cgpa']}, DB: {db_cert['cgpa']})")

    if mismatches:
        return False, payload, "; ".join(mismatches)

    return True, payload, "QR Code & Registry payload fully verified and matched!"

def generate_secure_qr(cert_id, reg_no, name, cgpa):
    """Generates QR code image for certificate registration."""
    payload = {
        "cert_id": cert_id,
        "reg_no": reg_no,
        "name": name,
        "cgpa": float(cgpa),
        "hash": hashlib.sha256(f"{cert_id}:{reg_no}:{cgpa}".encode()).hexdigest()[:16]
    }
    
    qr = qrcode.QRCode(box_size=4, border=1)
    qr.add_data(json.dumps(payload))
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white")
    
    buf = io.BytesIO()
    qr_img.save(buf, format="PNG")
    return buf.getvalue(), json.dumps(payload)
