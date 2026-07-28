/* Android MCP Dashboard v3.0 */
var ws = null, wsReconnectTimer = null;
var screenWs = null, screenStreaming = false, lastScreenB64 = null;
var chatHistory = [], shellHist = [], shellHistIdx = -1;
var lang = localStorage.getItem('lang') || 'en';
var currentProvider = 'anthropic';

var I = {
  en: { connected:'Connected',disconnected:'Disconnected',noDevice:'No device',mcpClient:'MCP',play:'Play',stop:'Stop',send:'Send',
    settings:'Settings',setupWizard:'Setup Wizard',language:'Language',langDesc:'Interface display language',
    deviceConn:'Device Connection',deviceDesc:'ADB tunnel to Android MCP app',aiVision:'AI Vision',
    visionDesc:'Enables AI chat and element recognition',serverConfig:'Server Configuration',
    serverDesc:'Changes require restart',webGui:'Web GUI',mcpServer:'MCP Server',
    connect:'Connect',enableTcpip:'Enable TCP/IP',refresh:'Refresh',provider:'Provider',custom:'Custom',
    saveSettings:'Save All Settings',shellPlaceholder:'shell command...',chatPlaceholder:'Describe what to do...'
  },
  zh: { connected:'\u5df2\u8fde\u63a5',disconnected:'\u672a\u8fde\u63a5',noDevice:'\u65e0\u8bbe\u5907',mcpClient:'MCP',play:'\u64ad\u653e',stop:'\u505c\u6b62',send:'\u53d1\u9001',
    settings:'\u8bbe\u7f6e',setupWizard:'\u5f15\u5bfc',language:'\u8bed\u8a00',langDesc:'\u754c\u9762\u663e\u793a\u8bed\u8a00',
    deviceConn:'\u8bbe\u5907\u8fde\u63a5',deviceDesc:'ADB \u8fde\u63a5 Android MCP \u5e94\u7528',aiVision:'AI \u89c6\u89c9',
    visionDesc:'\u542f\u7528 AI \u5bf9\u8bdd\u548c\u5143\u7d20\u8bc6\u522b',serverConfig:'\u670d\u52a1\u5668\u914d\u7f6e',
    serverDesc:'\u4fee\u6539\u540e\u9700\u91cd\u542f',webGui:'Web \u754c\u9762',mcpServer:'MCP \u670d\u52a1\u5668',
    connect:'\u8fde\u63a5',enableTcpip:'\u542f\u7528 TCP/IP',refresh:'\u5237\u65b0',provider:'\u63d0\u4f9b\u5546',custom:'\u81ea\u5b9a\u4e49',
    saveSettings:'\u4fdd\u5b58\u5168\u90e8\u8bbe\u7f6e',shellPlaceholder:'shell \u547d\u4ee4...',chatPlaceholder:'\u63cf\u8ff0\u4f60\u8981\u64cd\u4f5c\u7684\u5185\u5bb9...'
  }
};
var lang = localStorage.getItem('lang') || 'en';
function t(k){ return (T[lang]||T.en)[k]||k; }

(function init(){
  applyI18n();
  connectWS();
  updateClock(); setInterval(updateClock, 30000);
  refreshDeviceInfo();

  // Auto-show setup wizard if device not connected (once per session)
  if(!sessionStorage.getItem('setupShown')){
    setTimeout(function(){
      fetch('/api/status').then(function(r){ return r.json(); }).then(function(s){
        if(!s.connected && !s.shizuku_running){
          openSetup();
          sessionStorage.setItem('setupShown', '1');
        }
      }).catch(function(){});
    }, 3000);
  }
})();

function updateClock(){
  var el = document.getElementById('headerClock');
  if(el) el.textContent = new Date().toLocaleTimeString([],{hour:'2-digit',minute:'2-digit'});
}

// ===== WebSocket /ws =====
function connectWS(){
  if(ws && ws.readyState === WebSocket.OPEN) return;
  var proto = location.protocol === 'https:' ? 'wss:' : 'ws:';
  ws = new WebSocket(proto + '//' + location.host + '/ws');
  ws.onopen = function(){
    document.getElementById('statusDot').classList.add('online');
    document.getElementById('statusLabel').textContent = t('connected');
  };
  ws.onclose = function(){
    document.getElementById('statusDot').classList.remove('online');
    document.getElementById('statusLabel').textContent = t('disconnected');
    wsReconnectTimer = setTimeout(connectWS, 3000);
  };
  ws.onmessage = handleWS;
}

