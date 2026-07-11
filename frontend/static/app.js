// ── State ──────────────────────────────────────────────────────────────────────
let pendingFiles = [];
let isStreaming  = false;

// ── Init ───────────────────────────────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
  loadStatus();
  setupDropZone();
  autoResizeTextarea();
  if (window.lucide) lucide.createIcons();
});

// ── Status ─────────────────────────────────────────────────────────────────────
async function loadStatus() {
  try {
    const res  = await fetch("/status");
    const data = await res.json();
    updateStatus(data);
  } catch (e) {
    console.error("Status fetch failed:", e);
  }
}

function updateStatus(data) {
  const badge    = document.getElementById("dbStatus");
  const statusText = document.getElementById("dbStatusText");
  const clearBtn = document.getElementById("clearBtn");
  const indexed  = document.getElementById("indexedSection");
  const fileDiv  = document.getElementById("indexedFiles");
  const empty    = document.getElementById("emptyState");

  if (data.chunk_count > 0) {
    badge.className  = "status-badge success";
    if (statusText) statusText.textContent = `Pinecone: ${data.chunk_count} vectors stored`;
    clearBtn.style.display = "block";
  } else {
    badge.className  = "status-badge empty";
    if (statusText) statusText.textContent = "Pinecone: empty";
    clearBtn.style.display = "none";
  }

  if (data.indexed_files && data.indexed_files.length > 0) {
    indexed.style.display = "block";
    fileDiv.innerHTML = data.indexed_files.map(f => `
      <div class="indexed-file-card">
        <div class="file-info-main">
          <svg class="file-icon" xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
          <div class="file-name-container">
            <span class="file-name">${escapeHtml(f)}</span>
            <span class="file-status-badge">✓ Indexed</span>
          </div>
        </div>
      </div>
    `).join("");
  } else {
    indexed.style.display = "none";
  }

  if (data.ready) {
    if (empty) empty.style.display = "none";
  }
}

// ── File handling ───────────────────────────────────────────────────────────────
function setupDropZone() {
  const zone  = document.getElementById("dropZone");
  const input = document.getElementById("fileInput");

  zone.addEventListener("dragover", e => {
    e.preventDefault();
    zone.classList.add("drag-over");
  });
  zone.addEventListener("dragleave", () => zone.classList.remove("drag-over"));
  zone.addEventListener("drop", e => {
    e.preventDefault();
    zone.classList.remove("drag-over");
    addFiles([...e.dataTransfer.files]);
  });

  input.addEventListener("change", () => addFiles([...input.files]));
}

function addFiles(files) {
  const allowed = ["pdf","txt","md","docx","csv","xlsx","json","pptx"];
  for (const f of files) {
    const ext = f.name.split(".").pop().toLowerCase();
    if (!allowed.includes(ext)) {
      showToast(`${f.name}: unsupported type`, "error");
      continue;
    }
    if (f.size > 20 * 1024 * 1024) {
      showToast(`${f.name}: exceeds 20MB`, "error");
      continue;
    }
    if (!pendingFiles.find(p => p.name === f.name)) {
      pendingFiles.push(f);
    }
  }
  renderFileList();
}

function renderFileList() {
  const list = document.getElementById("fileList");
  const fmt = n => n < 1024 ? n + ' B' : n < 1048576 ? (n/1024).toFixed(1) + ' KB' : (n/1048576).toFixed(1) + ' MB';
  list.innerHTML = pendingFiles.map((f, i) => `
    <div class="file-item-card">
      <div class="file-details">
        <svg class="file-icon" xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
        <div class="file-meta">
          <span class="file-name">${escapeHtml(f.name)}</span>
          <span class="file-size">${fmt(f.size)}</span>
        </div>
      </div>
      <button class="btn-remove-file" onclick="removeFile(${i})" title="Remove">
        <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
      </button>
    </div>
  `).join("");
}

function removeFile(i) {
  pendingFiles.splice(i, 1);
  renderFileList();
}

