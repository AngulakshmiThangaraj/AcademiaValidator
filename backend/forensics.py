import os
import io
import cv2
import numpy as np
from PIL import Image, ImageChops, ImageEnhance
import base64

def generate_ela_heatmap(image_input, quality=95, scale=15):
    """
    Generates Error Level Analysis (ELA) heatmap image and computes forgery anomaly score.
    Returns: (ela_pil_image, ela_color_heatmap_base64, mean_ela_error, max_ela_patch_error)
    """
    if isinstance(image_input, Image.Image):
        orig_pil = image_input.convert("RGB")
    else:
        orig_pil = Image.fromarray(cv2.cvtColor(image_input, cv2.COLOR_BGR2RGB))

    # Save to memory buffer with specific JPEG compression quality
    buffer = io.BytesIO()
    orig_pil.save(buffer, format="JPEG", quality=quality)
    buffer.seek(0)
    compressed_pil = Image.open(buffer)

    # Compute absolute pixel difference between original and re-compressed image
    ela_diff = ImageChops.difference(orig_pil, compressed_pil)

    # Extrapolate difference scale
    extrema = ela_diff.getextrema()
    max_diff = max([ex[1] for ex in extrema])
    if max_diff == 0:
        max_diff = 1
    
    scale_factor = 255.0 / max_diff
    ela_enhanced = ImageEnhance.Brightness(ela_diff).enhance(scale_factor)

    # Convert ELA diff to OpenCV array for heatmap visualization
    ela_np = np.array(ela_enhanced)
    gray_ela = cv2.cvtColor(ela_np, cv2.COLOR_RGB2GRAY)
    
    # Apply JET colormap for forensic heatmap visual
    heatmap_colored = cv2.applyColorMap(gray_ela, cv2.COLORMAP_JET)

    # Encode heatmap as Base64 image string for frontend UI
    _, buffer_jpg = cv2.imencode('.jpg', cv2.cvtColor(heatmap_colored, cv2.COLOR_BGR2RGB))
    heatmap_b64 = base64.b64encode(buffer_jpg).decode('utf-8')

    mean_error = float(np.mean(gray_ela))
    max_patch_error = float(np.max(gray_ela))

    return ela_enhanced, heatmap_b64, mean_error, max_patch_error

def detect_suspicious_regions(image_input, threshold=120):
    """
    Scans image using ELA and noise variance to locate tampered copy-pasted or edited text blocks.
    Returns list of bounding boxes: [{"bbox": [x, y, w, h], "reason": "...", "confidence": 0.88}]
    """
    if isinstance(image_input, Image.Image):
        img_np = np.array(image_input)
    else:
        img_np = image_input

    suspicious_regions = []

    # 1. ELA variance check
    ela_img, _, _, _ = generate_ela_heatmap(Image.fromarray(img_np), quality=95, scale=20)
    ela_gray = cv2.cvtColor(np.array(ela_img), cv2.COLOR_RGB2GRAY)

    # Threshold high-contrast difference patches
    _, thresh = cv2.threshold(ela_gray, threshold, 255, cv2.THRESH_BINARY)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 10))
    dilated = cv2.dilate(thresh, kernel, iterations=2)

    contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    img_height, img_width = img_np.shape[:2]

    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        area = w * h
        
        # Filter out whole page border or tiny single-pixel noise
        if 400 < area < (img_width * img_height * 0.25):
            roi_ela = ela_gray[y:y+h, x:x+w]
            patch_score = float(np.mean(roi_ela))

            if patch_score > 80:
                suspicious_regions.append({
                    "bbox": [int(x), int(y), int(w), int(h)],
                    "reason": "Altered Text / High Compression Error Level (ELA)",
                    "severity": "HIGH" if patch_score > 140 else "MEDIUM",
                    "anomaly_score": round(patch_score / 2.55, 1)
                })

    # 2. Text alignment & Font Mismatch Heuristic
    # Convert image to grayscale and find text contours
    gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY) if len(img_np.shape) == 3 else img_np
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    _, text_thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    
    text_contours, _ = cv2.findContours(text_thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    line_y_coords = []
    for cnt in text_contours:
        x, y, w, h = cv2.boundingRect(cnt)
        if 15 < h < 40 and 30 < w < 250:
            line_y_coords.append((y, h, x, w))

    # Detect baseline alignment deviations
    line_y_coords.sort(key=lambda item: item[0])
    for i in range(1, len(line_y_coords)):
        prev_y, prev_h, prev_x, prev_w = line_y_coords[i-1]
        curr_y, curr_h, curr_x, curr_w = line_y_coords[i]
        
        # If text boxes overlap horizontally but have slight vertical misalignment (telltale sign of manual text edit)
        if abs(prev_x - curr_x) < 50 and 2 < abs(prev_y - curr_y) < 12 and abs(prev_h - curr_h) > 6:
            suspicious_regions.append({
                "bbox": [int(curr_x), int(curr_y), int(curr_w), int(curr_h)],
                "reason": "Font Baseline Alignment & Height Inconsistency",
                "severity": "MEDIUM",
                "anomaly_score": 75.5
            })

    # Limit to top suspicious regions to prevent clutter
    suspicious_regions = sorted(suspicious_regions, key=lambda r: r.get("anomaly_score", 0), reverse=True)[:5]

    return suspicious_regions

def annotate_suspicious_image(image_input, suspicious_regions):
    """
    Draws bounding box annotations on copy of input image.
    Returns: Base64 string of annotated image.
    """
    if isinstance(image_input, Image.Image):
        img_np = np.array(image_input)
    else:
        img_np = image_input.copy()

    annotated = img_np.copy()
    if len(annotated.shape) == 2:
        annotated = cv2.cvtColor(annotated, cv2.COLOR_GRAY2RGB)

    for region in suspicious_regions:
        x, y, w, h = region["bbox"]
        reason = region["reason"]
        
        # Color red for high, orange for medium
        color = (230, 40, 40) if region.get("severity") == "HIGH" else (240, 140, 20)
        
        cv2.rectangle(annotated, (x, y), (x + w, y + h), color, 3)
        cv2.rectangle(annotated, (x, max(0, y - 24)), (x + min(w, 280), y), color, -1)
        cv2.putText(annotated, "SUSPICIOUS", (x + 5, max(12, y - 6)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

    _, buffer_jpg = cv2.imencode('.jpg', cv2.cvtColor(annotated, cv2.COLOR_RGB2BGR))
    return base64.b64encode(buffer_jpg).decode('utf-8')
