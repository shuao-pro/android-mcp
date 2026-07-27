// ========== i18n ==========
const I18N = {
  zh: {
    statusConnected: '已连接', statusDisconnected: '未连接',
    noDevice: '无设备', setupWizard: '配置向导',
    deviceInfo: '设备信息', model: '型号', android: '安卓版本',
    display: '分辨率', battery: '电池', app: '当前应用', shizuku: 'Shizuku',
    quickActions: '快捷操作', shellTerminal: 'Shell 终端',
    shellPlaceholder: '输入命令...', run: '执行', shellDefault: '输入命令...',
    chatWelcome: '🤖 AI 手机助手',
    chatWelcomeDesc: '用自然语言操控你的 Android 设备。<br>在下方输入消息开始使用。',
    chatPlaceholder: '描述你想在手机上做什么...', send: '发送',
    liveScreen: '实时屏幕', refresh: '刷新', autoOff: '自动: 关', autoOn: '自动: 开',
    save: '保存', screenshotPlaceholder: '点击刷新加载截图',
    setupTitle: '连接配置向导',
    setupSubtitle: '按照以下步骤连接你的 Android 设备。',
    stepAdbTitle: '安装 ADB', stepAdbDesc: '下载 Android SDK Platform Tools 并添加到 PATH。',
    stepDeviceTitle: '连接设备', stepDeviceDesc: '通过 USB 连接手机并开启 USB 调试，或使用无线 ADB。',
    stepAndroidTitle: '启动 Android MCP 服务',
    stepAndroidDesc: '在手机上启动 <b>Shizuku</b> → 打开 <b>Android MCP</b> App → 授权 Shizuku → 点击 <b>Start</b>。服务监听 18080 端口接受设备控制指令。',
    stepMcpTitle: 'MCP 服务器 & API 前端',
    stepMcpDesc: 'MCP 服务器（SSE + Streamable HTTP）运行在 <b>9000</b> 端口。在手机上安装 <b>Kai 9000</b>（F-Droid），添加下方端点即可通过对话操控设备。',
    stepEnvTitle: '配置环境',
    stepEnvDesc: '在项目根目录创建 .env 文件（从 .env.example 复制），默认配置即可使用。',
    stepVisionTitle: 'AI 视觉 API',
    stepVisionDesc: '在 .env 中设置 VISION_PROVIDER 和 VISION_API_KEY，以启用 AI 对话和屏幕元素识别。',
    optional: '可选', checkAll: '全部检测', done: '完成',
    found: '已安装', notFound: '未找到',
    connected: '已连接', notConnected: '未连接',
    running: '运行中', notReachable: '无法连接',
    configured: '已配置', missing: '未配置',
    notSet: '未设置 (AI 对话不可用)',
    allPass: '全部检测通过 — 准备就绪！',
    someFail: '项通过 — 请修复上方问题',
    serverDown: '服务器无法访问',
    cannotCheck: '无法检测',
    clickRefresh: '点击刷新加载', loading: '加载中...',
    screenshotFailed: '截图失败', toastSent: '已发送',
    toastClicked: '已点击', quickSent: '已发送',
    language: '语言', refreshStatus: '刷新状态',
  },
  en: {
    statusConnected: 'Connected', statusDisconnected: 'Disconnected',
    noDevice: 'No device', setupWizard: 'Setup',
    deviceInfo: 'Device Info', model: 'Model', android: 'Android',
    display: 'Display', battery: 'Battery', app: 'App', shizuku: 'Shizuku',
    quickActions: 'Quick Actions', shellTerminal: 'Shell Terminal',
    shellPlaceholder: 'Enter command...', run: 'Run', shellDefault: 'Enter a command...',
    chatWelcome: '🤖 AI Phone Assistant',
    chatWelcomeDesc: 'Control your Android device with natural language.<br>Type a message below to get started.',
    chatPlaceholder: 'Describe what you want to do on the phone...', send: 'Send',
    liveScreen: 'Live Screen', refresh: 'Refresh', autoOff: 'Auto: Off', autoOn: 'Auto: On',
    save: 'Save', screenshotPlaceholder: 'Click Refresh to load',
    setupTitle: 'Connection Setup Wizard',
    setupSubtitle: 'Follow these steps to connect your Android device.',
    stepAdbTitle: 'Install ADB', stepAdbDesc: 'Download Android SDK Platform Tools and add to PATH.',
    stepDeviceTitle: 'Connect Device', stepDeviceDesc: 'Connect phone via USB with USB Debugging enabled, or use wireless ADB.',
    stepAndroidTitle: 'Start Android MCP Service',
    stepAndroidDesc: 'Start <b>Shizuku</b> → open <b>Android MCP</b> app → grant Shizuku permission → tap <b>Start</b>. The app listens on port 18080 for device control commands.',
    stepMcpTitle: 'MCP Server & API Frontend',
    stepMcpDesc: 'The MCP server (SSE + Streamable HTTP) runs on port <b>9000</b>. Connect <b>Kai 9000</b> (F-Droid) or any MCP client to the endpoints below, then chat to control the device.',
    stepEnvTitle: 'Configure Environment',
    stepEnvDesc: 'Create .env file in the project root (copy from .env.example). Default config works out of the box.',
    stepVisionTitle: 'AI Vision API',
    stepVisionDesc: 'Set VISION_PROVIDER and VISION_API_KEY in .env to enable AI chat and screen element recognition.',
    optional: 'Optional', checkAll: 'Check All', done: 'Done',
    found: 'Found', notFound: 'Not found',
    connected: 'Connected', notConnected: 'Not connected',
    running: 'Running', notReachable: 'Not reachable',
    configured: 'Configured', missing: 'Missing',
    notSet: 'Not set (AI disabled)',
    allPass: 'All checks passed — ready!',
    someFail: 'checks passed — fix issues above',
    serverDown: 'Server not reachable',
    cannotCheck: 'Cannot check',
    clickRefresh: 'Click Refresh to load', loading: 'Loading...',
    screenshotFailed: 'Screenshot failed', toastSent: 'Sent',
    toastClicked: 'Clicked', quickSent: 'Sent',
    language: 'Language', refreshStatus: 'Refresh Status',
  }
};

