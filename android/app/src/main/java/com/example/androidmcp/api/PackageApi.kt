package com.example.androidmcp.api

import com.example.androidmcp.util.ShizukuHelper
import org.json.JSONArray
import org.json.JSONObject

class PackageApi {

    fun install(params: JSONObject): JSONObject {
        val apkPath = params.optString("apk_path", "")
        if (apkPath.isEmpty()) throw IllegalArgumentException("apk_path required")

        val allowDowngrade = params.optBoolean("allow_downgrade", false)
        val cmd = buildString {
            append("pm install")
            if (allowDowngrade) append(" -d")
            append(" -r '$apkPath'")
        }

        val result = ShizukuHelper.exec(cmd)
        return JSONObject().apply {
            put("success", result.isSuccess)
            put("stdout", result.stdout)
            put("stderr", result.stderr)
        }
    }

    fun uninstall(params: JSONObject): JSONObject {
        val packageName = params.optString("package", "")
        if (packageName.isEmpty()) throw IllegalArgumentException("package required")

        val keepData = params.optBoolean("keep_data", false)
        val cmd = buildString {
            append("pm uninstall")
            if (keepData) append(" -k")
            append(" $packageName")
        }

        val result = ShizukuHelper.exec(cmd)
        return JSONObject().apply {
            put("success", result.isSuccess)
            put("stdout", result.stdout)
            put("stderr", result.stderr)
        }
    }

    fun open(params: JSONObject): JSONObject {
        val packageName = params.optString("package", "")
        val activity = params.optString("activity", "")

        val cmd = if (activity.isNotEmpty()) {
            val result = ShizukuHelper.exec("am start -n $packageName/$activity")
            result
        } else {
            val result = ShizukuHelper.exec("monkey -p $packageName -c android.intent.category.LAUNCHER 1")
            result
        }

        return JSONObject().apply {
            put("success", cmd.isSuccess)
            put("stdout", cmd.stdout)
            put("stderr", cmd.stderr)
        }
    }

    fun close(params: JSONObject): JSONObject {
        val packageName = params.optString("package", "")
        if (packageName.isEmpty()) throw IllegalArgumentException("package required")

        val result = ShizukuHelper.exec("am force-stop $packageName")
        return JSONObject().apply {
            put("success", result.isSuccess)
            put("stdout", result.stdout)
            put("stderr", result.stderr)
        }
    }

    fun clearData(params: JSONObject): JSONObject {
        val packageName = params.optString("package", "")
        if (packageName.isEmpty()) throw IllegalArgumentException("package required")

        val result = ShizukuHelper.exec("pm clear $packageName")
        return JSONObject().apply {
            put("success", result.isSuccess)
            put("stdout", result.stdout)
            put("stderr", result.stderr)
        }
    }

    fun list(params: JSONObject): JSONObject {
        val filter = params.optString("filter", "")
        val includeSystem = params.optBoolean("include_system", false)

        val cmd = if (includeSystem) "pm list packages" else "pm list packages -3"
        val result = ShizukuHelper.exec(cmd)

        val packages = JSONArray()
        result.stdout.lines().forEach { line ->
            val pkg = line.removePrefix("package:")
            if (pkg.isNotBlank() && (filter.isEmpty() || pkg.contains(filter, ignoreCase = true))) {
                packages.put(pkg)
            }
        }

        return JSONObject().apply {
            put("packages", packages)
            put("count", packages.length())
            put("success", true)
        }
    }
}