function handleWS(e){
  var msg;
  try { msg = JSON.parse(e.data); } catch(err) { return; }
  if(!msg.cmd) return;
  if(msg.cmd === 'chat'){
    var ti = document.querySelector('#chat-messages .typing-indicator');
    if(ti) ti.remove();
    renderChatReply(msg.result);
  } else if(msg.cmd === 'shell'){
    handleShellResult(msg.result);
  } else if(handleWS._pending && handleWS._pending[msg.cmd]){
    handleWS._pending[msg.cmd](msg.result);
    delete handleWS._pending[msg.cmd];
  }
}
handleWS._pending = {};

function sendWS(cmd, params, cb){
  if(!ws || ws.readyState !== WebSocket.OPEN){
    connectWS();
    setTimeout(function(){ sendWS(cmd, params, cb); }, 500);
    return;
  }
  if(cb) handleWS._pending[cmd] = cb;
  ws.send(JSON.stringify({cmd:cmd, params:params||{}}));
}

// ===== Device Info =====
function refreshDeviceInfo(){
  sendWS('get_device_info', {}, function(r){
    if(!r || !r.success) return;
    var d = r.data || r;
    setVal('devModel', (d.model || d.manufacturer || '--').substring(0,20));
    setVal('devAndroid', d.os_version || d.android || '--');
    setVal('devDisplay', d.screen_resolution || d.display || '--');
    setVal('devBattery', d.battery_level || d.battery || '--');
    setVal('devApp', (d.current_app || d.app || '--').substring(0,18));
    setVal('devShizuku', d.shizuku || '--');
    var m = d.model || d.manufacturer || '';
    if(m){
      var dm = document.getElementById('deviceModel');
      dm.textContent = m.substring(0,25); dm.title = m;
    }
  });
}

function setVal(id, val){
  var el = document.getElementById(id);
  if(el) el.textContent = val;
}

// ===== Quick Actions =====
function quick(cmd, params){
  if(cmd === 'screenshot' || cmd === 'take_screenshot'){
    sendWS('take_screenshot', {}, function(r){
      toast(r && r.success ? 'Screenshot saved' : 'Failed: ' + (r&&r.error||'unknown'));
    });
  } else if(cmd === 'press_key'){
    sendWS(cmd, params, function(r){
      if(r && !r.success) toast('Failed: ' + r.error);
    });
  } else {
    sendWS(cmd, params);
  }
}

// ===== Screen Stream =====
function toggleStream(){
  if(screenStreaming){ stopStream(); return; }
  startStream();
}

function startStream(){
  var proto = location.protocol === 'https:' ? 'wss:' : 'ws:';
  screenWs = new WebSocket(proto + '//' + location.host + '/ws/screen');
  screenWs.onopen = function(){
    screenStreaming = true;
    updateStreamUI();
    var frame = document.getElementById('screenFrame');
    var ph = frame.querySelector('.screen-placeholder');
    if(ph) ph.style.display = 'none';
    document.getElementById('streamBadge').style.display = 'flex';
    if(!frame.querySelector('img') && !frame.querySelector('.screen-skeleton')){
      var sk = document.createElement('div'); sk.className = 'screen-skeleton'; frame.appendChild(sk);
    }
  };
  screenWs.onmessage = function(e){
    var msg = JSON.parse(e.data);
    if(msg.type === 'frame' && msg.base64){
      lastScreenB64 = msg.base64;
      var frame = document.getElementById('screenFrame');
      var sk = frame.querySelector('.screen-skeleton'); if(sk) sk.remove();
      var ph = frame.querySelector('.screen-placeholder'); if(ph) ph.style.display = 'none';
      var img = frame.querySelector('img');
      if(!img){ img = document.createElement('img'); img.id = 'screenImg'; frame.appendChild(img); }
      img.src = 'data:image/png;base64,' + msg.base64;
      var badge = document.getElementById('streamBadge');
      if(badge){
        badge.style.display = 'flex';
        var fpsEl = document.getElementById('streamFps');
        if(fpsEl){
          var now = Date.now();
          if(!badge._last) badge._last = now;
          if(!badge._cnt) badge._cnt = 0;
          badge._cnt++;
          if(now - badge._last >= 1000){
            fpsEl.textContent = Math.round(badge._cnt * 1000 / (now - badge._last)) + 'fps';
            badge._cnt = 0; badge._last = now;
          }
        }
      }
    } else if(msg.type === 'status' && msg.error === 'device_offline'){
      stopStream();
      document.getElementById('screenFrame').innerHTML = '<span class="screen-placeholder">Device offline</span>';
    }
  };
  screenWs.onclose = function(){ screenStreaming = false; updateStreamUI(); };
}

