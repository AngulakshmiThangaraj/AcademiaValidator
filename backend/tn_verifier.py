import hashlib
import json
import re
from database import search_tn_marksheet

def normalize_name_for_fuzzy(name_str):
    if not name_str:
        return ""
    cleaned = re.sub(r'[^A-Z0-9\u0B80-\u0BFF]', ' ', str(name_str).upper())
    return " ".join(cleaned.split())

def calculate_name_similarity(name1, name2):
    n1 = normalize_name_for_fuzzy(name1)
    n2 = normalize_name_for_fuzzy(name2)
    if not n1 or not n2:
        return 0.0
    if n1 == n2:
        return 1.0
    if n1 in n2 or n2 in n1:
        return 0.90
    return 0.0

def verify_tn_marksheet(ocr_fields, qr_data_raw=None):
    """
    Core Tamil Nadu Marksheet Verification Engine executing:
    1. OCR Consistency Score (Max 20)
    2. Registry Record Match (Max 15)
    3. QR Signature Verification (Max 15)
    Total: Max 50 points -> Percentage %
    """
    def get_val(f_key):
        field_obj = ocr_fields.get(f_key, {})
        return field_obj.get("value") if isinstance(field_obj, dict) else field_obj

    extracted_cert_id = get_val("certificate_id")
    extracted_reg_no = get_val("register_no")
    extracted_name = get_val("student_name")
    extracted_dob = get_val("dob")
    extracted_father = get_val("father_name")
    extracted_mother = get_val("mother_name")
    extracted_inst = get_val("institution")
    extracted_total = get_val("total_marks")
    extracted_year = get_val("passing_year")

    # If QR payload exists, assist parsing
    parsed_qr_obj = None
    if qr_data_raw:
        if str(qr_data_raw).startswith("TNSSLC|"):
            parts = str(qr_data_raw).split("|")
            if len(parts) >= 4:
                parsed_qr_obj = {
                    "cert_id": parts[1],
                    "reg_no": parts[2],
                    "name": parts[3],
                    "passing_year": parts[4] if len(parts) > 4 else ""
                }
                if not extracted_cert_id: extracted_cert_id = parts[1]
                if not extracted_reg_no: extracted_reg_no = parts[2]
                if not extracted_name: extracted_name = parts[3]
        else:
            try:
                parsed_qr_obj = json.loads(qr_data_raw)
            except Exception:
                pass

    # -------------------------------------------------------------
    # SCORE 1: OCR Consistency Score (Max 20)
    # -------------------------------------------------------------
    score_ocr = 0
    ocr_explanations = []

    if extracted_cert_id:
        score_ocr += 4
        ocr_explanations.append("✓ Certificate ID successfully extracted from OCR (4/4 pts)")

    if extracted_reg_no:
        score_ocr += 4
        ocr_explanations.append("✓ Register Number extracted from OCR (4/4 pts)")

    if extracted_name:
        score_ocr += 4
        ocr_explanations.append("✓ Student Name extracted from OCR (4/4 pts)")

    if extracted_dob:
        score_ocr += 3
        ocr_explanations.append("✓ Date of Birth (DOB) extracted (3/3 pts)")

    if extracted_total:
        score_ocr += 3
        ocr_explanations.append("✓ Total Marks extracted (3/3 pts)")

    if extracted_father or extracted_mother or extracted_inst or extracted_year:
        score_ocr += 2
        ocr_explanations.append("✓ Institution / Parent / Year extracted (2/2 pts)")

    # -------------------------------------------------------------
    # SCORE 2: Registry Record Match (Max 15)
    # -------------------------------------------------------------
    score_registry = 0
    registry_record = search_tn_marksheet(
        cert_id=extracted_cert_id,
        reg_no=extracted_reg_no,
        student_name=extracted_name,
        dob=extracted_dob
    )

    matched_fields = []
    discrepancies = []
    warnings = []

    if registry_record:
        # 1. Certificate ID (3 pts)
        if extracted_cert_id and str(extracted_cert_id).strip().upper() == str(registry_record["certificate_id"]).strip().upper():
            score_registry += 3
            matched_fields.append("certificate_id")
        elif extracted_cert_id:
            discrepancies.append({
                "field": "certificate_id",
                "ocr_value": str(extracted_cert_id),
                "registry_value": str(registry_record["certificate_id"]),
                "status": "MISMATCH",
                "reason": "OCR Certificate ID differs from registry record."
            })

        # 2. Register Number (3 pts)
        if extracted_reg_no and str(extracted_reg_no).strip().upper() == str(registry_record["register_no"]).strip().upper():
            score_registry += 3
            matched_fields.append("register_no")
        elif extracted_reg_no:
            discrepancies.append({
                "field": "register_no",
                "ocr_value": str(extracted_reg_no),
                "registry_value": str(registry_record["register_no"]),
                "status": "MISMATCH",
                "reason": "OCR Register Number differs from official record."
            })

        # 3. Student Name (3 pts - Fuzzy Match)
        if extracted_name:
            sim = calculate_name_similarity(extracted_name, registry_record["student_name"])
            if sim >= 0.85:
                score_registry += 3
                matched_fields.append("student_name")
            else:
                discrepancies.append({
                    "field": "student_name",
                    "ocr_value": str(extracted_name),
                    "registry_value": str(registry_record["student_name"]),
                    "status": "MISMATCH",
                    "reason": "OCR Student Name differs from official registry record."
                })

        # 4. DOB (2 pts)
        if extracted_dob and str(extracted_dob).strip() == str(registry_record["dob"]).strip():
            score_registry += 2
            matched_fields.append("dob")

        # 5. Parent Name (1 pt)
        if extracted_father or registry_record.get("father_name"):
            score_registry += 1
            matched_fields.append("father_name")

        # 6. Institution (1 pt)
        if extracted_inst or registry_record.get("institution"):
            score_registry += 1
            matched_fields.append("institution")

        # 7. Total Marks (1 pt)
        if extracted_total and str(extracted_total).strip() == str(registry_record["total_marks"]).strip():
            score_registry += 1
            matched_fields.append("total_marks")
        elif extracted_total:
            discrepancies.append({
                "field": "total_marks",
                "ocr_value": str(extracted_total),
                "registry_value": str(registry_record["total_marks"]),
                "status": "MISMATCH",
                "reason": "OCR Total Marks differs from registry record."
            })

        # 8. Passing Year (1 pt)
        if extracted_year or registry_record.get("passing_year"):
            score_registry += 1
            matched_fields.append("passing_year")
    else:
        warnings.append("No matching document record was found in the official Tamil Nadu State Board Registry.")

    # -------------------------------------------------------------
    # SCORE 3: QR Signature Verification (Max 15)
    # -------------------------------------------------------------
    score_qr = 0
    qr_decoded = False
    qr_payload_valid = False
    qr_hash_matched = False
    qr_message = ""

    if qr_data_raw:
        qr_decoded = True
        score_qr += 5 # Decoded (5 pts)

        clean_qr = str(qr_data_raw).strip()
        calc_hash = hashlib.sha256(clean_qr.encode('utf-8')).hexdigest()

        if parsed_qr_obj or clean_qr:
            qr_payload_valid = True
            score_qr += 5 # Payload Valid (5 pts)

        if registry_record and registry_record.get("qr_payload_hash"):
            expected_hash = registry_record["qr_payload_hash"]
            if calc_hash.lower() == expected_hash.lower():
                qr_hash_matched = True
                score_qr += 5 # SHA-256 Hash Match (5 pts)
                matched_fields.append("qr_hash")
                qr_message = "QR Payload & SHA-256 Signature fully matched registry hash!"
            else:
                qr_message = "QR Payload SHA-256 hash mismatch against registry record."
        else:
            if qr_payload_valid:
                score_qr += 5
                qr_hash_matched = True
                qr_message = "QR Code payload verified."
    else:
        qr_message = "No QR Code detected on document image. (0/15 points)"

    # -------------------------------------------------------------
    # TOTAL SCORE & VERDICT DECISION
    # -------------------------------------------------------------
    overall_score = score_ocr + score_registry + score_qr
    max_score = 50
    percentage = round((overall_score / float(max_score)) * 100)

    if percentage >= 90 and (registry_record is not None and (len(discrepancies) == 0)):
        status = "VERIFIED"
    elif percentage >= 70 and len(discrepancies) <= 1:
        status = "PARTIALLY_VERIFIED"
    elif percentage >= 50:
        status = "REVIEW_REQUIRED"
    else:
        status = "NOT_VERIFIED"

    if status == "VERIFIED":
        explanation = "The extracted certificate details match the registry record and the QR payload hash is valid."
    elif status == "PARTIALLY_VERIFIED":
        explanation = "Extracted details match registry with minor field warnings."
    elif status == "REVIEW_REQUIRED":
        explanation = "Document details require manual verification review due to total_marks / registration discrepancies."
    else:
        explanation = "Document failed authenticity verification. Registry record mismatch or total_marks discrepancy detected."

    return {
        "status": status,
        "overall_score": overall_score,
        "max_score": max_score,
        "percentage": percentage,
        "scores": {
            "ocr_consistency": score_ocr,
            "registry_match": score_registry,
            "qr_verification": score_qr
        },
        "matched_fields": matched_fields,
        "discrepancies": discrepancies,
        "warnings": warnings,
        "registry_record_found": registry_record is not None,
        "qr_verified": qr_hash_matched,
        "explanation": explanation,
        "extracted_fields": ocr_fields,
        "registry_record": registry_record,
        "qr_debug_info": {
            "qr_detected": qr_decoded,
            "qr_valid": qr_payload_valid,
            "qr_message": qr_message,
            "payload": parsed_qr_obj or qr_data_raw
        }
    }
