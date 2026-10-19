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
  selectedEmployee: null,
  selectedVector: "spear_phish",
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
  document.getElementById("btn-cves-open").addEventListener("click", openCvesModal);
  document.getElementById("btn-rig-open").addEventListener("click", openRigModal);
  document.getElementById("btn-workshop-open").addEventListener("click", openWorkshopModal);
  document.getElementById("btn-shop-open").addEventListener("click", openShopModal);
  document.getElementById("btn-career-open").addEventListener("click", openCareerModal);
  document.getElementById("btn-reset-run").addEventListener("click", handleReset);
  document.getElementById("btn-quests-open").addEventListener("click", openQuestsModal);
  document.getElementById("btn-contacts-open").addEventListener("click", openContactsModal);
  document.getElementById("btn-overdrive").addEventListener("click", handleOverdrive);

  // Main menu
  document.getElementById("menu-jack-in").addEventListener("click", () => {
    document.getElementById("modal-main-menu").classList.add("hidden");
    sfx.success();
  });
  document.getElementById("menu-new-run").addEventListener("click", async () => {
    document.getElementById("modal-main-menu").classList.add("hidden");
    await handleReset();
  });
  document.getElementById("menu-story").addEventListener("click", () => {
    document.getElementById("modal-main-menu").classList.add("hidden");
    openQuestsModal();
  });
  document.getElementById("menu-contacts").addEventListener("click", () => {
    document.getElementById("modal-main-menu").classList.add("hidden");
    openContactsModal();
  });
  document.getElementById("menu-career").addEventListener("click", () => {
    document.getElementById("modal-main-menu").classList.add("hidden");
    openCareerModal();
  });
  document.getElementById("menu-help").addEventListener("click", () => {
    document.getElementById("main-menu-help").classList.toggle("hidden");
  });

  // Target Actions
  document.getElementById("btn-probe-node").addEventListener("click", handleProbeNode);
  document.getElementById("btn-init-hack").addEventListener("click", handleStartHack);
  document.getElementById("btn-bypass-fw").addEventListener("click", openBypassModal);
  document.getElementById("btn-evade-av").addEventListener("click", handleEvadeAv);
  document.getElementById("btn-social-eng").addEventListener("click", openSocialModal);
  document.getElementById("btn-move-node").addEventListener("click", handleMoveNode);
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
  document.getElementById("btn-close-cves").addEventListener("click", () => {
    document.getElementById("modal-cves").classList.add("hidden");
    sfx.click();
  });
  document.getElementById("btn-close-social").addEventListener("click", () => {
    document.getElementById("modal-social").classList.add("hidden");
    sfx.click();
  });
  document.getElementById("btn-close-quests").addEventListener("click", () => {
    document.getElementById("modal-quests").classList.add("hidden");
    sfx.click();
  });
  document.getElementById("btn-close-contacts").addEventListener("click", () => {
    document.getElementById("modal-contacts").classList.add("hidden");
    sfx.click();
  });
  document.getElementById("btn-close-bypass").addEventListener("click", () => {
    document.getElementById("modal-bypass").classList.add("hidden");
    sfx.click();
  });
  document.getElementById("btn-execute-social").addEventListener("click", executeSocialAttack);

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

  // Global Keyboard Navigation
  window.addEventListener("keydown", (e) => {
    if (["INPUT", "TEXTAREA"].includes(document.activeElement.tagName)) {
      return;
    }

    if (e.key === "Escape") {
      closeAllModals();
      return;
    }

    const mainMenu = document.getElementById("modal-main-menu");
    if (mainMenu && !mainMenu.classList.contains("hidden")) {
      return;
    }

    const key = e.code;
    if (key === "KeyS") {
      e.preventDefault();
      handleScan();
    } else if (key === "KeyP") {
      e.preventDefault();
      handleProbeNode();
    } else if (key === "KeyE") {
      e.preventDefault();
      handleStartHack();
    } else if (key === "KeyJ") {
      e.preventDefault();
      handleJackout();
    } else if (key === "KeyC") {
      e.preventDefault();
      toggleModal("modal-cves", openCvesModal);
    } else if (key === "KeyR") {
      e.preventDefault();
      toggleModal("modal-rig", openRigModal);
    } else if (key === "KeyM") {
      e.preventDefault();
      toggleModal("modal-workshop", openWorkshopModal);
    } else if (key === "KeyB") {
      e.preventDefault();
      toggleModal("modal-shop", openShopModal);
    } else if (key === "KeyD") {
      e.preventDefault();
      toggleModal("modal-career", openCareerModal);
    } else if (key === "KeyF") {
      e.preventDefault();
      openBypassModal();
    } else if (key === "KeyA") {
      e.preventDefault();
      handleEvadeAv();
    } else if (key === "KeyQ") {
      e.preventDefault();
      toggleModal("modal-quests", openQuestsModal);
    } else if (key === "KeyN") {
      e.preventDefault();
      toggleModal("modal-contacts", openContactsModal);
    } else if (key === "KeyO") {
      e.preventDefault();
      handleOverdrive();
    }
  });
}

