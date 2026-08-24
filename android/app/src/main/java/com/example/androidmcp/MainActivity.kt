package com.example.androidmcp

import android.Manifest
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Build
import android.os.Bundle
import android.os.Looper
import android.util.Log
import android.view.View
import android.widget.Button
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat
import com.example.androidmcp.util.PrivilegeExecutor
import com.example.androidmcp.util.RootHelper
import com.example.androidmcp.util.ShizukuHelper
import com.example.androidmcp.util.TokenStore
import com.google.android.material.button.MaterialButton
import java.util.concurrent.atomic.AtomicBoolean

class MainActivity : AppCompatActivity() {

    private lateinit var tvShellStatus: TextView
    private lateinit var tvShellDetail: TextView
    private lateinit var tvHttpAddress: TextView
    private lateinit var tvApiCount: TextView
    private lateinit var btnToggle: Button
    private lateinit var btnAuth: Button
    private lateinit var btnRefresh: Button
    private lateinit var layoutAuthButtons: View
    private lateinit var tvLog: TextView
    private lateinit var tvToken: TextView

    private lateinit var btnModeAuto: MaterialButton
    private lateinit var btnModeShizuku: MaterialButton
    private lateinit var btnModeRoot: MaterialButton

    private val logLines = mutableListOf<String>()
    private val isServiceRunning = AtomicBoolean(false)

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        tvShellStatus = findViewById(R.id.tvShellStatus)
        tvShellDetail = findViewById(R.id.tvShellDetail)
        tvHttpAddress = findViewById(R.id.tvHttpAddress)
        tvApiCount = findViewById(R.id.tvApiCount)
        btnToggle = findViewById(R.id.btnToggle)
        btnAuth = findViewById(R.id.btnAuth)
        btnRefresh = findViewById(R.id.btnRefresh)
        layoutAuthButtons = findViewById(R.id.layoutAuthButtons)
        tvLog = findViewById(R.id.tvLog)
        tvToken = findViewById(R.id.tvToken)

        btnModeAuto = findViewById(R.id.btnModeAuto)
        btnModeShizuku = findViewById(R.id.btnModeShizuku)
        btnModeRoot = findViewById(R.id.btnModeRoot)

        tvToken.text = TokenStore.getOrCreate(this)
        tvToken.setOnClickListener { copyTokenToClipboard() }

        PrivilegeExecutor.onStatusChanged = {
            runOnUiThread { updateUI() }
        }

        requestNotificationPermission()
        refreshStatus()

        btnToggle.setOnClickListener {
            if (isServiceRunning.get()) {
                stopService()
            } else {
                if (!PrivilegeExecutor.isReady()) {
                    attemptAuthorize()
                    return@setOnClickListener
                }
                startService()
            }
        }

        btnAuth.setOnClickListener { attemptAuthorize() }
        btnRefresh.setOnClickListener { refreshStatus() }

