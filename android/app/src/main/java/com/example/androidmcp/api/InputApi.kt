package com.example.androidmcp.api

import com.example.androidmcp.util.ShizukuHelper
import org.json.JSONObject

class InputApi {

    fun tap(params: JSONObject): JSONObject {
        val x = params.optInt("x", -1)
        val y = params.optInt("y", -1)
        if (x < 0 || y < 0) throw IllegalArgumentException("x and y required")

        val result = ShizukuHelper.exec("input tap $x $y")
        return JSONObject().apply {
            put("success", result.isSuccess)
            put("stdout", result.stdout)
            put("stderr", result.stderr)
        }
    }

    fun longPress(params: JSONObject): JSONObject {
        val x = params.optInt("x", -1)
        val y = params.optInt("y", -1)
        val duration = params.optInt("duration", 1000)
        if (x < 0 || y < 0) throw IllegalArgumentException("x and y required")

        val result = ShizukuHelper.exec("input swipe $x $y $x $y $duration")
        return JSONObject().apply {
            put("success", result.isSuccess)
            put("stdout", result.stdout)
            put("stderr", result.stderr)
        }
    }

    fun swipe(params: JSONObject): JSONObject {
        val x1 = params.optInt("x1", -1)
        val y1 = params.optInt("y1", -1)
        val x2 = params.optInt("x2", -1)
        val y2 = params.optInt("y2", -1)
        val duration = params.optInt("duration", 300)
        if (x1 < 0 || y1 < 0 || x2 < 0 || y2 < 0) {
            throw IllegalArgumentException("x1, y1, x2, y2 required")
        }

        val result = ShizukuHelper.exec("input swipe $x1 $y1 $x2 $y2 $duration")
        return JSONObject().apply {
            put("success", result.isSuccess)
            put("stdout", result.stdout)
            put("stderr", result.stderr)
        }
    }

    fun drag(params: JSONObject): JSONObject {
        val x1 = params.optInt("x1", -1)
        val y1 = params.optInt("y1", -1)
        val x2 = params.optInt("x2", -1)
        val y2 = params.optInt("y2", -1)
        val duration = params.optInt("duration", 500)
        val steps = params.optInt("steps", 10)
        if (x1 < 0 || y1 < 0 || x2 < 0 || y2 < 0) {
            throw IllegalArgumentException("x1, y1, x2, y2 required")
        }

        val stepTime = duration / steps
        val dx = (x2 - x1).toFloat() / steps
        val dy = (y2 - y1).toFloat() / steps

        val cmds = buildString {
            var cx = x1.toFloat()
            var cy = y1.toFloat()
            for (i in 1..steps) {
                cx += dx
                cy += dy
                append("input swipe ${cx.toInt()} ${cy.toInt()} ${cx.toInt()} ${cy.toInt()} $stepTime")
                if (i < steps) append(" && ")
            }
        }

        val result = ShizukuHelper.exec(cmds)
        return JSONObject().apply {
            put("success", result.isSuccess)
            put("stdout", result.stdout)
            put("stderr", result.stderr)
        }
    }

    fun keyEvent(params: JSONObject): JSONObject {
        val keycode = params.optInt("keycode", -1)
        if (keycode < 0) {
            val key = params.optString("key", "")
            if (key.isNotEmpty()) {
                val result = ShizukuHelper.exec("input keyevent $key")
                return JSONObject().apply {
                    put("success", result.isSuccess)
                    put("stdout", result.stdout)
                    put("stderr", result.stderr)
                }
            }
            throw IllegalArgumentException("keycode or key required")
        }

        val longpress = params.optBoolean("longpress", false)
        val cmd = if (longpress) "input keyevent --longpress $keycode" else "input keyevent $keycode"
        val result = ShizukuHelper.exec(cmd)
        return JSONObject().apply {
            put("success", result.isSuccess)
            put("stdout", result.stdout)
            put("stderr", result.stderr)
        }
    }

    fun text(params: JSONObject): JSONObject {
        val text = params.optString("text", "")
        if (text.isEmpty()) throw IllegalArgumentException("text required")

        val escaped = text
            .replace("\\", "\\\\")
            .replace("\"", "\\\"")
            .replace("'", "\\'")
            .replace(" ", "%s")
            .replace("&", "\\&")
            .replace("<", "\\<")
            .replace(">", "\\>")
            .replace("|", "\\|")
            .replace(";", "\\;")
            .replace("$", "\\$")
            .replace("`", "\\`")
            .replace("(", "\\(")
            .replace(")", "\\)")

        val result = ShizukuHelper.exec("input text '$escaped'")
        return JSONObject().apply {
            put("success", result.isSuccess)
            put("stdout", result.stdout)
            put("stderr", result.stderr)
        }
    }
}