let currentLang = localStorage.getItem('mcp-lang') || '';

function t(key) {
  const lang = currentLang || 'en';
  return (I18N[lang] && I18N[lang][key]) || (I18N['en'][key]) || key;
}

function setLang(lang) {
  currentLang = lang;
  localStorage.setItem('mcp-lang', lang);
  applyLanguage();
  highlightActiveLang();
}

function applyLanguage() {
  // Update data-i18n elements
  document.querySelectorAll('[data-i18n]').forEach(el => {
    const key = el.getAttribute('data-i18n');
    if (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA') {
      el.placeholder = t(key);
    } else {
      el.textContent = t(key);
    }
  });
  // Update dynamic UI elements
  updateDynamicLanguage();
}

function updateDynamicLanguage() {
  const statusLabel = document.getElementById('statusLabel');
  const statusDot = document.getElementById('statusDot');
  if (statusLabel && statusDot) {
    if (statusDot.classList.contains('online')) {
      statusLabel.textContent = t('statusConnected');
    } else {
      statusLabel.textContent = t('statusDisconnected');
    }
  }
  const deviceModel = document.getElementById('deviceModel');
  if (deviceModel && deviceModel.textContent === 'No device') deviceModel.textContent = t('noDevice');
  const shEl = document.getElementById('shellOutput');
  if (shEl && shEl.textContent === 'Enter a command...') shEl.textContent = t('shellDefault');
  const sfEl = document.getElementById('screenshotFrame');
  if (sfEl) {
    const ph = sfEl.querySelector('.placeholder');
    if (ph) ph.textContent = t('screenshotPlaceholder');
  }
  const welcome = document.getElementById('chatWelcome');
  if (welcome) {
    const h2 = welcome.querySelector('h2');
    const p = welcome.querySelector('p');
    if (h2) h2.textContent = t('chatWelcome');
    if (p) p.innerHTML = t('chatWelcomeDesc');
  }
  // Setup wizard labels
  var st = document.getElementById('setupSummary');
  if (st && st.classList) {
    if (st.classList.contains('all-pass')) st.textContent = t('allPass');
    else if (st.classList.contains('has-fail')) st.textContent = '';
  }
}

// ========== Header Menu ==========
function toggleMenu(e) {
  e.stopPropagation();
  document.getElementById('menuDropdown').classList.toggle('open');
  highlightActiveLang();
}

function closeMenu() {
  document.getElementById('menuDropdown').classList.remove('open');
}

function highlightActiveLang() {
  const zh = document.getElementById('menuLangZh');
  const en = document.getElementById('menuLangEn');
  if (zh && en) {
    zh.classList.toggle('active', currentLang === 'zh');
    en.classList.toggle('active', currentLang === 'en' || !currentLang);
  }
}

// Click outside to close
document.addEventListener('click', (e) => {
  const menu = document.getElementById('headerMenu');
  if (menu && !menu.contains(e.target)) {
    closeMenu();
  }
});

// Language picker (kept for setLang reference, now uses menu)
function toggleLangPicker() {}

// ========== State ==========
let ws = null;
let chatHistory = [];
let autoRefresh = false;
let autoTimer = null;
let lastScreenshotBase64 = null;
let lastScreenshotWidth = 0;
let lastScreenshotHeight = 0;

// ========== WebSocket ==========
function connectWS() {
  const proto = location.protocol === 'https:' ? 'wss' : 'ws';
  ws = new WebSocket(`${proto}://${location.host}/ws`);

  ws.onopen = () => {
    _wasEverConnected = true;
    console.log('WS connected');
    refreshDeviceInfo();
    setTimeout(refreshScreen, 800);
  };

  ws.onmessage = (e) => {
    const msg = JSON.parse(e.data);
    if (msg.type === 'status') {
      updateStatus(msg.data);
    } else if (msg.cmd === 'chat') {
      handleChatReply(msg.result);
    } else if (msg.cmd === 'screenshot') {
      handleScreenshot(msg.result);
    } else if (msg.cmd === 'device_info') {
      updateDeviceInfo(msg.result);
    } else if (msg.cmd === 'battery') {
      updateBattery(msg.result);
    } else if (msg.cmd === 'shell') {
      handleShellResult(msg.result);
    } else if (msg.result !== undefined) {
      // Generic feedback for quick actions (press_key, click, etc.)
      if (msg.result.success) {
        toast('✅ ' + (msg.cmd || 'Done'));
      } else if (msg.result.error) {
        toast('❌ ' + msg.result.error);
      }
    }
  };

  ws.onclose = () => {
    updateConnectionStatus(false);
    // Reconnect after a short delay
    setTimeout(connectWS, 2000);
  };

  ws.onerror = () => {
    // Will be followed by onclose, so just ignore here
  };
}

// ========== Connection Status ==========
function updateConnectionStatus(online) {
  const dot = document.getElementById('statusDot');
  const label = document.getElementById('statusLabel');
  if (online) {
    dot.classList.add('online');
    label.textContent = t('statusConnected');
  } else {
    dot.classList.remove('online');
    label.textContent = t('statusDisconnected');
  }
}

