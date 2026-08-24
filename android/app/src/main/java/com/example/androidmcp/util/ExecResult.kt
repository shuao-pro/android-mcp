package com.example.androidmcp.util

/**
 * Result of executing a shell command through a privilege backend
 * (Shizuku shell or root/su).
 *
 * [process] holds the backing process (may be null) so callers such as
 * [TaskManager] can cancel a still-running command. [timedOut] is true when the
 * command was killed because it exceeded its timeout.
 */
data class ExecResult(
    val exitCode: Int,
    val stdout: String,
    val stderr: String,
    val process: Process? = null,
    val timedOut: Boolean = false
) {
    val isSuccess: Boolean get() = exitCode == 0
}