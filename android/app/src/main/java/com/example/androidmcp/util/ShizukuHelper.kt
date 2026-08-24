package com.example.androidmcp.util

import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.net.Uri
import android.util.Log
import rikka.shizuku.Shizuku
import java.io.BufferedReader
import java.io.InputStreamReader

object ShizukuHelper {

    private const val TAG = "MCP_Shizuku"

    var isAvailable: Boolean = false
        private set
    var isPermissionGranted: Boolean = false
        private set
    var isVerified: Boolean = false
        private set

    var lastDiagnostic: String = ""
        private set

    var onStatusChanged: (() -> Unit)? = null

    fun resetStatus() {
        isAvailable = false
        isPermissionGranted = false
        isVerified = false
        lastDiagnostic = ""
        Log.i(TAG, "Status reset")
        onStatusChanged?.invoke()
    }

    fun checkStatus(): Boolean {
        val wasReady = isReady()
        val diag = StringBuilder()

        try {
            val binder = Shizuku.getBinder()
            diag.appendLine("getBinder = ${if (binder != null) "OK" else "NULL"}")
            Log.i(TAG, "getBinder = ${if (binder != null) "OK" else "NULL"}")

            isAvailable = binder != null
            if (!isAvailable) {
                isAvailable = try {
                    Shizuku.pingBinder()
                } catch (e: Exception) {
                    diag.appendLine("pingBinder fallback: ${e.message}")
                    false
                }
            }

            isPermissionGranted = try {
                if (isAvailable) {
                    val perm = Shizuku.checkSelfPermission()
                    val g = perm == PackageManager.PERMISSION_GRANTED
                    diag.appendLine("checkSelfPermission = $perm (granted=$g)")
                    Log.i(TAG, "checkSelfPermission = $perm")
                    g
                } else {
                    diag.appendLine("checkSelfPermission: skipped")
                    false
                }
            } catch (e: Exception) {
                diag.appendLine("checkSelfPermission error: ${e.message}")
                false
            }

            isVerified = if (isAvailable && isPermissionGranted) {
                try {
                    val result = execInternal("echo MCP_OK")
                    val ok = result.isSuccess && result.stdout.contains("MCP_OK")
                    diag.appendLine("verify: ${if (ok) "OK" else "FAILED"} (exit=${result.exitCode})")
                    ok
                } catch (e: Exception) {
                    diag.appendLine("verify error: ${e.message}")
                    false
                }
            } else {
                false
            }

            lastDiagnostic = diag.toString().trim()
        } catch (e: Exception) {
            isAvailable = false
            isPermissionGranted = false
            isVerified = false
            lastDiagnostic = "fatal: ${e.message}"
            Log.w(TAG, "checkStatus fatal", e)
        }

        val isNowReady = isReady()
        if (wasReady != isNowReady) {
            Log.i(TAG, "Status changed: ready=$isNowReady")
            onStatusChanged?.invoke()
        }

        return isNowReady
    }

    fun openShizukuManager(context: Context) {
        try {
            val intent = context.packageManager.getLaunchIntentForPackage("moe.shizuku.privileged.api")
            if (intent != null) {
                context.startActivity(intent)
            } else {
                context.startActivity(Intent(Intent.ACTION_VIEW).apply {
                    data = Uri.parse("market://details?id=moe.shizuku.privileged.api")
                })
            }
        } catch (e: Exception) {
            Log.w(TAG, "openShizukuManager error", e)
        }
    }

    fun exec(command: String): ExecResult {
        if (!isReady()) {
            return ExecResult(-1, "", "Shizuku not ready: ${getStatusSummary()}")
        }
        return execInternal(command)
    }

    private fun execInternal(command: String): ExecResult {
        return try {
            val method = Shizuku::class.java.getDeclaredMethod(
                "newProcess", Array<String>::class.java, Array<String>::class.java, String::class.java
            )
            method.isAccessible = true
            val process = method.invoke(null, arrayOf("sh", "-c", command), null, null) as Process
            val stdout = BufferedReader(InputStreamReader(process.inputStream)).readText()
            val stderr = BufferedReader(InputStreamReader(process.errorStream)).readText()
            val exitCode = process.waitFor()
            ExecResult(exitCode, stdout.trim(), stderr.trim())
        } catch (e: Exception) {
            ExecResult(-1, "", e.message ?: "Unknown error")
        }
    }

    fun isReady(): Boolean = isAvailable && isPermissionGranted && isVerified

    fun getStatusSummary(): String {
        return "available=$isAvailable, permission=$isPermissionGranted, verified=$isVerified"
    }
}