function updateStatus(data) {
  if (data && data.connected) {
    updateConnectionStatus(true);
    if (data.device_info) {
      updateDeviceInfo({ success: true, data: data.device_info });
      document.getElementById('devShizuku').textContent = 'Running';
    }
    // Show MCP client count if available
    if (data.mcp_clients !== undefined) {
      const el = document.getElementById('mcpClients');
      const sep = document.getElementById('mcpSep');
      el.textContent = data.mcp_clients + ' MCP';
      el.classList.toggle('has-clients', data.mcp_clients > 0);
      el.hidden = false;
      sep.hidden = false;
    }
  } else {
    updateConnectionStatus(false);
    // Keep showing MCP count if reported
    if (data && data.mcp_clients !== undefined) {
      const el = document.getElementById('mcpClients');
      const sep = document.getElementById('mcpSep');
      el.textContent = data.mcp_clients + ' MCP';
      el.classList.toggle('has-clients', data.mcp_clients > 0);
      el.hidden = false;
      sep.hidden = false;
    }
  }
}

// ========== Device Info ==========
async function refreshDeviceInfo() {
  sendWS('device_info');
  sendWS('battery');
}

function updateDeviceInfo(result) {
  if (!result.success) return;
  const d = result.data || {};
  setVal('devModel', d.device_name || d.model || '--');
  setVal('devAndroid', d.android_version || '--');
  setVal('devDisplay', d.display_size || '--');
  setVal('devApp', (d.current_app || '--').slice(0, 30));
  setVal('devShizuku', d.shizuku_running ? 'OK' : 'Off');
  document.getElementById('deviceModel').textContent = d.device_name || d.model || 'No device';
}

function updateBattery(result) {
  if (!result.success) return;
  const d = result.data || {};
  setVal('devBattery', `${d.level || '?'}%`);
}

// ========== Screen Stream (WebSocket) ==========
let screenWs = null;
let screenStreaming = false;

function toggleScreenStream() {
  if (screenStreaming) { stopScreenStream(); } else { startScreenStream(); }
}

function startScreenStream() {
  const proto = location.protocol === 'https:' ? 'wss' : 'ws';
  screenWs = new WebSocket(`${proto}://${location.host}/ws/screen`);
  screenWs.onopen = () => {
    screenStreaming = true;
    updateStreamUI();
    setInterval(() => {
      if (screenWs && screenWs.readyState === WebSocket.OPEN) {
        screenWs.send(JSON.stringify({ cmd: 'ping' }));
      }
    }, 15000);
  };
  screenWs.onmessage = (e) => {
    const msg = JSON.parse(e.data);
    if (msg.type === 'frame' && msg.base64) {
      lastScreenshotBase64 = msg.base64;
      const frame = document.getElementById('screenshotFrame');
      const ph = frame.querySelector('.placeholder');
      if (ph) ph.remove();
      let img = frame.querySelector('img');
      if (!img) { img = document.createElement('img'); img.id = 'screenshotImg'; frame.appendChild(img); }
      img.src = 'data:image/png;base64,' + msg.base64;
      if (!lastScreenshotWidth) {
        img.onload = () => { lastScreenshotWidth = img.naturalWidth; lastScreenshotHeight = img.naturalHeight; };
      }
      const badge = document.getElementById('streamBadge');
      if (badge) {
        badge.style.display = 'flex';
        // Update FPS display
        const fpsEl = document.getElementById('streamFps');
        if (fpsEl && msg.method) {
          const now = Date.now();
          if (!badge._lastFrame) badge._lastFrame = now;
          if (!badge._frameCount) badge._frameCount = 0;
          badge._frameCount++;
          if (now - badge._lastFrame >= 1000) {
            const fps = Math.round(badge._frameCount * 1000 / (now - badge._lastFrame));
            fpsEl.textContent = fps + 'fps';
            badge._frameCount = 0;
            badge._lastFrame = now;
          }
        }
      }
    } else if (msg.type === 'status' && msg.error === 'device_offline') {
      // Device not connected — stop streaming gracefully
      stopScreenStream();
      const frame = document.getElementById('screenshotFrame');
      frame.innerHTML = `<span class="placeholder">📱 <b>Device offline</b><br><br>Start <b>Shizuku</b> + <b>Android MCP</b> app<br>on your phone to see the live screen.</span>`;
    }
  };
  screenWs.onclose = () => { screenStreaming = false; updateStreamUI(); };
  screenWs.onerror = () => { screenStreaming = false; updateStreamUI(); };
}

function stopScreenStream() {
  if (screenWs) { screenWs.close(); screenWs = null; }
  screenStreaming = false; updateStreamUI();
}

function updateStreamUI() {
  const btn = document.getElementById('streamBtn');
  btn.textContent = screenStreaming ? '⏸ Stop' : '▶ Play';
  btn.classList.toggle('danger', screenStreaming);
}

function refreshScreen() {
  // Only refresh if streaming or if there's already an image (avoid spamming when offline)
  if (!screenStreaming) {
    const frame = document.getElementById('screenshotFrame');
    const hasImg = frame && frame.querySelector('img');
    const ph = frame && frame.querySelector('.placeholder');
    // Don't overwrite the "device offline" placeholder
    if (hasImg || (ph && ph.textContent.includes('Click'))) {
      sendWS('screenshot');
    }
  }
}

function handleScreenshot(result) {
  const frame = document.getElementById('screenshotFrame');
  if (result.success && result.data && result.data.base64) {
    lastScreenshotBase64 = result.data.base64;
    let img = frame.querySelector('img');
    if (!img) { const ph = frame.querySelector('.placeholder'); if (ph) ph.remove(); img = document.createElement('img'); img.id = 'screenshotImg'; frame.appendChild(img); }
    img.src = 'data:image/png;base64,' + result.data.base64;
    img.onload = () => { lastScreenshotWidth = img.naturalWidth; lastScreenshotHeight = img.naturalHeight; };
  } else {
    const err = result.error || '';
    if (err.includes('not reachable') || err.includes('disconnected')) {
      frame.innerHTML = `<span class="placeholder">📱 <b>Device offline</b><br><br>Start <b>Shizuku</b> + <b>Android MCP</b> app<br>on your phone to see the live screen.<br><br><small style="color:var(--text-muted)">Then click Refresh or Play</small></span>`;
    } else {
      frame.innerHTML = `<span class="placeholder">${t('screenshotFailed')}<br><small>${escHtml(err)}</small></span>`;
    }
  }
}

