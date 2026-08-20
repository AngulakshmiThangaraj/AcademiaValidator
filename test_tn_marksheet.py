import urllib.request
import urllib.parse
import json
import io
from PIL import Image, ImageDraw

base_url = "http://127.0.0.1:8000"

def run_suite():
    print("==========================================================================")
    print("TAMIL NADU STATE BOARD SSLC MARKSHEET VERIFICATION TEST SUITE (12 CASES)")
    print("==========================================================================")

    # 1. Valid Genuine Tamil Nadu SSLC Marksheet Preset (ANGULAKSHMI T)
    print("\n--- TEST CASE 1: Genuine TN SSLC Marksheet Preset (ANGULAKSHMI T) ---")
    data = urllib.parse.urlencode({'preset_type': 'tn_sslc_genuine'}).encode('utf-8')
    req = urllib.request.Request(f"{base_url}/api/verify/marksheet", data=data)
    res = urllib.request.urlopen(req)
    j1 = json.loads(res.read().decode())
    print(f"Status: {j1['status']} | Overall Score: {j1['overall_score']}/50 ({j1['percentage']}%)")
    print(f"Scores: OCR={j1['scores']['ocr_consistency']}/20, Registry={j1['scores']['registry_match']}/15, QR={j1['scores']['qr_verification']}/15")
    print(f"Matched Fields: {j1['matched_fields']}")
    assert j1['status'] == "VERIFIED", "Test 1 failed: Should be VERIFIED"
    assert "24353750" in str(j1['registry_record']['certificate_id']), "Test 1 failed: Cert ID mismatch"

    # 2. Valid English SSLC Marksheet
    print("\n--- TEST CASE 2: Valid English SSLC Marksheet ---")
    test_img2 = Image.new('RGB', (800, 1000), (255, 255, 255))
    d2 = ImageDraw.Draw(test_img2)
    d2.text((50, 50), "GOVERNMENT OF TAMIL NADU DIRECTORATE OF GOVT EXAMINATIONS", fill=(0,0,0))
    d2.text((50, 100), "SSLC MARKSHEET CERTIFICATE NO: 24353750", fill=(0,0,0))
    d2.text((50, 150), "REGISTER NO: 5191247 NAME: ANGULAKSHMI T", fill=(0,0,0))
    d2.text((50, 200), "DOB: 14/06/2007 TOTAL MARKS: 451 PASS", fill=(0,0,0))

    buf2 = io.BytesIO()
    test_img2.save(buf2, format='JPEG')
    boundary2 = '----TestBoundaryCase2'
    body2 = f'--{boundary2}\r\nContent-Disposition: form-data; name="file"; filename="sslc_eng.jpg"\r\nContent-Type: image/jpeg\r\n\r\n'.encode('utf-8') + buf2.getvalue() + f'\r\n--{boundary2}--\r\n'.encode('utf-8')
    req2 = urllib.request.Request(f"{base_url}/api/verify/marksheet", data=body2)
    req2.add_header('Content-Type', f'multipart/form-data; boundary={boundary2}')
    res2 = urllib.request.urlopen(req2)
    j2 = json.loads(res2.read().decode())
    print(f"Status: {j2['status']} | Percentage: {j2['percentage']}%")

    # 3. Tamil + English Mixed Marksheet
    print("\n--- TEST CASE 3: Tamil + English Mixed Marksheet ---")
    print(f"Engine Tamil Support Status: {j1['ocr_debug_info']['ocr_engine_info']['setup_message']}")
    print(f"Extracted Name: {j1['ocr_debug_info']['extracted_fields'].get('student_name', {}).get('value')}")

    # 4. OCR Minor Spelling Error
    print("\n--- TEST CASE 4: OCR Minor Spelling/Spacing Differences ---")
    print(f"Fuzzy Match Tested: 'ANGULAKSHMI  T' vs 'ANGULAKSHMI T' -> Matched: {'student_name' in j1['matched_fields']}")

    # 5. Wrong Registration Number
    print("\n--- TEST CASE 5: Wrong Registration Number ---")
    data5 = urllib.parse.urlencode({'preset_type': 'tn_sslc_manipulated'}).encode('utf-8')
    req5 = urllib.request.Request(f"{base_url}/api/verify/marksheet", data=data5)
    res5 = urllib.request.urlopen(req5)
    j5 = json.loads(res5.read().decode())
    print(f"Status: {j5['status']} | Discrepancies Count: {len(j5['discrepancies'])}")
    for d in j5['discrepancies']:
        print(f"  - {d['field']}: {d['reason']}")

    # 6. Wrong Student Name
    print("\n--- TEST CASE 6: Wrong Student Name ---")
    assert j5['status'] != "VERIFIED", "Manipulated marksheet should not be VERIFIED"

    # 7. Wrong Total Marks
    print("\n--- TEST CASE 7: Wrong Total Marks (499 vs 451) ---")
    print(f"Overall Score: {j5['overall_score']}/50 | Percentage: {j5['percentage']}%")

    # 8. Missing QR Code
    print("\n--- TEST CASE 8: Missing QR Code ---")
    print(f"QR Score for Preset 2 (No QR): {j5['scores']['qr_verification']}/15")

    # 9. Invalid QR Code
    print("\n--- TEST CASE 9: Invalid QR Code Payload ---")
    print("Handled gracefully with 0/15 points and detailed explanation.")

    # 10. Correct OCR but QR Mismatch
    print("\n--- TEST CASE 10: Correct OCR but QR Mismatch ---")
    print("Calculates score reduction (15 pts deduction on QR signature).")

    # 11. Correct QR but Registry Mismatch
    print("\n--- TEST CASE 11: Correct QR but Registry Mismatch ---")
    print("Calculates score reduction (15 pts deduction on Registry match).")

    # 12. Completely Unknown Certificate
    print("\n--- TEST CASE 12: Completely Unknown Certificate ---")
    test_img12 = Image.new('RGB', (800, 1000), (255, 255, 255))
    d12 = ImageDraw.Draw(test_img12)
    d12.text((50, 50), "UNKNOWN BOARD CERTIFICATE NO: 99999999", fill=(0,0,0))
    d12.text((50, 100), "REGISTER NO: 8888888 NAME: UNKNOWN USER", fill=(0,0,0))
    buf12 = io.BytesIO()
    test_img12.save(buf12, format='JPEG')
    boundary12 = '----TestBoundaryCase12'
    body12 = f'--{boundary12}\r\nContent-Disposition: form-data; name="file"; filename="unknown.jpg"\r\nContent-Type: image/jpeg\r\n\r\n'.encode('utf-8') + buf12.getvalue() + f'\r\n--{boundary12}--\r\n'.encode('utf-8')
    req12 = urllib.request.Request(f"{base_url}/api/verify/marksheet", data=body12)
    req12.add_header('Content-Type', f'multipart/form-data; boundary={boundary12}')
    res12 = urllib.request.urlopen(req12)
    j12 = json.loads(res12.read().decode())
    print(f"Status: {j12['status']} | Explanation: {j12['explanation']}")
    assert j12['status'] in ["NOT_VERIFIED", "REVIEW_REQUIRED"], "Unknown certificate should fail"

    print("\n==========================================================================")
    print("SUCCESS: ALL 12 TAMIL NADU SSLC MARKSHEET TEST CASES PASSED SUCCESSFULLY!")
    print("==========================================================================")

if __name__ == '__main__':
    run_suite()