function stopStream(){
  if(screenWs){ screenWs.close(); screenWs = null; }
  screenStreaming = false;
  updateStreamUI();
  document.getElementById('streamBadge').style.display = 'none';
}

function updateStreamUI(){
  var btn = document.getElementById('streamBtn');
  if(screenStreaming){
    btn.textContent = '\u25a0 Stop';
    btn.classList.add('btn-danger');
  } else {
    btn.textContent = '\u25b6 Play';
    btn.classList.remove('btn-danger');
  }
}

function onScreenClick(e){
  if(!lastScreenB64) return;
  var frame = document.getElementById('screenFrame');
  var rect = frame.getBoundingClientRect();
  var img = frame.querySelector('img');
  if(!img) return;
  var scaleX = img.naturalWidth / rect.width;
  var scaleY = img.naturalHeight / rect.height;
  var x = Math.round((e.clientX - rect.left) * scaleX);
  var y = Math.round((e.clientY - rect.top) * scaleY);
  var ci = document.createElement('div');
  ci.style.cssText = 'position:absolute;width:20px;height:20px;border:2px solid var(--accent);border-radius:50%;transform:translate(-50%,-50%);pointer-events:none;left:'+(e.clientX-rect.left)+'px;top:'+(e.clientY-rect.top)+'px';
  frame.appendChild(ci);
  setTimeout(function(){ ci.remove(); }, 500);
  sendWS('click', {x:x, y:y});
}

// ===== scrcpy =====
function toggleScrcpy(){
  fetch('/api/scrcpy/status').then(function(r){ return r.json(); }).then(function(s){
    if(s.running){
      fetch('/api/scrcpy/stop',{method:'POST'}).then(function(){ setScrcpyStatus('Stopped','success'); });
    } else {
      fetch('/api/scrcpy/start',{method:'POST'}).then(function(r){ return r.json(); }).then(function(d){
        setScrcpyStatus(d.message||'Started', d.success?'success':'error');
      });
    }
  });
}
function setScrcpyStatus(msg, cls){
  var el = document.getElementById('scrcpyStatus');
  el.textContent = msg; el.className = 'scrcpy-status ' + (cls||'');
}

// ===== Shell =====
function shellKey(e){
  if(e.key === 'Enter'){ runShell(); return; }
  if(e.key === 'ArrowUp'){ e.preventDefault(); shellHistUp(); }
  if(e.key === 'ArrowDown'){ e.preventDefault(); shellHistDown(); }
}
function shellHistUp(){
  if(!shellHist.length) return;
  if(shellHistIdx === -1) shellHistIdx = shellHist.length - 1;
  else if(shellHistIdx > 0) shellHistIdx--;
  document.getElementById('shellInput').value = shellHist[shellHistIdx]||'';
}
function shellHistDown(){
  if(shellHistIdx === -1) return;
  if(shellHistIdx < shellHist.length - 1){ shellHistIdx++; document.getElementById('shellInput').value = shellHist[shellHistIdx]; }
  else { shellHistIdx = -1; document.getElementById('shellInput').value = ''; }
}
function runShell(){
  var inp = document.getElementById('shellInput');
  var cmd = inp.value.trim(); if(!cmd) return;
  if(!shellHist.length || shellHist[shellHist.length-1] !== cmd){ shellHist.push(cmd); if(shellHist.length>50) shellHist.shift(); }
  shellHistIdx = -1; inp.value = '';
  termAppend('term-cmd','$ '+escHtml(cmd));
  termAppend('term-info','...');
  sendWS('shell', {command:cmd});
}
function handleShellResult(r){
  var out = document.getElementById('shellOutput');
  var lines = out.querySelectorAll('.term-line');
  var last = lines[lines.length-1];
  if(last && last.classList.contains('term-info') && last.textContent==='...') last.remove();
  if(r.success){
    var txt = (r.data&&r.data.output||r.stdout||'(empty)').trim();
    if(txt) txt.split('\n').forEach(function(l){ termAppend('term-out', escHtml(l)); });
    else termAppend('term-info', '(empty)');
  } else {
    termAppend('term-err', '[Error] '+escHtml(r.error||(r.data&&r.data.error)||'unknown'));
  }
  out.scrollTop = out.scrollHeight;
}
function termAppend(cls, html){
  var out = document.getElementById('shellOutput');
  var d = document.createElement('div'); d.className = 'term-line '+cls; d.innerHTML = html;
  out.appendChild(d); out.scrollTop = out.scrollHeight;
}

