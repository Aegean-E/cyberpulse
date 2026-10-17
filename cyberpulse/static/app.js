/**
 * CYBERPULSE // NEURAL INTRUSION CYBERDECK CLIENT
 * Pure Vanilla JavaScript: Web Audio Synthesizer, 2D Matrix Canvas, & Interactive Mini-Games
 */

// ==========================================================================
// 1. Web Audio API Sound Synthesizer (Zero External Audio Files)
// ==========================================================================
class SoundFX {
  constructor() {
    this.ctx = null;
    this.enabled = true;
  }

  init() {
    if (!this.ctx) {
      const AudioCtx = window.AudioContext || window.webkitAudioContext;
      if (AudioCtx) {
        this.ctx = new AudioCtx();
      }
    }
    if (this.ctx && this.ctx.state === "suspended") {
      this.ctx.resume();
    }
  }

  playTone(freq, type = "sine", duration = 0.1, gainVal = 0.15) {
    if (!this.enabled) return;
    this.init();
    if (!this.ctx) return;

    try {
      const osc = this.ctx.createOscillator();
      const gain = this.ctx.createGain();
      osc.type = type;
      osc.frequency.setValueAtTime(freq, this.ctx.currentTime);
      gain.gain.setValueAtTime(gainVal, this.ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, this.ctx.currentTime + duration);

      osc.connect(gain);
      gain.connect(this.ctx.destination);
      osc.start();
      osc.stop(this.ctx.currentTime + duration);
    } catch (_) {}
  }

  click() {
    this.playTone(850, "square", 0.03, 0.05);
  }

  scan() {
    if (!this.enabled) return;
    this.init();
    if (!this.ctx) return;
    try {
      const osc = this.ctx.createOscillator();
      const gain = this.ctx.createGain();
      osc.type = "sawtooth";
      osc.frequency.setValueAtTime(300, this.ctx.currentTime);
      osc.frequency.exponentialRampToValueAtTime(1400, this.ctx.currentTime + 0.25);
      gain.gain.setValueAtTime(0.12, this.ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, this.ctx.currentTime + 0.25);
      osc.connect(gain);
      gain.connect(this.ctx.destination);
      osc.start();
      osc.stop(this.ctx.currentTime + 0.25);
    } catch (_) {}
  }

  nearMiss() {
    // High-arousal double heart-thump
    this.playTone(180, "triangle", 0.12, 0.35);
    setTimeout(() => this.playTone(220, "triangle", 0.15, 0.4), 140);
  }

  success() {
    // Cyberpunk major arpeggio
    const notes = [523.25, 659.25, 783.99, 1046.50];
    notes.forEach((freq, idx) => {
      setTimeout(() => this.playTone(freq, "sine", 0.2, 0.2), idx * 75);
    });
  }

  jackpot() {
    // 2.5x Jackpot celebration chime
    const notes = [440, 554.37, 659.25, 880, 1108.73, 1318.51];
    notes.forEach((freq, idx) => {
      setTimeout(() => this.playTone(freq, "triangle", 0.28, 0.25), idx * 60);
    });
  }

  failure() {
    this.playTone(140, "sawtooth", 0.35, 0.3);
  }

  alarm() {
    this.playTone(480, "sawtooth", 0.2, 0.3);
    setTimeout(() => this.playTone(360, "sawtooth", 0.2, 0.3), 120);
  }
}

const sfx = new SoundFX();

// ==========================================================================
// 2. Cyberdeck Application State Coordinator
// ==========================================================================
const state = {
  data: null,
  selectedNodeId: null,
  activePuzzle: null,
  bufferInput: [],
  animFrameId: null,
  packetParticles: [],
};

// Node matrix layout coordinates on 800x560 canvas
const NODE_POSITIONS = {
  node_gateway:       { x: 100, y: 280, label: "GATEWAY" },
  node_proxy_a:       { x: 260, y: 150, label: "PROXY ALPHA" },
  node_proxy_b:       { x: 260, y: 410, label: "PROXY BETA" },
  node_vault_1:       { x: 450, y: 90,  label: "FINANCIAL VAULT" },
  node_vault_2:       { x: 450, y: 470, label: "PROTOTYPE ARCHIVE" },
  node_ice_perimeter: { x: 500, y: 280, label: "BLACK ICE CLUSTER" },
  node_central_core:  { x: 700, y: 280, label: "SUPERCORE" },
};

// ==========================================================================
// 3. API Communication Layer
// ==========================================================================
async function apiGet(endpoint) {
  try {
    const res = await fetch(endpoint);
    return await res.json();
  } catch (err) {
    console.error("API GET Error:", err);
    return null;
  }
}