// ── Build index ─────────────────────────────────────────────────────────────────
async function buildIndex() {
  if (pendingFiles.length === 0) {
    showToast("Please upload at least one document.", "error");
    return;
  }

  const btn = document.getElementById("buildBtn");
  btn.disabled = true;
  btn.innerHTML = '<span class="spinner"></span> Uploading...';

  // Upload files
  const formData = new FormData();
  for (const f of pendingFiles) formData.append("files", f);

  try {
    const upRes  = await fetch("/upload", { method: "POST", body: formData });
    const upData = await upRes.json();

    if (upData.errors && upData.errors.length > 0) {
      showToast(upData.errors.join("\n"), "error");
    }

    if (!upData.saved || upData.saved.length === 0) {
      showToast("No files were uploaded.", "error");
      btn.disabled = false;
      btn.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="4" width="16" height="16" rx="2"/><rect x="9" y="9" width="6" height="6"/><line x1="9" y1="2" x2="9" y2="4"/><line x1="15" y1="2" x2="15" y2="4"/><line x1="9" y1="20" x2="9" y2="22"/><line x1="15" y1="20" x2="15" y2="22"/><line x1="20" y1="9" x2="22" y2="9"/><line x1="20" y1="15" x2="22" y2="15"/><line x1="2" y1="9" x2="4" y2="9"/><line x1="2" y1="15" x2="4" y2="15"/></svg> Build Index';
      return;
    }

    btn.innerHTML = '<span class="spinner"></span> Building index...';

    const buildRes  = await fetch("/build", { method: "POST" });
    const buildData = await buildRes.json();

    if (!buildRes.ok) {
      showToast(buildData.detail || "Build failed.", "error");
      btn.disabled = false;
      btn.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="4" width="16" height="16" rx="2"/><rect x="9" y="9" width="6" height="6"/><line x1="9" y1="2" x2="9" y2="4"/><line x1="15" y1="2" x2="15" y2="4"/><line x1="9" y1="20" x2="9" y2="22"/><line x1="15" y1="20" x2="15" y2="22"/><line x1="20" y1="9" x2="22" y2="9"/><line x1="20" y1="15" x2="22" y2="15"/><line x1="2" y1="9" x2="4" y2="9"/><line x1="2" y1="15" x2="4" y2="15"/></svg> Build Index';
      return;
    }

    pendingFiles = [];
    renderFileList();
    updateStatus({ ...buildData, ready: true });
    showToast(`✅ Index built — ${buildData.chunk_count} vectors stored`, "success");

    const empty = document.getElementById("emptyState");
    if (empty) empty.style.display = "none";

  } catch (e) {
    showToast("Build failed: " + e.message, "error");
  }

  btn.disabled = false;
  btn.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="4" width="16" height="16" rx="2"/><rect x="9" y="9" width="6" height="6"/><line x1="9" y1="2" x2="9" y2="4"/><line x1="15" y1="2" x2="15" y2="4"/><line x1="9" y1="20" x2="9" y2="22"/><line x1="15" y1="20" x2="15" y2="22"/><line x1="20" y1="9" x2="22" y2="9"/><line x1="20" y1="15" x2="22" y2="15"/><line x1="2" y1="9" x2="4" y2="9"/><line x1="2" y1="15" x2="4" y2="15"/></svg> Build Index';
}

// ── Clear database ──────────────────────────────────────────────────────────────
async function clearDatabase() {
  if (!confirm("Clear all indexed documents? This cannot be undone.")) return;
  try {
    await fetch("/clear", { method: "POST" });
    updateStatus({ chunk_count: 0, indexed_files: [], ready: false });
    document.getElementById("messages").innerHTML = `
      <div class="empty-state" id="emptyState">
        <div class="empty-state-welcome">Good to see you 👋</div>
        <p class="empty-state-desc">Upload your documents in the sidebar and click <strong>Build Index</strong> to start chatting with your knowledge base.</p>
      </div>`;
    showToast("Database cleared.", "success");
  } catch (e) {
    showToast("Clear failed: " + e.message, "error");
  }
}

// ── Chat ────────────────────────────────────────────────────────────────────────
function handleKey(e) {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
}

