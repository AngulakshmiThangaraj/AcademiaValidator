# Authenticity Validator for Academia

An **AI-Powered Forensic Verification Layer** that complements existing academic credential systems (like DigiLocker / NAD) by performing deep forensic multi-factor analysis on physical, scanned, photographed, or digitally manipulated academic certificates and marksheets.

---

## Architecture Overview

```
                   ┌─────────────────────────────────────────┐
                   │    User Upload / Camera / Demo Preset   │
                   └────────────────────┬────────────────────┘
                                        │
                                        ▼
                           ┌──────────────────────────┐
                           │   Image Preprocessing    │
                           └────────────┬─────────────┘
                                        │
             ┌──────────────────────────┼──────────────────────────┐
             ▼                          ▼                          ▼
┌─────────────────────────┐  ┌────────────────────┐  ┌────────────────────┐
│  PyTorch MobileNetV2    │  │  Multi-Engine OCR  │  │ Forensic ELA Check │
│  Transfer Learning CNN  │  │  Document Parser   │  │ Heatmap & Anomalies│
└────────────┬────────────┘  └──────────┬─────────┘  └──────────┬─────────┘
             │                          │                       │
             └──────────────────────────┼───────────────────────┘
                                        │
                                        ▼
                        ┌───────────────────────────────┐
                        │   QR Code & SHA-256 Fingerprint│
                        │   Database Registry Matching  │
                        └───────────────┬───────────────┘
                                        │
                                        ▼
                        ┌───────────────────────────────┐
                        │ Multi-Factor Authenticity Score│
                        │ (0-100% -> VERIFIED/SUSPICIOUS│
                        └───────────────┬───────────────┘
                                        │
                                        ▼
                        ┌───────────────────────────────┐
                        │ Interactive Glassmorphism UI  │
                        │ & Explainable Forensic Report │
                        └───────────────────────────────┘
```

---

## Features

1. **Lightweight AI Forgery Classifier**:
   - Transfer learning using **MobileNetV2** in PyTorch.
   - Evaluated with Precision (**100.0%**), Recall (**54.55%**), Accuracy (**77.78%**), and Confusion Matrix.

2. **Error Level Analysis (ELA) & Tampering Visualization**:
   - Re-compresses documents at 95% JPEG quality to compute pixel-level compression difference maps (`cv2.COLORMAP_JET`).
   - Detects copy-move patches and font baseline height inconsistencies with visual bounding box highlights.

3. **Cryptographic SHA-256 Fingerprinting & QR Payload Verification**:
   - Computes exact document SHA-256 byte hashes to catch post-registration digital edits.
   - Decodes QR code signatures and validates student name, register number, and CGPA against official database records.

4. **Multi-Factor Authenticity Scoring**:
   $$\text{Score} = (35\% \times \text{AI}) + (20\% \times \text{OCR}) + (15\% \times \text{QR}) + (15\% \times \text{Hash}) + (15\% \times \text{ELA})$$
   - Score $\ge$ 80%: **`STATUS: VERIFIED`** (Green)
   - Score $<$ 80%: **`STATUS: SUSPICIOUS`** (Red)

5. **SIH Demo Scenarios**:
   - **Certificate A (Genuine)**: Score **97.2%**, Status **VERIFIED**, SHA-256 Hash Matched.
   - **Certificate B (Manipulated)**: Score **63.1%**, Status **SUSPICIOUS**, SHA-256 Mismatch, Suspicious region highlighted.

---

## Project Structure

```text
authenticity-validator-academia/
├── backend/
│   ├── main.py              # FastAPI server & REST API routes
│   ├── ai_model.py          # PyTorch MobileNetV2 classifier wrapper
│   ├── forensics.py         # ELA heatmap generator & tampering detector
│   ├── ocr_engine.py        # OCR text extraction & field parser
│   ├── security.py         # SHA-256 hashing & QR payload decoder
│   ├── scoring.py          # Multi-factor authenticity score calculator
│   ├── database.py         # SQLite registry & verification logs
│   ├── sample_generator.py # Demo sample certificate generator
│   ├── model.pth           # Trained PyTorch weights
│   └── metrics.json        # Evaluation metrics & confusion matrix
├── dataset/
│   ├── generate_dataset.py # Synthetic certificate dataset generator
│   └── train_model.py      # Model training & evaluation pipeline
├── frontend/
│   ├── index.html          # Glassmorphism dashboard UI
│   ├── style.css           # Modern dark-mode aesthetics
│   └── app.js              # REST API integration & viewer logic
├── vercel.json             # Serverless deployment configuration
├── requirements.txt        # Python dependency specifications
├── .env.example            # Environment variables template
└── .gitignore              # Production git ignore rules
```

---

## Local Setup & Quick Start

1. **Clone Repository**:
   ```bash
   git clone https://github.com/your-username/authenticity-validator-academia.git
   cd authenticity-validator-academia
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run Dev Server**:
   ```bash
   python -m uvicorn main:app --app-dir backend --host 127.0.0.1 --port 8000 --reload
   ```

4. **Access Web Application**:
   Open browser at `http://127.0.0.1:8000`

---

## Production Deployment (Vercel)

This repository includes a pre-configured `vercel.json` for seamless Vercel serverless deployment.

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy to Vercel
vercel
```

- **Frontend Static Route**: `/` -> Serves `frontend/index.html`
- **Backend API Route**: `/api/*` -> Serverless execution via `backend/main.py`
