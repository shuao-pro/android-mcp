/* Android MCP Dashboard v3.0 */
var ws = null, wsReconnectTimer = null;
var screenWs = null, screenStreaming = false, lastScreenB64 = null;
var chatHistory = [], shellHist = [], shellHistIdx = -1;
var lang = localStorage.getItem('lang') || 'en';
var currentProvider = 'anthropic';

var T = {
  en: { connected:'Connected', disconnected:'Disconnected', noDevice:'No device', play:'\u25b6 Play', stop:'\u25a0 Stop', send:'Send' },
  zh: { connected:'\u5df2\u8fde\u63a5', disconnected:'\u672a\u8fde\u63a5', noDevice:'\u65e0\u8bbe\u5907', play:'\u25b6 \u64ad\u653e', stop:'\u25a0 \u505c\u6b62', send:'\u53d1\u9001' }
};
function t(k){ return (T[lang]||T.en)[k]||k; }

(function init(){
  connectWS();
  updateClock(); setInterval(updateClock, 30000);
  refreshDeviceInfo();
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
  document.querySelectorAll('.prov-tab').forEach(function(t){ t.classList.toggle('active', t.dataset.prov === p); });
  document.getElementById('customUrlGroup').style.display = p === 'custom' ? 'block' : 'none';
}
function loadSettings(){
  fetch('/api/settings').then(function(r){ return r.json(); }).then(function(r){
    if(r.provider){ currentProvider = r.provider; selectProvider(r.provider); }
    if(r.api_key) document.getElementById('setApiKey').value = r.api_key;
    if(r.model) document.getElementById('setModel').value = r.model;
    if(r.api_base) document.getElementById('setApiBase').value = r.api_base;
  }).catch(function(){});
}
function saveSettings(e){
  e.preventDefault();
  var data = {
    provider: currentProvider,
    api_key: document.getElementById('setApiKey').value,
    model: document.getElementById('setModel').value,
    api_base: document.getElementById('setApiBase').value
  };
  fetch('/api/settings',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)})
    .then(function(r){ return r.json(); }).then(function(r){
      var st = document.getElementById('settingsStatus');
      st.textContent = r.success ? 'Saved' : ('Error: '+r.error);
      st.className = 'form-status ' + (r.success ? 'success' : 'error');
    }).catch(function(e){
      var st = document.getElementById('settingsStatus');
      st.textContent = 'Error: '+e.message; st.className = 'form-status error';
    });
}
function toggleApiKey(){
  var el = document.getElementById('setApiKey'); el.type = el.type === 'password' ? 'text' : 'password';
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

// ===== Helpers =====
function escHtml(s){
  var d = document.createElement('div');
  d.textContent = s;
  return d.innerHTML;
}