import os
import io
import base64
import numpy as np
from PIL import Image, ImageChops, ImageEnhance, ImageDraw, ImageFont

def generate_ela_heatmap(image_input, quality=95, scale=18):
    """
    Generates Error Level Analysis (ELA) false-color heatmap image using pure Pillow & NumPy.
    Returns: (ela_pil_image, ela_color_heatmap_base64, mean_ela_error, max_ela_patch_error)
    """
    if isinstance(image_input, Image.Image):
        orig_pil = image_input.convert("RGB")
    else:
        orig_pil = Image.fromarray(np.uint8(image_input)).convert("RGB")

    # Save to memory buffer with specific JPEG compression quality
    buffer = io.BytesIO()
    orig_pil.save(buffer, format="JPEG", quality=quality)
    buffer.seek(0)
    compressed_pil = Image.open(buffer)

    # Compute absolute pixel difference between original and re-compressed image
    ela_diff = ImageChops.difference(orig_pil, compressed_pil)

    # Scale differences
    extrema = ela_diff.getextrema()
    max_diff = max([ex[1] for ex in extrema])
    if max_diff == 0:
        max_diff = 1
    
    scale_factor = 255.0 / max_diff
    ela_enhanced = ImageEnhance.Brightness(ela_diff).enhance(scale_factor)

    # Convert ELA diff grayscale map to false-color heatmap array (Blue -> Cyan -> Yellow -> Red)
    ela_gray = np.array(ela_enhanced.convert("L"))
    
    height, width = ela_gray.shape
    heatmap_rgb = np.zeros((height, width, 3), dtype=np.uint8)

    # Map error level intensity to RGB false colors
    # Low difference (0-40) -> Dark Navy/Blue
    # Medium difference (41-120) -> Cyan/Green
    # High difference (121-255) -> Yellow/Red
    val = ela_gray.astype(np.float32) / 255.0
    heatmap_rgb[:, :, 0] = np.clip(val * 2.0 * 255, 0, 255).astype(np.uint8) # Red channel
    heatmap_rgb[:, :, 1] = np.clip((1.0 - np.abs(val - 0.5) * 2.0) * 255, 0, 255).astype(np.uint8) # Green channel
    heatmap_rgb[:, :, 2] = np.clip((1.0 - val) * 255, 0, 255).astype(np.uint8) # Blue channel

    heatmap_pil = Image.fromarray(heatmap_rgb)

    buf = io.BytesIO()
    heatmap_pil.save(buf, format="JPEG", quality=90)
    heatmap_b64 = base64.b64encode(buf.getvalue()).decode("utf-8")

    mean_error = float(np.mean(ela_gray))
    max_patch_error = float(np.max(ela_gray))

    return ela_enhanced, heatmap_b64, mean_error, max_patch_error

def detect_suspicious_regions(image_input, threshold=110):
    """
    Scans document image using ELA patch variance and baseline grid checks.
    Returns list of bounding boxes: [{"bbox": [x, y, w, h], "reason": "...", "severity": "HIGH"}]
    """
    if isinstance(image_input, Image.Image):
        orig_pil = image_input.convert("RGB")
    else:
        orig_pil = Image.fromarray(np.uint8(image_input)).convert("RGB")

    suspicious_regions = []

    ela_img, _, mean_err, _ = generate_ela_heatmap(orig_pil, quality=95, scale=18)
    ela_gray = np.array(ela_img.convert("L"))
    img_height, img_width = ela_gray.shape

    # Grid search for high variance patches (e.g. 60x30 text blocks)
    step_y, step_x = 40, 80
    for y in range(120, img_height - 120, step_y):
        for x in range(80, img_width - 80, step_x):
            patch = ela_gray[y:y+step_y, x:x+step_x]
            patch_score = float(np.mean(patch))

            if patch_score > threshold:
                suspicious_regions.append({
                    "bbox": [int(x), int(y), int(step_x), int(step_y)],
                    "reason": "Altered Text / High Compression Error Level (ELA)",
                    "severity": "HIGH" if patch_score > 150 else "MEDIUM",
                    "anomaly_score": round(patch_score / 2.55, 1)
                })

    # Deduplicate overlapping bounding boxes
    suspicious_regions = sorted(suspicious_regions, key=lambda r: r.get("anomaly_score", 0), reverse=True)[:4]

    return suspicious_regions

def annotate_suspicious_image(image_input, suspicious_regions):
    """
    Draws bounding box annotations on copy of input image using pure Pillow ImageDraw.
    Returns: Base64 string of annotated image.
    """
    if isinstance(image_input, Image.Image):
        annotated = image_input.convert("RGB").copy()
    else:
        annotated = Image.fromarray(np.uint8(image_input)).convert("RGB").copy()

    draw = ImageDraw.Draw(annotated)

    try:
        font = ImageFont.truetype("arial.ttf", 14)
    except OSError:
        font = ImageFont.load_default()

    for region in suspicious_regions:
        x, y, w, h = region["bbox"]
        color = (230, 40, 40) if region.get("severity") == "HIGH" else (240, 140, 20)
        
        # Bounding box
        draw.rectangle([x, y, x + w, y + h], outline=color, width=3)
        # Header tag box
        draw.rectangle([x, max(0, y - 20), x + min(w, 140), y], fill=color)
        draw.text((x + 4, max(0, y - 18)), "SUSPICIOUS", fill=(255, 255, 255), font=font)

    buf = io.BytesIO()
    annotated.save(buf, format="JPEG", quality=90)
    return base64.b64encode(buf.getvalue()).decode("utf-8")