async function apiPost(endpoint, payload) {
  try {
    const res = await fetch(endpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    return await res.json();
  } catch (err) {
    console.error("API POST Error:", err);
    return null;
  }
}

// ==========================================================================
// 4. Initial Setup & Event Listeners
// ==========================================================================
document.addEventListener("DOMContentLoaded", () => {
  initUIEvents();
  initMatrixCanvas();
  refreshFullState();
});

function initUIEvents() {
  // First user interaction unlocks AudioContext
  document.body.addEventListener("click", () => sfx.init(), { once: true });

  // Header toggles
  const btnAudio = document.getElementById("btn-audio");
  btnAudio.addEventListener("click", () => {
    sfx.enabled = !sfx.enabled;
    btnAudio.textContent = sfx.enabled ? "🔊 FX: ON" : "🔇 FX: OFF";
    if (sfx.enabled) sfx.click();
  });

  const btnCrt = document.getElementById("btn-crt");
  btnCrt.addEventListener("click", () => {
    document.body.classList.toggle("crt-effects");
    btnCrt.textContent = document.body.classList.contains("crt-effects") ? "📺 CRT: ON" : "📺 CRT: OFF";
    sfx.click();
  });

  const themeSelector = document.getElementById("theme-selector");
  themeSelector.addEventListener("change", (e) => {
    document.body.classList.remove("theme-phosphor", "theme-cyber", "theme-amber");
    document.body.classList.add(e.target.value);
    sfx.click();
  });

  // Action Buttons
  document.getElementById("btn-scan").addEventListener("click", handleScan);
  document.getElementById("btn-spoof").addEventListener("click", handleSpoof);
  document.getElementById("btn-jackout").addEventListener("click", handleJackout);
  document.getElementById("btn-rig-open").addEventListener("click", openRigModal);
  document.getElementById("btn-workshop-open").addEventListener("click", openWorkshopModal);
  document.getElementById("btn-shop-open").addEventListener("click", openShopModal);
  document.getElementById("btn-career-open").addEventListener("click", openCareerModal);
  document.getElementById("btn-reset-run").addEventListener("click", handleReset);

  // Target Actions
  document.getElementById("btn-probe-node").addEventListener("click", handleProbeNode);
  document.getElementById("btn-init-hack").addEventListener("click", handleStartHack);
  document.getElementById("btn-move-node").addEventListener("click", handleMoveNode);
  document.getElementById("btn-phish-node").addEventListener("click", handlePhishNode);
  document.getElementById("btn-keylogger-node").addEventListener("click", handleDeployKeylogger);
  document.getElementById("btn-wipe-logs").addEventListener("click", handleWipeLogs);
  document.getElementById("btn-close-viewer").addEventListener("click", () => {
    document.getElementById("fs-file-viewer").classList.add("hidden");
    sfx.click();
  });

  // Modals
  document.getElementById("btn-close-shop").addEventListener("click", () => {
    document.getElementById("modal-shop").classList.add("hidden");
    sfx.click();
  });
  document.getElementById("btn-close-career").addEventListener("click", () => {
    document.getElementById("modal-career").classList.add("hidden");
    sfx.click();
  });
  document.getElementById("btn-close-rig").addEventListener("click", () => {
    document.getElementById("modal-rig").classList.add("hidden");
    sfx.click();
  });
  document.getElementById("btn-close-workshop").addEventListener("click", () => {
    document.getElementById("modal-workshop").classList.add("hidden");
    sfx.click();
  });

  // Frequency slider live readout
  const freqSlider = document.getElementById("freq-slider");
  freqSlider.addEventListener("input", (e) => {
    document.getElementById("freq-val").textContent = `${parseFloat(e.target.value).toFixed(1)} GHz`;
  });
  document.getElementById("btn-tune-freq").addEventListener("click", handleTuneFrequency);

  // Buffer controls
  document.getElementById("btn-clear-buf").addEventListener("click", () => {
    state.bufferInput = [];
    renderBufferPlayerSequence();
    sfx.click();
  });
  document.getElementById("btn-inject-buf").addEventListener("click", handleInjectBuffer);

  // Banner action button
  document.getElementById("btn-banner-action").addEventListener("click", () => {
    document.getElementById("announcement-banner").classList.add("hidden");
    handleReset();
  });
}

// ==========================================================================
// 5. State Synchronization & HUD Rendering
// ==========================================================================
async function refreshFullState() {
  const data = await apiGet("/api/state");
  if (!data) return;
  state.data = data;
  renderHUD(data);
  updateExploitChips(data.deck.exploits);
  if (state.selectedNodeId) {
    updateTargetCard(state.selectedNodeId);
  }
}

function renderHUD(data) {
  const { deck, state: gState, current_node, career } = data;

  // CPU Gauge
  const cpuPercent = (deck.cpu_cycles / deck.max_cpu) * 100;
  document.getElementById("fill-cpu").style.width = `${cpuPercent}%`;
  document.getElementById("val-cpu").textContent = `${deck.cpu_cycles}/${deck.max_cpu}`;

  // RAM Gauge
  document.getElementById("val-ram").textContent = `${deck.ram_mb}MB`;

  // Trace Danger Meter
  const trace = gState.trace_percent;
  document.getElementById("fill-trace").style.width = `${trace}%`;
  document.getElementById("val-trace").textContent = `${trace}%`;

  if (trace >= 80 && trace < 100) {
    sfx.alarm();
    addTerminalLog(`⚠️ CRITICAL TRACE: ${trace}%! Black ICE locks tightening!`, "danger");
  }

  // Unbanked & Career Bank
  document.getElementById("val-loot").textContent = `${gState.unbanked_creds} CR`;
  document.getElementById("val-bank").textContent = `${career.banked_creds} CR`;

  // Syndicate Bounty Contract
  const contract = gState.active_contract;
  if (contract) {
    document.getElementById("contract-card").classList.remove("hidden");
    document.getElementById("contract-bounty-val").textContent = `+${contract.reward_creds} CR`;
    document.getElementById("contract-title").textContent = contract.title;
    document.getElementById("contract-status").textContent = contract.completed
      ? "STATUS: COMPLETED [FUNDS GRANTED]"
      : `TARGET: ${contract.target_node_type} | TRACE LIMIT: ${contract.max_trace_limit}%`;
  }

  // Check Game Over / Victory Overlays
  if (gState.is_victory) {
    showBanner("MISSION ACCOMPLISHED", "System Supercore Infiltrated. You escaped with all neural payloads.");
    sfx.jackpot();
  } else if (gState.is_game_over) {
    showBanner("CONNECTION TERMINATED", "Security ICE traced your deck. All unbanked credits destroyed.");
    sfx.failure();
  }
}

function updateExploitChips(exploits) {
  const container = document.getElementById("exploit-chips-container");
  container.innerHTML = "";
  if (!exploits || exploits.length === 0) {
    container.innerHTML = '<span class="empty-chips">No consumable chips loaded.</span>';
    return;
  }

  exploits.forEach((name) => {
    const btn = document.createElement("button");
    btn.className = "exploit-chip-btn";
    btn.textContent = `⚡ ${name.toUpperCase()}`;
    btn.title = `Deploy exploit chip: ${name}`;
    btn.addEventListener("click", () => handleUseExploit(name));
    container.appendChild(btn);
  });
}

function addTerminalLog(msg, type = "info") {
  const stream = document.getElementById("terminal-stream");
  const line = document.createElement("div");
  line.className = `log-line ${type}`;
  line.textContent = `> ${msg}`;
  stream.appendChild(line);
  stream.scrollTop = stream.scrollHeight;
}

function showBanner(title, sub) {
  const banner = document.getElementById("announcement-banner");
  document.getElementById("banner-heading").textContent = title;
  document.getElementById("banner-sub").textContent = sub;
  banner.classList.remove("hidden");
}

// ==========================================================================
// 6. Action Handlers (Scan, Spoof, Jackout, Reset, Exploits)
// ==========================================================================
async function handleScan() {
  sfx.scan();
  addTerminalLog("Emitting neural pulse across adjacent subnet...", "info");
  const res = await apiPost("/api/action", { action: "scan" });
  if (res && res.ok) {
    addTerminalLog(res.message, "success");
    state.data = res.state;
    renderHUD(res.state);
  }
}

async function handleSpoof() {
  sfx.click();
  const res = await apiPost("/api/action", { action: "spoof" });
  if (res && res.ok) {
    sfx.success();
    addTerminalLog(res.message, "success");
    state.data = res.state;
    renderHUD(res.state);
  } else if (res) {
    sfx.failure();
    addTerminalLog(res.message || "Failed to bounce proxy.", "warn");
  }
}

async function handleJackout() {
  sfx.click();
  const res = await apiPost("/api/action", { action: "jackout" });
  if (res && res.ok) {
    sfx.jackpot();
    addTerminalLog(res.message, "success");
    state.data = res.state;
    renderHUD(res.state);
    showBanner("EXTRACTION CONFIRMED", res.message);
  } else if (res) {
    sfx.failure();
    addTerminalLog(res.message || "Cannot jack out here.", "warn");
  }
}

async function handleReset() {
  sfx.click();
  const res = await apiPost("/api/action", { action: "reset" });
  if (res && res.ok) {
    addTerminalLog("Rebooted terminal with fresh cyberspace seed.", "info");
    state.data = res.state;
    state.selectedNodeId = null;
    closePuzzleBay();
    renderHUD(res.state);
  }
}

async function handleUseExploit(name) {
  sfx.click();
  const target = state.selectedNodeId;
  const res = await apiPost("/api/action", { action: "exploit", name, target });
  if (res && res.ok) {
    sfx.success();
    addTerminalLog(res.message, "success");
    state.data = res.state;
    renderHUD(res.state);
  } else if (res) {
    sfx.failure();
    addTerminalLog(res.message || "Exploit execution failed.", "warn");
  }
}

// ==========================================================================
// 7. Interactive Cyberspace Node Matrix Canvas (2D Topology Graph)
// ==========================================================================
function initMatrixCanvas() {
  const canvas = document.getElementById("matrix-canvas");
  const ctx = canvas.getContext("2d");

  // Mouse interaction
  canvas.addEventListener("click", (e) => {
    sfx.init();
    const rect = canvas.getBoundingClientRect();
    const scaleX = canvas.width / rect.width;
    const scaleY = canvas.height / rect.height;
    const mouseX = (e.clientX - rect.left) * scaleX;
    const mouseY = (e.clientY - rect.top) * scaleY;

    // Hit test against nodes
    for (const [nid, pos] of Object.entries(NODE_POSITIONS)) {
      const dist = Math.hypot(mouseX - pos.x, mouseY - pos.y);
      if (dist <= 28) {
        selectNode(nid);
        sfx.click();
        return;
      }
    }
  });

  // Continuous animation loop
  function renderLoop(time) {
    drawMatrix(ctx, time);
    state.animFrameId = requestAnimationFrame(renderLoop);
  }
  state.animFrameId = requestAnimationFrame(renderLoop);
}

function selectNode(nodeId) {
  state.selectedNodeId = nodeId;
  updateTargetCard(nodeId);
  if (state.data && state.data.nodes[nodeId] && state.data.nodes[nodeId].status === "BREACHED") {
    loadFilesystemView(nodeId);
  } else {
    document.getElementById("filesystem-container").classList.add("hidden");
    document.getElementById("puzzle-idle").classList.remove("hidden");
  }
}

function updateTargetCard(nodeId) {
  if (!state.data || !state.data.nodes[nodeId]) return;
  const node = state.data.nodes[nodeId];
  const deck = state.data.deck;
  const curr = state.data.current_node;

  document.getElementById("target-badge").textContent = node.status;
  document.getElementById("target-name").textContent = node.name;
  document.getElementById("target-ip").textContent = node.ip_address || "127.0.0.1";
  document.getElementById("target-hostname").textContent = node.hostname || "localhost";
  document.getElementById("target-type").textContent = node.node_type;
  document.getElementById("target-sec").textContent = `LEVEL ${node.security_level}`;
  document.getElementById("target-ram").textContent = `${node.security_level * 16}MB (Deck: ${deck.ram_mb}MB)`;
  document.getElementById("target-trace").textContent = `+${node.trace_rate}%`;

  const btnProbe = document.getElementById("btn-probe-node");
  const btnHack = document.getElementById("btn-init-hack");
  const btnMove = document.getElementById("btn-move-node");
  const btnPhish = document.getElementById("btn-phish-node");
  const btnKeylogger = document.getElementById("btn-keylogger-node");
  const btnWipe = document.getElementById("btn-wipe-logs");

  const isAdjacent = curr.connected_ids.includes(nodeId) || curr.node_id === nodeId;
  const isBreached = node.status === "BREACHED";

  btnProbe.disabled = node.status === "LOCKED" && !isAdjacent;
  btnHack.disabled = isBreached || !isAdjacent;
  btnMove.disabled = !isBreached || curr.node_id === nodeId;
  btnPhish.disabled = isBreached || (node.status === "LOCKED" && !isAdjacent);
  btnKeylogger.disabled = !isBreached;
  btnWipe.disabled = !isBreached;
}

async function loadFilesystemView(nodeId) {
  const node = state.data.nodes[nodeId];
  if (!node || node.status !== "BREACHED") {
    document.getElementById("filesystem-container").classList.add("hidden");
    return;
  }

  document.getElementById("puzzle-idle").classList.add("hidden");
  document.getElementById("puzzle-frequency").classList.add("hidden");
  document.getElementById("puzzle-buffer").classList.add("hidden");
  document.getElementById("puzzle-hash").classList.add("hidden");
  document.getElementById("filesystem-container").classList.remove("hidden");
  document.getElementById("fs-target-host").textContent = `${node.hostname} (${node.ip_address})`;

  const portsList = document.getElementById("target-ports-list");
  portsList.innerHTML = "";
  if (node.ports && node.ports.length > 0) {
    node.ports.forEach((p) => {
      const pDiv = document.createElement("div");
      pDiv.className = "port-item";
      const tagClass = p.breached ? "port-tag-breached" : (p.vulnerable ? "port-tag-vulnerable" : "");
      const tagText = p.breached ? "BREACHED" : (p.vulnerable ? "VULNERABLE" : "SECURE");
      pDiv.innerHTML = `<span><strong>${p.port}/tcp</strong> ${p.service} (${p.version})</span><span class="${tagClass}">[${tagText}]</span>`;
      portsList.appendChild(pDiv);
    });
  }

  const res = await apiPost("/api/action", { action: "list_files", target: nodeId });
  const tbody = document.getElementById("fs-file-tbody");
  tbody.innerHTML = "";
  if (res && res.ok && res.files) {
    res.files.forEach((f) => {
      const tr = document.createElement("tr");
      const targetMark = f.is_target_data ? '<strong class="highlight-value">★ TARGET</strong>' : "";
      const valStr = f.value_creds > 0 ? `${f.value_creds} CR` : "---";
      tr.innerHTML = `
        <td>${f.path} ${targetMark}</td>
        <td>${f.size_kb}KB</td>
        <td>${valStr}</td>
        <td>
          <button class="icon-btn small-btn btn-cat" data-path="${f.path}">CAT</button>
          <button class="icon-btn small-btn btn-steal" data-path="${f.path}">STEAL</button>
        </td>
      `;
      tr.querySelector(".btn-cat").addEventListener("click", () => handleCatFile(nodeId, f.path));
      tr.querySelector(".btn-steal").addEventListener("click", () => handleStealFile(nodeId, f.path));
      tbody.appendChild(tr);
    });
  }
}

function drawMatrix(ctx, time) {
  ctx.clearRect(0, 0, ctx.canvas.width, ctx.canvas.height);

  if (!state.data) return;
  const nodes = state.data.nodes;
  const currNodeId = state.data.state.current_node_id;

  // 1. Draw Network Connection Edges
  for (const [nid, node] of Object.entries(nodes)) {
    const p1 = NODE_POSITIONS[nid];
    if (!p1) continue;

    for (const cid of node.connected_ids) {
      const p2 = NODE_POSITIONS[cid];
      if (!p2 || nid > cid) continue; // Draw each edge once

      ctx.beginPath();
      ctx.moveTo(p1.x, p1.y);
      ctx.lineTo(p2.x, p2.y);
      ctx.strokeStyle = "rgba(40, 160, 90, 0.25)";
      ctx.lineWidth = 2;
      ctx.stroke();

      // Moving data packet dots along active connections
      const packetPhase = (time * 0.0008 + (p1.x * 0.01)) % 1;
      const px = p1.x + (p2.x - p1.x) * packetPhase;
      const py = p1.y + (p2.y - p1.y) * packetPhase;
      ctx.beginPath();
      ctx.arc(px, py, 2.5, 0, Math.PI * 2);
      ctx.fillStyle = "rgba(0, 255, 170, 0.6)";
      ctx.fill();
    }
  }

  // 2. Draw Host Nodes
  for (const [nid, node] of Object.entries(nodes)) {
    const pos = NODE_POSITIONS[nid];
    if (!pos) continue;

    const isCurrent = nid === currNodeId;
    const isSelected = nid === state.selectedNodeId;
    const isBreached = node.status === "BREACHED";
    const isDiscovered = node.status === "DISCOVERED";

    // Glowing Outer Ring
    ctx.beginPath();
    ctx.arc(pos.x, pos.y, 22, 0, Math.PI * 2);
    if (isCurrent) {
      ctx.fillStyle = "rgba(0, 220, 255, 0.2)";
      ctx.strokeStyle = "hsl(185, 100%, 50%)";
      ctx.lineWidth = 2.5;
    } else if (isBreached) {
      ctx.fillStyle = "rgba(0, 255, 120, 0.15)";
      ctx.strokeStyle = "hsl(140, 100%, 50%)";
      ctx.lineWidth = 2;
    } else if (isDiscovered) {
      ctx.fillStyle = "rgba(255, 180, 0, 0.1)";
      ctx.strokeStyle = "hsl(45, 100%, 50%)";
      ctx.lineWidth = 1.5;
    } else {
      ctx.fillStyle = "rgba(40, 40, 40, 0.3)";
      ctx.strokeStyle = "#555";
      ctx.lineWidth = 1;
    }
    ctx.fill();
    ctx.stroke();

    // Node Center Icon / Circle
    ctx.beginPath();
    ctx.arc(pos.x, pos.y, 10, 0, Math.PI * 2);
    ctx.fillStyle = isCurrent ? "hsl(185, 100%, 50%)" : (isBreached ? "hsl(140, 100%, 50%)" : (isDiscovered ? "hsl(45, 100%, 50%)" : "#444"));
    ctx.fill();

    // Target Selection Halo
    if (isSelected) {
      ctx.beginPath();
      ctx.arc(pos.x, pos.y, 30, 0, Math.PI * 2);
      ctx.strokeStyle = "rgba(255, 255, 255, 0.8)";
      ctx.lineWidth = 1.5;
      ctx.setLineDash([4, 4]);
      ctx.stroke();
      ctx.setLineDash([]);
    }

    // Node Label & IP
    ctx.font = "11px 'Share Tech Mono', monospace";
    ctx.fillStyle = isCurrent ? "hsl(185, 100%, 90%)" : "#aaa";
    ctx.textAlign = "center";
    ctx.fillText(pos.label, pos.x, pos.y + 34);

    ctx.font = "9px 'Share Tech Mono', monospace";
    ctx.fillStyle = isBreached ? "hsl(140, 80%, 70%)" : (isDiscovered ? "hsl(45, 80%, 70%)" : "#666");
    ctx.fillText(node.ip_address || "", pos.x, pos.y + 46);

    if (isCurrent) {
      ctx.font = "9px 'Orbitron', sans-serif";
      ctx.fillStyle = "hsl(185, 100%, 70%)";
      ctx.fillText("[ACTIVE TERMINAL]", pos.x, pos.y - 28);
    }
  }
}

// ==========================================================================
// 8. Move, Probe & Intrusion Handlers
// ==========================================================================
async function handleMoveNode() {
  if (!state.selectedNodeId) return;
  sfx.click();
  const res = await apiPost("/api/action", { action: "move", target: state.selectedNodeId });
  if (res && res.ok) {
    sfx.success();
    addTerminalLog(res.message, "success");
    state.data = res.state;
    renderHUD(res.state);
    updateTargetCard(state.selectedNodeId);
    if (state.data.nodes[state.selectedNodeId].status === "BREACHED") {
      loadFilesystemView(state.selectedNodeId);
    }
  } else if (res) {
    sfx.failure();
    addTerminalLog(res.message || "Move disallowed.", "warn");
  }
}

async function handleProbeNode() {
  if (!state.selectedNodeId) return;
  sfx.scan();
  addTerminalLog(`Scanning open ports on ${state.selectedNodeId}...`, "info");
  const res = await apiPost("/api/action", { action: "probe", target: state.selectedNodeId });
  if (res && res.ok) {
    sfx.success();
    addTerminalLog(res.message, "success");
    state.data = res.state;
    renderHUD(res.state);
    updateTargetCard(state.selectedNodeId);
    if (res.report && res.report.ports) {
      res.report.ports.forEach((p) => {
        addTerminalLog(`  [PORT ${p.port}/tcp] ${p.service} (${p.version}) - ${p.vulnerable ? 'VULNERABLE' : 'SECURE'}`, p.vulnerable ? 'warn' : 'info');
      });
    }
  } else if (res) {
    sfx.failure();
    addTerminalLog(res.message || "Port scan failed.", "warn");
  }
}

async function handleStartHack() {
  if (!state.selectedNodeId) return;
  const node = state.data.nodes[state.selectedNodeId];
  if (!node) return;

  // 1-Click Zero-Day Exploit if vulnerable port is present
  const vulnPort = (node.ports || []).find(p => p.vulnerable && !p.breached);
  if (vulnPort) {
    sfx.click();
    addTerminalLog(`⚡ Infiltrating via port ${vulnPort.port}/tcp (${vulnPort.service})...`, "info");
    const res = await apiPost("/api/action", {
      action: "exploit_service",
      target: state.selectedNodeId,
      port: vulnPort.port,
    });
    if (res && res.ok) {
      sfx.success();
      addTerminalLog(res.message, "success");
      state.data = res.state;
      renderHUD(res.state);
      updateTargetCard(state.selectedNodeId);
      loadFilesystemView(state.selectedNodeId);
      return;
    } else if (res) {
      sfx.failure();
      addTerminalLog(res.message || "Exploit payload failed.", "danger");
      state.data = res.state;
      renderHUD(res.state);
      return;
    }
  }

  // Fallback to minigame puzzle
  sfx.click();
  const data = await apiGet(`/api/puzzle?node_id=${state.selectedNodeId}`);
  if (!data || !data.ok) {
    sfx.failure();
    addTerminalLog(data ? data.error : "Failed to initiate intrusion.", "warn");
    return;
  }

  sfx.scan();
  addTerminalLog(`⚡ Commencing cyber-attack on ${data.node_name}...`, "info");
  state.activePuzzle = data;
  displayPuzzle(data);
}

async function handleCatFile(nodeId, path) {
  sfx.click();
  const res = await apiPost("/api/action", { action: "read_file", target: nodeId, path });
  if (res && res.ok) {
    document.getElementById("viewer-path").textContent = path;
    document.getElementById("viewer-content").textContent = res.content || "(empty file)";
    document.getElementById("fs-file-viewer").classList.remove("hidden");
  }
}

async function handleStealFile(nodeId, path) {
  sfx.click();
  const res = await apiPost("/api/action", { action: "download_file", target: nodeId, path });
  if (res && res.ok) {
    sfx.jackpot();
    addTerminalLog(res.message, "success");
    state.data = res.state;
    renderHUD(res.state);
  } else if (res) {
    sfx.failure();
    addTerminalLog(res.message || "Failed to steal file.", "warn");
  }
}

async function handleWipeLogs() {
  if (!state.selectedNodeId) return;
  sfx.click();
  const res = await apiPost("/api/action", { action: "wipe_logs", target: state.selectedNodeId });
  if (res && res.ok) {
    sfx.success();
    addTerminalLog(res.message, "success");
    state.data = res.state;
    renderHUD(res.state);
  } else if (res) {
    sfx.failure();
    addTerminalLog(res.message || "Failed to wipe logs.", "warn");
  }
}

async function handlePhishNode() {
  if (!state.selectedNodeId) return;
  sfx.scan();
  addTerminalLog(`Dispatching spear-phishing credential lure to ${state.selectedNodeId}...`, "info");
  const res = await apiPost("/api/action", { action: "phish", target: state.selectedNodeId });
  if (res && res.ok) {
    sfx.success();
    addTerminalLog(res.message, "success");
    state.data = res.state;
    renderHUD(res.state);
    updateTargetCard(state.selectedNodeId);
  } else if (res) {
    sfx.failure();
    addTerminalLog(res.message || "Phishing lure ignored.", "warn");
    if (res.state) {
      state.data = res.state;
      renderHUD(res.state);
    }
  }
}

async function handleDeployKeylogger() {
  if (!state.selectedNodeId) return;
  sfx.click();
  addTerminalLog(`Injecting background keylogger listener into ${state.selectedNodeId}...`, "info");
  const res = await apiPost("/api/action", { action: "deploy_daemon", target: state.selectedNodeId, daemon_type: "keylogger" });
  if (res && res.ok) {
    sfx.success();
    addTerminalLog(res.message, "success");
    state.data = res.state;
    renderHUD(res.state);
  } else if (res) {
    sfx.failure();
    addTerminalLog(res.message || "Keylogger deployment failed.", "warn");
  }
}

function closePuzzleBay() {
  document.getElementById("puzzle-idle").classList.remove("hidden");
  document.getElementById("puzzle-frequency").classList.add("hidden");
  document.getElementById("puzzle-buffer").classList.add("hidden");
  document.getElementById("puzzle-hash").classList.add("hidden");
  state.activePuzzle = null;
}

function displayPuzzle(pData) {
  document.getElementById("puzzle-idle").classList.add("hidden");
  document.getElementById("puzzle-frequency").classList.add("hidden");
  document.getElementById("puzzle-buffer").classList.add("hidden");
  document.getElementById("puzzle-hash").classList.add("hidden");

  if (pData.puzzle_type === "frequency") {
    document.getElementById("puzzle-frequency").classList.remove("hidden");
    document.getElementById("freq-tries").textContent = `TRIES: ${pData.attempts_left}`;
    startOscilloscopeAnimation();
  } else if (pData.puzzle_type === "buffer") {
    document.getElementById("puzzle-buffer").classList.remove("hidden");
    renderBufferTarget(pData.target_seq);
    renderBufferMatrix(pData.matrix);
    state.bufferInput = [];
    renderBufferPlayerSequence();
  } else if (pData.puzzle_type === "hash") {
    document.getElementById("puzzle-hash").classList.remove("hidden");
    document.getElementById("hash-tries").textContent = `TRIES: ${pData.attempts_left}`;
    renderHashPool(pData.word_list);
    document.getElementById("hash-history").innerHTML = "";
  }
}

// --------------------------------------------------------------------------
// Mini-Game 1: Oscilloscope Frequency Tuning
// --------------------------------------------------------------------------
let oscTimer = null;
function startOscilloscopeAnimation() {
  const oscCanvas = document.getElementById("osc-canvas");
  const ctx = oscCanvas.getContext("2d");
  let t = 0;

  if (oscTimer) cancelAnimationFrame(oscTimer);

  function drawOsc() {
    ctx.fillStyle = "rgba(0, 0, 0, 0.25)";
    ctx.fillRect(0, 0, oscCanvas.width, oscCanvas.height);

    const dialVal = parseFloat(document.getElementById("freq-slider").value);
    const midY = oscCanvas.height / 2;

    // Target Carrier Wave (Cyan)
    ctx.beginPath();
    ctx.strokeStyle = "rgba(0, 220, 255, 0.4)";
    ctx.lineWidth = 1.5;
    for (let x = 0; x < oscCanvas.width; x++) {
      const y = midY + Math.sin(x * 0.05 + t * 0.05) * 30;
      if (x === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    }
    ctx.stroke();

    // Tuned Player Wave (Green)
    ctx.beginPath();
    ctx.strokeStyle = "hsl(140, 100%, 55%)";
    ctx.lineWidth = 2;
    for (let x = 0; x < oscCanvas.width; x++) {
      const y = midY + Math.sin(x * (dialVal * 0.001) + t * 0.05) * 35;
      if (x === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    }
    ctx.stroke();

    t++;
    if (!document.getElementById("puzzle-frequency").classList.contains("hidden")) {
      oscTimer = requestAnimationFrame(drawOsc);
    }
  }
  oscTimer = requestAnimationFrame(drawOsc);
}

async function handleTuneFrequency() {
  sfx.click();
  const guess = parseFloat(document.getElementById("freq-slider").value);
  const res = await apiPost("/api/puzzle/solve", { guess });
  if (!res) return;

  if (res.solved) {
    sfx.success();
    addTerminalLog(res.message, "success");
    closePuzzleBay();
    refreshFullState();
  } else {
    if (res.near_miss) {
      sfx.nearMiss();
      addTerminalLog("⚡ NEAR-MISS DETECTED! Resonance harmonic almost aligned!", "warn");
    } else {
      sfx.failure();
    }
    document.getElementById("freq-tries").textContent = `TRIES: ${res.attempts_left}`;
    addTerminalLog(res.message, "warn");
    if (res.attempts_left <= 0) {
      closePuzzleBay();
      refreshFullState();
    }
  }
}

// --------------------------------------------------------------------------
// Mini-Game 2: Buffer Overflow Matrix
// --------------------------------------------------------------------------
function renderBufferTarget(targetSeq) {
  const container = document.getElementById("buf-target-seq");
  container.innerHTML = "";
  targetSeq.forEach((hex) => {
    const el = document.createElement("span");
    el.className = "hex-block";
    el.textContent = hex;
    container.appendChild(el);
  });
}

function renderBufferMatrix(matrix) {
  const grid = document.getElementById("buf-matrix-grid");
  grid.innerHTML = "";
  matrix.forEach((row) => {
    row.forEach((hex) => {
      const cell = document.createElement("div");
      cell.className = "matrix-cell";
      cell.textContent = hex;
      cell.addEventListener("click", () => {
        sfx.click();
        state.bufferInput.push(hex);
        renderBufferPlayerSequence();
      });
      grid.appendChild(cell);
    });
  });
}

function renderBufferPlayerSequence() {
  const container = document.getElementById("buf-player-seq");
  container.innerHTML = "";
  state.bufferInput.forEach((hex) => {
    const el = document.createElement("span");
    el.className = "hex-block";
    el.textContent = hex;
    container.appendChild(el);
  });
}

async function handleInjectBuffer() {
  sfx.click();
  const res = await apiPost("/api/puzzle/solve", { guess: state.bufferInput });
  if (!res) return;

  if (res.solved) {
    sfx.success();
    addTerminalLog(res.message, "success");
    closePuzzleBay();
    refreshFullState();
  } else {
    if (res.near_miss) {
      sfx.nearMiss();
      addTerminalLog("⚡ NEAR-MISS! Primary buffer block aligned!", "warn");
    } else {
      sfx.failure();
    }
    addTerminalLog(res.message, "warn");
    state.bufferInput = [];
    renderBufferPlayerSequence();
    closePuzzleBay();
    refreshFullState();
  }
}

// --------------------------------------------------------------------------
// Mini-Game 3: Cryptographic Hash Cipher
// --------------------------------------------------------------------------
function renderHashPool(wordList) {
  const container = document.getElementById("hash-word-pool");
  container.innerHTML = "";
  wordList.forEach((word) => {
    const btn = document.createElement("button");
    btn.className = "hash-word-btn";
    btn.textContent = word;
    btn.addEventListener("click", () => handleGuessHash(word));
    container.appendChild(btn);
  });
}

async function handleGuessHash(word) {
  sfx.click();
  const res = await apiPost("/api/puzzle/solve", { guess: word });
  if (!res) return;

  const history = document.getElementById("hash-history");
  const entry = document.createElement("div");
  entry.className = "hash-entry";
  entry.textContent = `${word} >> ${res.message}`;
  history.prepend(entry);

  if (res.solved) {
    sfx.success();
    addTerminalLog(res.message, "success");
    closePuzzleBay();
    refreshFullState();
  } else {
    if (res.near_miss) {
      sfx.nearMiss();
      addTerminalLog("⚡ CRITICAL NEAR-MISS! Only 1 character off!", "warn");
    } else {
      sfx.failure();
    }
    document.getElementById("hash-tries").textContent = `TRIES: ${res.attempts_left}`;
    if (res.attempts_left <= 0) {
      addTerminalLog("Lockout threshold reached on cipher node.", "danger");
      closePuzzleBay();
      refreshFullState();
    }
  }
}

// ==========================================================================
// 9. Black Market Shop & Career Dossier Modals
// ==========================================================================
async function openShopModal() {
  sfx.click();
  const data = await apiGet("/api/shop");
  if (!data) return;

  document.getElementById("shop-creds").textContent = data.creds;
  const grid = document.getElementById("shop-items-grid");
  grid.innerHTML = "";

  data.items.forEach((item) => {
    const card = document.createElement("div");
    card.className = "shop-item-card";

    const statusText = item.max_level > 1
      ? `Level ${item.current_level}/${item.max_level}`
      : (item.current_level > 0 ? "LOADED IN FIRMWARE" : "AVAILABLE");

    card.innerHTML = `
      <div class="shop-item-info">
        <div class="item-name">${item.name} (${statusText})</div>
        <div class="item-desc">${item.description}</div>
      </div>
      <div class="shop-item-action">
        <span class="item-cost">${item.cost} CR</span>
        <button class="buy-btn" ${!item.can_buy ? "disabled" : ""}>PURCHASE</button>
      </div>
    `;

    const buyBtn = card.querySelector(".buy-btn");
    buyBtn.addEventListener("click", async () => {
      sfx.click();
      const res = await apiPost("/api/action", { action: "shop_buy", item_id: item.item_id });
      if (res && res.ok) {
        sfx.success();
        addTerminalLog(res.message, "success");
        openShopModal(); // Refresh modal
        refreshFullState();
      } else if (res) {
        sfx.failure();
        addTerminalLog(res.message || "Purchase denied.", "warn");
      }
    });

    grid.appendChild(card);
  });

  document.getElementById("modal-shop").classList.remove("hidden");
}

async function openCareerModal() {
  sfx.click();
  const data = await apiGet("/api/career");
  if (!data) return;

  document.getElementById("dossier-alias").textContent = data.alias;
  document.getElementById("dossier-banked").textContent = `${data.banked_creds} CR`;
  document.getElementById("dossier-lifetime").textContent = `${data.lifetime_creds} CR`;
  document.getElementById("dossier-wins").textContent = data.successful_runs;
  document.getElementById("dossier-fails").textContent = data.failed_runs;
  document.getElementById("dossier-streak").textContent = `${data.current_streak} HEISTS`;
  document.getElementById("dossier-best").textContent = `${data.best_streak} HEISTS`;
  document.getElementById("dossier-upgrades").textContent = data.purchased_upgrades.length > 0
    ? data.purchased_upgrades.join(", ")
    : "Standard Factory Rig";

  document.getElementById("modal-career").classList.remove("hidden");
}

async function openRigModal() {
  sfx.click();
  const data = await apiGet("/api/local_files");
  if (!data) return;

  document.getElementById("rig-ip").textContent = data.ip;
  document.getElementById("rig-hostname").textContent = data.hostname;
  if (state.data && state.data.deck && state.data.deck.model_name) {
    document.getElementById("rig-model").textContent = state.data.deck.model_name;
  }

  // Render Local Files
  const tbody = document.getElementById("rig-file-tbody");
  tbody.innerHTML = "";
  if (data.files && data.files.length > 0) {
    data.files.forEach((f) => {
      const tr = document.createElement("tr");
      const valStr = f.value_creds > 0 ? `${f.value_creds} CR` : "---";
      tr.innerHTML = `
        <td>${f.path}</td>
        <td>${f.size_kb}KB</td>
        <td>${valStr}</td>
        <td>
          <button class="icon-btn small-btn btn-cat-local" data-path="${f.path}">CAT</button>
        </td>
      `;
      tr.querySelector(".btn-cat-local").addEventListener("click", () => {
        document.getElementById("viewer-path").textContent = `[LOCAL] ${f.path}`;
        document.getElementById("viewer-content").textContent = f.content || "(empty file)";
        document.getElementById("fs-file-viewer").classList.remove("hidden");
        document.getElementById("modal-rig").classList.add("hidden");
      });
      tbody.appendChild(tr);
    });
  } else {
    tbody.innerHTML = '<tr><td colspan="4">No local files stored.</td></tr>';
  }

  // Render Active Daemons
  const daemonsGrid = document.getElementById("rig-daemons-grid");
  daemonsGrid.innerHTML = "";
  if (data.daemons && data.daemons.length > 0) {
    data.daemons.forEach((d) => {
      const card = document.createElement("div");
      card.className = "daemon-card";
      card.innerHTML = `
        <div>
          <span class="daemon-title">👾 ${d.daemon_type.toUpperCase()}</span>
          <span class="daemon-target">on node ${d.target_node_id} (active ${d.turns_active} turns)</span>
        </div>
        <div class="daemon-yield">+${d.yield_per_turn} CR / turn (${d.detection_risk}% trace)</div>
      `;
      daemonsGrid.appendChild(card);
    });
  } else {
    daemonsGrid.innerHTML = '<span class="empty-chips">No active background daemons deployed.</span>';
  }

  document.getElementById("modal-rig").classList.remove("hidden");
}

async function openWorkshopModal() {
  sfx.click();
  const data = await apiGet("/api/workshop");
  if (!data) return;

  const currentCreds = (state.data && state.data.state) ? state.data.state.unbanked_creds : 0;
  document.getElementById("workshop-creds").textContent = currentCreds;
  const grid = document.getElementById("workshop-recipes-grid");
  grid.innerHTML = "";

  data.recipes.forEach((recipe) => {
    const card = document.createElement("div");
    card.className = "workshop-recipe-card";
    const canCraft = currentCreds >= recipe.cost_creds;

    card.innerHTML = `
      <div class="recipe-info">
        <div class="recipe-name">${recipe.name} (${recipe.recipe_id})</div>
        <div class="recipe-desc">${recipe.description}</div>
      </div>
      <div class="recipe-action">
        <span class="recipe-cost">${recipe.cost_creds} CR</span>
        <button class="craft-btn" ${!canCraft ? "disabled" : ""}>SYNTHESIZE</button>
      </div>
    `;

    const craftBtn = card.querySelector(".craft-btn");
    craftBtn.addEventListener("click", async () => {
      sfx.click();
      const res = await apiPost("/api/action", { action: "craft", recipe: recipe.recipe_id });
      if (res && res.ok) {
        sfx.jackpot();
        addTerminalLog(res.message, "success");
        state.data = res.state;
        renderHUD(res.state);
        updateExploitChips(res.state.deck.exploits);
        openWorkshopModal(); // Refresh modal
      } else if (res) {
        sfx.failure();
        addTerminalLog(res.message || "Synthesis failed.", "warn");
      }
    });

    grid.appendChild(card);
  });

  document.getElementById("modal-workshop").classList.remove("hidden");
}
