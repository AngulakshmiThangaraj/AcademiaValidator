import os
import io
import hashlib
import json
import sys
from PIL import Image, ImageDraw, ImageFont
import cv2
import numpy as np
import qrcode

# Add backend directory to sys.path
backend_dir = os.path.dirname(__file__)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from database import register_certificate, init_db

SAMPLES_DIR = os.path.join(os.path.dirname(__file__), "samples")
os.makedirs(SAMPLES_DIR, exist_ok=True)

def load_font(size=18):
    font_names = ["arial.ttf", "dejavusans.ttf", "calibri.ttf", "liberation-sans.ttf"]
    for font_name in font_names:
        try:
            return ImageFont.truetype(font_name, size)
        except OSError:
            pass
    return ImageFont.load_default()

def draw_seal(draw, center=(425, 940), radius=42):
    cx, cy = center
    draw.ellipse([cx - radius, cy - radius, cx + radius, cy + radius], outline=(180, 40, 40), width=3)
    draw.ellipse([cx - radius + 5, cy - radius + 5, cx + radius - 5, cy + radius - 5], outline=(180, 40, 40), width=1)
    font = load_font(10)
    draw.text((cx - 30, cy - 6), "OFFICIAL SEAL", fill=(180, 40, 40), font=font)

def create_demo_certificates():
    init_db()
    print("Generating preset demo certificates (Certificate A Genuine & Certificate B Manipulated)...")
    
    # -------------------------------------------------------------
    # CERTIFICATE A: Genuine Certificate
    # -------------------------------------------------------------
    width, height = 850, 1100
    img_a = Image.new("RGB", (width, height), (254, 253, 250))
    draw_a = ImageDraw.Draw(img_a)

    # Decorative Border
    draw_a.rectangle([20, 20, width - 20, height - 20], outline=(30, 50, 90), width=4)
    draw_a.rectangle([28, 28, width - 28, height - 28], outline=(190, 160, 70), width=2)

    font_title = load_font(23)
    font_sub = load_font(15)
    font_body = load_font(15)
    font_bold = load_font(15)

    # Header
    draw_a.text((width // 2, 70), "NATIONAL INSTITUTE OF TECHNOLOGY, TIRUCHIRAPPALLI", fill=(20, 35, 75), font=font_title, anchor="mm")
    draw_a.text((width // 2, 105), "OFFICIAL STATEMENT OF MARKS & ACADEMIC TRANSCRIPT", fill=(90, 90, 90), font=font_sub, anchor="mm")
    draw_a.line([(60, 130), (width - 60, 130)], fill=(190, 160, 70), width=2)

    # Student Info
    draw_a.rectangle([60, 150, width - 60, 270], fill=(245, 248, 252), outline=(200, 210, 230), width=1)
    draw_a.text((80, 165), "Student Name   : Rohan Verma", fill=(20, 20, 20), font=font_bold)
    draw_a.text((80, 195), "Register No    : 3122211001", fill=(20, 20, 20), font=font_body)
    draw_a.text((80, 225), "Course         : BACHELOR OF TECHNOLOGY IN COMPUTER SCIENCE & ENGINEERING", fill=(20, 20, 20), font=font_body)
    draw_a.text((550, 165), "Cert ID: CERT-2025-1001", fill=(50, 50, 50), font=font_body)
    draw_a.text((550, 195), "Date   : 15-05-2024", fill=(50, 50, 50), font=font_body)

    # Table Header
    draw_a.rectangle([60, 300, width - 60, 335], fill=(30, 50, 90))
    draw_a.text((80, 308), "Code", fill=(255, 255, 255), font=font_bold)
    draw_a.text((170, 308), "Subject Title", fill=(255, 255, 255), font=font_bold)
    draw_a.text((540, 308), "Credits", fill=(255, 255, 255), font=font_bold)
    draw_a.text((650, 308), "Marks Obtained", fill=(255, 255, 255), font=font_bold)

    subjects = [
        ("CS301", "Data Structures & Algorithms", 4, 92),
        ("CS302", "Database Management Systems", 4, 88),
        ("CS303", "Operating Systems", 3, 85),
        ("CS304", "Computer Networks", 3, 86),
        ("CS305", "Artificial Intelligence & ML", 4, 90),
        ("CS306", "Software Engineering Lab", 2, 94)
    ]

    y = 335
    for code, title, credits, mark in subjects:
        bg = (255, 255, 255) if (y // 35) % 2 == 0 else (248, 250, 254)
        draw_a.rectangle([60, y, width - 60, y + 35], fill=bg, outline=(230, 230, 230))
        draw_a.text((80, y + 8), code, fill=(30, 30, 30), font=font_body)
        draw_a.text((170, y + 8), title, fill=(30, 30, 30), font=font_body)
        draw_a.text((560, y + 8), str(credits), fill=(30, 30, 30), font=font_body)
        draw_a.text((670, y + 8), f"{mark} / 100", fill=(20, 20, 20), font=font_bold)
        y += 35

    # Total CGPA Summary
    draw_a.rectangle([60, y + 10, width - 60, y + 55], fill=(235, 242, 255), outline=(180, 200, 230))
    draw_a.text((80, y + 22), "Total Marks: 535 / 600", fill=(20, 35, 75), font=font_bold)
    draw_a.text((540, y + 22), "CGPA: 8.75 / 10.0", fill=(20, 35, 75), font=font_bold)

    # QR Code for Cert A
    qr_payload_a = json.dumps({
        "cert_id": "CERT-2025-1001",
        "reg_no": "3122211001",
        "name": "Rohan Verma",
        "cgpa": 8.75,
        "hash": "a8f5f167f44f4964e6c998dee827110c"
    })
    qr_a = qrcode.QRCode(box_size=3, border=1)
    qr_a.add_data(qr_payload_a)
    qr_a.make(fit=True)
    qr_img_a = qr_a.make_image(fill_color="black", back_color="white").resize((110, 110))
    img_a.paste(qr_img_a, (80, 900))
    draw_a.text((80, 1020), "Scan to Verify Credential", fill=(80, 80, 80), font=load_font(12))

    draw_seal(draw_a, center=(425, 940), radius=45)
    draw_a.line([(600, 970), (770, 970)], fill=(40, 40, 40), width=2)
    draw_a.text((615, 975), "Controller of Examinations", fill=(60, 60, 60), font=load_font(12))
    draw_a.text((620, 940), "Dr. A. K. Sharma", fill=(20, 30, 90), font=load_font(16))

    path_a = os.path.join(SAMPLES_DIR, "certificate_a_genuine.jpg")
    img_a.save(path_a, quality=95)

    # Compute exact saved file hash
    with open(path_a, "rb") as f_a:
        hash_a = hashlib.sha256(f_a.read()).hexdigest()

    register_certificate(
        cert_id="CERT-2025-1001",
        student_name="Rohan Verma",
        reg_no="3122211001",
        institution="NATIONAL INSTITUTE OF TECHNOLOGY, TIRUCHIRAPPALLI",
        course="BACHELOR OF TECHNOLOGY IN COMPUTER SCIENCE & ENGINEERING",
        cgpa=8.75,
        issue_date="15-05-2024",
        sha256_hash=hash_a
    )

    # -------------------------------------------------------------
    # CERTIFICATE B: Manipulated Certificate (Edited CGPA & Name + Resampled Patch)
    # -------------------------------------------------------------
    img_b_np = np.array(img_a.copy())

    # 1. Tamper CGPA box: erase "CGPA: 8.75 / 10.0" and replace with "CGPA: 9.95 / 10.0" in mismatched font
    cv2.rectangle(img_b_np, (535, y + 15), (780, y + 50), (255, 255, 255), -1)
    cv2.putText(img_b_np, "CGPA: 9.95 / 10.0 (GOLD)", (538, y + 42), cv2.FONT_HERSHEY_DUPLEX, 0.65, (180, 20, 20), 2)

    # 2. Tamper student name
    cv2.rectangle(img_b_np, (215, 160), (450, 188), (245, 248, 252), -1)
    cv2.putText(img_b_np, "Rohan Verma (RANK 1)", (217, 183), cv2.FONT_HERSHEY_COMPLEX_SMALL, 0.85, (0, 0, 0), 2)

    # 3. Tamper CS301 Mark: change 92 to 99 with a high-compression blurry resampled patch
    patch = img_b_np[338:368, 660:735].copy()
    cv2.rectangle(patch, (0, 0), (75, 30), (255, 255, 255), -1)
    cv2.putText(patch, "99 / 100", (2, 22), cv2.FONT_HERSHEY_TRIPLEX, 0.6, (0, 0, 160), 2)
    pil_p = Image.fromarray(patch)
    buf_p = io.BytesIO()
    pil_p.save(buf_p, format="JPEG", quality=20)
    buf_p.seek(0)
    degraded_p = np.array(Image.open(buf_p))
    img_b_np[338:368, 660:735] = degraded_p

    img_b = Image.fromarray(img_b_np)
    path_b = os.path.join(SAMPLES_DIR, "certificate_b_manipulated.jpg")
    img_b.save(path_b, quality=95)

    print(f"Sample Certificate A saved to: {path_a}")
    print(f"Sample Certificate B saved to: {path_b}")
    return path_a, path_b

if __name__ == "__main__":
    create_demo_certificates()