// ===== Chat =====
function chatKey(e){
  if(e.key === 'Enter' && !e.shiftKey){ e.preventDefault(); sendChat(); }
}
function sendChat(){
  var inp = document.getElementById('chatInput');
  var text = inp.value.trim(); if(!text) return;
  inp.value = ''; inp.style.height = 'auto';
  var w = document.getElementById('chatWelcome'); if(w) w.remove();
  renderMsg('user', text);
  var ti = document.createElement('div'); ti.className = 'typing-indicator';
  ti.innerHTML = '<span></span><span></span><span></span>';
  document.getElementById('chat-messages').appendChild(ti);
  document.getElementById('chat-messages').scrollTop = 9e9;
  var history = chatHistory.slice(-10).map(function(h){ return {role:h.role,content:h.content}; });
  if(ws && ws.readyState === WebSocket.OPEN){
    ws.send(JSON.stringify({cmd:'chat',text:text,history:history}));
  } else {
    connectWS();
    setTimeout(function(){ sendChat(); }, 500);
    return;
  }
  chatHistory.push({role:'user',content:text});
}
function sendExample(t){ document.getElementById('chatInput').value = t; sendChat(); }
function renderMsg(role, text){
  var msgs = document.getElementById('chat-messages');
  var d = document.createElement('div'); d.className = 'msg '+role;
  var time = new Date().toLocaleTimeString([],{hour:'2-digit',minute:'2-digit'});
  d.innerHTML = '<div class="msg-avatar">'+(role==='user'?'\uD83D\uDC64':'\uD83E\uDD16')+'</div>'+
    '<div class="msg-body"><div class="msg-bubble">'+escHtml(text)+'</div>'+
    '<div class="msg-time">'+time+'</div></div>';
  msgs.appendChild(d); msgs.scrollTop = 9e9;
}
function renderChatReply(result){
  var msgs = document.getElementById('chat-messages');
  if(!result.success){
    var d = document.createElement('div'); d.className = 'msg system';
    d.innerHTML = '<div class="msg-avatar">\u26A0</div>'+
      '<div class="msg-body"><div class="msg-bubble">Error: '+escHtml(result.error||'unknown')+'</div></div>';
    msgs.appendChild(d);
    chatHistory.push({role:'assistant',content:'Error: '+(result.error||'unknown')});
  } else {
    var text = result.reply || (result.data&&result.data.reply) || JSON.stringify(result.data||result);
    renderMsg('assistant', text);
    chatHistory.push({role:'assistant',content:text});
  }
  msgs.scrollTop = 9e9;
}

// ===== Toast =====
function toast(msg){
  var el = document.getElementById('toast');
  el.textContent = msg; el.classList.add('show');
  clearTimeout(el._t); el._t = setTimeout(function(){ el.classList.remove('show'); }, 2500);
}

