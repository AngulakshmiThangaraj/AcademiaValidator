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

// 1-Click Preset Scenario Trigger
async function runPreset(type) {
  startProcessingAnimation();

  try {
    const formData = new FormData();
    formData.append('preset_type', type);

    const targetEndpoint = type.startsWith('tn_sslc') ? `${API_BASE}/api/verify/marksheet` : `${API_BASE}/api/verify`;

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
    alert("Verification failed: " + err.message);
  } finally {
    stopProcessingAnimation();
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
  document.getElementById('scanner-line').style.display = 'block';
  
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
  document.getElementById('scanner-line').style.display = 'none';
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
  scoreVal.textContent = `${scorePct}%`;

  const statusStr = data.status || 'VERIFIED';
  verdictTag.textContent = `STATUS: ${statusStr.replace('_', ' ')}`;

  if (statusStr === 'VERIFIED') {
    verdictTag.className = 'verdict-tag verified';
    scoreCircle.style.background = `conic-gradient(#10b981 ${scorePct * 3.6}deg, rgba(255,255,255,0.1) 0deg)`;
  } else if (statusStr === 'PARTIALLY_VERIFIED' || statusStr === 'REVIEW_REQUIRED') {
    verdictTag.className = 'verdict-tag warning';
    verdictTag.style.background = 'rgba(245, 158, 11, 0.2)';
    verdictTag.style.color = '#fde68a';
    scoreCircle.style.background = `conic-gradient(#f59e0b ${scorePct * 3.6}deg, rgba(255,255,255,0.1) 0deg)`;
  } else {
    verdictTag.className = 'verdict-tag suspicious';
    scoreCircle.style.background = `conic-gradient(#ef4444 ${scorePct * 3.6}deg, rgba(255,255,255,0.1) 0deg)`;
  }

  if (data.qr_verified || data.hash_matched_in_registry) {
    hashStatus.textContent = "✓ SHA-256 & Registry Hash Verified";
    hashStatus.style.color = "var(--success-green)";
  } else {
    hashStatus.textContent = "✗ Registry Hash Mismatch / Unverified";
    hashStatus.style.color = "var(--danger-red)";
  }

  // 2. Score Factor Breakdown Bars
  const scores = data.scores || {};
  const bd = data.score_breakdown || {};

  const ocrPts = scores.ocr_consistency !== undefined ? scores.ocr_consistency : bd.ocr_consistency_score;
  document.getElementById('score-ocr').textContent = `${ocrPts} / 20.0`;
  document.getElementById('bar-ocr').style.width = `${(ocrPts / 20.0) * 100}%`;

  const regPts = scores.registry_match !== undefined ? scores.registry_match : bd.id_hash_score;
  document.getElementById('score-id').textContent = `${regPts} / 15.0`;
  document.getElementById('bar-id').style.width = `${(regPts / 15.0) * 100}%`;

  const qrPts = scores.qr_verification !== undefined ? scores.qr_verification : bd.qr_validity_score;
  document.getElementById('score-qr').textContent = `${qrPts} / 15.0`;
  document.getElementById('bar-qr').style.width = `${(qrPts / 15.0) * 100}%`;

  const elaPts = bd.ela_forensics_score !== undefined ? bd.ela_forensics_score : '--';
  document.getElementById('score-ela').textContent = `${elaPts}`;
  document.getElementById('bar-ela').style.width = `${typeof elaPts === 'number' ? (elaPts / 15.0) * 100 : 80}%`;

  // 3. Image Viewer
  switchViewerTab('orig');

  // 4. Extracted Metadata Table
  const tableBody = document.getElementById('metadata-table-body');
  tableBody.innerHTML = '';

  const fieldsList = [
    { key: 'certificate_id', label: 'Certificate ID' },
    { key: 'register_no', label: 'Register Number' },
    { key: 'student_name', label: 'Student Name' },
    { key: 'dob', label: 'Date of Birth (DOB)' },
    { key: 'total_marks', label: 'Total Marks' },
    { key: 'father_name', label: "Father's Name" },
    { key: 'passing_year', label: 'Passing Year' }
  ];

  const dbRec = data.registry_record || data.database_registry_record || {};
  const extractedObj = data.ocr_debug_info?.extracted_fields || data.extracted_ocr_fields || {};

  fieldsList.forEach(f => {
    const tr = document.createElement('tr');
    
    let extValObj = extractedObj[f.key];
    let extVal = 'Not Extracted';
    let confStr = '';
    if (extValObj && typeof extValObj === 'object') {
      extVal = extValObj.value !== null && extValObj.value !== undefined ? extValObj.value : 'Not Extracted';
      if (extValObj.confidence) {
        confStr = ` (${Math.round(extValObj.confidence * 100)}%)`;
      }
    } else if (extValObj) {
      extVal = extValObj;
    }

    let dbVal = dbRec[f.key] || dbRec['cert_id'] || 'Not Registered';
    if (f.key === 'certificate_id') dbVal = dbRec['certificate_id'] || dbRec['cert_id'] || 'Not Registered';
    if (f.key === 'total_marks') dbVal = dbRec['total_marks'] || dbRec['cgpa'] || 'Not Registered';

    let isMatched = false;
    if (data.matched_fields && data.matched_fields.includes(f.key)) {
      isMatched = true;
    } else if (extVal !== 'Not Extracted' && dbVal !== 'Not Registered') {
      if (String(extVal).toLowerCase().replace(/\s/g, '').includes(String(dbVal).toLowerCase().replace(/\s/g, ''))) {
        isMatched = true;
      }
    }

    tr.innerHTML = `
      <td style="font-weight: 600;">${f.label}</td>
      <td>${extVal}${confStr}</td>
      <td>${dbVal}</td>
      <td>
        <span class="match-tag ${isMatched ? 'match' : 'mismatch'}">
          ${isMatched ? 'MATCH ✓' : 'DISCREPANCY ✗'}
        </span>
      </td>
    `;
    tableBody.appendChild(tr);
  });

  // 5. Explainable Report Bullets & Discrepancies
  const explanationEl = document.getElementById('explanation-text');
  if (explanationEl) {
    explanationEl.textContent = data.explanation || 'Verification scan completed successfully.';
  }

  const bulletList = document.getElementById('report-bullets-list');
  bulletList.innerHTML = '';

  const reportItems = [];
  if (data.matched_fields && data.matched_fields.length > 0) {
    reportItems.push(`✓ Verified Matched Fields: ${data.matched_fields.join(', ')}`);
  }
  if (data.discrepancies && data.discrepancies.length > 0) {
    data.discrepancies.forEach(d => {
      reportItems.push(`✗ Discrepancy in ${d.field}: OCR '${d.ocr_value}' vs Registry '${d.registry_value}' (${d.reason})`);
    });
  }
  if (data.explainable_report) {
    data.explainable_report.forEach(b => reportItems.push(b));
  }

  reportItems.forEach(bullet => {
    const li = document.createElement('li');
    li.textContent = bullet;
    if (bullet.startsWith('✓')) {
      li.style.borderColor = 'rgba(16, 185, 129, 0.3)';
      li.style.color = '#a7f3d0';
    } else if (bullet.startsWith('✗')) {
      li.style.borderColor = 'rgba(239, 68, 68, 0.3)';
      li.style.color = '#fca5a5';
    } else {
      li.style.borderColor = 'rgba(245, 158, 11, 0.3)';
      li.style.color = '#fde68a';
    }
    bulletList.appendChild(li);
  });

  // 6. OCR Debug Information Fill
  if (data.ocr_debug_info) {
    const dbg = data.ocr_debug_info;
    document.getElementById('debug-engine').textContent = dbg.ocr_engine_info?.engine_used || 'Dictionary Fallback Parser';
    document.getElementById('debug-rec-id').textContent = dbg.matching_record_id || 'None';
    document.getElementById('debug-qr-payload').textContent = JSON.stringify(dbg.qr_debug?.payload || dbg.qr_debug || {}, null, 2);
    document.getElementById('debug-raw-ocr').textContent = dbg.raw_text || 'Raw text processed.';
  }
}

// Viewer Tab Switcher
function switchViewerTab(tabType) {
  currentActiveTab = tabType;
  const viewerImg = document.getElementById('viewer-img');

  ['orig', 'ela', 'annot'].forEach(t => {
    const btn = document.getElementById(`tab-${t}`);
    if (btn) {
      if (t === tabType) {
        btn.classList.add('active');
      } else {
        btn.classList.remove('active');
      }
    }
  });

  if (!currentVerificationData) return;

  const imgs = currentVerificationData.images || {};
  if (tabType === 'orig') {
    viewerImg.src = imgs.original_b64 || '';
  } else if (tabType === 'ela') {
    viewerImg.src = imgs.ela_heatmap_b64 || '';
  } else if (tabType === 'annot') {
    viewerImg.src = imgs.annotated_suspicious_b64 || '';
  }
}

// Fetch Model Metrics
async function fetchModelMetrics() {
  try {
    const response = await fetch(`${API_BASE}/api/metrics`);
    if (response.ok) {
      const m = await response.json();
      document.getElementById('metric-acc').textContent = `${(m.accuracy * 100).toFixed(1)}%`;
      document.getElementById('metric-prec').textContent = `${(m.precision * 100).toFixed(1)}%`;
      document.getElementById('metric-rec').textContent = `${(m.recall * 100).toFixed(1)}%`;
      document.getElementById('metric-f1').textContent = `${(m.f1_score * 100).toFixed(1)}%`;

      if (m.confusion_matrix) {
        document.getElementById('cm-00').textContent = m.confusion_matrix[0][0];
        document.getElementById('cm-01').textContent = m.confusion_matrix[0][1];
        document.getElementById('cm-10').textContent = m.confusion_matrix[1][0];
        document.getElementById('cm-11').textContent = m.confusion_matrix[1][1];
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
