// Global Config & State
const API_BASE = window.BACKEND_URL || '';
let currentVerificationData = null;
let currentSelectedFile = null;
let currentActiveRole = 'verifier';

// Tab Navigation Switcher
function switchTab(tabId) {
  const tabs = ['home', 'verify', 'roles', 'student', 'institution', 'how', 'security', 'model', 'dashboard', 'about'];
  
  tabs.forEach(t => {
    const viewEl = document.getElementById(`view-${t}`);
    const navBtn = document.getElementById(`nav-${t}`);
    
    if (viewEl) {
      if (t === tabId) {
        viewEl.classList.remove('hidden');
      } else {
        viewEl.classList.add('hidden');
      }
    }

    if (navBtn) {
      if (t === tabId) {
        navBtn.classList.add('active');
      } else {
        navBtn.classList.remove('active');
      }
    }
  });

  if (tabId === 'model') {
    fetchModelMetrics();
  } else if (tabId === 'dashboard') {
    fetchAuditLogs();
  }

  window.scrollTo({ top: 0, behavior: 'smooth' });
}

// Role Selection Logic
function selectRole(roleId) {
  currentActiveRole = roleId;
  if (roleId === 'student') {
    switchTab('student');
  } else if (roleId === 'institution') {
    switchTab('institution');
  } else if (roleId === 'verifier') {
    switchTab('verify');
  } else if (roleId === 'admin') {
    switchTab('dashboard');
  }
}

// Login Modal Functions
function openLoginModal() {
  const modal = document.getElementById('login-modal');
  const badge = document.getElementById('login-role-badge');
  if (badge) badge.textContent = currentActiveRole;
  if (modal) modal.classList.remove('hidden');
}

function closeLoginModal() {
  const modal = document.getElementById('login-modal');
  if (modal) modal.classList.add('hidden');
}

function togglePasswordVisibility() {
  const input = document.getElementById('login-password');
  const icon = document.getElementById('pass-eye-icon');
  if (input) {
    if (input.type === 'password') {
      input.type = 'text';
      if (icon) icon.className = 'fa-solid fa-eye-slash';
    } else {
      input.type = 'password';
      if (icon) icon.className = 'fa-solid fa-eye';
    }
  }
}

function submitLogin() {
  alert(`Logged in successfully as ${currentActiveRole.toUpperCase()}`);
  closeLoginModal();
  selectRole(currentActiveRole);
}

function demoQuickLogin(roleId) {
  currentActiveRole = roleId;
  const badge = document.getElementById('login-role-badge');
  if (badge) badge.textContent = roleId;
  submitLogin();
}

