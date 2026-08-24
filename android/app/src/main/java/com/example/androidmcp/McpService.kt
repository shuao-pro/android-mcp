package com.example.androidmcp

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.app.Service
import android.content.Intent
import android.content.pm.ServiceInfo
import android.os.Build
import android.os.IBinder
import android.util.Log
import com.example.androidmcp.server.HttpServer
import com.example.androidmcp.server.Router
import com.example.androidmcp.util.PrivilegeExecutor
import com.example.androidmcp.util.TokenStore
import java.net.Inet4Address
import java.net.NetworkInterface

class McpService : Service() {

    companion object {
        const val TAG = "McpService"
        const val CHANNEL_ID = "mcp_service_channel"
        const val NOTIFICATION_ID = 1001
        const val ACTION_STOP = "com.example.androidmcp.STOP_SERVICE"
        const val PORT = 18080

        var serviceRunning = false
            private set
        var httpAddress = ""
            private set

        fun getLocalIpAddress(): String {
            try {
                val interfaces = NetworkInterface.getNetworkInterfaces()
                while (interfaces.hasMoreElements()) {
                    val networkInterface = interfaces.nextElement()
                    val addresses = networkInterface.inetAddresses
                    while (addresses.hasMoreElements()) {
                        val address = addresses.nextElement()
                        if (!address.isLoopbackAddress && address is Inet4Address) {
                            return address.hostAddress ?: "127.0.0.1"
                        }
                    }
                }
            } catch (e: Exception) {
                Log.e(TAG, "Failed to get local IP", e)
            }
            return "127.0.0.1"
        }
    }

    private var httpServer: HttpServer? = null

    override fun onCreate() {
        super.onCreate()
        Log.i(TAG, "Service created")
        createNotificationChannel()
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        if (intent?.action == ACTION_STOP) {
            stopSelf()
            return START_NOT_STICKY
        }

        startForeground()
        startHttpServer()

        return START_STICKY
    }

    override fun onBind(intent: Intent?): IBinder? = null

    override fun onDestroy() {
        stopHttpServer()
        serviceRunning = false
        httpAddress = ""
        Log.i(TAG, "Service destroyed")
        super.onDestroy()
    }

    private fun startForeground() {
        val pendingIntent = PendingIntent.getService(
            this, 0,
            Intent(this, McpService::class.java).apply { action = ACTION_STOP },
            PendingIntent.FLAG_IMMUTABLE or PendingIntent.FLAG_UPDATE_CURRENT
        )
        val stopIcon = android.graphics.drawable.Icon.createWithResource(
            this, android.R.drawable.ic_media_pause
        )
        val stopAction = Notification.Action.Builder(stopIcon, "停止", pendingIntent).build()

        val notification = Notification.Builder(this, CHANNEL_ID)
            .setContentTitle(getString(R.string.notification_title))
            .setContentText(getString(R.string.notification_text))
            .setSmallIcon(android.R.drawable.ic_menu_manage)
            .setOngoing(true)
            .addAction(stopAction)
            .build()

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.UPSIDE_DOWN_CAKE) {
            startForeground(
                NOTIFICATION_ID, notification,
                ServiceInfo.FOREGROUND_SERVICE_TYPE_SPECIAL_USE
            )
        } else {
            startForeground(NOTIFICATION_ID, notification)
        }

        serviceRunning = true
    }

    private fun startHttpServer() {
        val router = Router()
        val token = TokenStore.getOrCreate(this)
        httpServer = HttpServer(PORT, router, authToken = token)

        PrivilegeExecutor.checkStatus()
        Log.i(TAG, "Privilege mode=${PrivilegeExecutor.getMode()}, backend=${PrivilegeExecutor.activeBackendName()}")

        httpServer?.start()
        val ip = getLocalIpAddress()
        httpAddress = "$ip:$PORT"
        Log.i(TAG, "HTTP server running at $httpAddress")
    }

    private fun stopHttpServer() {
        httpServer?.stop()
        httpServer = null
        Log.i(TAG, "HTTP server stopped")
    }

    private fun createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(
                CHANNEL_ID,
                getString(R.string.notification_channel_name),
                NotificationManager.IMPORTANCE_LOW
            ).apply {
                description = "Android MCP 后台服务通知"
            }
            val manager = getSystemService(NotificationManager::class.java)
            manager.createNotificationChannel(channel)
        }
    }
}
