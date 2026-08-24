package com.example.androidmcp.util

import android.util.Log
import java.io.ByteArrayOutputStream
import java.io.File
import java.io.InputStream
import java.util.concurrent.Executors
import java.util.concurrent.TimeUnit

/**
 * Root (su) privilege backend for rooted devices (Magisk / KernelSU / APatch / SuperSU).
 *
 * Mirrors [ShizukuHelper]'s surface so [PrivilegeExecutor] can route commands to
 * either backend transparently. Every command runs as uid 0 via the `su` binary.
 *
 * Status probing (`su -c id`) can block while the superuser prompt is shown, so
 * [checkStatus] and [requestGrant] run on a background thread and notify via
 * [onStatusChanged]. Command execution ([exec]) is synchronous and is expected to
 * be called from HTTP worker threads, not the main thread.
 */
object RootHelper {

    private const val TAG = "MCP_Root"

    /** Timeout for a single root shell command. */
    private const val EXEC_TIMEOUT_MS = 60_000L

    @Volatile
    var isAvailable: Boolean = false
        private set
    @Volatile
    var isPermissionGranted: Boolean = false
        private set
    @Volatile
    var isVerified: Boolean = false
        private set

    @Volatile
    var lastDiagnostic: String = ""
        private set

    /** Path of the detected `su` binary (empty if not found). */
    @Volatile
    var suPath: String = ""
        private set

    var onStatusChanged: (() -> Unit)? = null

    private val executor = Executors.newSingleThreadExecutor { r ->
        Thread(r, "mcp-root").apply { isDaemon = true }
    }

    @Volatile
    private var checking = false

    fun resetStatus() {
        isAvailable = false
        isPermissionGranted = false
        isVerified = false
        suPath = ""
        lastDiagnostic = ""
        Log.i(TAG, "Status reset")
        onStatusChanged?.invoke()
    }

    /**
     * Asynchronously detect root availability and permission. Does not block the
     * caller. Notifies [onStatusChanged] when the state changes.
     */
    fun checkStatus() {
        if (checking) return
        checking = true
        executor.execute {
            try {
                val wasReady = isReady()
                val diag = StringBuilder()

                suPath = findSu(diag)
                isAvailable = suPath.isNotEmpty()

                if (isAvailable) {
                    isPermissionGranted = verifyRoot(diag)
                    isVerified = isPermissionGranted
                } else {
                    isPermissionGranted = false
                    isVerified = false
                }

                lastDiagnostic = diag.toString().trim()

                if (wasReady != isReady()) {
                    Log.i(TAG, "Status changed: ready=${isReady()}")
                    onStatusChanged?.invoke()
                } else {
                    onStatusChanged?.invoke()
                }
            } catch (e: Exception) {
                isAvailable = false
                isPermissionGranted = false
                isVerified = false
                lastDiagnostic = "fatal: ${e.message}"
                Log.w(TAG, "checkStatus fatal", e)
                onStatusChanged?.invoke()
            } finally {
                checking = false
            }
        }
    }

    /**
     * Trigger the superuser manager prompt (e.g. Magisk) by running a benign
     * `id` command as root, then refresh status. Runs off the main thread.
     */
    fun requestGrant() {
        executor.execute {
            val result = runProcess(listOf("su", "-c", "id"), 10_000L)
            isPermissionGranted = result.isSuccess && result.stdout.contains("uid=0")
            isVerified = isPermissionGranted
            lastDiagnostic = "su id: ${if (isPermissionGranted) "uid=0 OK" else "denied (exit=${result.exitCode})"}"
            Log.i(TAG, "requestGrant -> granted=$isPermissionGranted")
            onStatusChanged?.invoke()
        }
    }

    fun exec(command: String): ExecResult {
        if (!isReady()) {
            return ExecResult(-1, "", "Root not ready: ${getStatusSummary()}")
        }
        return runProcess(listOf("su", "-c", command), EXEC_TIMEOUT_MS)
    }

    fun isReady(): Boolean = isAvailable && isPermissionGranted && isVerified

    fun getStatusSummary(): String =
        "available=$isAvailable, permission=$isPermissionGranted, verified=$isVerified, su=$suPath"

    // ------------------------------------------------------------------
    // Internals
    // ------------------------------------------------------------------

    /** Locate the `su` binary without requesting root (never prompts). */
    private fun findSu(diag: StringBuilder): String {
        val candidates = listOf(
            "/system/bin/su",
            "/system/xbin/su",
            "/sbin/su",
            "/system/sbin/su",
            "/su/bin/su",
            "/data/adb/su/bin/su"
        )
        for (p in candidates) {
            if (File(p).exists()) {
                diag.appendLine("su found: $p")
                return p
            }
        }

        val which = runProcess(listOf("sh", "-c", "command -v su"), 3_000L)
        val line = which.stdout.trim().lineSequence().firstOrNull { it.isNotBlank() }
        if (which.isSuccess && !line.isNullOrBlank()) {
            diag.appendLine("su (command -v): $line")
            return line
        }

        diag.appendLine("su: not found")
        return ""
    }

    /** Verify root access by running `su -c id` and checking for uid=0. */
    private fun verifyRoot(diag: StringBuilder): Boolean {
        val result = runProcess(listOf("su", "-c", "id"), 8_000L)
        val ok = result.isSuccess && result.stdout.contains("uid=0")
        diag.appendLine("su id: ${if (ok) "uid=0 OK" else "failed (exit=${result.exitCode})"}")
        if (!ok && result.stderr.isNotBlank()) {
            diag.appendLine("stderr: ${result.stderr.take(160)}")
        }
        return ok
    }

    /** Run a process, reading stdout/stderr concurrently to avoid pipe deadlock. */
    private fun runProcess(cmd: List<String>, timeoutMs: Long): ExecResult {
        return try {
            val process = ProcessBuilder(cmd)
                .redirectErrorStream(false)
                .start()

            val outReader = StreamReader(process.inputStream)
            val errReader = StreamReader(process.errorStream)
            outReader.start()
            errReader.start()

            val finished = process.waitFor(timeoutMs, TimeUnit.MILLISECONDS)
            if (!finished) {
                process.destroyForcibly()
            }

            outReader.join(2_000)
            errReader.join(2_000)

            if (!finished) {
                ExecResult(-1, outReader.text, "timeout after ${timeoutMs}ms")
            } else {
                ExecResult(process.exitValue(), outReader.text.trim(), errReader.text.trim())
            }
        } catch (e: Exception) {
            ExecResult(-1, "", e.message ?: "Unknown error")
        }
    }

    private class StreamReader(private val input: InputStream) : Thread() {
        @Volatile
        var text: String = ""
            private set

        override fun run() {
            val buffer = ByteArrayOutputStream()
            val chunk = ByteArray(8192)
            try {
                var n = input.read(chunk)
                while (n >= 0) {
                    buffer.write(chunk, 0, n)
                    n = input.read(chunk)
                }
            } catch (_: Exception) {
            } finally {
                text = buffer.toString("UTF-8")
            }
        }
    }
}