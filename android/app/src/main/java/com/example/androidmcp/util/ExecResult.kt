package com.example.androidmcp.util

/**
 * Result of executing a shell command through a privilege backend
 * (Shizuku shell or root/su).
 */
data class ExecResult(
    val exitCode: Int,
    val stdout: String,
    val stderr: String
) {
    val isSuccess: Boolean get() = exitCode == 0
}