// ===== Setup Wizard =====
function openSetup(){
  document.getElementById('setupModal').classList.add('show');
  checkSetup();
}
function closeSetup(){ document.getElementById('setupModal').classList.remove('show'); }
function checkSetup(){
  var steps = document.getElementById('wizSteps');
  steps.innerHTML = '<div class="wiz-step"><div class="wiz-content"><div class="wiz-title">Checking...</div></div></div>';
  fetch('/api/setup/status').then(function(r){ return r.json(); }).then(function(r){
    var items = [
      {key:'adb_installed',title:'ADB',desc:'Android SDK Platform Tools',detail:r.adb_path||'Not found',pass:r.adb_installed},
      {key:'adb_device',title:'Device',desc:'USB or wireless ADB',detail:r.adb_device_info||(r.adb_device_list&&r.adb_device_list.length)+' device(s)',pass:r.adb_device},
      {key:'android_service',title:'Android MCP Service',desc:'Start Shizuku + Android MCP on phone',detail:r.android_service_detail&&r.android_service_detail.ip||'Port 18080',pass:r.android_service},
      {key:'dotenv_exists',title:'.env Config',desc:'Environment file',detail:r.dotenv_path,pass:r.dotenv_exists},
      {key:'vision_configured',title:'AI Vision API',desc:'Claude/GPT-4o for element recognition',detail:r.vision_provider||'Not set',pass:r.vision_configured,optional:true}
    ];
    var passCount = 0, failCount = 0;
    steps.innerHTML = items.map(function(it,i){
      var cls = it.pass ? 'pass' : 'fail';
      if(it.pass) passCount++; else if(!it.optional) failCount++;
      return '<div class="wiz-step '+cls+'"><div class="wiz-icon"><span class="wiz-num">'+(i+1)+'</span></div>'+
        '<div class="wiz-content"><div class="wiz-title">'+it.title+(it.optional?'<span class="badge-opt">optional</span>':'')+'</div>'+
        '<div class="wiz-desc">'+it.desc+'</div>'+
        '<div class="wiz-detail"><div class="detail-row">'+escHtml(it.detail)+'</div></div></div>'+
        '<div class="wiz-status '+cls+'">'+(it.pass?'OK':'Fail')+'</div></div>';
    }).join('');
    var sm = document.getElementById('setupSummary');
    sm.textContent = passCount+'/'+items.length+' checks passed';
    sm.className = failCount > 0 ? '' : '';
  }).catch(function(e){
    steps.innerHTML = '<div class="wiz-step fail"><div class="wiz-content"><div class="wiz-title">Error</div><div class="wiz-desc">'+escHtml(e.message)+'</div></div></div>';
  });
}

// ===== Settings =====
function openSettings(){ document.getElementById('settingsModal').classList.add('show'); loadSettings(); refreshAdbDevices(); }
function closeSettings(){ document.getElementById('settingsModal').classList.remove('show'); }
function selectProvider(p){
  currentProvider = p;
  document.querySelectorAll('.prov-card').forEach(function(t){ t.classList.toggle('active', t.dataset.prov === p); });
  document.getElementById('customUrlGroup').style.display = (p === 'custom' || p === 'deepseek' || p === 'gemini') ? 'block' : 'none';
  var modelEl = document.getElementById('setModel');
  var baseEl = document.getElementById('setApiBase');
  var hint = document.getElementById('modelHint');
  var defaults = {anthropic:'claude-sonnet-5-20251001',openai:'gpt-4o',deepseek:'deepseek-chat',gemini:'gemini-2.5-pro-exp-03-25',custom:''};
  var bases = {anthropic:'https://api.anthropic.com',openai:'https://api.openai.com/v1',deepseek:'https://api.deepseek.com',gemini:'https://generativelanguage.googleapis.com/v1beta/openai',custom:''};
  if(defaults[p] && (!modelEl.value || modelEl.dataset.auto === '1')){
    modelEl.value = defaults[p]; modelEl.dataset.auto = '1';
  }
  if(bases[p]){ baseEl.value = bases[p]; baseEl.dataset.auto = '1'; }
  else { baseEl.value = ''; baseEl.dataset.auto = ''; }
  if(hint){ hint.textContent = p === 'custom' ? ' ? enter your model name' : ' ? auto-filled'; }
}
function loadSettings(){
  fetch('/api/settings').then(function(r){ return r.json(); }).then(function(r){
    var d = r.data || r;
    if(d.vision_provider){ currentProvider = d.vision_provider; selectProvider(d.vision_provider); }
    if(d.vision_api_key) document.getElementById('setApiKey').value = d.vision_api_key;
    if(d.vision_model) document.getElementById('setModel').value = d.vision_model;
    if(d.vision_api_base) document.getElementById('setApiBase').value = d.vision_api_base;
    if(d.android_host) document.getElementById('setAndroidHost').value = d.android_host;
    if(d.android_port) document.getElementById('setAndroidPort').value = d.android_port;
    if(d.mcp_host) document.getElementById('setMcpHost').value = d.mcp_host;
    if(d.mcp_port) document.getElementById('setMcpPort').value = d.mcp_port;
    if(d.web_host) document.getElementById('setWebHost').value = d.web_host;
    if(d.web_port) document.getElementById('setWebPort').value = d.web_port;
  }).catch(function(){});
}
function saveAllSettings(e){
  if(e) e.preventDefault();
  var data = {
    vision_provider: currentProvider,
    vision_api_key: document.getElementById('setApiKey').value,
    vision_model: document.getElementById('setModel').value,
    vision_api_base: currentProvider==='custom' ? document.getElementById('setApiBase').value : '',
    android_host: document.getElementById('setAndroidHost').value,
    android_port: document.getElementById('setAndroidPort').value,
    mcp_host: document.getElementById('setMcpHost').value,
    mcp_port: document.getElementById('setMcpPort').value,
    web_host: document.getElementById('setWebHost').value,
    web_port: document.getElementById('setWebPort').value
  };
  var st = document.getElementById('settingsStatus');
  st.textContent = 'Saving...'; st.className = 'form-status';
  fetch('/api/settings',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)})
    .then(function(r){ return r.json(); }).then(function(r){
      st.textContent = r.success ? '✅ ' + t('saveSettings') + ' OK — restart server to apply' : ('Error: '+(r.error||''));
      st.className = 'form-status ' + (r.success ? 'success' : 'error');
    }).catch(function(e){
      st.textContent = 'Error: '+e.message; st.className = 'form-status error';
    });
}

