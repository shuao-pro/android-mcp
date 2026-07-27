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
import com.example.androidmcp.util.ShizukuHelper
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

        ShizukuHelper.onStatusChanged = {
            runOnUiThread { updateUI() }
        }

        requestNotificationPermission()
        checkShizukuStatus()

        btnToggle.setOnClickListener {
            if (isServiceRunning.get()) {
                stopService()
            } else {
                if (!ShizukuHelper.isReady()) {
                    attemptAuthorize()
                    return@setOnClickListener
                }
                startService()
            }
        }

        btnAuth.setOnClickListener { attemptAuthorize() }
        btnRefresh.setOnClickListener { checkShizukuStatus() }
    }

    override fun onResume() {
        super.onResume()
        checkShizukuStatus()
        isServiceRunning.set(McpService.serviceRunning)
        updateUI()
    }

    override fun onDestroy() {
        super.onDestroy()
        ShizukuHelper.onStatusChanged = null
    }

    private fun checkShizukuStatus() {
        val wasReady = ShizukuHelper.isReady()
        ShizukuHelper.checkStatus()
        val isNowReady = ShizukuHelper.isReady()

        val diag = ShizukuHelper.lastDiagnostic
        appendLog(if (diag.isNotEmpty()) diag else "检查: ready=$isNowReady")

        if (isNowReady && !wasReady) {
            appendLog("✓ Shizuku 已就绪！")
        }

        updateUI()

        if (!isNowReady && !ShizukuHelper.isAvailable && retryCount < MAX_RETRY) {
            scheduleRetry()
        }
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
            checkShizukuStatus()
        }, 800)
    }

    private fun attemptAuthorize() {
        retryCount = 0
        retryHandler?.removeCallbacksAndMessages(null)

        appendLog("正在打开 Shizuku Manager...")
        appendLog("请在 Shizuku → 已授权应用 → 找到 Android MCP → 开启授权")
        ShizukuHelper.openShizukuManager(this)
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
        val available = ShizukuHelper.isAvailable
        val granted = ShizukuHelper.isPermissionGranted
        val verified = ShizukuHelper.isVerified
        val running = isServiceRunning.get()

        tvShellStatus.text = when {
            !available -> "Shizuku 未启动"
            !granted -> "等待授权"
            !verified -> "验证中..."
            else -> "已就绪"
        }
        tvShellStatus.setTextColor(
            when {
                verified -> 0xFF4CAF50.toInt()
                available -> 0xFFFF9800.toInt()
                else -> 0xFFF44336.toInt()
            }
        )

        val diag = ShizukuHelper.lastDiagnostic
        tvShellDetail.visibility = if (!verified && diag.isNotEmpty()) View.VISIBLE else View.GONE
        tvShellDetail.text = if (diag.isNotEmpty()) diag else ""

        if (running) {
            tvHttpAddress.text = McpService.httpAddress.ifEmpty { "启动中..." }
            tvHttpAddress.setTextColor(0xFF4CAF50.toInt())
        } else {
            tvHttpAddress.text = "未启动"
            tvHttpAddress.setTextColor(0xFFFF9800.toInt())
        }

        tvApiCount.text = "29"
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

        layoutAuthButtons.visibility = if (!verified) View.VISIBLE else View.GONE
        btnAuth.text = if (available) "前往授权" else "打开 Shizuku"
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