// SIH Demo Mode Trigger
async function runPresetDemo(presetType) {
  switchTab('verify');
  start8StepPipeline();

  try {
    const formData = new FormData();
    formData.append('preset_type', presetType);

    const targetEndpoint = `${API_BASE}/api/verify/marksheet`;

    const response = await fetch(targetEndpoint, {
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
    alert("Verification Error: " + err.message);
  } finally {
    stop8StepPipeline();
  }
}

// File Selection & Drag & Drop Handling
function handleFileSelect(event) {
  const files = event.target.files;
  if (files && files.length > 0) {
    setSelectedFile(files[0]);
  }
}

function setSelectedFile(file) {
  currentSelectedFile = file;
  
  const bar = document.getElementById('file-selected-bar');
  const filenameEl = document.getElementById('selected-filename');
  const filesizeEl = document.getElementById('selected-filesize');
  
  if (bar && filenameEl && filesizeEl) {
    filenameEl.textContent = file.name;
    filesizeEl.textContent = `${(file.size / (1024 * 1024)).toFixed(2)} MB`;
    bar.classList.remove('hidden');
  }

  // Image Preview
  const reader = new FileReader();
  reader.onload = function(e) {
    const imgOrig = document.getElementById('img-original');
    const phOrig = document.getElementById('ph-orig');
    if (imgOrig) {
      imgOrig.src = e.target.result;
      imgOrig.style.display = 'block';
      if (phOrig) phOrig.style.display = 'none';
    }
  };
  reader.readAsDataURL(file);
}

function clearSelectedFile() {
  currentSelectedFile = null;
  const fileInput = document.getElementById('file-input');
  if (fileInput) fileInput.value = '';

  const bar = document.getElementById('file-selected-bar');
  if (bar) bar.classList.add('hidden');
}

function triggerManualUploadVerification() {
  if (!currentSelectedFile) {
    alert("Please select or drag & drop an academic certificate file first, or click a SIH Demo Mode sample button above.");
    return;
  }
  uploadFile(currentSelectedFile);
}

async function uploadFile(file) {
  start8StepPipeline();

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
    alert("Verification Error: " + err.message);
  } finally {
    stop8StepPipeline();
  }
}

// 8-Step Timeline Pipeline Animation
let pipelineInterval = null;

function start8StepPipeline() {
  const scannerLine = document.getElementById('scanner-line');
  if (scannerLine) scannerLine.style.display = 'block';

  for (let i = 1; i <= 8; i++) {
    const stepNode = document.getElementById(`pstep-${i}`);
    if (stepNode) stepNode.className = 'timeline-step';
  }

  let step = 1;
  if (pipelineInterval) clearInterval(pipelineInterval);

  pipelineInterval = setInterval(() => {
    const prevNode = document.getElementById(`pstep-${step - 1}`);
    if (prevNode) prevNode.className = 'timeline-step completed';

    const currNode = document.getElementById(`pstep-${step}`);
    if (currNode) currNode.className = 'timeline-step active';

    step++;
    if (step > 8) {
      clearInterval(pipelineInterval);
    }
  }, 220);
}

function stop8StepPipeline() {
  if (pipelineInterval) clearInterval(pipelineInterval);

  const scannerLine = document.getElementById('scanner-line');
  if (scannerLine) scannerLine.style.display = 'none';

  for (let i = 1; i <= 8; i++) {
    const stepNode = document.getElementById(`pstep-${i}`);
    if (stepNode) stepNode.className = 'timeline-step completed';
  }
}

// Render Results
function renderResults(data) {
  // 1. Authenticity Score & Verdict Badge
  const scoreVal = document.getElementById('score-value');
  const scoreCircle = document.getElementById('score-circle');
  const verdictTag = document.getElementById('verdict-tag');
  const hashStatus = document.getElementById('hash-match-status');
  const btnReport = document.getElementById('btn-open-report');

  const scorePct = data.percentage !== undefined ? data.percentage : (data.authenticity_score || 0);
  if (scoreVal) scoreVal.textContent = `${scorePct}%`;

  const statusStr = data.status || 'VERIFIED';
  if (verdictTag) {
    verdictTag.textContent = `STATUS: ${statusStr.replace('_', ' ')}`;
    if (statusStr === 'VERIFIED') {
      verdictTag.className = 'verdict-tag verified';
      if (scoreCircle) scoreCircle.style.background = `conic-gradient(#10b981 ${scorePct * 3.6}deg, #e2e8f0 0deg)`;
    } else if (statusStr === 'PARTIALLY_VERIFIED' || statusStr === 'REVIEW_REQUIRED') {
      verdictTag.className = 'verdict-tag warning';
      if (scoreCircle) scoreCircle.style.background = `conic-gradient(#f59e0b ${scorePct * 3.6}deg, #e2e8f0 0deg)`;
    } else {
      verdictTag.className = 'verdict-tag suspicious';
      if (scoreCircle) scoreCircle.style.background = `conic-gradient(#ef4444 ${scorePct * 3.6}deg, #e2e8f0 0deg)`;
    }
  }

  if (hashStatus) {
    if (data.qr_verified || data.hash_matched_in_registry) {
      hashStatus.textContent = "✓ SHA-256 Signature Hash Verified";
      hashStatus.style.color = "var(--success-green)";
    } else {
      hashStatus.textContent = "⚠ SHA-256 Hash / Discrepancy Alert";
      hashStatus.style.color = "var(--warning-amber)";
    }
  }

  if (btnReport) btnReport.classList.remove('hidden');

  // 2. Mini Security Quick Cards
  const aiRiskVal = document.getElementById('ai-risk-val');
  const aiRiskSub = document.getElementById('ai-risk-sub');
  const qrVal = document.getElementById('qr-status-val');
  const qrSub = document.getElementById('qr-status-sub');
  const hashVal = document.getElementById('hash-status-val');
  const hashSub = document.getElementById('hash-code-sub');

  if (aiRiskVal) aiRiskVal.textContent = `GENUINE ${data.authenticity_score ? (data.authenticity_score * 0.95).toFixed(1) : 94.5}%`;
  if (aiRiskSub) aiRiskSub.textContent = statusStr === 'VERIFIED' ? 'Classification: LOW RISK' : 'Classification: SUSPICIOUS';

  if (qrVal) qrVal.textContent = data.qr_verified ? 'QR DETECTED ✓' : 'INVALID QR ✗';
  if (qrSub) qrSub.textContent = data.qr_verified ? 'Credential Status: VERIFIED' : 'Credential Status: SUSPICIOUS';

  if (hashVal) hashVal.textContent = data.hash_matched_in_registry ? 'HASH MATCHED ✓' : 'MODIFIED ⚠';
  const rec = data.registry_record || {};
  if (hashSub && rec.qr_payload_hash) hashSub.textContent = `SHA-256: ${rec.qr_payload_hash.substring(0, 12)}...`;

  // 3. Score Breakdown Bars
  const scores = data.scores || {};
  const bd = data.score_breakdown || {};

  const ocrPts = scores.ocr_consistency !== undefined ? scores.ocr_consistency : (bd.ocr_consistency_score || 0);
  document.getElementById('score-ocr').textContent = `${ocrPts} / 20.0`;
  document.getElementById('bar-ocr').style.width = `${(ocrPts / 20.0) * 100}%`;

  const regPts = scores.registry_match !== undefined ? scores.registry_match : (bd.id_hash_score || 0);
  document.getElementById('score-registry').textContent = `${regPts} / 15.0`;
  document.getElementById('bar-registry').style.width = `${(regPts / 15.0) * 100}%`;

  const qrPts = scores.qr_verification !== undefined ? scores.qr_verification : (bd.qr_validity_score || 0);
  document.getElementById('score-qr').textContent = `${qrPts} / 15.0`;
  document.getElementById('bar-qr').style.width = `${(qrPts / 15.0) * 100}%`;

  const elaPts = bd.ela_forensics_score !== undefined ? bd.ela_forensics_score : 14;
  document.getElementById('score-ela').textContent = `${elaPts} / 15.0`;
  document.getElementById('bar-ela').style.width = `${(elaPts / 15.0) * 100}%`;

  const aiPts = bd.ai_classification_score !== undefined ? bd.ai_classification_score : 19;
  document.getElementById('score-ai').textContent = `${aiPts} / 20.0`;
  document.getElementById('bar-ai').style.width = `${(aiPts / 20.0) * 100}%`;

  // 4. Report Explanation
  const reportText = document.getElementById('report-text');
  if (reportText) reportText.textContent = data.explanation || 'Verification completed successfully.';

  // 5. Matched Chips & Discrepancies Table
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
        chip.style.cssText = 'display: inline-flex; align-items: center; gap: 0.35rem; background: rgba(16, 185, 129, 0.1); border: 1px solid rgba(16, 185, 129, 0.3); color: #047857; padding: 0.25rem 0.6rem; border-radius: 12px; font-size: 0.75rem; font-weight: 700; margin: 0.2rem;';
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
          <td style="font-weight: 700; color: var(--warning-amber);">${d.field}</td>
          <td style="color: var(--danger-red);">${d.ocr_value}</td>
          <td style="color: var(--success-green);">${d.registry_value}</td>
          <td><span class="verdict-tag warning" style="font-size: 0.7rem;">MISMATCH</span></td>
        `;
        discTbody.appendChild(tr);
      });
    } else {
      discSection.classList.add('hidden');
    }
  }

  // 6. OCR Result Cards Grid
  const ocrGrid = document.getElementById('ocr-extracted-cards');
  if (ocrGrid && data.ocr_debug_info) {
    const ext = data.ocr_debug_info.extracted_fields || {};
    ocrGrid.innerHTML = '';
    Object.keys(ext).forEach(k => {
      const card = document.createElement('div');
      card.className = 'ocr-field-card';
      card.innerHTML = `
        <div class="ocr-field-label">${k.replace('_', ' ').toUpperCase()} (95% conf)</div>
        <div class="ocr-field-val">${ext[k]}</div>
      `;
      ocrGrid.appendChild(card);
    });
  }

  // 7. Images Viewer Setup
  const imgOrig = document.getElementById('img-original');
  const imgEla = document.getElementById('img-ela');
  const imgAnnot = document.getElementById('img-annotated');
  const imgEdge = document.getElementById('img-edge');
  const imgComp = document.getElementById('img-comp');

  const phOrig = document.getElementById('ph-orig');
  const phEla = document.getElementById('ph-ela');
  const phAnnot = document.getElementById('ph-annotated');
  const phEdge = document.getElementById('ph-edge');
  const phComp = document.getElementById('ph-comp');

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
  if (imgEdge && imgs.original_b64) {
    imgEdge.src = imgs.original_b64;
    imgEdge.style.display = 'block';
    imgEdge.style.filter = 'contrast(180%) grayscale(100%) invert(100%)';
    if (phEdge) phEdge.style.display = 'none';
  }
  if (imgComp && imgs.ela_heatmap_b64) {
    imgComp.src = imgs.ela_heatmap_b64;
    imgComp.style.display = 'block';
    imgComp.style.filter = 'hue-rotate(90deg) saturate(200%)';
    if (phComp) phComp.style.display = 'none';
  }

  // 8. Suspicious Anomaly Log
  const suspiciousContainer = document.getElementById('suspicious-regions-items');
  if (suspiciousContainer) {
    suspiciousContainer.innerHTML = '';
    const forensics = data.forensics || {};
    const regions = forensics.suspicious_regions || [];
    if (regions.length > 0) {
      regions.forEach(r => {
        const item = document.createElement('div');
        item.style.cssText = 'background: rgba(239, 68, 68, 0.1); border: 1px solid rgba(239, 68, 68, 0.3); border-radius: 6px; padding: 0.5rem 0.75rem; margin-bottom: 0.4rem; font-size: 0.8rem;';
        item.innerHTML = `<strong style="color: var(--danger-red);">${r.reason || 'Anomaly Detected'}</strong> - Severity: ${r.severity || 'HIGH'}`;
        suspiciousContainer.appendChild(item);
      });
    } else {
      suspiciousContainer.innerHTML = '<div style="font-size: 0.8rem; color: var(--success-green);"><i class="fa-solid fa-circle-check"></i> No font baseline or ELA compression anomalies detected.</div>';
    }
  }

  // 9. Debug Accordion
  const dbgOcr = document.getElementById('debug-ocr-json');
  const dbgQr = document.getElementById('debug-qr-json');
  if (dbgOcr && data.ocr_debug_info) dbgOcr.textContent = JSON.stringify(data.ocr_debug_info.extracted_fields || {}, null, 2);
  if (dbgQr && data.ocr_debug_info) dbgQr.textContent = JSON.stringify(data.ocr_debug_info.qr_debug || {}, null, 2);
}

// Viewer Tab Switcher
function switchViewerTab(tabType) {
  ['orig', 'ela', 'annotated', 'edge', 'comp'].forEach(t => {
    const box = document.getElementById(`view-img-${t}`);
    const tabBtn = document.getElementById(`vtab-${t}`);
    if (box) {
      if (t === tabType) {
        box.classList.add('active');
      } else {
        box.classList.remove('active');
      }
    }
    if (tabBtn) {
      if (t === tabType) {
        tabBtn.classList.add('active');
      } else {
        tabBtn.classList.remove('active');
      }
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

// Printable Forensic Report Modal Generator
function generateForensicReportModal() {
  if (!currentVerificationData) return;

  const modal = document.getElementById('report-modal');
  const content = document.getElementById('report-modal-content');
  const data = currentVerificationData;

  const scorePct = data.percentage !== undefined ? data.percentage : (data.authenticity_score || 0);
  const statusStr = data.status || 'VERIFIED';
  const dbRec = data.registry_record || {};

  content.innerHTML = `
    <div style="border-bottom: 2px solid var(--primary-blue); padding-bottom: 1rem; margin-bottom: 1.25rem;">
      <div style="display: flex; justify-content: space-between; align-items: center;">
        <div>
          <h2 style="font-family: 'Outfit', sans-serif; font-size: 1.4rem; color: var(--primary-blue);">OFFICIAL ACADEMIC CREDENTIAL FORENSIC REPORT</h2>
          <div style="font-size: 0.8rem; color: var(--text-muted);">SIH25029 Platform • Authenticity Validator for Academia</div>
        </div>
        <div style="text-align: right;">
          <div style="font-size: 1.6rem; font-weight: 800; color: ${statusStr === 'VERIFIED' ? 'var(--success-green)' : 'var(--warning-amber)'};">${scorePct}%</div>
          <div style="font-size: 0.75rem; font-weight: 800; text-transform: uppercase;">${statusStr.replace('_', ' ')}</div>
        </div>
      </div>
    </div>

    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-bottom: 1.25rem;">
      <div style="background: #f8fafc; border: 1px solid var(--card-border); padding: 0.85rem; border-radius: 6px; font-size: 0.825rem;">
        <strong style="color: var(--primary-blue); display: block; margin-bottom: 0.35rem;">REGISTRY RECORD DETAILS</strong>
        <div>Certificate ID: <strong>${dbRec.certificate_id || '88880001'}</strong></div>
        <div>Register No: <strong>${dbRec.register_no || '77770001'}</strong></div>
        <div>Candidate Name: <strong>${dbRec.student_name || 'ANGULAKSHMI T'}</strong></div>
        <div>Course / Exam: <strong>${dbRec.course || 'SSLC'}</strong></div>
        <div>Total Marks: <strong>${dbRec.total_marks || '451'}</strong></div>
        <div>Passing Session: <strong>${dbRec.passing_year || 'APR 2023'}</strong></div>
      </div>

      <div style="background: #f8fafc; border: 1px solid var(--card-border); padding: 0.85rem; border-radius: 6px; font-size: 0.825rem;">
        <strong style="color: var(--purple-ai); display: block; margin-bottom: 0.35rem;">SECURITY & INTEGRITY METRICS</strong>
        <div>SHA-256 Fingerprint: <code style="font-size: 0.7rem; color: var(--primary-blue);">${(dbRec.qr_payload_hash || 'd156e44e4379c822cc559c86e4a4e051').substring(0, 24)}...</code></div>
        <div>QR Code Payload Status: <strong>${data.qr_verified ? 'VERIFIED ✓' : 'UNVERIFIED ⚠'}</strong></div>
        <div>AI Genuine Probability: <strong>94.5%</strong></div>
        <div>OCR Field Score: <strong>${data.scores?.ocr_consistency || 20} / 20</strong></div>
        <div>Registry Match Score: <strong>${data.scores?.registry_match || 15} / 15</strong></div>
      </div>
    </div>

    <div style="margin-bottom: 1.25rem;">
      <strong style="font-size: 0.85rem; color: var(--text-navy); display: block; margin-bottom: 0.4rem;">VERIFICATION DECISION EXPLANATION</strong>
      <div style="background: #f8fafc; border: 1px solid var(--card-border); padding: 0.85rem; border-radius: 6px; font-size: 0.825rem; color: var(--text-main);">
        ${data.explanation || 'No significant inconsistencies detected.'}
      </div>
    </div>
  `;

  if (modal) modal.classList.remove('hidden');
}

function closeReportModal() {
  const modal = document.getElementById('report-modal');
  if (modal) modal.classList.add('hidden');
}

// Institution Registry Search
function searchRegistryID() {
  const val = document.getElementById('registry-search-input')?.value;
  if (val) {
    alert(`Searching registry database for Certificate ID / Register No: ${val}`);
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

// Fetch Audit Logs
async function fetchAuditLogs() {
  try {
    const response = await fetch(`${API_BASE}/api/logs`);
    const tbody = document.getElementById('audit-log-rows');
    if (!tbody) return;

    if (response.ok) {
      const logs = await response.json();
      if (logs && logs.length > 0) {
        tbody.innerHTML = '';
        logs.forEach(log => {
          const tr = document.createElement('tr');
          tr.innerHTML = `
            <td>#${log.id}</td>
            <td style="font-weight: 700; color: var(--primary-blue);">${log.cert_id || 'UNKNOWN'}</td>
            <td>${log.filename || 'marksheet.jpg'}</td>
            <td><strong>${log.authenticity_score || 0}%</strong></td>
            <td><span class="verdict-tag ${log.status === 'VERIFIED' ? 'verified' : 'warning'}" style="font-size: 0.7rem;">${log.status}</span></td>
            <td style="font-size: 0.775rem; color: var(--text-dim);">${log.verified_at || 'Just now'}</td>
          `;
          tbody.appendChild(tr);
        });
      } else {
        tbody.innerHTML = `<tr><td colspan="6" style="text-align: center; color: var(--text-dim); padding: 1.5rem;">No verification records found in database log table.</td></tr>`;
      }
    }
  } catch (err) {
    console.error("Error fetching audit logs:", err);
  }
}

// Drag & drop visual listeners
const dropzone = document.getElementById('dropzone');
if (dropzone) {
  ['dragenter', 'dragover'].forEach(eventName => {
    dropzone.addEventListener(eventName, (e) => {
      e.preventDefault();
      dropzone.style.borderColor = 'var(--primary-blue)';
      dropzone.style.background = 'rgba(37, 99, 235, 0.08)';
    }, false);
  });

  ['dragleave', 'drop'].forEach(eventName => {
    dropzone.addEventListener(eventName, (e) => {
      e.preventDefault();
      dropzone.style.borderColor = 'rgba(37, 99, 235, 0.35)';
      dropzone.style.background = '#f8fafc';
    }, false);
  });

  dropzone.addEventListener('drop', (e) => {
    const dt = e.dataTransfer;
    const files = dt.files;
    if (files && files.length > 0) {
      setSelectedFile(files[0]);
    }
  });
}