function onScreenshotClick(e) {
  const frame = document.getElementById('screenshotFrame');
  const img = frame.querySelector('img');
  if (!img || !lastScreenshotWidth) return;
  const rect = img.getBoundingClientRect();
  const devX = Math.round((e.clientX - rect.left) * lastScreenshotWidth / rect.width);
  const devY = Math.round((e.clientY - rect.top) * lastScreenshotHeight / rect.height);
  const indicator = document.createElement('div');
  indicator.className = 'click-indicator';
  indicator.style.left = (e.clientX - rect.left) + 'px';
  indicator.style.top = (e.clientY - rect.top) + 'px';
  frame.appendChild(indicator);
  setTimeout(() => indicator.remove(), 500);
  sendWS('click', { x: devX, y: devY });
  toast(`Clicked (${devX}, ${devY})`);
}

function toggleAuto() { toggleScreenStream(); }

// ========== scrcpy Controls ==========
async function toggleScrcpy() {
  try {
    const sr = await fetch('/api/scrcpy/status'); const st = await sr.json();
    const running = st.data?.running;
    const resp = await fetch(running ? '/api/scrcpy/stop' : '/api/scrcpy/start', { method: 'POST' });
    const result = await resp.json();
    const sel = document.getElementById('scrcpyStatus');
    sel.textContent = result.success ? (running ? 'scrcpy stopped' : 'scrcpy started') : (result.error || 'Failed');
    sel.className = 'scrcpy-status ' + (result.success ? 'success' : 'error');
    if (result.success) updateScrcpyUI(!running);
    setTimeout(() => { sel.textContent = ''; sel.className = 'scrcpy-status'; }, 3000);
  } catch (e) {}
}

function updateScrcpyUI(running) {
  const btn = document.getElementById('scrcpyBtn');
  btn.textContent = running ? '📱 Stop scrcpy' : '📱 scrcpy';
  btn.classList.toggle('danger', running);
}

async function checkScrcpyStatus() {
  try {
    const resp = await fetch('/api/scrcpy/status');
    const json = await resp.json();
    if (json.data?.installed) updateScrcpyUI(json.data.running);
    else { document.getElementById('scrcpyBtn').textContent = '📱 scrcpy (not installed)'; document.getElementById('scrcpyBtn').style.opacity = '0.5'; }
  } catch (e) {}
}

// ========== AI Chat ==========
function sendChat() {
  const input = document.getElementById('chatInput');
  const text = input.value.trim();
  if (!text) return;

  input.value = '';
  input.style.height = 'auto';

  // Hide welcome
  const welcome = document.getElementById('chatWelcome');
  if (welcome) welcome.style.display = 'none';

  // Add user message
  addChatMessage('user', text);

  // Show typing indicator
  showTyping();

  // Send to server
  ws.send(JSON.stringify({
    cmd: 'chat',
    text: text,
    history: chatHistory,
  }));

  // Disable send while waiting
  document.getElementById('chat-send-btn').disabled = true;
}

function sendExample(el) {
  document.getElementById('chatInput').value = el.textContent;
  sendChat();
}

function handleChatReply(result) {
  hideTyping();
  document.getElementById('chat-send-btn').disabled = false;

  if (!result) return;

  // Build reply text
  let replyText = result.reply || '';

  // If a tool was called, show result
  if (result.tool_called) {
    const toolName = result.tool_called;
    const toolResult = result.tool_result;

    if (toolResult && toolResult.success) {
      // For screenshot, show it in right panel
      if (toolName === 'take_screenshot' && toolResult.data && toolResult.data.base64) {
        handleScreenshot(toolResult);
      }
      // Add a system message with tool result summary
      let summary = formatToolResult(toolName, toolResult);
      if (summary) {
        addChatMessage('system', summary);
      }
    } else if (toolResult && !toolResult.success) {
      addChatMessage('system', `**${toolName}** failed: ${toolResult.error || 'unknown error'}`);
    }
  }

  // Update chat history
  chatHistory.push({ role: 'user', content: result.reply ? 'previous request' : '' });
  chatHistory.push({ role: 'assistant', content: replyText || 'Done' });
  if (chatHistory.length > 20) chatHistory = chatHistory.slice(-20);

  // Refresh screenshot after any action
  setTimeout(refreshScreen, 800);
  setTimeout(refreshDeviceInfo, 1000);
}

function formatToolResult(toolName, result) {
  const data = result.data || result;

  // Check for bridge-level errors (device not connected)
  if (!result.success && result.error) {
    const err = result.error;
    if (err.includes('not reachable') || err.includes('disconnected')) {
      return `⚠️ **Device offline** — Start Shizuku and Android MCP app on your phone, then run:\n\`\`\`\nadb forward tcp:18080 tcp:18080\n\`\`\``;
    }
    return `❌ **${toolName}** failed: ${err}`;
  }

  switch (toolName) {
    case 'shell':
      return `**Shell Output:**\n\`\`\`\n${(data.output || '').slice(0, 500)}\n\`\`\``;
    case 'take_screenshot':
      return 'Screenshot taken (shown in right panel)';
    case 'click':
      return `Clicked successfully`;
    case 'click_element':
      if (data.element_clicked) {
        const el = data.element_clicked;
        return `Clicked **${el.description}** at (${el.center_x}, ${el.center_y}), confidence: ${(el.confidence * 100).toFixed(0)}%`;
      }
      return 'Click completed';
    case 'find_element':
      if (data.found && data.elements && data.elements.length > 0) {
        const items = data.elements.map(e =>
          `- **${e.description}**: (${e.center_x}, ${e.center_y}) [${(e.confidence * 100).toFixed(0)}%]`
        ).join('\n');
        return `Found ${data.elements.length} element(s):\n${items}`;
      }
      return 'No matching elements found';
    case 'open_app':
    case 'close_app':
    case 'clear_app_data':
      return `${toolName.replace('_', ' ')} completed`;
    case 'get_device_info':
      if (data.device_name) return `Device: **${data.device_name}**, Android ${data.android_version}, Display: ${data.display_size}`;
      return 'Device info retrieved';
    case 'get_battery_info':
      return `Battery: **${data.level}%**`;
    case 'press_key':
      return `Key pressed`;
    case 'get_clipboard':
      return `Clipboard: \`${(data.output || '').slice(0, 200)}\``;
    case 'get_notifications':
      return `Notifications retrieved`;
    case 'list_installed_apps':
      return `App list retrieved (${(data.output || '').split('\n').length} packages)`;
    default:
      return `**${toolName}** executed`;
  }
}

