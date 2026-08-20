import os
import random
import io
import json
import hashlib
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops
import qrcode
import cv2
import numpy as np

DATASET_DIR = os.path.join(os.path.dirname(__file__), "data")
GENUINE_DIR = os.path.join(DATASET_DIR, "genuine")
FORGED_DIR = os.path.join(DATASET_DIR, "forged")

os.makedirs(GENUINE_DIR, exist_ok=True)
os.makedirs(FORGED_DIR, exist_ok=True)

INSTITUTIONS = [
    "NATIONAL INSTITUTE OF TECHNOLOGY, TIRUCHIRAPPALLI",
    "INDIAN INSTITUTE OF TECHNOLOGY, MADRAS",
    "ANNA UNIVERSITY, CHENNAI",
    "BITS PILANI, HYDERABAD CAMPUS",
    "VELLORE INSTITUTE OF TECHNOLOGY, VELLORE"
]

COURSES = [
    "BACHELOR OF TECHNOLOGY IN COMPUTER SCIENCE & ENGINEERING",
    "BACHELOR OF TECHNOLOGY IN ELECTRONICS & COMMUNICATION",
    "BACHELOR OF TECHNOLOGY IN MECHANICAL ENGINEERING",
    "BACHELOR OF TECHNOLOGY IN INFORMATION TECHNOLOGY"
]

FIRST_NAMES = ["Rohan", "Priya", "Arjun", "Ananya", "Karthik", "Divya", "Siddharth", "Meera", "Vikram", "Sneha", "Aditya", "Pooja", "Rahul", "Nisha"]
LAST_NAMES = ["Sharma", "Verma", "Rao", "Nair", "Iyer", "Gupta", "Patel", "Reddy", "Singh", "Subramanian", "Joshi", "Chatterjee"]

SUBJECTS = [
    ("CS301", "Data Structures & Algorithms", 4),
    ("CS302", "Database Management Systems", 4),
    ("CS303", "Operating Systems", 3),
    ("CS304", "Computer Networks", 3),
    ("CS305", "Artificial Intelligence & ML", 4),
    ("CS306", "Software Engineering Lab", 2)
]

def load_font(size=18, bold=False):
    font_names = ["arial.ttf", "dejavusans.ttf", "calibri.ttf", "liberation-sans.ttf"]
    for font_name in font_names:
        try:
            return ImageFont.truetype(font_name, size)
        except OSError:
            pass
    return ImageFont.load_default()

def draw_watermark(image, text="OFFICIAL ACADEMIC TRANSCRIPT"):
    txt_img = Image.new("RGBA", image.size, (255, 255, 255, 0))
    d = ImageDraw.Draw(txt_img)
    font = load_font(40)
    d.text((120, 450), text, fill=(200, 210, 230, 40), font=font)
    txt_img = txt_img.rotate(25, resample=Image.BICUBIC)
    return Image.alpha_composite(image.convert("RGBA"), txt_img).convert("RGB")

def draw_seal(draw, center=(700, 950), radius=50):
    cx, cy = center
    draw.ellipse([cx - radius, cy - radius, cx + radius, cy + radius], outline=(180, 40, 40), width=3)
    draw.ellipse([cx - radius + 6, cy - radius + 6, cx + radius - 6, cy + radius - 6], outline=(180, 40, 40), width=1)
    font = load_font(11, bold=True)
    draw.text((cx - 32, cy - 8), "SEAL OF EXCELLENCE", fill=(180, 40, 40), font=font)

