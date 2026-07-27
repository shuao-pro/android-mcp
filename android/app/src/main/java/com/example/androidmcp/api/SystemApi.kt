package com.example.androidmcp.api

import android.content.ClipData
import android.content.ClipboardManager
import android.content.Context
import android.os.Build
import android.os.Handler
import android.os.Looper
import android.util.Base64
import com.example.androidmcp.App
import com.example.androidmcp.util.ShizukuHelper
import org.json.JSONArray
import org.json.JSONObject
import java.io.File
import java.util.concurrent.CountDownLatch

class SystemApi {

    fun info(): JSONObject {
        val osBuild = Build.VERSION.RELEASE
        val sdk = Build.VERSION.SDK_INT
        val manufacturer = Build.MANUFACTURER
        val model = Build.MODEL
        val brand = Build.BRAND

        val screenRes = ShizukuHelper.exec("wm size")
        val density = ShizukuHelper.exec("wm density")
        val battery = ShizukuHelper.exec("dumpsys battery | grep level")
        val uptime = ShizukuHelper.exec("cat /proc/uptime")

        return JSONObject().apply {
            put("os_version", osBuild)
            put("sdk_int", sdk)
            put("manufacturer", manufacturer)
            put("model", model)
            put("brand", brand)
            put("screen_resolution", screenRes.stdout.trim())
            put("screen_density", density.stdout.trim())
            put("battery_level", battery.stdout.trim().lines().firstOrNull()?.trim() ?: "")
            put("uptime_seconds", uptime.stdout.split(" ").firstOrNull()?.toDoubleOrNull() ?: 0.0)
            put("success", true)
        }
    }

    fun screenshot(params: JSONObject): JSONObject {
        val quality = params.optInt("quality", 80)
        if (quality !in 1..100) throw IllegalArgumentException("quality must be 1-100")

        val tmpPath = "/data/local/tmp/mcp_screenshot_${System.currentTimeMillis()}.png"
        val result = ShizukuHelper.exec("screencap -p $tmpPath")

        if (!result.isSuccess) {
            return JSONObject().apply {
                put("success", false)
                put("error", result.stderr)
            }
        }

        val catResult = ShizukuHelper.exec("cat $tmpPath | base64 -w 0")
        ShizukuHelper.exec("rm -f $tmpPath")

        if (!catResult.isSuccess) {
            return JSONObject().apply {
                put("success", false)
                put("error", catResult.stderr)
            }
        }

        return JSONObject().apply {
            put("success", true)
            put("image_base64", catResult.stdout.trim())
            put("format", "png")
        }
    }

    fun getSetting(params: JSONObject): JSONObject {
        val namespace = params.optString("namespace", "system")
        val key = params.optString("key", "")
        if (key.isEmpty()) throw IllegalArgumentException("key required")

        val result = ShizukuHelper.exec("settings get $namespace $key")
        return JSONObject().apply {
            put("success", result.isSuccess)
            put("key", key)
            put("namespace", namespace)
            put("value", result.stdout.trim())
        }
    }

    fun putSetting(params: JSONObject): JSONObject {
        val namespace = params.optString("namespace", "system")
        val key = params.optString("key", "")
        val value = params.optString("value", "")
        if (key.isEmpty()) throw IllegalArgumentException("key required")

        val result = ShizukuHelper.exec("settings put $namespace $key $value")
        return JSONObject().apply {
            put("success", result.isSuccess)
            put("stdout", result.stdout)
            put("stderr", result.stderr)
        }
    }

    fun getClipboard(): JSONObject {
        val latch = CountDownLatch(1)
        var text = ""

        Handler(Looper.getMainLooper()).post {
            try {
                val cm = App.instance.getSystemService(Context.CLIPBOARD_SERVICE) as ClipboardManager
                val clip = cm.primaryClip
                text = clip?.getItemAt(0)?.text?.toString() ?: ""
            } catch (e: Exception) {
                text = ""
            } finally {
                latch.countDown()
            }
        }

        latch.await()

        return JSONObject().apply {
            put("success", true)
            put("text", text)
        }
    }

    fun setClipboard(params: JSONObject): JSONObject {
        val clipText = params.optString("text", "")
        val latch = CountDownLatch(1)

        Handler(Looper.getMainLooper()).post {
            try {
                val cm = App.instance.getSystemService(Context.CLIPBOARD_SERVICE) as ClipboardManager
                val clip = ClipData.newPlainText("mcp_clipboard", clipText)
                cm.setPrimaryClip(clip)
            } catch (_: Exception) {
            } finally {
                latch.countDown()
            }
        }

        latch.await()

        return JSONObject().apply {
            put("success", true)
        }
    }

    fun listNotifications(): JSONObject {
        val result = ShizukuHelper.exec("dumpsys notification --noredact 2>/dev/null | grep 'NotificationRecord' || dumpsys notification 2>/dev/null | grep 'NotificationRecord'")

        val notifications = JSONArray()
        result.stdout.lines().forEach { line ->
            val pkgStart = line.indexOf("pkg=")
            if (pkgStart >= 0) {
                val pkgEnd = line.indexOf(" ", pkgStart)
                val pkg = if (pkgEnd > pkgStart) {
                    line.substring(pkgStart + 4, pkgEnd)
                } else {
                    line.substring(pkgStart + 4)
                }
                notifications.put(JSONObject().apply {
                    put("package", pkg)
                    put("raw", line.trim())
                })
            }
        }

        return JSONObject().apply {
            put("success", true)
            put("notifications", notifications)
            put("count", notifications.length())
        }
    }

    fun cancelNotification(params: JSONObject): JSONObject {
        val pkg = params.optString("package", "")
        if (pkg.isEmpty()) throw IllegalArgumentException("package required")

        val result = ShizukuHelper.exec("service call notification 5 s16 '$pkg' 2>/dev/null || service call notification 4 s16 '$pkg' 2>/dev/null")
        return JSONObject().apply {
            put("success", true)
            put("stdout", result.stdout)
            put("stderr", result.stderr)
        }
    }

    fun reboot(): JSONObject {
        val result = ShizukuHelper.exec("reboot")
        return JSONObject().apply {
            put("success", true)
            put("message", "Rebooting device")
        }
    }

    fun screenOn(): JSONObject {
        val checkResult = ShizukuHelper.exec("dumpsys power | grep 'mWakefulness'")
        val isAwake = checkResult.stdout.contains("Awake")
        if (isAwake) {
            return JSONObject().apply {
                put("success", true)
                put("message", "Screen already on")
            }
        }
        val result = ShizukuHelper.exec("input keyevent 224")
        return JSONObject().apply {
            put("success", result.isSuccess)
            if (!result.isSuccess) {
                put("error", result.stderr)
            }
        }
    }

    fun screenOff(): JSONObject {
        val checkResult = ShizukuHelper.exec("dumpsys power | grep 'mWakefulness'")
        val isAwake = checkResult.stdout.contains("Awake")
        if (!isAwake) {
            return JSONObject().apply {
                put("success", true)
                put("message", "Screen already off")
            }
        }
        val result = ShizukuHelper.exec("input keyevent 26")
        return JSONObject().apply {
            put("success", result.isSuccess)
            if (!result.isSuccess) {
                put("error", result.stderr)
            }
        }
    }
}