function addChatMessage(role, text) {
  const container = document.getElementById('chat-messages');
  const div = document.createElement('div');
  div.className = `chat-msg ${role}`;

  const avatars = { user: '👤', assistant: '🤖', system: '📋' };
  const now = new Date();
  const time = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

  div.innerHTML = `
    <div class="chat-avatar">${avatars[role] || '•'}</div>
    <div class="chat-body">
      <div class="chat-bubble">${renderMarkdown(text)}</div>
      <div class="chat-time">${time}</div>
    </div>
  `;

  container.appendChild(div);
  container.scrollTop = container.scrollHeight;
}

function renderMarkdown(text) {
  let html = text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    // Links
    .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>')
    // Bold / italic / code / pre
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    .replace(/`([^`]+)`/g, '<code>$1</code>')
    .replace(/```([\s\S]*?)```/g, '<pre>$1</pre>')
    // Tables: pipe-separated rows
    .replace(/\|(.+)\|/g, (match) => {
      const cells = match.split('|').filter(c => c.trim());
      if (cells.every(c => /^[-:]+$/.test(c.trim()))) return ''; // skip separator rows
      const tag = match.includes('\n') ? 'td' : 'td';
      return '<tr>' + cells.map(c => `<${tag}>${c.trim()}</${tag}>`).join('') + '</tr>';
    })
    .replace(/(<tr>[\s\S]*?<\/tr>)/g, (match) => {
      // Wrap consecutive <tr> in <table>
      return match;
    })
    .replace(/\n/g, '<br>');
  return html;
}

function showTyping() {
  const container = document.getElementById('chat-messages');
  const div = document.createElement('div');
  div.className = 'chat-typing';
  div.id = 'typingIndicator';
  div.innerHTML = '<span></span><span></span><span></span>';
  container.appendChild(div);
  container.scrollTop = container.scrollHeight;
}

function hideTyping() {
  const el = document.getElementById('typingIndicator');
  if (el) el.remove();
}

function chatKey(e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    sendChat();
  }
}

// ========== Quick Actions ==========
function quick(cmd, params = {}) {
  sendWS(cmd, params);
  toast(t('toastSent'));
  setTimeout(refreshScreen, 1200);
  setTimeout(refreshDeviceInfo, 1500);

  // Also show in chat
  const welcome = document.getElementById('chatWelcome');
  if (welcome) welcome.style.display = 'none';
  addChatMessage('system', `⚡ Quick: **${cmd}**`);
}

// Debounce utility
function debounce(fn, delay) {
  let timer;
  return function (...args) {
    clearTimeout(timer);
    timer = setTimeout(() => fn.apply(this, args), delay);
  };
}

// ========== Shell Terminal ==========
let _shellHistory = [];
let _shellHistIdx = -1;

function shellKey(e) {
  if (e.key === 'Enter') { runShell(); return; }
  if (e.key === 'ArrowUp') { e.preventDefault(); shellHistPrev(); return; }
  if (e.key === 'ArrowDown') { e.preventDefault(); shellHistNext(); return; }
}

function shellHistPrev() {
  if (_shellHistory.length === 0) return;
  if (_shellHistIdx === -1) _shellHistIdx = _shellHistory.length - 1;
  else if (_shellHistIdx > 0) _shellHistIdx--;
  document.getElementById('shellInput').value = _shellHistory[_shellHistIdx] || '';
}

function shellHistNext() {
  if (_shellHistIdx === -1) return;
  if (_shellHistIdx < _shellHistory.length - 1) { _shellHistIdx++; document.getElementById('shellInput').value = _shellHistory[_shellHistIdx]; }
  else { _shellHistIdx = -1; document.getElementById('shellInput').value = ''; }
}

function runShell() {
  const input = document.getElementById('shellInput');
  const output = document.getElementById('shellOutput');
  const cmd = input.value.trim();
  if (!cmd) return;

  if (_shellHistory.length === 0 || _shellHistory[_shellHistory.length-1] !== cmd) {
    _shellHistory.push(cmd);
    if (_shellHistory.length > 50) _shellHistory.shift();
  }
  _shellHistIdx = -1;
  input.value = '';

  appendTermLine('term-cmd', '<span class="term-prompt-text">$</span>' + escHtml(cmd));
  appendTermLine('term-info', '...');
  sendWS('shell', { command: cmd });
}

function handleShellResult(result) {
  // Remove the "..." line
  const output = document.getElementById('shellOutput');
  const lines = output.querySelectorAll('.term-line');
  const last = lines[lines.length - 1];
  if (last && last.classList.contains('term-info') && last.textContent === '...') {
    last.remove();
  }

  if (result.success) {
    const out = (result.data?.output || result.stdout || '(no output)').trim();
    if (out) {
      out.split('\n').forEach(function(l) { appendTermLine('term-out', escHtml(l)); });
    } else {
      appendTermLine('term-info', '(empty)');
    }
  } else {
    appendTermLine('term-err', '[Error] ' + escHtml(result.error || result.data?.error || 'unknown'));
  }
  output.scrollTop = output.scrollHeight;
}

function appendTermLine(cls, html) {
  const output = document.getElementById('shellOutput');
  const div = document.createElement('div');
  div.className = 'term-line ' + cls;
  div.innerHTML = html;
  output.appendChild(div);
  output.scrollTop = output.scrollHeight;
}

// ========== WebSocket Send ==========
function sendWS(cmd, params = {}) {
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ cmd, params }));
  }
}

// ========== Toast ==========
function toast(msg) {
  const el = document.getElementById('toast');
  el.textContent = msg;
  el.classList.add('show');
  clearTimeout(el._timeout);
  el._timeout = setTimeout(() => el.classList.remove('show'), 2000);
}

// ========== Helpers ==========
function escHtml(s) {
  const d = document.createElement('div');
  d.textContent = s;
  return d.innerHTML;
}

function setVal(id, val) {
  const el = document.getElementById(id);
  if (el) el.textContent = val;
}

// Auto-resize chat textarea
document.addEventListener('DOMContentLoaded', () => {
  const ta = document.getElementById('chatInput');
  if (ta) {
    ta.addEventListener('input', () => {
      ta.style.height = 'auto';
      ta.style.height = Math.min(ta.scrollHeight, 120) + 'px';
    });
  }
});

// ========== Setup Wizard ==========
function openSetupWizard() {
  document.getElementById('setupModal').classList.add('show');
  checkAllSetup();
}

function closeSetupWizard() {
  document.getElementById('setupModal').classList.remove('show');
}

async function checkAllSetup() {
  var summary = document.getElementById('setupSummary');
  if (!summary) return;
  summary.textContent = '⏳ Detecting...';
  summary.className = 'setup-summary';

  var ids = ['adb','device','android','mcp','env','vision'];
  ids.forEach(function(id) {
    var s = document.getElementById('status-'+id);
    var e = document.getElementById('step-'+id);
    if (s && e) { s.textContent = '...'; s.className = 'step-status checking'; e.classList.remove('pass','fail'); }
  });

  var data;
  try {
    var resp = await fetch('/api/setup/status');
    var json = await resp.json();
    data = json.data || {};
  } catch(e) {
    ids.forEach(function(id) { setStepStatus(id, false, '', t('cannotCheck')); });
    summary.textContent = t('serverDown');
    summary.className = 'setup-summary has-fail';
    return;
  }

  // Render detail sections
  // ADB
  var adbDetail = document.getElementById('detail-adb');
  if (data.adb_installed) {
    adbDetail.innerHTML = '<div class=\"detail-row\"><span class=\"detail-k\">Path:</span><code>' + escHtml(data.adb_path) + '</code></div><div class=\"detail-row\"><span class=\"detail-k\">Version:</span>' + escHtml(data.adb_version) + '</div>';
  } else {
    adbDetail.innerHTML = '<div class=\"detail-row hint\">Run: <code>scoop install adb</code> or download from developer.android.com</div>';
  }

  // Device
  var devDetail = document.getElementById('detail-device');
  if (data.adb_device && data.adb_device_list && data.adb_device_list.length) {
    var html = '';
    data.adb_device_list.forEach(function(d) {
      html += '<div class=\"detail-row\"><span class=\"detail-k\">ID:</span><code>' + escHtml(d.id) + '</code>';
      if (d.model) html += ' <span class=\"detail-val\">' + escHtml(d.model.replace(/_/g, ' ')) + '</span>';
      html += '</div>';
    });
    devDetail.innerHTML = html;
  } else if (data.adb_installed) {
    devDetail.innerHTML = '<div class=\"detail-row hint\">Connect via USB with USB Debugging enabled, or <code>adb connect &lt;ip&gt;:5555</code></div>';
  } else {
    devDetail.innerHTML = '';
  }

  // Android MCP service (Shizuku, port 18080)
  var adDetail = document.getElementById('detail-android');
  if (data.android_service && data.android_service_detail) {
    var d = data.android_service_detail;
    var ahtml = '';
    if (d.device_name) ahtml += '<div class=\"detail-row\"><span class=\"detail-k\">Device:</span><span class=\"detail-val\">' + escHtml(d.device_name) + '</span></div>';
    if (d.android_version) ahtml += '<div class=\"detail-row\"><span class=\"detail-k\">Android:</span><span class=\"detail-val\">' + escHtml(d.android_version) + '</span></div>';
    ahtml += '<div class=\"detail-row\"><span class=\"detail-k\">Shizuku:</span><span class=\"detail-val ' + (d.shizuku_running ? 'pass' : 'fail') + '\">' + (d.shizuku_running ? 'Running' : 'Not running') + '</span></div>';
    adDetail.innerHTML = ahtml;
  } else {
    adDetail.innerHTML = '<div class=\"detail-row hint\">Start <b>Shizuku</b> &rarr; open <b>Android MCP</b> app &rarr; grant Shizuku permission &rarr; tap <b>Start</b> (port 18080)</div>';
  }

  // MCP Server status
  var mcpDetail = document.getElementById('detail-mcp');
  if (mcpDetail && data.mcp_server_running) {
    mcpDetail.innerHTML = '<div class=\"detail-row\"><span class=\"detail-k\">MCP Server:</span><span class=\"detail-val pass\">Running</span> <span class=\"detail-val\">(port ' + (data.mcp_server_port || 9000) + ')</span></div><div class=\"detail-row\"><span class=\"detail-k\">Transports:</span><span class=\"detail-val\">SSE + Streamable HTTP</span></div>';
    var mpd = document.getElementById('mcpPortDisplay');
    if (mpd) mpd.textContent = data.mcp_server_port || '9000';
  }

  // Server address box
  var addrBox = document.getElementById('serverAddressBox');
  if (addrBox && data.server_address) {
    addrBox.style.display = 'block';
    var mcpLocal = data.server_local.replace(/\/sse$/, '/mcp');
    var mcpLan = data.server_address.replace(/\/sse$/, '/mcp');
    var addrHtml = '<div style=\"margin-bottom:6px;color:var(--text-muted);font-size:11px;font-family:inherit\">MCP Endpoints — add in Kai 9000 / Cherry Studio:</div>';
    addrHtml += '<div style=\"display:flex;flex-direction:column;gap:4px\">';
    addrHtml += '<div style=\"display:flex;align-items:center;gap:8px\"><span style=\"font-size:10px;background:var(--accent);color:#fff;padding:1px 5px;border-radius:3px;font-family:inherit\">SSE</span><code style=\"color:var(--accent);font-size:13px\">' + escHtml(data.server_local) + '</code></div>';
    addrHtml += '<div style=\"display:flex;align-items:center;gap:8px\"><span style=\"font-size:10px;background:var(--green);color:#fff;padding:1px 5px;border-radius:3px;font-family:inherit\">HTTP</span><code style=\"color:var(--green);font-size:13px\">' + escHtml(mcpLocal) + '</code></div>';
    addrHtml += '</div>';
    if (data.server_ip !== '127.0.0.1') {
      addrHtml += '<div style=\"margin-top:8px;padding-top:8px;border-top:1px solid var(--border);font-size:10px;color:var(--text-muted);font-family:inherit\">Same WiFi (phone):</div>';
      addrHtml += '<div style=\"display:flex;flex-direction:column;gap:3px;margin-top:4px\"><code style=\"color:var(--text);font-size:12px\">' + escHtml(data.server_address) + '</code><code style=\"color:var(--text);font-size:12px\">' + escHtml(mcpLan) + '</code></div>';
    }
    addrBox.innerHTML = addrHtml;
  }

  // Env
  var envDetail = document.getElementById('detail-env');
  if (data.dotenv_exists) {
    envDetail.innerHTML = '<div class=\"detail-row\"><span class=\"detail-k\">Path:</span><code>' + escHtml(data.dotenv_path) + '</code></div>';
  } else {
    envDetail.innerHTML = '<div class=\"detail-row hint\">Copy <code>.env.example</code> to <code>.env</code> in the project root</div>';
  }

  // Vision
  var visDetail = document.getElementById('detail-vision');
  if (data.vision_configured) {
    visDetail.innerHTML = '<div class=\"detail-row\"><span class=\"detail-k\">Provider:</span><span class=\"detail-val\">' + escHtml(data.vision_provider) + '</span></div>';
  } else {
    visDetail.innerHTML = '<div class=\"detail-row hint\">Configure via <b>Menu &rarr; Settings</b> or edit <code>.env</code> directly</div>';
  }

  // Step statuses
  setStepStatus('adb', data.adb_installed, t('found'), t('notFound'));
  setStepStatus('device', data.adb_device, t('connected'), t('notConnected'));
  setStepStatus('android', data.android_service, t('running'), t('notReachable'));
  setStepStatus('mcp', data.mcp_server_running, t('running'), t('notReachable'));
  setStepStatus('env', data.dotenv_exists, t('configured'), t('missing'));
  setStepStatus('vision', data.vision_configured, t('configured'), t('notSet'), t('notSet'), true);

  var checks = [data.adb_installed, data.adb_device, data.android_service, data.mcp_server_running, data.dotenv_exists];
  var allPass = checks.every(Boolean);
  var passed = checks.filter(Boolean).length;

  if (allPass) {
    summary.textContent = t('allPass');
    summary.className = 'setup-summary all-pass';
  } else if (!data.android_service && passed >= checks.length - 1) {
    summary.textContent = passed + '/' + checks.length + ' passed — start Shizuku + Android MCP app on your phone';
    summary.className = 'setup-summary has-fail';
  } else {
    summary.textContent = passed + '/' + checks.length + ' ' + t('someFail');
    summary.className = 'setup-summary has-fail';
  }
}

function setStepStatus(id, pass, passText, failText, _neutralText, optional) {
  const statusEl = document.getElementById(`status-${id}`);
  const stepEl = document.getElementById(`step-${id}`);

  if (pass) {
    statusEl.textContent = passText;
    statusEl.className = 'step-status pass';
    stepEl.classList.add('pass');
    stepEl.classList.remove('fail');
  } else if (optional) {
    statusEl.textContent = failText || 'Skipped';
    statusEl.className = 'step-status';
    stepEl.classList.remove('pass', 'fail');
  } else {
    statusEl.textContent = failText;
    statusEl.className = 'step-status fail';
    stepEl.classList.add('fail');
    stepEl.classList.remove('pass');
  }
}

// ========== ADB Device Management ==========
async function refreshAdbDevices() {
  const list = document.getElementById('adbDeviceList');
  try {
    const resp = await fetch('/api/adb/devices');
    const json = await resp.json();
    if (json.success && json.data?.devices?.length) {
      list.innerHTML = json.data.devices.map(d => `
        <div class="adb-device-item">
          <span class="adb-device-dot ${d.status}"></span>
          <div class="adb-device-info">
            <span class="adb-device-id">${escHtml(d.id)}</span>
            ${d.model ? `<span class="adb-device-model">${escHtml(d.model)}</span>` : ''}
          </div>
          <span class="adb-device-transport">${d.transport}</span>
          ${d.transport === 'wireless' ? `<button class="btn small danger" onclick="adbDisconnect('${escHtml(d.id)}')">Disconnect</button>` : ''}
        </div>
      `).join('');
    } else {
      list.innerHTML = '<span class="text-muted">No devices connected</span>';
    }
  } catch (e) {
    list.innerHTML = '<span class="text-muted">ADB not available</span>';
  }
}

async function adbConnect() {
  const input = document.getElementById('adbHostInput');
  const target = input.value.trim();
  if (!target) return;

  const status = document.getElementById('adbStatus');
  status.textContent = 'Connecting...';
  status.className = 'form-status';

  const parts = target.split(':');
  const host = parts[0];
  const port = parts[1] || '5555';

  try {
    const resp = await fetch('/api/adb/connect', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ host, port }),
    });
    const json = await resp.json();
    if (json.success) {
      status.textContent = `Connected to ${json.data?.target}`;
      status.className = 'form-status success';
      input.value = '';
      refreshAdbDevices();
    } else {
      status.textContent = json.error || json.data?.output || 'Failed';
      status.className = 'form-status error';
    }
  } catch (e) {
    status.textContent = 'Network error';
    status.className = 'form-status error';
  }
}

async function adbDisconnect(target) {
  const status = document.getElementById('adbStatus');
  try {
    const resp = await fetch('/api/adb/disconnect', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ target }),
    });
    const json = await resp.json();
    status.textContent = json.data?.output || 'Disconnected';
    status.className = 'form-status success';
    refreshAdbDevices();
  } catch (e) {
    status.textContent = 'Failed';
    status.className = 'form-status error';
  }
}

async function adbEnableTcpip() {
  const status = document.getElementById('adbStatus');
  status.textContent = 'Enabling TCP/IP...';
  status.className = 'form-status';
  try {
    const resp = await fetch('/api/adb/tcpip', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ port: '5555' }),
    });
    const json = await resp.json();
    if (json.success) {
      status.textContent = 'TCP/IP enabled on port 5555. You can now disconnect USB.';
      status.className = 'form-status success';
    } else {
      status.textContent = json.error || 'Failed — ensure device is connected via USB';
      status.className = 'form-status error';
    }
  } catch (e) {
    status.textContent = 'Network error';
    status.className = 'form-status error';
  }
}

// ========== Settings Panel ==========
let selectedProvider = '';

async function openSettings() {
  document.getElementById('settingsModal').classList.add('show');
  document.getElementById('settingsStatus').textContent = '';
  document.getElementById('settingsStatus').className = 'form-status';
  refreshAdbDevices();

  // Load current settings
  try {
    const resp = await fetch('/api/settings');
    const json = await resp.json();
    if (json.success && json.data) {
      const d = json.data;
      selectProvider(d.vision_provider || 'anthropic');
      document.getElementById('setApiKey').value = d.vision_api_key || '';
      document.getElementById('setModel').value = d.vision_model || '';
      document.getElementById('setApiBase').value = d.vision_api_base || '';
      document.getElementById('customUrlGroup').style.display =
        selectedProvider === 'custom' ? 'block' : 'none';
    }
  } catch (e) {
    document.getElementById('settingsStatus').textContent = 'Failed to load settings';
    document.getElementById('settingsStatus').className = 'form-status error';
  }
}

function closeSettings() {
  document.getElementById('settingsModal').classList.remove('show');
}

function selectProvider(prov) {
  selectedProvider = prov;
  document.querySelectorAll('.prov-tab').forEach(t => t.classList.remove('active'));
  document.querySelector(`.prov-tab[data-prov="${prov}"]`)?.classList.add('active');
  document.getElementById('customUrlGroup').style.display =
    prov === 'custom' ? 'block' : 'none';
}

function toggleApiKeyVisibility() {
  const input = document.getElementById('setApiKey');
  input.type = input.type === 'password' ? 'text' : 'password';
}

async function saveSettings(e) {
  e.preventDefault();
  const status = document.getElementById('settingsStatus');

  const body = {
    vision_provider: selectedProvider,
    vision_api_key: document.getElementById('setApiKey').value.trim(),
    vision_model: document.getElementById('setModel').value.trim(),
  };

  if (selectedProvider === 'custom') {
    body.vision_api_base = document.getElementById('setApiBase').value.trim();
  }

  try {
    const resp = await fetch('/api/settings', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    const json = await resp.json();

    if (json.success) {
      status.textContent = 'Settings saved successfully! Restart server to apply.';
      status.className = 'form-status success';
    } else {
      status.textContent = json.error || 'Failed to save';
      status.className = 'form-status error';
    }
  } catch (e) {
    status.textContent = 'Network error';
    status.className = 'form-status error';
  }
}

// Auto-open wizard only if still disconnected after 8 seconds (not just a flash)
let _wizardShown = false;
let _wasEverConnected = false;
setTimeout(() => {
  const dot = document.getElementById('statusDot');
  if (dot && dot.classList.contains('online')) {
    _wasEverConnected = true;
  }
  if (dot && !dot.classList.contains('online') && !_wizardShown && !_wasEverConnected) {
    _wizardShown = true;
    openSetupWizard();
  }
}, 8000);

// ========== Init ==========
(function initI18n() {
  if (!currentLang) {
    currentLang = 'en';  // default to English
    localStorage.setItem('mcp-lang', 'en');
  }
  applyLanguage();
  highlightActiveLang();
})();

connectWS();
setTimeout(checkScrcpyStatus, 1500);
setInterval(refreshDeviceInfo, 15000);

// ===== Header clock =====
(function updateClock() {
  const el = document.getElementById('headerClock');
  if (el) {
    const now = new Date();
    el.textContent = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  }
  setTimeout(updateClock, 30000);
})();

// ===== Mobile sidebar toggle =====
function toggleSidebar() {
  const lp = document.getElementById('left-panel');
  const rp = document.getElementById('right-panel');
  if (lp) lp.classList.toggle('mobile-open');
  if (rp) rp.classList.remove('mobile-open');
}