        btnModeAuto.setOnClickListener {
            PrivilegeExecutor.setMode(this, PrivilegeExecutor.Mode.AUTO)
            refreshStatus()
        }
        btnModeShizuku.setOnClickListener {
            PrivilegeExecutor.setMode(this, PrivilegeExecutor.Mode.SHIZUKU)
            refreshStatus()
        }
        btnModeRoot.setOnClickListener {
            PrivilegeExecutor.setMode(this, PrivilegeExecutor.Mode.ROOT)
            refreshStatus()
        }
    }

    override fun onResume() {
        super.onResume()
        refreshStatus()
        isServiceRunning.set(McpService.serviceRunning)
        updateUI()
    }

    override fun onDestroy() {
        super.onDestroy()
        PrivilegeExecutor.onStatusChanged = null
    }

    private fun refreshStatus() {
        val wasReady = PrivilegeExecutor.isReady()
        PrivilegeExecutor.checkStatus()
        val isNowReady = PrivilegeExecutor.isReady()

        val diag = buildDiagnostic()
        appendLog(if (diag.isNotEmpty()) diag else "检查: ready=$isNowReady")

        if (isNowReady && !wasReady) {
            appendLog("✓ ${PrivilegeExecutor.activeBackendName().uppercase()} 已就绪！")
        }

        updateUI()

        if (!isNowReady && retryCount < MAX_RETRY) {
            scheduleRetry()
        }
    }

    private fun buildDiagnostic(): String {
        val parts = mutableListOf<String>()
        if (ShizukuHelper.lastDiagnostic.isNotEmpty()) {
            parts.add("Shizuku: ${ShizukuHelper.lastDiagnostic}")
        }
        if (RootHelper.lastDiagnostic.isNotEmpty()) {
            parts.add("Root: ${RootHelper.lastDiagnostic}")
        }
        return parts.joinToString("\n")
    }

    private var retryCount = 0
    private val MAX_RETRY = 5
    private var retryHandler: android.os.Handler? = null

    private fun scheduleRetry() {
        retryCount++
        retryHandler?.removeCallbacksAndMessages(null)
        val handler = android.os.Handler(Looper.getMainLooper())
        retryHandler = handler
        handler.postDelayed({
            appendLog("重试 #$retryCount...")
            refreshStatus()
        }, 800)
    }

    private fun attemptAuthorize() {
        retryCount = 0
        retryHandler?.removeCallbacksAndMessages(null)

        val mode = PrivilegeExecutor.getMode()
        val requestRoot = mode == PrivilegeExecutor.Mode.ROOT ||
            (mode == PrivilegeExecutor.Mode.AUTO &&
                RootHelper.isAvailable && !RootHelper.isPermissionGranted)

        if (requestRoot) {
            appendLog("正在请求 Root 权限...")
            appendLog("请在 Superuser 管理器（Magisk/KernelSU 等）弹出时点击允许")
            RootHelper.requestGrant()
            android.os.Handler(Looper.getMainLooper()).postDelayed({
                refreshStatus()
            }, 800)
        } else {
            appendLog("正在打开 Shizuku Manager...")
            appendLog("请在 Shizuku → 已授权应用 → 找到 Android MCP → 开启授权")
            ShizukuHelper.openShizukuManager(this)
        }
    }

    private fun requestNotificationPermission() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            if (ContextCompat.checkSelfPermission(
                    this, Manifest.permission.POST_NOTIFICATIONS
                ) != PackageManager.PERMISSION_GRANTED
            ) {
                ActivityCompat.requestPermissions(
                    this,
                    arrayOf(Manifest.permission.POST_NOTIFICATIONS),
                    100
                )
            }
        }
    }

    private fun startService() {
        val intent = Intent(this, McpService::class.java)
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            startForegroundService(intent)
        } else {
            startService(intent)
        }

        isServiceRunning.set(true)
        updateUI()
        appendLog("服务启动中...")

        android.os.Handler(Looper.getMainLooper()).postDelayed({
            if (McpService.serviceRunning) {
                isServiceRunning.set(true)
                updateUI()
                val ip = McpService.getLocalIpAddress()
                appendLog("HTTP 服务已启动")
                appendLog("地址: http://$ip:${McpService.PORT}/mcp")
                appendLog("健康检查: http://$ip:${McpService.PORT}/health")
            }
        }, 2000)
    }

    private fun stopService() {
        val intent = Intent(this, McpService::class.java)
        stopService(intent)
        isServiceRunning.set(false)
        updateUI()
        appendLog("服务已停止")
    }

    private fun updateUI() {
        val mode = PrivilegeExecutor.getMode()
        val ready = PrivilegeExecutor.isReady()
        val backend = PrivilegeExecutor.activeBackendName()
        val running = isServiceRunning.get()

        tvShellStatus.text = when {
            ready -> if (backend == "root") "已就绪 · Root" else "已就绪 · Shizuku"
            mode == PrivilegeExecutor.Mode.ROOT -> when {
                !RootHelper.isAvailable -> "未检测到 Root"
                !RootHelper.isPermissionGranted -> "Root 未授权"
                else -> "Root 验证中"
            }
            mode == PrivilegeExecutor.Mode.SHIZUKU -> when {
                !ShizukuHelper.isAvailable -> "Shizuku 未启动"
                !ShizukuHelper.isPermissionGranted -> "等待授权"
                else -> "Shizuku 验证中"
            }
            else -> when {
                RootHelper.isAvailable || ShizukuHelper.isAvailable -> "等待授权"
                else -> "无可用特权"
            }
        }

        tvShellStatus.setTextColor(
            when {
                ready -> 0xFF4CAF50.toInt()
                RootHelper.isAvailable || ShizukuHelper.isAvailable -> 0xFFFF9800.toInt()
                else -> 0xFFF44336.toInt()
            }
        )

        val diag = buildDiagnostic()
        tvShellDetail.visibility = if (!ready && diag.isNotEmpty()) View.VISIBLE else View.GONE
        tvShellDetail.text = if (diag.isNotEmpty()) diag else ""

        if (running) {
            tvHttpAddress.text = McpService.httpAddress.ifEmpty { "启动中..." }
            tvHttpAddress.setTextColor(0xFF4CAF50.toInt())
        } else {
            tvHttpAddress.text = "未启动"
            tvHttpAddress.setTextColor(0xFFFF9800.toInt())
        }

        tvApiCount.text = "31"
        tvApiCount.setTextColor(0xFF42A5F5.toInt())

        if (running) {
            btnToggle.text = getString(R.string.stop_service)
            btnToggle.backgroundTintList =
                android.content.res.ColorStateList.valueOf(0xFFD32F2F.toInt())
        } else {
            btnToggle.text = getString(R.string.start_service)
            btnToggle.backgroundTintList =
                android.content.res.ColorStateList.valueOf(0xFF1565C0.toInt())
        }

        layoutAuthButtons.visibility = if (!ready) View.VISIBLE else View.GONE
        btnAuth.text = when {
            mode == PrivilegeExecutor.Mode.ROOT -> "请求 Root 权限"
            mode == PrivilegeExecutor.Mode.AUTO &&
                RootHelper.isAvailable && !RootHelper.isPermissionGranted -> "请求 Root 权限"
            else -> if (ShizukuHelper.isAvailable) "前往授权" else "打开 Shizuku"
        }

        updateModeButtons(mode)
    }

    private fun updateModeButtons(active: PrivilegeExecutor.Mode) {
        val on = android.content.res.ColorStateList.valueOf(0xFF1565C0.toInt())
        val off = android.content.res.ColorStateList.valueOf(0xFF424242.toInt())

        btnModeAuto.backgroundTintList = if (active == PrivilegeExecutor.Mode.AUTO) on else off
        btnModeShizuku.backgroundTintList = if (active == PrivilegeExecutor.Mode.SHIZUKU) on else off
        btnModeRoot.backgroundTintList = if (active == PrivilegeExecutor.Mode.ROOT) on else off
    }

    private fun copyTokenToClipboard() {
        val token = TokenStore.getOrCreate(this)
        val clipboard = getSystemService(android.content.Context.CLIPBOARD_SERVICE)
            as android.content.ClipboardManager
        clipboard.setPrimaryClip(
            android.content.ClipData.newPlainText("Android MCP Token", token)
        )
        tvToken.text = token
        appendLog("Token 已复制到剪贴板")
    }

    private fun appendLog(message: String) {
        val ts = java.text.SimpleDateFormat("HH:mm:ss", java.util.Locale.getDefault())
            .format(java.util.Date())
        logLines.add("$ts $message")
        if (logLines.size > 200) {
            logLines.removeAt(0)
        }
        runOnUiThread {
            if (::tvLog.isInitialized) {
                tvLog.text = logLines.joinToString("\n")
            }
        }
    }
}