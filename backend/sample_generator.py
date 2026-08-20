import os
import io
import hashlib
import json
import sys
import tempfile
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import qrcode

backend_dir = os.path.dirname(__file__)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from database import register_certificate, init_db

if os.access(backend_dir, os.W_OK):
    SAMPLES_DIR = os.path.join(backend_dir, "samples")
else:
    SAMPLES_DIR = os.path.join(tempfile.gettempdir(), "samples")

try:
    os.makedirs(SAMPLES_DIR, exist_ok=True)
except Exception:
    pass

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
    try:
        init_db()
    except Exception as e:
        print(f"Init DB notice: {e}")

    width, height = 850, 1100

    img_a = Image.new("RGB", (width, height), (254, 253, 250))
    draw_a = ImageDraw.Draw(img_a)

    draw_a.rectangle([20, 20, width - 20, height - 20], outline=(30, 50, 90), width=4)
    draw_a.rectangle([28, 28, width - 28, height - 28], outline=(190, 160, 70), width=2)

    font_title = load_font(23)
    font_sub = load_font(15)
    font_body = load_font(15)
    font_bold = load_font(15)

    draw_a.text((width // 2, 70), "NATIONAL INSTITUTE OF TECHNOLOGY, TIRUCHIRAPPALLI", fill=(20, 35, 75), font=font_title, anchor="mm")
    draw_a.text((width // 2, 105), "OFFICIAL STATEMENT OF MARKS & ACADEMIC TRANSCRIPT", fill=(90, 90, 90), font=font_sub, anchor="mm")
    draw_a.line([(60, 130), (width - 60, 130)], fill=(190, 160, 70), width=2)

    draw_a.rectangle([60, 150, width - 60, 270], fill=(245, 248, 252), outline=(200, 210, 230), width=1)
    draw_a.text((80, 165), "Student Name   : Rohan Verma", fill=(20, 20, 20), font=font_bold)
    draw_a.text((80, 195), "Register No    : 3122211001", fill=(20, 20, 20), font=font_body)
    draw_a.text((80, 225), "Course         : BACHELOR OF TECHNOLOGY IN COMPUTER SCIENCE & ENGINEERING", fill=(20, 20, 20), font=font_body)
    draw_a.text((550, 165), "Cert ID: CERT-2025-1001", fill=(50, 50, 50), font=font_body)
    draw_a.text((550, 195), "Date   : 15-05-2024", fill=(50, 50, 50), font=font_body)

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

    draw_a.rectangle([60, y + 10, width - 60, y + 55], fill=(235, 242, 255), outline=(180, 200, 230))
    draw_a.text((80, y + 22), "Total Marks: 535 / 600", fill=(20, 35, 75), font=font_bold)
    draw_a.text((540, y + 22), "CGPA: 8.75 / 10.0", fill=(20, 35, 75), font=font_bold)

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

    buf_a = io.BytesIO()
    img_a.save(buf_a, format="JPEG", quality=95)
    bytes_a = buf_a.getvalue()
    hash_a = hashlib.sha256(bytes_a).hexdigest()

    try:
        path_a = os.path.join(SAMPLES_DIR, "certificate_a_genuine.jpg")
        with open(path_a, "wb") as f:
            f.write(bytes_a)
    except Exception:
        pass

    try:
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
    except Exception:
        pass

    img_b = img_a.copy()
    draw_b = ImageDraw.Draw(img_b)

    draw_b.rectangle([535, y + 15, 780, y + 50], fill=(255, 255, 255))
    draw_b.text((538, y + 20), "CGPA: 9.95 / 10.0 (GOLD)", fill=(180, 20, 20), font=font_bold)
    draw_b.rectangle([215, 160, 450, 188], fill=(245, 248, 252))
    draw_b.text((217, 165), "Rohan Verma (RANK 1)", fill=(0, 0, 0), font=font_bold)
    draw_b.rectangle([660, 338, 735, 368], fill=(255, 255, 255))
    draw_b.text((662, 342), "99 / 100", fill=(0, 0, 160), font=font_bold)

    buf_b = io.BytesIO()
    img_b.save(buf_b, format="JPEG", quality=95)
    bytes_b = buf_b.getvalue()

    try:
        path_b = os.path.join(SAMPLES_DIR, "certificate_b_manipulated.jpg")
        with open(path_b, "wb") as f:
            f.write(bytes_b)
    except Exception:
        pass

    return img_a, img_b

def create_tn_sslc_sample(preset_type="tn_sslc_genuine"):
    """
    Generates Tamil Nadu State Board SSLC Marksheet image.
    Genuine: ANGULAKSHMI T (Cert ID: 88880001, Reg: 77770001, Total: 451)
    Manipulated: Altered Total Marks to 499 (discrepancy detected).
    """
    width, height = 850, 1100
    img = Image.new("RGB", (width, height), (255, 253, 248))
    draw = ImageDraw.Draw(img)

    draw.rectangle([15, 15, width - 15, height - 15], outline=(140, 30, 30), width=4)
    draw.rectangle([22, 22, width - 22, height - 22], outline=(200, 160, 60), width=2)

    font_title = load_font(20)
    font_sub = load_font(14)
    font_body = load_font(13)
    font_bold = load_font(14)

    draw.text((width // 2, 50), "GOVERNMENT OF TAMIL NADU", fill=(140, 30, 30), font=font_title, anchor="mm")
    draw.text((width // 2, 78), "DIRECTORATE OF GOVERNMENT EXAMINATIONS, CHENNAI", fill=(30, 30, 30), font=font_sub, anchor="mm")
    draw.text((width // 2, 104), "SSLC MARKSHEET / இடைநிலைப் பள்ளி விடுப்புச் சான்றிதழ்", fill=(10, 60, 130), font=font_bold, anchor="mm")
    draw.line([(50, 125), (width - 50, 125)], fill=(200, 160, 60), width=2)

    cert_id_str = "88880001"
    draw.text((580, 138), f"CERTIFICATE NO : {cert_id_str}", fill=(180, 20, 20), font=font_bold)
    draw.text((580, 158), "SESSION : APR 2023", fill=(40, 40, 40), font=font_body)

    draw.rectangle([50, 185, width - 50, 310], fill=(248, 250, 255), outline=(180, 200, 230), width=1)
    
    name_str = "ANGULAKSHMI T"
    reg_str = "77770001"

    draw.text((70, 200), f"NAME OF CANDIDATE  : {name_str}", fill=(20, 20, 20), font=font_bold)
    draw.text((70, 226), f"REGISTER NUMBER    : {reg_str}", fill=(20, 20, 20), font=font_bold)
    draw.text((70, 252), "DATE OF BIRTH      : 07/07/2007", fill=(20, 20, 20), font=font_body)
    draw.text((70, 278), "FATHER'S NAME      : THANGARAJ A", fill=(20, 20, 20), font=font_body)

    draw.text((500, 200), "COURSE : SSLC", fill=(20, 20, 20), font=font_body)
    draw.text((500, 226), "MOTHER : CHITHRA T", fill=(20, 20, 20), font=font_body)
    draw.text((500, 252), "SCHOOL : GOVT HIGHER SECONDARY SCHOOL", fill=(20, 20, 20), font=font_body)

    draw.rectangle([50, 335, width - 50, 370], fill=(140, 30, 30))
    draw.text((70, 345), "SUBJECT CODE & TITLE", fill=(255, 255, 255), font=font_bold)
    draw.text((450, 345), "MAX MARKS", fill=(255, 255, 255), font=font_bold)
    draw.text((620, 345), "MARKS OBTAINED", fill=(255, 255, 255), font=font_bold)

    subjects = [
        ("01 TAMIL", 100, 88),
        ("02 ENGLISH", 100, 85),
        ("03 MATHEMATICS", 100, 92),
        ("04 SCIENCE", 100, 94),
        ("05 SOCIAL SCIENCE", 100, 92)
    ]

    y = 370
    for code_title, max_m, obt in subjects:
        bg = (255, 255, 255) if (y // 40) % 2 == 0 else (250, 252, 255)
        draw.rectangle([50, y, width - 50, y + 40], fill=bg, outline=(220, 220, 220))
        draw.text((70, y + 10), code_title, fill=(30, 30, 30), font=font_body)
        draw.text((470, y + 10), str(max_m), fill=(30, 30, 30), font=font_body)
        draw.text((640, y + 10), f"{obt:03d}  P", fill=(20, 20, 20), font=font_bold)
        y += 40

    total_val = 451 if preset_type == "tn_sslc_genuine" else 499
    draw.rectangle([50, y + 15, width - 50, y + 65], fill=(240, 245, 255), outline=(160, 180, 220), width=2)
    draw.text((70, y + 28), "GRAND TOTAL : FIVE SUBJECTS", fill=(30, 30, 30), font=font_bold)

    total_color = (20, 35, 75) if preset_type == "tn_sslc_genuine" else (180, 20, 20)
    draw.text((550, y + 28), f"TOTAL MARKS: {total_val} / 500   RESULT: PASS", fill=total_color, font=font_bold)

    # Embed Normalized QR Code payload
    qr_payload = "TNSSLC|88880001|77770001|ANGULAKSHMI T|APR 2023"
    qr = qrcode.QRCode(box_size=3, border=1)
    qr.add_data(qr_payload)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white").resize((120, 120))
    img.paste(qr_img, (70, 900))
    draw.text((70, 1030), "Scan to Verify TN Registry", fill=(80, 80, 80), font=load_font(11))

    draw_seal(draw, center=(425, 950), radius=45)
    draw.line([(600, 980), (780, 980)], fill=(40, 40, 40), width=2)
    draw.text((615, 986), "DIRECTOR OF GOVT EXAMINATIONS", fill=(60, 60, 60), font=load_font(11))

    return img

def get_demo_certificate_bytes(preset_type):
    """Returns sample image bytes in memory for presets."""
    if preset_type in ["tn_sslc_genuine", "tn_sslc_manipulated"]:
        img = create_tn_sslc_sample(preset_type)
    else:
        img_a, img_b = create_demo_certificates()
        img = img_a if preset_type == "genuine" else img_b

    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=95)
    return buf.getvalue()

if __name__ == "__main__":
    create_demo_certificates()
