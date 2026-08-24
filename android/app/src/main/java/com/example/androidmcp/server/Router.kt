package com.example.androidmcp.server

import android.util.Log
import com.example.androidmcp.api.FileApi
import com.example.androidmcp.api.InputApi
import com.example.androidmcp.api.PackageApi
import com.example.androidmcp.api.ShellApi
import com.example.androidmcp.api.SystemApi
import com.example.androidmcp.api.TaskApi
import org.json.JSONObject

class Router {
    private val tag = "Router"
    private val shellApi = ShellApi()
    private val inputApi = InputApi()
    private val packageApi = PackageApi()
    private val systemApi = SystemApi()
    private val fileApi = FileApi()
    private val taskApi = TaskApi()

    fun handle(request: JSONObject): JSONObject {
        val id = request.opt("id")
        val method = request.optString("method", "")
        val params = request.optJSONObject("params") ?: JSONObject()

        try {
            if (request.optString("jsonrpc") != "2.0") {
                return errorResponse(id, -32600, "Invalid Request: jsonrpc must be 2.0")
            }

            val result = dispatch(method, params)
            return JSONObject().apply {
                put("jsonrpc", "2.0")
                put("result", result)
                put("id", id)
            }
        } catch (e: Exception) {
            Log.e(tag, "Error handling method: $method", e)
            return errorResponse(id, -32603, "Internal error: ${e.message}")
        }
    }

    private fun errorResponse(id: Any?, code: Int, message: String): JSONObject {
        return JSONObject().apply {
            put("jsonrpc", "2.0")
            put("error", JSONObject().apply {
                put("code", code)
                put("message", message)
            })
            put("id", id)
        }
    }

    private fun dispatch(method: String, params: JSONObject): Any {
        return when (method) {
            // Shell
            "shell.exec" -> shellApi.exec(params)

            // Input
            "input.tap" -> inputApi.tap(params)
            "input.long_press" -> inputApi.longPress(params)
            "input.swipe" -> inputApi.swipe(params)
            "input.drag" -> inputApi.drag(params)
            "input.keyevent" -> inputApi.keyEvent(params)
            "input.text" -> inputApi.text(params)

            // Package
            "package.install" -> packageApi.install(params)
            "package.uninstall" -> packageApi.uninstall(params)
            "package.open" -> packageApi.open(params)
            "package.close" -> packageApi.close(params)
            "package.clear_data" -> packageApi.clearData(params)
            "package.list" -> packageApi.list(params)

            // System
            "system.info" -> systemApi.info()
            "system.screenshot" -> systemApi.screenshot(params)
            "system.settings.get" -> systemApi.getSetting(params)
            "system.settings.put" -> systemApi.putSetting(params)
            "system.clipboard.get" -> systemApi.getClipboard()
            "system.clipboard.set" -> systemApi.setClipboard(params)

            // Privilege mode (root / shizuku / auto)
            "system.mode.get" -> systemApi.getMode()
            "system.mode.set" -> systemApi.setMode(params)

            // System - Notifications
            "system.notification.list" -> systemApi.listNotifications()
            "system.notification.cancel" -> systemApi.cancelNotification(params)

            // File
            "file.read" -> fileApi.read(params)
            "file.write" -> fileApi.write(params)
            "file.list" -> fileApi.list(params)
            "file.stat" -> fileApi.stat(params)
            "file.delete" -> fileApi.delete(params)

            // Task (long-running background commands)
            "task.submit" -> taskApi.submit(params)
            "task.status" -> taskApi.status(params)
            "task.result" -> taskApi.result(params)
            "task.cancel" -> taskApi.cancel(params)
            "task.list" -> taskApi.list(params)

            // Device
            "device.reboot" -> systemApi.reboot()
            "device.screen.on" -> systemApi.screenOn()
            "device.screen.off" -> systemApi.screenOff()

            else -> throw IllegalArgumentException("Unknown method: $method")
        }
    }
}
