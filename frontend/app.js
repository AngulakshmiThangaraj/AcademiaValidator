// Global Config & State
const API_BASE = window.BACKEND_URL || '';
let currentVerificationData = null;
let currentActiveTab = 'orig';

// Navigation Tab Switcher
function switchTab(tabId) {
  const tabs = ['dashboard', 'metrics'];
  tabs.forEach(t => {
    const view = document.getElementById(`view-${t}`);
    if (view) {
      if (t === tabId) {
        view.classList.remove('hidden');
      } else {
        view.classList.add('hidden');
      }
    }
  });

  document.querySelectorAll('.nav-btn').forEach(btn => {
    btn.classList.remove('active');
    if (btn.getAttribute('onclick') && btn.getAttribute('onclick').includes(tabId)) {
      btn.classList.add('active');
    }
  });

  if (tabId === 'metrics') {
    fetchModelMetrics();
  }
}

// Drag & Drop File Upload Handler
function handleFileSelect(event) {
  const files = event.target.files;
  if (files && files.length > 0) {
    uploadFile(files[0]);
  }
}

async function uploadFile(file) {
  startProcessingAnimation();

  try {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${API_BASE}/api/verify/marksheet`, {
      method: 'POST',
      body: formData
    });

    if (!response.ok) {
      const errText = await response.text();
      throw new Error(`API Error ${response.status}: ${errText}`);
    }

    const data = await response.json();
    currentVerificationData = data;
    renderResults(data);
  } catch (err) {
    alert("Verification failed: " + err.message);
  } finally {
    stopProcessingAnimation();
  }
}

// Step-by-Step Scanner Animation
function startProcessingAnimation() {
  const scannerLine = document.getElementById('scanner-line');
  if (scannerLine) scannerLine.style.display = 'block';
  
  let step = 1;
  const interval = setInterval(() => {
    const el = document.getElementById(`step-${step}`);
    if (el) {
      el.classList.add('active');
    }
    step++;
    if (step > 6) {
      clearInterval(interval);
    }
  }, 250);
}

function stopProcessingAnimation() {
  const scannerLine = document.getElementById('scanner-line');
  if (scannerLine) scannerLine.style.display = 'none';
  for (let i = 1; i <= 6; i++) {
    const el = document.getElementById(`step-${i}`);
    if (el) {
      el.classList.remove('active');
      el.classList.add('completed');
    }
  }
}

// Render Results to UI Dashboard
function renderResults(data) {
  // 1. Authenticity Score & Verdict Badge
  const scoreVal = document.getElementById('score-value');
  const scoreCircle = document.getElementById('score-circle');
  const verdictTag = document.getElementById('verdict-tag');
  const hashStatus = document.getElementById('hash-match-status');

  const scorePct = data.percentage !== undefined ? data.percentage : data.authenticity_score;
  if (scoreVal) scoreVal.textContent = `${scorePct}%`;

  const statusStr = data.status || 'VERIFIED';
  if (verdictTag) {
    verdictTag.textContent = `STATUS: ${statusStr.replace('_', ' ')}`;
    if (statusStr === 'VERIFIED') {
      verdictTag.className = 'verdict-tag verified';
      if (scoreCircle) scoreCircle.style.background = `conic-gradient(#10b981 ${scorePct * 3.6}deg, rgba(255,255,255,0.1) 0deg)`;
    } else if (statusStr === 'PARTIALLY_VERIFIED' || statusStr === 'REVIEW_REQUIRED') {
      verdictTag.className = 'verdict-tag warning';
      verdictTag.style.background = 'rgba(245, 158, 11, 0.2)';
      verdictTag.style.color = '#fde68a';
      if (scoreCircle) scoreCircle.style.background = `conic-gradient(#f59e0b ${scorePct * 3.6}deg, rgba(255,255,255,0.1) 0deg)`;
    } else {
      verdictTag.className = 'verdict-tag suspicious';
      if (scoreCircle) scoreCircle.style.background = `conic-gradient(#ef4444 ${scorePct * 3.6}deg, rgba(255,255,255,0.1) 0deg)`;
    }
  }

  if (hashStatus) {
    if (data.qr_verified || data.hash_matched_in_registry) {
      hashStatus.textContent = "✓ SHA-256 & Registry Hash Verified";
      hashStatus.style.color = "var(--success-green)";
    } else {
      hashStatus.textContent = "✗ Registry Hash Mismatch / Unverified";
      hashStatus.style.color = "var(--danger-red)";
    }
  }

  // 2. Score Factor Breakdown Bars
  const scores = data.scores || {};
  const bd = data.score_breakdown || {};

  const ocrPts = scores.ocr_consistency !== undefined ? scores.ocr_consistency : (bd.ocr_consistency_score || 0);
  const elOcr = document.getElementById('score-ocr');
  const barOcr = document.getElementById('bar-ocr');
  if (elOcr) elOcr.textContent = `${ocrPts} / 20.0`;
  if (barOcr) barOcr.style.width = `${(ocrPts / 20.0) * 100}%`;

  const regPts = scores.registry_match !== undefined ? scores.registry_match : (bd.id_hash_score || 0);
  const elReg = document.getElementById('score-registry') || document.getElementById('score-id');
  const barReg = document.getElementById('bar-registry') || document.getElementById('bar-id');
  if (elReg) elReg.textContent = `${regPts} / 15.0`;
  if (barReg) barReg.style.width = `${(regPts / 15.0) * 100}%`;

  const qrPts = scores.qr_verification !== undefined ? scores.qr_verification : (bd.qr_validity_score || 0);
  const elQr = document.getElementById('score-qr');
  const barQr = document.getElementById('bar-qr');
  if (elQr) elQr.textContent = `${qrPts} / 15.0`;
  if (barQr) barQr.style.width = `${(qrPts / 15.0) * 100}%`;

  // 3. Explainable Report & Discrepancies
  const reportBox = document.getElementById('explainable-report-box');
  const reportText = document.getElementById('report-text');
  if (reportText) {
    reportText.textContent = data.explanation || 'Verification scan completed successfully.';
  }

  const fieldsCard = document.getElementById('fields-verification-card');
  const matchedContainer = document.getElementById('matched-chips');
  const discSection = document.getElementById('discrepancies-section');
  const discTbody = document.getElementById('discrepancy-rows');

  if (fieldsCard) fieldsCard.classList.remove('hidden');

  if (matchedContainer) {
    matchedContainer.innerHTML = '';
    const matched = data.matched_fields || [];
    if (matched.length > 0) {
      matched.forEach(f => {
        const chip = document.createElement('span');
        chip.className = 'matched-chip';
        chip.style.cssText = 'display: inline-flex; align-items: center; gap: 0.35rem; background: rgba(16, 185, 129, 0.15); border: 1px solid rgba(16, 185, 129, 0.3); color: var(--success-green); padding: 0.25rem 0.6rem; border-radius: 12px; font-size: 0.75rem; font-weight: 600; margin: 0.2rem;';
        chip.innerHTML = `<i class="fa-solid fa-check"></i> ${f.replace('_', ' ').toUpperCase()}`;
        matchedContainer.appendChild(chip);
      });
    } else {
      matchedContainer.innerHTML = '<span style="font-size: 0.8rem; color: var(--text-dim);">No exact matching fields.</span>';
    }
  }

  if (discSection && discTbody) {
    discTbody.innerHTML = '';
    const discs = data.discrepancies || [];
    if (discs.length > 0) {
      discSection.classList.remove('hidden');
      discs.forEach(d => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
          <td style="font-weight: 600; color: var(--warning-amber);">${d.field}</td>
          <td style="color: var(--danger-red);">${d.ocr_value}</td>
          <td style="color: var(--success-green);">${d.registry_value}</td>
          <td style="font-size: 0.8rem; color: var(--text-muted);">${d.reason}</td>
        `;
        discTbody.appendChild(tr);
      });
    } else {
      discSection.classList.add('hidden');
    }
  }

  // 4. Image Viewer Rendering
  const imgOrig = document.getElementById('img-original');
  const imgEla = document.getElementById('img-ela');
  const imgAnnot = document.getElementById('img-annotated');
  
  const phOrig = document.getElementById('ph-orig');
  const phEla = document.getElementById('ph-ela');
  const phAnnot = document.getElementById('ph-annotated');

  const imgs = data.images || {};
  if (imgOrig && imgs.original_b64) {
    imgOrig.src = imgs.original_b64;
    imgOrig.style.display = 'block';
    if (phOrig) phOrig.style.display = 'none';
  }
  if (imgEla && imgs.ela_heatmap_b64) {
    imgEla.src = imgs.ela_heatmap_b64;
    imgEla.style.display = 'block';
    if (phEla) phEla.style.display = 'none';
  }
  if (imgAnnot && imgs.annotated_suspicious_b64) {
    imgAnnot.src = imgs.annotated_suspicious_b64;
    imgAnnot.style.display = 'block';
    if (phAnnot) phAnnot.style.display = 'none';
  }

  // 5. Suspicious Regions List Rendering
  const suspiciousContainer = document.getElementById('suspicious-regions-items');
  if (suspiciousContainer) {
    suspiciousContainer.innerHTML = '';
    const forensics = data.forensics || {};
    const regions = forensics.suspicious_regions || [];
    if (regions.length > 0) {
      regions.forEach(r => {
        const item = document.createElement('div');
        item.style.cssText = 'background: rgba(239, 68, 68, 0.1); border: 1px solid rgba(239, 68, 68, 0.3); border-radius: 6px; padding: 0.5rem 0.75rem; margin-bottom: 0.4rem; font-size: 0.8rem;';
        item.innerHTML = `<strong style="color: var(--danger-red);">${r.reason || 'Anomaly Detected'}</strong> - Severity: ${r.severity || 'MEDIUM'}`;
        suspiciousContainer.appendChild(item);
      });
    } else {
      suspiciousContainer.innerHTML = '<div style="font-size: 0.8rem; color: var(--success-green);"><i class="fa-solid fa-circle-check"></i> No suspicious compression or font anomalies detected.</div>';
    }
  }

  // 6. Expandable OCR & QR Debug technical details
  const dbgOcr = document.getElementById('debug-ocr-json');
  const dbgQr = document.getElementById('debug-qr-json');
  if (dbgOcr && data.ocr_debug_info) {
    dbgOcr.textContent = JSON.stringify(data.ocr_debug_info.extracted_fields || {}, null, 2);
  }
  if (dbgQr && data.ocr_debug_info) {
    dbgQr.textContent = JSON.stringify(data.ocr_debug_info.qr_debug || {}, null, 2);
  }
}

// Viewer Tab Switcher
function switchViewerTab(tabType) {
  currentActiveTab = tabType;

  ['orig', 'ela', 'annotated'].forEach(t => {
    const box = document.getElementById(`view-img-${t}`);
    if (box) {
      if (t === tabType) {
        box.classList.add('active');
        box.style.display = 'block';
      } else {
        box.classList.remove('active');
        box.style.display = 'none';
      }
    }
  });

  document.querySelectorAll('.viewer-tab').forEach(btn => {
    btn.classList.remove('active');
    if (btn.getAttribute('onclick') && btn.getAttribute('onclick').includes(tabType)) {
      btn.classList.add('active');
    }
  });
}

// Toggle Debug Accordion
function toggleDebugAccordion() {
  const body = document.getElementById('debug-content-body');
  const icon = document.getElementById('accordion-icon');
  if (body) {
    if (body.classList.contains('hidden')) {
      body.classList.remove('hidden');
      if (icon) icon.className = 'fa-solid fa-chevron-up';
    } else {
      body.classList.add('hidden');
      if (icon) icon.className = 'fa-solid fa-chevron-down';
    }
  }
}

// Fetch Model Metrics
async function fetchModelMetrics() {
  try {
    const response = await fetch(`${API_BASE}/api/metrics`);
    if (response.ok) {
      const m = await response.json();
      const elAcc = document.getElementById('metric-accuracy');
      const elPrec = document.getElementById('metric-precision');
      const elRec = document.getElementById('metric-recall');
      const elF1 = document.getElementById('metric-f1');

      if (elAcc) elAcc.textContent = `${(m.accuracy * 100).toFixed(1)}%`;
      if (elPrec) elPrec.textContent = `${(m.precision * 100).toFixed(1)}%`;
      if (elRec) elRec.textContent = `${(m.recall * 100).toFixed(1)}%`;
      if (elF1) elF1.textContent = `${(m.f1_score * 100).toFixed(1)}%`;

      if (m.confusion_matrix) {
        const cmTp = document.getElementById('cm-tp');
        const cmFn = document.getElementById('cm-fn');
        const cmFp = document.getElementById('cm-fp');
        const cmTn = document.getElementById('cm-tn');
        if (cmTp) cmTp.textContent = `${m.confusion_matrix[0][0]} (TP)`;
        if (cmFn) cmFn.textContent = `${m.confusion_matrix[0][1]} (FN)`;
        if (cmFp) cmFp.textContent = `${m.confusion_matrix[1][0]} (FP)`;
        if (cmTn) cmTn.textContent = `${m.confusion_matrix[1][1]} (TN)`;
      }
    }
  } catch (err) {
    console.error("Error fetching metrics:", err);
  }
}

// Drag & drop visual events
const dropzone = document.getElementById('dropzone');
if (dropzone) {
  ['dragenter', 'dragover'].forEach(eventName => {
    dropzone.addEventListener(eventName, (e) => {
      e.preventDefault();
      dropzone.style.borderColor = 'var(--primary-cyan)';
      dropzone.style.background = 'rgba(56, 189, 248, 0.1)';
    }, false);
  });

  ['dragleave', 'drop'].forEach(eventName => {
    dropzone.addEventListener(eventName, (e) => {
      e.preventDefault();
      dropzone.style.borderColor = 'rgba(56, 189, 248, 0.4)';
      dropzone.style.background = 'rgba(15, 23, 42, 0.5)';
    }, false);
  });

  dropzone.addEventListener('drop', (e) => {
    const dt = e.dataTransfer;
    const files = dt.files;
    if (files && files.length > 0) {
      uploadFile(files[0]);
    }
  });
}