async function sendMessage() {
  const input = document.getElementById("userInput");
  const msg   = input.value.trim();
  if (!msg || isStreaming) return;

  input.value = "";
  input.style.height = "auto";
  isStreaming = true;

  const sendBtn = document.getElementById("sendBtn");
  sendBtn.disabled = true;

  // Remove empty state
  const empty = document.getElementById("emptyState");
  if (empty) empty.remove();

  // Add user message
  appendMessage("user", msg);

  // Add assistant bubble with typing indicator
  const assistantId = "msg-" + Date.now();
  appendAssistantBubble(assistantId);

  try {
    const res = await fetch("/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: msg }),
    });

    if (!res.ok) {
      const err = await res.json();
      updateBubble(assistantId, "⚠️ " + (err.detail || "Error occurred."), []);
      isStreaming = false;
      sendBtn.disabled = false;
      return;
    }

    const reader  = res.body.getReader();
    const decoder = new TextDecoder();
    let   buffer  = "";
    let   fullText = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop();

      for (const line of lines) {
        if (!line.startsWith("data: ")) continue;
        try {
          const event = JSON.parse(line.slice(6));
          if (event.type === "text") {
            fullText += event.content;
            updateBubbleText(assistantId, fullText);
          } else if (event.type === "done") {
            updateBubble(assistantId, fullText, event.sources || []);
          } else if (event.type === "error") {
            updateBubble(assistantId, "⚠️ " + event.content, []);
          }
        } catch {}
      }
    }
  } catch (e) {
    updateBubble(assistantId, "⚠️ Connection error: " + e.message, []);
  }

  isStreaming = false;
  sendBtn.disabled = false;
  scrollToBottom();
}

// ── DOM helpers ─────────────────────────────────────────────────────────────────
function appendMessage(role, content) {
  const messages = document.getElementById("messages");
  const div = document.createElement("div");
  div.className = `message ${role}`;
  div.innerHTML = `
    <div class="avatar">${role === "user" ? "👤" : "🤖"}</div>
    <div class="bubble">${escapeHtml(content)}</div>
  `;
  messages.appendChild(div);
  scrollToBottom();
}

function appendAssistantBubble(id) {
  const messages = document.getElementById("messages");
  const div = document.createElement("div");
  div.className = "message assistant";
  div.id = id;
  div.innerHTML = `
    <div class="avatar">🤖</div>
    <div class="bubble">
      <div class="typing"><span></span><span></span><span></span></div>
    </div>
  `;
  messages.appendChild(div);
  scrollToBottom();
}

function updateBubbleText(id, text) {
  const el = document.getElementById(id);
  if (!el) return;
  const bubble = el.querySelector(".bubble");
  bubble.classList.add('stream-cursor');
  bubble.innerHTML = formatText(text);
  scrollToBottom();
}

function updateBubble(id, text, sources) {
  const el = document.getElementById(id);
  if (!el) return;
  const bubble = el.querySelector(".bubble");

  let html = formatText(text);

  if (sources && sources.length > 0) {
    html += `<div class="sources">
      <div class="sources-title">
        <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
        Sources
      </div>
      <div class="sources-grid">
      ${sources.map(s => `
        <div class="source-item-card">
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
          <div class="source-file-details">
            <span class="source-file-name">${escapeHtml(s.file)}</span>
            <span class="source-file-page">${s.page ? `Page ${s.page}` : 'Document'}</span>
          </div>
          <span class="source-score-badge">${s.score}</span>
        </div>
      `).join("")}
      </div>
    </div>`;
  }

  bubble.classList.remove('stream-cursor');
  bubble.innerHTML = html;

  // Inject copy button
  const actions = document.createElement('div');
  actions.className = 'bubble-actions';
  actions.innerHTML = `
    <button class="copy-btn" onclick="copyBubble(this, ${JSON.stringify(text)})">
      <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
      Copy
    </button>`;
  bubble.appendChild(actions);

  scrollToBottom();
}