def generate_certificate(cert_id, student_name, reg_no, inst, course, marks_dict, date_str, is_forged=False):
    width, height = 850, 1100
    img = Image.new("RGB", (width, height), (253, 252, 248))
    draw = ImageDraw.Draw(img)

    # Decorative Border
    draw.rectangle([20, 20, width - 20, height - 20], outline=(40, 60, 100), width=4)
    draw.rectangle([28, 28, width - 28, height - 28], outline=(180, 150, 80), width=2)

    # Header
    font_title = load_font(24)
    font_subtitle = load_font(16)
    font_body = load_font(15)
    font_body_bold = load_font(15)

    # Institution
    draw.text((width // 2, 70), inst, fill=(20, 35, 75), font=font_title, anchor="mm")
    draw.text((width // 2, 105), "OFFICIAL STATEMENT OF MARKS & ACADEMIC CREDENTIAL", fill=(100, 100, 100), font=font_subtitle, anchor="mm")
    draw.line([(60, 130), (width - 60, 130)], fill=(180, 150, 80), width=2)

    # Student Info Box
    draw.rectangle([60, 150, width - 60, 270], fill=(245, 247, 250), outline=(210, 215, 225), width=1)
    draw.text((80, 165), f"Student Name   : {student_name}", fill=(20, 20, 20), font=font_body_bold)
    draw.text((80, 195), f"Register No    : {reg_no}", fill=(20, 20, 20), font=font_body)
    draw.text((80, 225), f"Course         : {course}", fill=(20, 20, 20), font=font_body)
    draw.text((550, 165), f"Cert ID: {cert_id}", fill=(60, 60, 60), font=font_body)
    draw.text((550, 195), f"Date   : {date_str}", fill=(60, 60, 60), font=font_body)

    # Marks Table Header
    table_top = 300
    draw.rectangle([60, table_top, width - 60, table_top + 35], fill=(40, 60, 100))
    draw.text((80, table_top + 8), "Code", fill=(255, 255, 255), font=font_body_bold)
    draw.text((170, table_top + 8), "Subject Title", fill=(255, 255, 255), font=font_body_bold)
    draw.text((540, table_top + 8), "Credits", fill=(255, 255, 255), font=font_body_bold)
    draw.text((650, table_top + 8), "Marks Obtained", fill=(255, 255, 255), font=font_body_bold)

    y = table_top + 35
    total_marks = 0
    max_marks = len(SUBJECTS) * 100

    for code, title, credits in SUBJECTS:
        mark = marks_dict[code]
        total_marks += mark
        bg_col = (255, 255, 255) if (y // 35) % 2 == 0 else (248, 249, 252)
        draw.rectangle([60, y, width - 60, y + 35], fill=bg_col, outline=(230, 230, 230))
        draw.text((80, y + 8), code, fill=(30, 30, 30), font=font_body)
        draw.text((170, y + 8), title, fill=(30, 30, 30), font=font_body)
        draw.text((560, y + 8), str(credits), fill=(30, 30, 30), font=font_body)
        
        # Draw mark
        draw.text((670, y + 8), f"{mark} / 100", fill=(20, 20, 20), font=font_body_bold)
        y += 35

    # Total Summary Box
    draw.rectangle([60, y + 10, width - 60, y + 55], fill=(235, 240, 250), outline=(180, 195, 220))
    cgpa = round((total_marks / max_marks) * 10, 2)
    draw.text((80, y + 22), f"Total Marks: {total_marks} / {max_marks}", fill=(20, 35, 75), font=font_body_bold)
    draw.text((540, y + 22), f"CGPA: {cgpa} / 10.0", fill=(20, 35, 75), font=font_body_bold)

    # Watermark background
    img = draw_watermark(img)
    draw = ImageDraw.Draw(img)

    # QR Code Generation (Genuine payload vs tampered)
    qr_data = json.dumps({
        "cert_id": cert_id,
        "reg_no": reg_no,
        "name": student_name,
        "cgpa": cgpa,
        "hash": hashlib.sha256(f"{cert_id}:{reg_no}:{cgpa}".encode()).hexdigest()[:16]
    })
    
    if is_forged and random.random() < 0.4:
        # Tamper QR code payload string mismatch
        qr_data = "INVALID_PAYLOAD_TAMPERED_QR_CODE"

    qr = qrcode.QRCode(box_size=3, border=1)
    qr.add_data(qr_data)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white").resize((110, 110))
    img.paste(qr_img, (80, 900))
    draw.text((80, 1020), "Scan to Verify", fill=(80, 80, 80), font=load_font(12))

    # Official Seal and Signatures
    draw_seal(draw, center=(425, 950), radius=45)

    # Controller of Examinations Signature Line
    draw.line([(600, 970), (770, 970)], fill=(40, 40, 40), width=2)
    draw.text((615, 975), "Registrar / Controller", fill=(60, 60, 60), font=load_font(12))
    # Simulated Cursive Signature
    draw.text((620, 940), "Dr. A. K. Sharma", fill=(20, 30, 90), font=load_font(16, bold=True))

    # Convert to numpy array for image manipulation if forged
    if is_forged:
        img_np = np.array(img)
        
        tamper_type = random.choice(["altered_text", "copy_paste_patch", "font_mismatch", "ela_compression_patch"])
        
        if tamper_type == "altered_text":
            # Tamper a mark region (e.g. overlaying a new score with mismatched font and offset)
            cv2.rectangle(img_np, (665, 342), (730, 365), (255, 255, 255), -1)
            cv2.putText(img_np, "99 / 100", (666, 361), cv2.FONT_HERSHEY_TRIPLEX, 0.55, (10, 10, 150), 2)
        elif tamper_type == "copy_paste_patch":
            # Copy a seal or mark block and paste elsewhere with slight offset/artifact
            patch = img_np[340:375, 660:740].copy()
            # Paste patch over CGPA area with mismatch
            img_np[y + 15:y + 50, 530:610] = cv2.GaussianBlur(patch, (3, 3), 0)
            cv2.rectangle(img_np, (530, y + 15), (610, y + 50), (200, 50, 50), 1)
        elif tamper_type == "font_mismatch":
            # Tamper name block
            cv2.rectangle(img_np, (200, 160), (450, 188), (245, 247, 250), -1)
            cv2.putText(img_np, "Rohan Verma (MOD)", (202, 182), cv2.FONT_HERSHEY_COMPLEX_SMALL, 0.9, (0, 0, 0), 2)
        elif tamper_type == "ela_compression_patch":
            # Insert high-compression resampled artifact on register number
            patch = img_np[190:220, 200:350]
            pil_patch = Image.fromarray(patch)
            buffer = io.BytesIO()
            pil_patch.save(buffer, format="JPEG", quality=30)
            buffer.seek(0)
            degraded_patch = np.array(Image.open(buffer))
            img_np[190:220, 200:350] = degraded_patch
            
        img = Image.fromarray(img_np)

    return img

def create_dataset(num_samples=300):
    print(f"Generating {num_samples} academic document dataset...")
    records = []
    
    for i in range(num_samples):
        is_forged = (i % 2 == 1)
        cert_id = f"CERT-2025-{1000 + i}"
        name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
        reg_no = f"312221{random.randint(1000, 9999)}"
        inst = random.choice(INSTITUTIONS)
        course = random.choice(COURSES)
        date_str = f"{random.randint(10, 28):02d}-05-2024"
        
        marks_dict = {code: random.randint(65, 95) for code, title, credits in SUBJECTS}
        
        img = generate_certificate(cert_id, name, reg_no, inst, course, marks_dict, date_str, is_forged=is_forged)
        
        target_dir = FORGED_DIR if is_forged else GENUINE_DIR
        filename = f"{'forged' if is_forged else 'genuine'}_{i:04d}.jpg"
        filepath = os.path.join(target_dir, filename)
        
        # Save as JPEG with 95% quality
        img.save(filepath, format="JPEG", quality=95)
        
        records.append({
            "filename": filename,
            "filepath": filepath,
            "cert_id": cert_id,
            "student_name": name,
            "reg_no": reg_no,
            "institution": inst,
            "course": course,
            "is_forged": is_forged
        })
        
    metadata_file = os.path.join(DATASET_DIR, "dataset_metadata.json")
    with open(metadata_file, "w") as f:
        json.dump(records, f, indent=2)
        
    print(f"Dataset generated successfully! Total samples: {num_samples} ({num_samples//2} Genuine, {num_samples - num_samples//2} Forged)")

if __name__ == "__main__":
    create_dataset(300)
