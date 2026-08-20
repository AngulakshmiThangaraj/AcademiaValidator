import urllib.request
import urllib.parse
import json
import hashlib

base_url = "http://127.0.0.1:8000"

def run_suite():
    print("==========================================================================")
    print("ACADEMIA VALIDATOR TN SSLC MARKSHEET VERIFICATION SUITE")
    print("Target Record: Certificate ID 88880001 (Reg: 77770001 / ANGULAKSHMI T)")
    print("==========================================================================")

    # 1. Test Genuine SSLC Marksheet Preset (88880001)
    print("\n--- 1. Testing Genuine SSLC Marksheet (88880001 / ANGULAKSHMI T) ---")
    data = urllib.parse.urlencode({'preset_type': 'tn_sslc_genuine'}).encode('utf-8')
    req = urllib.request.Request(f"{base_url}/api/verify/marksheet", data=data)
    res = urllib.request.urlopen(req)
    j1 = json.loads(res.read().decode())

    print(f"Status: {j1['status']} | Percentage: {j1['percentage']}%")
    print(f"Scores Breakdown:")
    print(f"  - OCR Consistency  : {j1['scores']['ocr_consistency']} / 20")
    print(f"  - Registry Match   : {j1['scores']['registry_match']} / 15")
    print(f"  - QR Verification  : {j1['scores']['qr_verification']} / 15")
    print(f"  - Total Score      : {j1['overall_score']} / {j1['max_score']}")
    print(f"\nMatched Fields Check:")
    print(f"  - Certificate ID   : {'[MATCH]' if 'certificate_id' in j1['matched_fields'] else '[MISMATCH]'}")
    print(f"  - Register No      : {'[MATCH]' if 'register_no' in j1['matched_fields'] else '[MISMATCH]'}")
    print(f"  - Student Name     : {'[MATCH]' if 'student_name' in j1['matched_fields'] else '[MISMATCH]'}")
    print(f"  - Passing Year     : {'[MATCH]' if 'passing_year' in j1['matched_fields'] else '[MISMATCH]'}")
    print(f"  - Total Marks      : {'[MATCH]' if 'total_marks' in j1['matched_fields'] else '[MISMATCH]'}")
    print(f"  - QR Hash          : {'[MATCH]' if 'qr_hash' in j1['matched_fields'] or j1['qr_verified'] else '[MISMATCH]'}")

    assert j1['status'] == "VERIFIED", f"Genuine record should be VERIFIED, got {j1['status']}"
    assert j1['overall_score'] == 50, f"Expected 50/50 score, got {j1['overall_score']}/50"

    # 2. Test Tampered SSLC Marksheet Preset (Total Marks 499 vs 451)
    print("\n--- 2. Testing Tampered SSLC Marksheet (Total Marks 499 vs 451) ---")
    data_m = urllib.parse.urlencode({'preset_type': 'tn_sslc_manipulated'}).encode('utf-8')
    req_m = urllib.request.Request(f"{base_url}/api/verify/marksheet", data=data_m)
    res_m = urllib.request.urlopen(req_m)
    j2 = json.loads(res_m.read().decode())

    print(f"Status: {j2['status']} | Percentage: {j2['percentage']}%")
    print("Discrepancies Detected:")
    for d in j2['discrepancies']:
        print(f"  - Field: {d['field']} | Extracted: '{d['ocr_value']}' vs Registry: '{d['registry_value']}' -> {d['reason']}")

    assert j2['status'] in ["REVIEW_REQUIRED", "NOT_VERIFIED", "PARTIALLY_VERIFIED"], f"Tampered record status, got {j2['status']}"
    assert len(j2['discrepancies']) > 0, "Discrepancy in total marks must be detected"

    print("\n==========================================================================")
    print("[SUCCESS] RECORD 88880001 (ANGULAKSHMI T) VERIFICATION SUITE 100% PASSED!")
    print("   OCR Consistency: 20/20 | Registry Match: 15/15 | QR Verification: 15/15")
    print("   Total Score: 50/50 (100% VERIFIED)")
    print("==========================================================================")

if __name__ == '__main__':
    run_suite()