function closeAllModals() {
  document.querySelectorAll(".modal-overlay").forEach(m => m.classList.add("hidden"));
  const viewer = document.getElementById("fs-file-viewer");
  if (viewer) viewer.classList.add("hidden");
  sfx.click();
}

function toggleModal(modalId, openFn) {
  const el = document.getElementById(modalId);
  if (!el) return;
  if (el.classList.contains("hidden")) {
    openFn();
  } else {
    el.classList.add("hidden");
    sfx.click();
  }
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

function renderGridTicker(world) {
  const bar = document.getElementById("grid-bar");
  if (!bar || !world) return;

  document.getElementById("grid-clock").textContent = (world.clock || "Day 1 08:00").toUpperCase();
  document.getElementById("grid-shift").textContent = (world.shift || "Morning").toUpperCase();

  const alertEl = document.getElementById("grid-alert");
  const alertLevel = world.alert_level || 0;
  alertEl.textContent = `GRID ALERT ${alertLevel}%`;
  alertEl.classList.toggle("hot", alertLevel >= 50);

  const market = world.market_multiplier || 1;
  document.getElementById("grid-market").textContent = `MARKET x${Number(market).toFixed(3)}`;

  const ticker = document.getElementById("grid-ticker");
  const headlines = world.news || [];
  if (ticker && headlines.length) {
    const latest = headlines[headlines.length - 1];
    const text = `${latest.source || "GRIDWIRE"}: ${latest.headline}`;
    if (ticker.textContent !== text) {
      ticker.textContent = text;
      ticker.classList.remove("ticker-flash");
      void ticker.offsetWidth;
      ticker.classList.add("ticker-flash");
    }
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
  document.getElementById("val-combo").textContent = `x${gState.combo_streak || 0}`;

  // Living grid ticker: clock, alert, market, and the newest headline
  renderGridTicker(data.world || gState.world);

  // Story beat and active objective
  if (data.story) {
    document.getElementById("story-act").textContent =
      `${data.story.act_title} // ${data.story.chapter_title}`;
    const activeQuest = (data.quests || []).find(q => q.accepted && !q.completed);
    document.getElementById("story-objective").textContent = activeQuest
      ? activeQuest.description
      : "Open MISSIONS or talk to an operative to pick up the next job.";
    const menuStory = document.getElementById("main-menu-story");
    if (menuStory) menuStory.textContent = `${data.story.act_title} // ${data.story.chapter_title}`;
    const menuSub = document.getElementById("main-menu-sub");
    if (menuSub && data.story.intro) menuSub.textContent = data.story.intro;
  }

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
    const summary = data.run_summary || {};
    const legacy = (summary.epilogue || []).join(" ");
    const stats = `Best combo x${summary.best_combo || 0} | Quests ${summary.quests_completed_count || 0}/${summary.quests_total || 0}.`;
    showBanner(summary.outcome_title || "MISSION ACCOMPLISHED", `${legacy} ${stats}`.trim());
    sfx.jackpot();
  } else if (gState.is_game_over) {
    const summary = data.run_summary || {};
    const legacy = (summary.epilogue || []).join(" ");
    const stats = `Best combo x${summary.best_combo || 0} | Quests ${summary.quests_completed_count || 0}/${summary.quests_total || 0}.`;
    showBanner(summary.outcome_title || "CONNECTION TERMINATED", `${legacy} ${stats}`.trim());
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

async function handleOverdrive() {
  sfx.scan();
  const res = await apiPost("/api/action", { action: "overdrive" });
  if (res && res.ok) {
    sfx.success();
    addTerminalLog(res.message, "success");
    state.data = res.state;
    renderHUD(res.state);
  } else if (res) {
    sfx.failure();
    addTerminalLog(res.message || "Overdrive refused.", "warn");
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

  // Firewall Status Indicator
  const fwEl = document.getElementById("target-firewall");
  if (fwEl) {
    if (node.firewall && node.firewall.enabled) {
      const blockedRules = (node.firewall.rules || []).filter(r => r.action === "BLOCK");
      const activeBlocks = blockedRules.filter(r => !r.bypassed);
      if (activeBlocks.length > 0) {
        fwEl.textContent = `FILTERING (${activeBlocks.length} BLOCKED)`;
        fwEl.className = "val fw-blocked";
      } else if (blockedRules.length > 0) {
        fwEl.textContent = "BYPASSED";
        fwEl.className = "val fw-bypassed";
      } else {
        fwEl.textContent = "ALLOW ALL";
        fwEl.className = "val fw-allowed";
      }
    } else {
      fwEl.textContent = "DISABLED";
      fwEl.className = "val";
    }
  }

  // Antivirus / EDR Indicator
  const avEl = document.getElementById("target-antivirus");
  if (avEl) {
    if (node.antivirus && node.antivirus.enabled) {
      if (node.antivirus.evaded) {
        avEl.textContent = `${node.antivirus.name} [EVADED]`;
        avEl.className = "val av-evaded";
      } else {
        const alertLvl = node.antivirus.alert_level || 0;
        avEl.textContent = `${node.antivirus.name} (${alertLvl}%)`;
        if (alertLvl >= 50) {
          avEl.className = "val av-alert-high";
        } else if (alertLvl >= 20) {
          avEl.className = "val av-alert-med";
        } else {
          avEl.className = "val";
        }
      }
    } else {
      avEl.textContent = "NONE";
      avEl.className = "val";
    }
  }

  const btnProbe = document.getElementById("btn-probe-node");
  const btnHack = document.getElementById("btn-init-hack");
  const btnMove = document.getElementById("btn-move-node");
  const btnPhish = document.getElementById("btn-phish-node");
  const btnKeylogger = document.getElementById("btn-keylogger-node");
  const btnWipe = document.getElementById("btn-wipe-logs");
  const btnBypass = document.getElementById("btn-bypass-fw");
  const btnEvade = document.getElementById("btn-evade-av");
  const btnSocial = document.getElementById("btn-social-eng");

  const isAdjacent = curr.connected_ids.includes(nodeId) || curr.node_id === nodeId;
  const isBreached = node.status === "BREACHED";

  btnProbe.disabled = node.status === "LOCKED" && !isAdjacent;
  btnHack.disabled = isBreached || !isAdjacent;
  btnMove.disabled = !isBreached || curr.node_id === nodeId;
  if (btnPhish) btnPhish.disabled = isBreached || (node.status === "LOCKED" && !isAdjacent);
  btnKeylogger.disabled = !isBreached;
  btnWipe.disabled = !isBreached;

  if (btnBypass) {
    const hasBlocked = node.firewall && node.firewall.enabled && (node.firewall.rules || []).some(r => r.action === "BLOCK" && !r.bypassed);
    btnBypass.disabled = !isAdjacent || !hasBlocked || isBreached;
  }
  if (btnEvade) {
    const hasAv = node.antivirus && node.antivirus.enabled && !node.antivirus.evaded;
    btnEvade.disabled = !isAdjacent || !hasAv;
  }
  if (btnSocial) {
    btnSocial.disabled = isBreached || (node.status === "LOCKED" && !isAdjacent);
  }

  if (isBreached) {
    document.getElementById("probed-ports-container").classList.add("hidden");
    loadFilesystemView(nodeId);
  } else if (node.ports && node.ports.length > 0 && node.status !== "LOCKED") {
    renderProbedPortsBay(node);
  } else {
    document.getElementById("probed-ports-container").classList.add("hidden");
    document.getElementById("filesystem-container").classList.add("hidden");
    document.getElementById("puzzle-idle").classList.remove("hidden");
  }
}

function renderProbedPortsBay(node) {
  const container = document.getElementById("probed-ports-container");
  const grid = document.getElementById("probed-ports-grid");
  document.getElementById("probed-target-host").textContent = `${node.hostname} (${node.ip_address})`;

  document.getElementById("puzzle-idle").classList.add("hidden");
  document.getElementById("filesystem-container").classList.add("hidden");
  document.getElementById("puzzle-frequency").classList.add("hidden");
  document.getElementById("puzzle-buffer").classList.add("hidden");
  document.getElementById("puzzle-hash").classList.add("hidden");
  container.classList.remove("hidden");

  grid.innerHTML = "";
  if (!node.ports || node.ports.length === 0) {
    grid.innerHTML = '<div style="color:var(--c-text-dim); font-size:11px; padding:6px;">No open ports identified. Click PROBE PORTS [P] to scan.</div>';
    return;
  }

  node.ports.forEach((p) => {
    const card = document.createElement("div");
    card.className = "probed-port-card";

    let fwBlocked = false;
    let fwBypassed = false;
    if (node.firewall && node.firewall.enabled) {
      const rule = (node.firewall.rules || []).find(r => r.port === p.port);
      if (rule) {
        if (rule.bypassed) fwBypassed = true;
        else if (rule.action === "BLOCK") fwBlocked = true;
      }
    }

    let badgeClass = "badge-secure";
    let badgeText = "SECURE";
    if (p.breached) {
      badgeClass = "badge-breached";
      badgeText = "BREACHED";
    } else if (fwBlocked) {
      badgeClass = "badge-blocked";
      badgeText = "FW BLOCKED";
    } else if (p.vulnerable) {
      badgeClass = "badge-vuln";
      badgeText = "VULNERABLE";
    }

    const fwNotice = fwBypassed ? '<span style="color:var(--c-warning); font-size:9px;">[FW BYPASSED]</span> ' : '';

    card.innerHTML = `
      <div class="port-card-info">
        <div class="port-card-title">PORT ${p.port}/tcp : ${p.service.toUpperCase()} ${fwNotice}</div>
        <div class="port-card-service">${p.version || "Service Banner"}</div>
        <span class="port-status-badge ${badgeClass}">${badgeText}</span>
      </div>
      <div class="port-card-actions">
        ${fwBlocked ? `<button class="port-action-btn bypass-btn" data-port="${p.port}">BYPASS FW</button>` : ''}
        ${p.vulnerable && !p.breached && !fwBlocked ? `<button class="port-action-btn exploit-btn" data-port="${p.port}">💥 EXPLOIT</button>` : ''}
      </div>
    `;

    const bypassBtn = card.querySelector(".bypass-btn");
    if (bypassBtn) {
      bypassBtn.onclick = (e) => {
        e.stopPropagation();
        openBypassModal(p.port);
      };
    }

    const exploitBtn = card.querySelector(".exploit-btn");
    if (exploitBtn) {
      exploitBtn.onclick = async (e) => {
        e.stopPropagation();
        sfx.click();
        addTerminalLog(`⚡ Launching targeted exploit against port ${p.port}/tcp (${p.service})...`, "info");
        const res = await apiPost("/api/action", {
          action: "exploit_service",
          target: node.node_id,
          port: p.port,
        });
        if (res && res.ok) {
          sfx.success();
          addTerminalLog(res.message, "success");
          state.data = res.state;
          renderHUD(res.state);
          updateTargetCard(node.node_id);
          loadFilesystemView(node.node_id);
        } else if (res) {
          sfx.failure();
          addTerminalLog(res.message || "Exploit execution failed.", "danger");
          state.data = res.state;
          renderHUD(res.state);
        }
      };
    }

    grid.appendChild(card);
  });
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
      let fwTag = "";
      if (node.firewall && node.firewall.enabled) {
        const rule = (node.firewall.rules || []).find(r => r.port === p.port);
        if (rule) {
          if (rule.bypassed) {
            fwTag = ' <span style="color:var(--c-warning); font-size:9px;">[FW: BYPASSED]</span>';
          } else if (rule.action === "BLOCK") {
            fwTag = ' <span style="color:var(--c-danger); font-size:9px;">[FW: BLOCKED]</span>';
          }
        }
      }
      const tagClass = p.breached ? "port-tag-breached" : (p.vulnerable ? "port-tag-vulnerable" : "");
      const tagText = p.breached ? "BREACHED" : (p.vulnerable ? "VULNERABLE" : "SECURE");
      pDiv.innerHTML = `<span><strong>${p.port}/tcp</strong> ${p.service} (${p.version})${fwTag}</span><span class="${tagClass}">[${tagText}]</span>`;
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
    if (state.data.nodes[state.selectedNodeId] && state.data.nodes[state.selectedNodeId].status !== "BREACHED") {
      renderProbedPortsBay(state.data.nodes[state.selectedNodeId]);
    }
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
// 9. Story, Mission Board & Operative Interactions
// ==========================================================================
function openQuestsModal() {
  sfx.click();
  if (!state.data) return;
  const story = state.data.story || {};
  const quests = state.data.quests || [];

  document.getElementById("story-brief").innerHTML = `
    <div class="story-brief-act">${story.act_title || "ACT I"} // ${story.chapter_title || "Ghost in the Gateway"}</div>
    <div class="story-brief-text">${story.intro || ""}</div>
    ${story.choice_label ? `<div class="story-choice">CHOICE LOCKED: ${story.choice_label}</div>` : ""}
  `;

  const logEl = document.getElementById("story-log");
  logEl.innerHTML = "";
  (story.log || []).slice(-10).forEach((line) => {
    const entry = document.createElement("div");
    entry.className = "story-log-line";
    entry.textContent = `> ${line}`;
    logEl.appendChild(entry);
  });

  const grid = document.getElementById("quests-grid");
  grid.innerHTML = "";
  quests.forEach((quest) => {
    const card = document.createElement("div");
    const complete = quest.completed;
    const active = quest.accepted && !complete;
    const locked = quest.locked;
    card.className = `quest-card ${complete ? "quest-complete" : locked ? "quest-locked" : active ? "quest-active" : "quest-available"}`;
    const status = complete ? "COMPLETE" : locked ? "LOCKED" : active ? `${quest.progress}/${quest.required}` : "AVAILABLE";
    card.innerHTML = `
      <div class="quest-card-head">
        <span class="quest-title">${quest.title}</span>
        <span class="quest-status">${status}</span>
      </div>
      <div class="quest-desc">${quest.description}</div>
      <div class="quest-meta">GIVER: ${quest.giver} | REWARD: ${quest.reward_creds} CR</div>
      ${!quest.accepted && !complete && !locked ? `<button class="hack-btn small-btn accept-quest-btn" data-quest="${quest.quest_id}">ACCEPT JOB</button>` : ""}
    `;
    const acceptBtn = card.querySelector(".accept-quest-btn");
    if (acceptBtn) {
      acceptBtn.addEventListener("click", () => handleAcceptQuest(quest.quest_id));
    }
    grid.appendChild(card);
  });

  document.getElementById("modal-quests").classList.remove("hidden");
}

async function handleAcceptQuest(questId) {
  sfx.click();
  const res = await apiPost("/api/action", { action: "accept_quest", quest_id: questId });
  if (res && res.ok) {
    sfx.success();
    addTerminalLog(res.message, "success");
    state.data = res.state;
    renderHUD(res.state);
    openQuestsModal();
  } else if (res) {
    sfx.failure();
    addTerminalLog(res.message || "Quest unavailable.", "warn");
  }
}

function openContactsModal() {
  sfx.click();
  if (!state.data) return;
  const grid = document.getElementById("contacts-grid");
  grid.innerHTML = "";

  (state.data.contacts || []).forEach((contact) => {
    const card = document.createElement("div");
    if (contact.locked) {
      card.className = "contact-card contact-locked";
      card.innerHTML = `
        <div class="contact-name">${contact.name}</div>
        <div class="contact-role">${contact.handle} // SIGNAL LOCKED</div>
        <div class="contact-tagline">Advance the story to open this channel.</div>
      `;
      grid.appendChild(card);
      return;
    }

    card.className = "contact-card";
    card.innerHTML = `
      <div class="contact-head">
        <div>
          <div class="contact-name">${contact.name}</div>
          <div class="contact-role">${contact.handle} // ${contact.role}</div>
        </div>
        <span class="contact-trust">TRUST ${contact.trust}</span>
      </div>
      <div class="contact-tagline">${contact.tagline}</div>
      <div class="contact-dialogue">"${contact.dialogue}"</div>
      <div class="contact-favor">${contact.favor_description}</div>
      <div class="contact-actions">
        <button class="action-btn small-btn contact-action" data-mode="talk">TALK</button>
        <button class="action-btn small-btn contact-action" data-mode="job">JOB</button>
        <button class="action-btn small-btn contact-action" data-mode="favor" ${contact.favor_used ? "disabled" : ""}>
          ${contact.favor_used ? "FAVOR SPENT" : "CALL FAVOR"}
        </button>
      </div>
      ${contact.pact_available ? `
        <div class="contact-pact">
          <div class="contact-pact-label">ACT III ALLIANCE // ONE CHOICE</div>
          <div class="contact-actions">
            <button class="action-btn small-btn contact-action pact-ally" data-mode="ally">ALLY WITH ZERO</button>
            <button class="action-btn small-btn contact-action pact-defy" data-mode="defy">DEFY ZERO</button>
          </div>
        </div>
      ` : ""}
    `;
    card.querySelectorAll(".contact-action").forEach((button) => {
      button.addEventListener("click", () => handleContactInteraction(contact.contact_id, button.dataset.mode));
    });
    grid.appendChild(card);
  });

  document.getElementById("modal-contacts").classList.remove("hidden");
}

async function handleContactInteraction(contactId, mode) {
  sfx.click();
  const res = await apiPost("/api/action", { action: "contact", contact_id: contactId, mode });
  if (res && res.ok) {
    sfx.success();
    addTerminalLog(res.message, "success");
    state.data = res.state;
    renderHUD(res.state);
    openContactsModal();
  } else if (res) {
    sfx.failure();
    addTerminalLog(res.message || "No response on the channel.", "warn");
  }
}

// ==========================================================================
// 10. Black Market Shop & Career Dossier Modals
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
  document.getElementById("dossier-combo").textContent = `x${data.best_combo || 0}`;
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

  const unbanked = (state.data && state.data.state) ? state.data.state.unbanked_creds : 0;
  const banked = (state.data && state.data.deck) ? state.data.deck.cryptocreds : 0;
  const totalCreds = unbanked + banked;
  document.getElementById("workshop-creds").textContent = `${totalCreds} (${banked} BANKED + ${unbanked} UNBANKED)`;
  const grid = document.getElementById("workshop-recipes-grid");
  grid.innerHTML = "";

  data.recipes.forEach((recipe) => {
    const card = document.createElement("div");
    card.className = "workshop-recipe-card";
    const canCraft = totalCreds >= recipe.cost_creds;

    card.innerHTML = `
      <div class="recipe-info">
        <div class="recipe-name">${recipe.name} [${recipe.vector}]</div>
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
      const res = await apiPost("/api/action", { action: "craft", recipe: recipe.name });
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

// ==========================================================================
// 10. Weaponized CVE Exploit Arsenal Modal
// ==========================================================================
async function openCvesModal() {
  sfx.click();
  const data = await apiGet("/api/cves");
  const cves = (data && data.cves) ? data.cves : (state.data && state.data.known_cves ? state.data.known_cves : []);

  document.getElementById("cves-count").textContent = cves.length;
  const grid = document.getElementById("cves-grid");
  grid.innerHTML = "";

  cves.forEach((c) => {
    const card = document.createElement("div");
    card.className = "cve-card";
    card.innerHTML = `
      <div class="cve-header">
        <span class="cve-id">${c.cve_id}</span>
        <span class="cve-badge">${c.target_service.toUpperCase()} SERVICE</span>
      </div>
      <div class="cve-name">${c.name}</div>
      <div class="cve-meta-row">
        <span>RAM: <strong>${c.required_ram_mb}MB</strong></span>
        <span>CPU: <strong>${c.cpu_cost} Cycles</strong></span>
        <span>STEALTH: <strong>${c.stealth_rating}/5</strong></span>
        <span>TRACE: <strong>+${c.damage_trace}%</strong></span>
      </div>
      <div class="cve-desc">${c.description}</div>
    `;
    grid.appendChild(card);
  });

  document.getElementById("modal-cves").classList.remove("hidden");
}

// ==========================================================================
// 11. Multi-Vector Social Engineering Suite
// ==========================================================================
function openSocialModal() {
  if (!state.selectedNodeId) return;
  const node = state.data.nodes[state.selectedNodeId];
  if (!node) return;

  sfx.click();
  document.getElementById("social-target-name").textContent = node.hostname;
  document.getElementById("social-target-ip").textContent = node.ip_address;

  // Render employees
  const empGrid = document.getElementById("social-employees-grid");
  empGrid.innerHTML = "";
  const employees = node.employees || [];

  if (employees.length === 0) {
    empGrid.innerHTML = '<span class="empty-chips">No identifiable staff on host. Using default associate.</span>';
    state.selectedEmployee = null;
  } else {
    state.selectedEmployee = employees[0].name;
    employees.forEach((emp, idx) => {
      const card = document.createElement("div");
      card.className = `employee-card ${idx === 0 ? "selected" : ""}`;
      const badgeClass = (emp.awareness_level || "STANDARD").toLowerCase();
      card.innerHTML = `
        <div class="employee-name">${emp.name}</div>
        <div class="employee-role">${emp.role}</div>
        <span class="employee-badge ${badgeClass}">${emp.awareness_level}</span>
      `;
      card.addEventListener("click", () => {
        sfx.click();
        empGrid.querySelectorAll(".employee-card").forEach(c => c.classList.remove("selected"));
        card.classList.add("selected");
        state.selectedEmployee = emp.name;
      });
      empGrid.appendChild(card);
    });
  }

  // Setup vector cards selection
  const vectorCards = document.querySelectorAll("#social-vectors-grid .vector-card");
  vectorCards.forEach((card) => {
    card.onclick = () => {
      sfx.click();
      vectorCards.forEach(c => c.classList.remove("selected"));
      card.classList.add("selected");
      state.selectedVector = card.dataset.vector;
    };
  });

  document.getElementById("modal-social").classList.remove("hidden");
}

async function executeSocialAttack() {
  if (!state.selectedNodeId) return;
  sfx.scan();
  addTerminalLog(`⚡ Launching ${state.selectedVector.toUpperCase()} campaign against ${state.selectedNodeId}...`, "info");
  document.getElementById("modal-social").classList.add("hidden");

  const res = await apiPost("/api/action", {
    action: "social",
    target: state.selectedNodeId,
    vector: state.selectedVector || "spear_phish",
    employee: state.selectedEmployee,
  });

  if (res && res.ok) {
    sfx.success();
    addTerminalLog(res.message, "success");
    state.data = res.state;
    renderHUD(res.state);
    updateTargetCard(state.selectedNodeId);
  } else if (res) {
    sfx.alarm();
    addTerminalLog(res.message || "Social engineering campaign failed.", "danger");
    if (res.state) {
      state.data = res.state;
      renderHUD(res.state);
      updateTargetCard(state.selectedNodeId);
    }
  }
}

// ==========================================================================
// 12. Firewall Ingress Bypass & Antivirus Evasion Handlers
// ==========================================================================
function openBypassModal(port) {
  if (!state.selectedNodeId) return;
  const node = state.data.nodes[state.selectedNodeId];
  if (!node || !node.firewall) return;

  sfx.click();
  const blockedRules = (node.firewall.rules || []).filter(r => r.action === "BLOCK" && !r.bypassed);
  if (blockedRules.length === 0) {
    addTerminalLog("No active blocked firewall rules to bypass on this host.", "info");
    return;
  }

  const requestedRule = blockedRules.find(r => r.port === port);
  const targetPort = (requestedRule || blockedRules[0]).port;
  document.getElementById("bypass-target-info").innerHTML = `
    <div>TARGET HOST: <strong>${node.hostname} (${node.ip_address})</strong></div>
    <div>BLOCKED PORT: <strong style="color:var(--c-danger);">${targetPort}/tcp</strong> | POLICY: <strong>${node.firewall.policy}</strong></div>
  `;

  const grid = document.getElementById("bypass-methods-grid");
  grid.innerHTML = "";

  const methods = [
    { key: "knock", name: "Port Knocking Sequence (TCP SYN)", cost: "1 CPU", trace: "+5% TRACE", desc: "Craft sequence of closed-port connection attempts to trigger dynamic firewall rule opening." },
    { key: "fragment", name: "Packet Fragmentation Cloak", cost: "1 CPU", trace: "+7% TRACE", desc: "Split malicious TCP headers across microscopic MTU IP fragments to evade stateful inspection." },
    { key: "tunnel", name: "Proxy Tunnel Injection", cost: "2 CPU", trace: "+9% TRACE", desc: "Encapsulate port payloads inside legitimate SSH/HTTP tunnel to silently pass ingress inspection." },
  ];

  methods.forEach((m) => {
    const card = document.createElement("div");
    card.className = "bypass-method-card";
    card.innerHTML = `
      <div>
        <div class="bypass-method-name">${m.name}</div>
        <div class="bypass-method-desc">${m.desc}</div>
      </div>
      <div style="text-align:right;">
        <span style="font-size:10px; color:var(--c-accent);">${m.cost}</span><br>
        <span style="font-size:9px; color:var(--c-warning);">${m.trace}</span>
      </div>
    `;
    card.addEventListener("click", async () => {
      sfx.click();
      document.getElementById("modal-bypass").classList.add("hidden");
      addTerminalLog(`Injecting ${m.name} on ${node.hostname}:${targetPort}...`, "info");
      const res = await apiPost("/api/action", {
        action: "bypass",
        target: state.selectedNodeId,
        port: targetPort,
        method: m.key,
      });
      if (res && res.ok) {
        sfx.success();
        addTerminalLog(res.message, "success");
        state.data = res.state;
        renderHUD(res.state);
        updateTargetCard(state.selectedNodeId);
      } else if (res) {
        sfx.failure();
        addTerminalLog(res.message || "Firewall bypass failed.", "warn");
      }
    });
    grid.appendChild(card);
  });

  document.getElementById("modal-bypass").classList.remove("hidden");
}

async function handleEvadeAv() {
  if (!state.selectedNodeId) return;
  const node = state.data.nodes[state.selectedNodeId];
  if (!node || !node.antivirus) return;

  sfx.click();
  addTerminalLog(`Deploying Kernel Rootkit Evasion Hook against ${node.antivirus.name}...`, "info");
  const res = await apiPost("/api/action", {
    action: "evade",
    target: state.selectedNodeId,
    method: "rootkit",
  });
  if (res && res.ok) {
    sfx.success();
    addTerminalLog(res.message, "success");
    state.data = res.state;
    renderHUD(res.state);
    updateTargetCard(state.selectedNodeId);
  } else if (res) {
    sfx.failure();
    addTerminalLog(res.message || "AV evasion failed.", "warn");
  }
}

