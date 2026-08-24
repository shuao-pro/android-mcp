package com.example.androidmcp.api

import com.example.androidmcp.util.PrivilegeExecutor
import org.json.JSONObject

class ShellApi {

    fun exec(params: JSONObject): JSONObject {
        val command = params.optString("command", "")
        if (command.isEmpty()) {
            throw IllegalArgumentException("command is required")
        }

        val timeout = params.optInt("timeout", 30)
        val result = PrivilegeExecutor.exec(command)

        return JSONObject().apply {
            put("exitCode", result.exitCode)
            put("stdout", result.stdout)
            put("stderr", result.stderr)
            put("success", result.isSuccess)
        }
    }
}
