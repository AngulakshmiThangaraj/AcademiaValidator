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

  // Update navbar active state
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

    const response = await fetch(`${API_BASE}/api/verify`, {
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

    const response = await fetch(`${API_BASE}/api/verify`, {
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

  const score = data.authenticity_score;
  scoreVal.textContent = `${score}%`;

  if (data.status === 'VERIFIED') {
    verdictTag.textContent = 'STATUS: VERIFIED';
    verdictTag.className = 'verdict-tag verified';
    scoreCircle.style.background = `conic-gradient(#10b981 ${score * 3.6}deg, rgba(255,255,255,0.1) 0deg)`;
  } else {
    verdictTag.textContent = 'STATUS: SUSPICIOUS';
    verdictTag.className = 'verdict-tag suspicious';
    scoreCircle.style.background = `conic-gradient(#ef4444 ${score * 3.6}deg, rgba(255,255,255,0.1) 0deg)`;
  }

  if (data.hash_matched_in_registry) {
    hashStatus.textContent = "✓ SHA-256 Hash Matched Registry Copy";
    hashStatus.style.color = "var(--success-green)";
  } else {
    hashStatus.textContent = "✗ Document Hash Modified / Unregistered";
    hashStatus.style.color = "var(--danger-red)";
  }

  // 2. Score Factor Breakdown Bars
  const bd = data.score_breakdown;
  document.getElementById('score-ai').textContent = `${bd.ai_prediction_score} / 35.0`;
  document.getElementById('bar-ai').style.width = `${(bd.ai_prediction_score / 35.0) * 100}%`;

  document.getElementById('score-ocr').textContent = `${bd.ocr_consistency_score} / 20.0`;
  document.getElementById('bar-ocr').style.width = `${(bd.ocr_consistency_score / 20.0) * 100}%`;

  document.getElementById('score-qr').textContent = `${bd.qr_validity_score} / 15.0`;
  document.getElementById('bar-qr').style.width = `${(bd.qr_validity_score / 15.0) * 100}%`;

  document.getElementById('score-id').textContent = `${bd.id_hash_score} / 15.0`;
  document.getElementById('bar-id').style.width = `${(bd.id_hash_score / 15.0) * 100}%`;

  document.getElementById('score-ela').textContent = `${bd.ela_forensics_score} / 15.0`;
  document.getElementById('bar-ela').style.width = `${(bd.ela_forensics_score / 15.0) * 100}%`;

  // 3. Image Viewer
  switchViewerTab('orig');

  // 4. Extracted Metadata Table
  const tableBody = document.getElementById('metadata-table-body');
  tableBody.innerHTML = '';

  const fields = [
    { key: 'student_name', label: 'Student Name' },
    { key: 'reg_no', label: 'Register Number' },
    { key: 'institution', label: 'Institution' },
    { key: 'course', label: 'Course' },
    { key: 'cgpa', label: 'CGPA / Marks' },
    { key: 'cert_id', label: 'Certificate ID' }
  ];

  const dbRec = data.database_registry_record || {};
  const ocrRec = data.extracted_ocr_fields || {};

  fields.forEach(f => {
    const tr = document.createElement('tr');
    const extVal = ocrRec[f.key] || 'Not Extracted';
    const dbVal = dbRec[f.key] || 'Not Registered';

    let isMatch = false;
    if (extVal !== 'Not Extracted' && dbVal !== 'Not Registered') {
      if (String(extVal).toLowerCase().includes(String(dbVal).toLowerCase()) || String(dbVal).toLowerCase().includes(String(extVal).toLowerCase())) {
        isMatch = true;
      }
    }

    tr.innerHTML = `
      <td style="font-weight: 600;">${f.label}</td>
      <td>${extVal}</td>
      <td>${dbVal}</td>
      <td>
        <span class="match-tag ${isMatch ? 'match' : 'mismatch'}">
          ${isMatch ? 'MATCH' : 'DISCREPANCY'}
        </span>
      </td>
    `;
    tableBody.appendChild(tr);
  });

  // 5. Explainable Report Bullets
  const bulletList = document.getElementById('report-bullets-list');
  bulletList.innerHTML = '';
  (data.explainable_report || []).forEach(bullet => {
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

// Certificate Registration Form Handler
async function handleRegisterSubmit(event) {
  event.preventDefault();

  const formData = new FormData();
  formData.append('cert_id', document.getElementById('reg-cert-id').value);
  formData.append('reg_no', document.getElementById('reg-student-no').value);
  formData.append('student_name', document.getElementById('reg-student-name').value);
  formData.append('institution', document.getElementById('reg-institution').value);
  formData.append('course', document.getElementById('reg-course').value);
  formData.append('cgpa', document.getElementById('reg-cgpa').value);
  formData.append('issue_date', document.getElementById('reg-date').value);

  try {
    const response = await fetch(`${API_BASE}/api/register`, {
      method: 'POST',
      body: formData
    });

    if (response.ok) {
      const res = await response.json();
      document.getElementById('register-result-box').classList.remove('hidden');
      document.getElementById('reg-sha-hash').textContent = `SHA-256 Document Fingerprint: ${res.sha256_fingerprint}`;
      document.getElementById('reg-qr-img').src = res.qr_code_b64;
    } else {
      alert("Registration failed: " + await response.text());
    }
  } catch (err) {
    alert("Error: " + err.message);
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