function formatText(text) {
  // Process code fences first (``` ... ``` blocks)
  let html = String(text).replace(/```([\s\S]*?)```/g, (_, code) => {
    return `<pre><code>${escapeHtml(code.trim())}</code></pre>`;
  });

  // Inline code (`...`)
  html = html.replace(/`([^`]+)`/g, (_, code) => `<code>${escapeHtml(code)}</code>`);

  // Escape remaining HTML in non-code segments
  html = html.split('<pre>').map((segment, i) => {
    if (i === 0) {
      return segment
        .replace(/&(?!amp;|lt;|gt;|quot;)/g, '&amp;')
        .replace(/(?<!<code>.*?)<(?!\/?(pre|code|strong|em|p|br|ul|ol|li|h[1-6])[ >])/g, '&lt;');
    }
    return segment;
  }).join('<pre>');

  // Headers
  html = html.replace(/^### (.+)$/gm, '<h3>$1</h3>');
  html = html.replace(/^## (.+)$/gm, '<h2>$1</h2>');
  html = html.replace(/^# (.+)$/gm, '<h1>$1</h1>');

  // Bold and italic
  html = html.replace(/\*\*\*(.+?)\*\*\*/g, '<strong><em>$1</em></strong>');
  html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
  html = html.replace(/\*(.+?)\*/g, '<em>$1</em>');

  // Unordered lists
  html = html.replace(/^[-*] (.+)$/gm, '<li>$1</li>');
  html = html.replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>');

  // Ordered lists
  html = html.replace(/^\d+\. (.+)$/gm, '<li>$1</li>');

  // Horizontal rules
  html = html.replace(/^---+$/gm, '<hr>');

  // Paragraphs from double line breaks
  html = html.replace(/\n\n+/g, '</p><p>');
  html = html.replace(/\n/g, '<br>');

  return `<p>${html}</p>`;
}

function escapeHtml(text) {
  return String(text)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function scrollToBottom() {
  const messages = document.getElementById("messages");
  messages.scrollTop = messages.scrollHeight;
}

function autoResizeTextarea() {
  const ta = document.getElementById("userInput");
  ta.addEventListener("input", () => {
    ta.style.height = "auto";
    ta.style.height = Math.min(ta.scrollHeight, 120) + "px";
  });
}

// ── Toast ───────────────────────────────────────────────────────────────────────
const TOAST_ICONS = {
  success: `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>`,
  error:   `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>`,
  info:    `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>`,
};

function showToast(msg, type = "info") {
  const toast = document.createElement("div");
  toast.className = `toast ${type}`;
  toast.innerHTML = `${TOAST_ICONS[type] || ''}<span>${escapeHtml(msg)}</span>`;
  document.body.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(8px)';
    toast.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}

// ── Suggestion Chips ────────────────────────────────────────────────────────────
function sendSuggestion(btn) {
  const input = document.getElementById('userInput');
  if (!input) return;
  input.value = btn.textContent.trim();
  input.focus();
  // Auto-resize
  input.style.height = 'auto';
  input.style.height = Math.min(input.scrollHeight, 120) + 'px';
  sendMessage();
}

// ── Copy Bubble ──────────────────────────────────────────────────────────────────
function copyBubble(btn, text) {
  navigator.clipboard.writeText(text).then(() => {
    btn.classList.add('copied');
    btn.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg> Copied!`;
    setTimeout(() => {
      btn.classList.remove('copied');
      btn.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg> Copy`;
    }, 2000);
  }).catch(() => showToast('Copy failed', 'error'));
}

/* ==========================================================
   Camera + Image Detection
========================================================== */

let currentStream = null;
let selectedImage = null;

// DOM
const cameraBtn = document.getElementById("cameraBtn");
const uploadBtn = document.getElementById("uploadImageBtn");
const imageInput = document.getElementById("imageInput");

const cameraModal = document.getElementById("cameraModal");
const cameraVideo = document.getElementById("cameraVideo");
const cameraCanvas = document.getElementById("cameraCanvas");

const captureBtn = document.getElementById("captureBtn");
const closeCameraBtn = document.getElementById("closeCameraBtn");

const previewContainer = document.getElementById("imagePreviewContainer");
const previewImage = document.getElementById("previewImage");
const removeImageBtn = document.getElementById("removeImageBtn");

const detectionPanel = document.getElementById("detectionResults");
const detectedObjects = document.getElementById("detectedObjects");


// ----------------------------------------------------
// Open Camera
// ----------------------------------------------------

cameraBtn?.addEventListener("click", openCamera);

async function openCamera(){

    try{

        currentStream = await navigator.mediaDevices.getUserMedia({

            video:{
                facingMode:"environment"
            },

            audio:false

        });

        cameraVideo.srcObject = currentStream;

        cameraModal.style.display = "flex";

    }

    catch(err){

        showToast("Unable to access camera.","error");

        console.error(err);

    }

}


// ----------------------------------------------------
// Close Camera
// ----------------------------------------------------

closeCameraBtn?.addEventListener("click", closeCamera);

function closeCamera(){

    if(currentStream){

        currentStream.getTracks().forEach(track=>track.stop());

        currentStream=null;

    }

    cameraModal.style.display="none";

}


// ----------------------------------------------------
// Capture
// ----------------------------------------------------

captureBtn?.addEventListener("click",()=>{

    cameraCanvas.width=cameraVideo.videoWidth;

    cameraCanvas.height=cameraVideo.videoHeight;

    const ctx=cameraCanvas.getContext("2d");

    ctx.drawImage(

        cameraVideo,

        0,

        0,

        cameraCanvas.width,

        cameraCanvas.height

    );

    cameraCanvas.toBlob(blob=>{

        selectedImage=new File(

            [blob],

            "capture.jpg",

            {

                type:"image/jpeg"

            }

        );

        showPreview(selectedImage);

        closeCamera();

        detectImage(selectedImage);

    });

});


// ----------------------------------------------------
// Upload Image
// ----------------------------------------------------

uploadBtn?.addEventListener("click",()=>{

    imageInput.click();

});

imageInput?.addEventListener("change",(e)=>{
    const files = [...e.target.files];
    if (!files || files.length === 0) return;

    const docs = [];
    let imageFile = null;
    const allowedDocs = ["pdf","txt","md","docx","csv","xlsx","json","pptx"];

    for (const file of files) {
        const ext = file.name.split(".").pop().toLowerCase();
        if (allowedDocs.includes(ext)) {
            docs.push(file);
        } else if (file.type.startsWith("image/")) {
            imageFile = file;
        } else {
            showToast(`${file.name}: unsupported format`, "error");
        }
    }

    if (docs.length > 0) {
        addFiles(docs);
        showToast(`Added ${docs.length} document(s) to sidebar queue`, "success");
    }

    if (imageFile) {
        selectedImage = imageFile;
        showPreview(imageFile);
        detectImage(imageFile);
    }

    imageInput.value = "";
});

function toggleSidebar() {
    const layout = document.querySelector(".layout");
    const sidebar = document.querySelector(".sidebar");
    if (window.innerWidth <= 768) {
        sidebar.classList.toggle("open");
    } else {
        layout.classList.toggle("sidebar-collapsed");
    }
}


// ----------------------------------------------------
// Preview
// ----------------------------------------------------

function showPreview(file){

    const reader=new FileReader();

    reader.onload=(e)=>{

        previewImage.src=e.target.result;

        previewContainer.style.display="block";

    };

    reader.readAsDataURL(file);

}

removeImageBtn?.addEventListener("click",()=>{

    previewContainer.style.display="none";

    detectionPanel.style.display="none";

    previewImage.src="";

    imageInput.value="";

    selectedImage=null;

});


// ----------------------------------------------------
// Detect
// ----------------------------------------------------

async function detectImage(file){

    const formData=new FormData();

    formData.append("image",file);

    try{

        showToast("Running AI detection...");

        const response=await fetch("/detect",{

            method:"POST",

            body:formData

        });

        if(!response.ok){

            throw new Error("Detection failed.");

        }

        const result=await response.json();

        renderDetection(result);

    }

    catch(err){

        console.error(err);

        showToast(err.message,"error");

    }

}


// ----------------------------------------------------
// Detection UI
// ----------------------------------------------------

function renderDetection(result){

    detectionPanel.style.display="block";

    detectedObjects.innerHTML="";

    if(!result.detections?.length){

        detectedObjects.innerHTML="<p>No objects detected.</p>";

        return;

    }

    let summary=[];

    result.detections.forEach(item=>{

        summary.push(item.class);

        detectedObjects.innerHTML+=`

        <div class="detect-card">

            <div class="detect-left">

                <div class="detect-class">

                    ${item.class}

                </div>

                <div class="detect-conf">

                    Confidence

                </div>

            </div>

            <div class="detect-score">

                ${(item.confidence*100).toFixed(1)}%

            </div>

        </div>

        `;

    });

    if(result.annotated_image){

        detectedObjects.innerHTML+=`

        <div class="bounding-preview">

            <img src="${result.annotated_image}">

        </div>

        `;

    }

    document.getElementById("userInput").value=

`Detected:

${summary.join(", ")}

Explain this industrial drawing.`;

}