// ===== ADB =====
function refreshAdbDevices(){
  var el = document.getElementById('adbDeviceList');
  fetch('/api/adb/devices').then(function(r){ return r.json(); }).then(function(r){
    if(!r.devices || !r.devices.length){ el.innerHTML = '<span class="text-muted">No devices</span>'; return; }
    el.innerHTML = r.devices.map(function(d){
      return '<div class="adb-device"><span class="adb-device-dot '+d.status+'"></span>'+
        '<div class="adb-device-info"><span class="adb-device-id">'+escHtml(d.id)+'</span>'+
        '<span class="adb-device-model">'+escHtml(d.model||'')+'</span></div></div>';
    }).join('');
  }).catch(function(){ el.innerHTML = '<span class="text-muted">Error</span>'; });
}
function adbConnect(){
  var host = document.getElementById('adbHostInput').value.trim(); if(!host) return;
  var st = document.getElementById('adbStatus');
  fetch('/api/adb/connect',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({host:host})})
    .then(function(r){ return r.json(); }).then(function(r){
      st.textContent = r.success ? 'Connected' : r.error;
      st.className = 'form-status '+(r.success?'success':'error');
      refreshAdbDevices();
    }).catch(function(){ st.textContent='Error'; st.className='form-status error'; });
}
function adbEnableTcpip(){
  var st = document.getElementById('adbStatus');
  fetch('/api/adb/tcpip',{method:'POST'}).then(function(r){ return r.json(); }).then(function(r){
    st.textContent = r.success ? 'TCP/IP enabled' : r.error;
    st.className = 'form-status '+(r.success?'success':'error');
  }).catch(function(){ st.textContent='Error'; st.className='form-status error'; });
}

// ===== Mobile =====
function togglePanel(panel){
  var el = document.getElementById(panel==='left'?'left-panel':'right-panel');
  if(el) el.classList.toggle('mobile-open');
}


function applyI18n(){
  document.querySelectorAll('[data-i18n]').forEach(function(el){
    var k = el.getAttribute('data-i18n');
    var v = t(k); if(v) el.textContent = v;
  });
  var si = document.getElementById('shellInput');
  if(si) si.placeholder = t('shellPlaceholder');
  var ci = document.getElementById('chatInput');
  if(ci) ci.placeholder = t('chatPlaceholder');
  var zb = document.getElementById('langBtnZh'); var eb = document.getElementById('langBtnEn');
  if(zb) zb.classList.toggle('active', lang==='zh'); if(eb) eb.classList.toggle('active', lang==='en');
  var he = document.getElementById('hlEn'); var hz = document.getElementById('hlZh');
  if(he) he.classList.toggle('active', lang==='en'); if(hz) hz.classList.toggle('active', lang==='zh');
}
function switchLang(l){ lang=l; localStorage.setItem('lang',l); applyI18n(); var he=document.getElementById('hlEn'); var hz=document.getElementById('hlZh'); if(he) he.classList.toggle('active',l==='en'); if(hz) hz.classList.toggle('active',l==='zh'); }
function cls(id){ document.getElementById(id).classList.remove('show'); }

// ===== Helpers =====
function escHtml(s){
  var d = document.createElement('div');
  d.textContent = s;
  return d.innerHTML;
}