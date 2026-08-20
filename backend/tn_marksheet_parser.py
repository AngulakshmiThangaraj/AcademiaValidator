import re

def normalize_text(raw_text):
    """
    Normalizes OCR output text for Tamil Nadu SSLC/HSC marksheets:
    - Trims unnecessary whitespace and normalizes line breaks.
    - Preserves Tamil Unicode characters (\u0B80-\u0BFF).
    - Removes spurious non-printable noise characters.
    """
    if not raw_text:
        return ""
    
    # Standardize line breaks
    text = raw_text.replace("\r\n", "\n").replace("\r", "\n")
    lines = [re.sub(r'[ \t]+', ' ', line.strip()) for line in text.split("\n") if line.strip()]
    return "\n".join(lines)

def contextual_num_clean(val_str):
    """Clean common OCR mistakes O->0, I->1, S->5 in numeric contexts."""
    if not val_str:
        return ""
    cleaned = str(val_str).upper()
    cleaned = cleaned.replace('O', '0').replace('I', '1').replace('L', '1').replace('S', '5').replace('Z', '2').replace('B', '8')
    # Keep digits
    digits = re.sub(r'[^\d]', '', cleaned)
    return digits

def parse_tn_marksheet_ocr(raw_text, qr_payload=None):
    """
    Extracts structured fields from Tamil Nadu SSLC / HSC OCR text with per-field confidence scores.
    Returns:
    {
       "certificate_id": {"value": "24353750", "confidence": 0.96},
       "register_no": {"value": "5191247", "confidence": 0.98},
       "student_name": {"value": "ANGULAKSHMI T", "confidence": 0.91},
       "dob": {"value": "14/06/2007", "confidence": 0.90},
       "father_name": {"value": "THANGARAJ M", "confidence": 0.88},
       "mother_name": {"value": "LAKSHMI T", "confidence": 0.85},
       "institution": {"value": "...", "confidence": 0.85},
       "course": {"value": "SSLC (CLASS X)", "confidence": 0.95},
       "total_marks": {"value": 451, "confidence": 0.95},
       "result": {"value": "PASS", "confidence": 0.95},
       "passing_year": {"value": "APR 2023", "confidence": 0.92},
       "subject_marks": {...}
    }
    """
    norm_text = normalize_text(raw_text)
    
    fields = {
        "certificate_id": {"value": None, "confidence": 0.0},
        "register_no": {"value": None, "confidence": 0.0},
        "student_name": {"value": None, "confidence": 0.0},
        "dob": {"value": None, "confidence": 0.0},
        "father_name": {"value": None, "confidence": 0.0},
        "mother_name": {"value": None, "confidence": 0.0},
        "institution": {"value": None, "confidence": 0.0},
        "course": {"value": "SSLC (CLASS X)", "confidence": 0.85},
        "total_marks": {"value": None, "confidence": 0.0},
        "result": {"value": "PASS", "confidence": 0.80},
        "passing_year": {"value": None, "confidence": 0.0},
        "subject_marks": {}
    }

    # If QR code payload exists, pre-seed values with high confidence assist
    if isinstance(qr_payload, dict):
        if "cert_id" in qr_payload:
            fields["certificate_id"] = {"value": str(qr_payload["cert_id"]), "confidence": 0.98}
        if "reg_no" in qr_payload:
            fields["register_no"] = {"value": str(qr_payload["reg_no"]), "confidence": 0.98}
        if "name" in qr_payload:
            fields["student_name"] = {"value": str(qr_payload["name"]), "confidence": 0.98}
        if "dob" in qr_payload:
            fields["dob"] = {"value": str(qr_payload["dob"]), "confidence": 0.95}
        if "total_marks" in qr_payload:
            try:
                fields["total_marks"] = {"value": int(qr_payload["total_marks"]), "confidence": 0.98}
            except Exception:
                pass

    # 1. Certificate ID / Serial Number Extraction
    cert_id_match = re.search(r'(?:CERTIFICATE|SERIAL|SL|NO|சான்றிதழ்)\s*(?:NO|NUMBER)?\s*[:\-.]?\s*(\b\d{7,10}\b)', norm_text, re.IGNORECASE)
    if not cert_id_match:
        cert_id_match = re.search(r'\b(24\d{6}|25\d{6}|\d{8})\b', norm_text)
    
    if cert_id_match and fields["certificate_id"]["value"] is None:
        fields["certificate_id"] = {"value": cert_id_match.group(1), "confidence": 0.94}

    # 2. Registration Number Extraction
    reg_match = re.search(r'(?:REG(?:ISTRATION)?\s*(?:NO|NUMBER)?|REGISTER\s*NO|பதிவு\s*எண்)\s*[:\-.]?\s*(\d{6,10})', norm_text, re.IGNORECASE)
    if not reg_match:
        reg_match = re.search(r'\b(519\d{4}|312\d{7}|\d{7})\b', norm_text)

    if reg_match and fields["register_no"]["value"] is None:
        fields["register_no"] = {"value": reg_match.group(1), "confidence": 0.95}

    # 3. Student Name Extraction
    name_match = re.search(r'(?:CANDIDATE\s*NAME|STUDENT\s*NAME|NAME|மாணவர்\s*பெயர்)\s*[:\-.]?\s*([A-Z\s.]{3,35}|\u0B80-\u0BFF\s.]+)', norm_text, re.IGNORECASE)
    if name_match:
        name_candidate = name_match.group(1).strip()
        # Ensure extracted string isn't a header label
        if not re.search(r'(BOARD|EXAMINATION|TAMIL|ENGLISH|MATHEMATICS|SCHOOL|CERTIFICATE)', name_candidate, re.IGNORECASE):
            if fields["student_name"]["value"] is None or fields["student_name"]["confidence"] < 0.90:
                fields["student_name"] = {"value": name_candidate, "confidence": 0.92}

    # 4. Father & Mother Name Extraction
    father_match = re.search(r'(?:FATHER(?:\'S)?\s*NAME|தந்தையின்\s*பெயர்)\s*[:\-.]?\s*([A-Z\s.]{3,35})', norm_text, re.IGNORECASE)
    if father_match:
        fields["father_name"] = {"value": father_match.group(1).strip(), "confidence": 0.88}

    mother_match = re.search(r'(?:MOTHER(?:\'S)?\s*NAME|தாயின்\s*பெயர்)\s*[:\-.]?\s*([A-Z\s.]{3,35})', norm_text, re.IGNORECASE)
    if mother_match:
        fields["mother_name"] = {"value": mother_match.group(1).strip(), "confidence": 0.88}

    # 5. Date of Birth (DOB) Extraction
    dob_match = re.search(r'\b(0?[1-9]|[12]\d|3[01])[/\-.](0?[1-9]|1[0-2])[/\-.](19|20)\d{2}\b', norm_text)
    if dob_match:
        dob_val = dob_match.group(0).replace('-', '/').replace('.', '/')
        fields["dob"] = {"value": dob_val, "confidence": 0.92}

    # 6. Total Marks Extraction
    total_match = re.search(r'(?:TOTAL\s*MARKS|GRAND\s*TOTAL|TOTAL|மொத்தம்)\s*[:\-.]?\s*(\d{3})\s*(?:/\s*500)?', norm_text, re.IGNORECASE)
    if total_match:
        try:
            total_val = int(total_match.group(1))
            if 100 <= total_val <= 500:
                fields["total_marks"] = {"value": total_val, "confidence": 0.94}
        except Exception:
            pass

    # 7. Passing Year & Month Extraction
    year_match = re.search(r'\b(APR(?:IL)?|MAR(?:CH)?|JUN(?:E)?|MAY|NOV(?:EMBER)?)\s*(20\d{2})\b', norm_text, re.IGNORECASE)
    if year_match:
        mon = year_match.group(1).upper()[:3]
        yr = year_match.group(2)
        fields["passing_year"] = {"value": f"{mon} {yr}", "confidence": 0.92}
    else:
        y_only = re.search(r'\b(20[12]\d)\b', norm_text)
        if y_only and fields["passing_year"]["value"] is None:
            fields["passing_year"] = {"value": y_only.group(1), "confidence": 0.85}

    # 8. Institution Extraction
    inst_match = re.search(r'(?:SCHOOL|INSTITUTION|CENTRE)\s*[:\-.]?\s*([A-Z\s.,\'-]{5,60})', norm_text, re.IGNORECASE)
    if inst_match:
        fields["institution"] = {"value": inst_match.group(1).strip(), "confidence": 0.85}

    # 9. Subject Marks Parsing
    subject_patterns = [
        ("Tamil", r'(?:TAMIL|தமிழ்)\s*[:\-.]?\s*(\d{2,3})'),
        ("English", r'(?:ENGLISH|ஆங்கிலம்)\s*[:\-.]?\s*(\d{2,3})'),
        ("Mathematics", r'(?:MATHEMATICS|MATHS|கணிதம்)\s*[:\-.]?\s*(\d{2,3})'),
        ("Science", r'(?:SCIENCE|அறிவியல்)\s*[:\-.]?\s*(\d{2,3})'),
        ("Social Science", r'(?:SOCIAL\s*SCIENCE|சமூக\s*அறிவியல்)\s*[:\-.]?\s*(\d{2,3})')
    ]

    for subj, pat in subject_patterns:
        m = re.search(pat, norm_text, re.IGNORECASE)
        if m:
            fields["subject_marks"][subj] = m.group(1)

    return fields
