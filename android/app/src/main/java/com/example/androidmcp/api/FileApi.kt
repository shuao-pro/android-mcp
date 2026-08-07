package com.example.androidmcp.api

import android.util.Base64
import com.example.androidmcp.util.ShizukuHelper
import org.json.JSONArray
import org.json.JSONObject

class FileApi {

    fun read(params: JSONObject): JSONObject {
        val path = params.optString("path", "")
        if (path.isEmpty()) throw IllegalArgumentException("path required")

        val result = ShizukuHelper.exec("cat '$path'")

        return JSONObject().apply {
            put("success", result.isSuccess)
            put("content", result.stdout)
            if (!result.isSuccess) {
                put("error", result.stderr)
            }
        }
    }

    fun write(params: JSONObject): JSONObject {
        val path = params.optString("path", "")
        val content = params.optString("content", "")
        val append = params.optBoolean("append", false)
        val base64 = params.optBoolean("base64", false)

        if (path.isEmpty()) throw IllegalArgumentException("path required")
        if (content.isEmpty()) throw IllegalArgumentException("content required")

        // Decode content (may be plain text or base64)
        val decodedBytes = if (base64) {
            try {
                Base64.decode(content, Base64.DEFAULT)
            } catch (e: Exception) {
                throw IllegalArgumentException("Invalid base64 content")
            }
        } else {
            content.toByteArray(Charsets.UTF_8)
        }

        // Write via base64 to avoid shell escaping issues
        val b64 = Base64.encodeToString(decodedBytes, Base64.NO_WRAP)
        val tmpPath = "/data/local/tmp/mcp_filewrite_${System.currentTimeMillis()}.tmp"
        ShizukuHelper.exec("echo $b64 | base64 -d > $tmpPath 2>/dev/null")

        val redirect = if (append) ">>" else ">"
        val result = ShizukuHelper.exec("cat $tmpPath $redirect '$path'")
        ShizukuHelper.exec("rm -f $tmpPath")

        return JSONObject().apply {
            put("success", result.isSuccess)
            if (!result.isSuccess) {
                put("error", result.stderr)
            }
        }
    }

    fun list(params: JSONObject): JSONObject {
        val path = params.optString("path", "/sdcard")
        if (path.isEmpty()) throw IllegalArgumentException("path required")

        val result = ShizukuHelper.exec("ls -la '$path'")

        val files = JSONArray()
        result.stdout.lines().forEach { line ->
            if (line.startsWith("total ") || line.isBlank()) return@forEach
            val parts = line.trim().split("\\s+".toRegex())
            if (parts.size >= 6) {
                val isDir = parts[0].startsWith("d") || parts[0].startsWith("l")
                val nameStart = if (parts.size >= 9) 8
                    else if (parts[0].contains("+")) 7
                    else 7
                files.put(JSONObject().apply {
                    put("permissions", parts[0])
                    put("owner", parts[2])
                    put("group", parts[3])
                    put("size", parts[4])
                    put("name", parts.drop(nameStart).joinToString(" "))
                    put("is_directory", isDir)
                })
            }
        }

        return JSONObject().apply {
            put("success", result.isSuccess)
            put("path", path)
            put("files", files)
            put("count", files.length())
            if (!result.isSuccess) {
                put("error", result.stderr)
            }
        }
    }

    fun stat(params: JSONObject): JSONObject {
        val path = params.optString("path", "")
        if (path.isEmpty()) throw IllegalArgumentException("path required")

        val result = ShizukuHelper.exec("stat -c '%n|%s|%a|%U|%G|%Y|%F' '$path'")

        return if (result.isSuccess && result.stdout.isNotBlank()) {
            val parts = result.stdout.split("|")
            JSONObject().apply {
                put("success", true)
                put("name", parts.getOrElse(0) { "" })
                put("size", parts.getOrElse(1) { "0" }.toLongOrNull() ?: 0L)
                put("permissions", parts.getOrElse(2) { "" })
                put("owner", parts.getOrElse(3) { "" })
                put("group", parts.getOrElse(4) { "" })
                put("mtime", parts.getOrElse(5) { "0" }.toLongOrNull() ?: 0L)
                put("type", parts.getOrElse(6) { "" })
            }
        } else {
            JSONObject().apply {
                put("success", false)
                put("error", result.stderr)
            }
        }
    }

    fun delete(params: JSONObject): JSONObject {
        val path = params.optString("path", "")
        val recursive = params.optBoolean("recursive", false)

        if (path.isEmpty()) throw IllegalArgumentException("path required")
        // Prevent dangerous recursive deletions
        if (recursive && (path == "/" || path == "/data" || path == "/system" || path == "/sdcard")) {
            throw IllegalArgumentException("Refusing to recursively delete root-level path: $path")
        }

        val cmd = if (recursive) "rm -rf '$path'" else "rm -f '$path'"
        val result = ShizukuHelper.exec(cmd)

        return JSONObject().apply {
            put("success", result.isSuccess)
            if (!result.isSuccess) {
                put("error", result.stderr)
            }
        }
    }
}
