package com.example.androidmcp.util

import android.content.Context
import android.util.Log

/**
 * Unified privilege execution layer.
 *
 * Routes shell commands to the best available backend:
 *  - ROOT    -> run as uid 0 via `su` (rooted devices: Magisk / KernelSU / APatch / SuperSU)
 *  - SHIZUKU -> run as shell user via the Shizuku binder
 *  - AUTO    -> prefer root when available, otherwise fall back to Shizuku
 *
 * The selected mode is persisted so it survives process restarts.
 */
object PrivilegeExecutor {

    enum class Mode { AUTO, SHIZUKU, ROOT }

    private const val TAG = "MCP_PrivExec"
    private const val PREFS_NAME = "mcp_privilege"
    private const val KEY_MODE = "mode"

    @Volatile
    private var mode: Mode = Mode.AUTO

    /** Combined status change callback (fires when either backend changes). */
    var onStatusChanged: (() -> Unit)? = null

    fun init(context: Context) {
        val prefs = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
        mode = runCatching {
            Mode.valueOf(prefs.getString(KEY_MODE, Mode.AUTO.name) ?: Mode.AUTO.name)
        }.getOrDefault(Mode.AUTO)

        ShizukuHelper.onStatusChanged = { onStatusChanged?.invoke() }
        RootHelper.onStatusChanged = { onStatusChanged?.invoke() }
        Log.i(TAG, "Initialized mode=$mode")
    }

    fun getMode(): Mode = mode

    fun setMode(context: Context, newMode: Mode) {
        mode = newMode
        context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
            .edit().putString(KEY_MODE, newMode.name).apply()
        Log.i(TAG, "Mode set to $newMode")
        onStatusChanged?.invoke()
    }

    fun cycleMode(context: Context) {
        val next = when (mode) {
            Mode.AUTO -> Mode.SHIZUKU
            Mode.SHIZUKU -> Mode.ROOT
            Mode.ROOT -> Mode.AUTO
        }
        setMode(context, next)
    }

    fun checkStatus() {
        ShizukuHelper.checkStatus()
        RootHelper.checkStatus()
    }

    fun isReady(): Boolean = when (resolveBackend()) {
        Backend.ROOT -> true
        Backend.SHIZUKU -> true
        Backend.NONE -> false
    }

    fun exec(command: String): ExecResult {
        return when (resolveBackend()) {
            Backend.ROOT -> RootHelper.exec(command)
            Backend.SHIZUKU -> ShizukuHelper.exec(command)
            Backend.NONE -> ExecResult(
                -1,
                "",
                "No privilege backend ready (root unavailable, Shizuku unavailable)"
            )
        }
    }

    /**
     * Execute a command with an explicit timeout (<= 0 means unlimited) and an
     * optional [onProcess] callback invoked as soon as the process is spawned —
     * used by [TaskManager] to expose the Process for cancellation.
     */
    fun exec(command: String, timeoutMs: Long, onProcess: ((Process) -> Unit)? = null): ExecResult {
        return when (resolveBackend()) {
            Backend.ROOT -> RootHelper.exec(command, timeoutMs, onProcess)
            Backend.SHIZUKU -> ShizukuHelper.exec(command, timeoutMs, onProcess)
            Backend.NONE -> ExecResult(
                -1,
                "",
                "No privilege backend ready (root unavailable, Shizuku unavailable)"
            )
        }
    }

    /** Name of the backend that will actually be used right now: "root" | "shizuku" | "none". */
    fun activeBackendName(): String = resolveBackend().name.lowercase()

    fun isRootActive(): Boolean = resolveBackend() == Backend.ROOT
    fun isShizukuActive(): Boolean = resolveBackend() == Backend.SHIZUKU

    fun shizukuReady(): Boolean = ShizukuHelper.isReady()
    fun rootReady(): Boolean = RootHelper.isReady()

    fun getStatusSummary(): String =
        "mode=$mode, backend=${activeBackendName()}, shizuku=${ShizukuHelper.isReady()}, root=${RootHelper.isReady()}"

    // ------------------------------------------------------------------
    // Internals
    // ------------------------------------------------------------------

    private enum class Backend { ROOT, SHIZUKU, NONE }

    private fun resolveBackend(): Backend {
        return when (mode) {
            Mode.ROOT -> if (RootHelper.isReady()) Backend.ROOT else Backend.NONE
            Mode.SHIZUKU -> if (ShizukuHelper.isReady()) Backend.SHIZUKU else Backend.NONE
            Mode.AUTO -> when {
                RootHelper.isReady() -> Backend.ROOT
                ShizukuHelper.isReady() -> Backend.SHIZUKU
                else -> Backend.NONE
            }
        }
    }
}