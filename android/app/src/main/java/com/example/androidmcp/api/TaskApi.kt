package com.example.androidmcp.api

import com.example.androidmcp.util.TaskManager
import org.json.JSONArray
import org.json.JSONObject

/**
 * JSON-RPC API for long-running background tasks.
 *
 * submit/status are instant (milliseconds) so they never hit the HTTP 30s
 * timeout; the actual command runs on TaskManager's background thread pool.
 */
class TaskApi {

    fun submit(params: JSONObject): JSONObject {
        val command = params.optString("command", "")
        if (command.isEmpty()) throw IllegalArgumentException("command required")
        val timeout = params.optLong("timeout", 0L) // milliseconds; 0 = unlimited
        val t = TaskManager.submit(command, timeout)
        return JSONObject().apply {
            put("success", true)
            put("task_id", t.id)
            put("state", t.state.name)
        }
    }

    fun status(params: JSONObject): JSONObject {
        val id = params.optString("task_id", "")
        if (id.isEmpty()) throw IllegalArgumentException("task_id required")
        val t = TaskManager.get(id)
            ?: return JSONObject().apply {
                put("success", false)
                put("error", "task not found: $id")
            }

        return JSONObject().apply {
            put("success", true)
            put("task_id", t.id)
            put("state", t.state.name)
            if (t.exitCode == null) put("exit_code", JSONObject.NULL) else put("exit_code", t.exitCode)
            put("stdout_tail", t.stdout.takeLast(4096))
            put("stderr_tail", t.stderr.takeLast(4096))
            put("started_at", t.startedAt)
            if (t.finishedAt == null) put("finished_at", JSONObject.NULL) else put("finished_at", t.finishedAt)
        }
    }

    fun result(params: JSONObject): JSONObject {
        val id = params.optString("task_id", "")
        if (id.isEmpty()) throw IllegalArgumentException("task_id required")
        val t = TaskManager.get(id)
            ?: return JSONObject().apply {
                put("success", false)
                put("error", "task not found: $id")
            }

        return JSONObject().apply {
            put("success", true)
            put("task_id", t.id)
            put("state", t.state.name)
            if (t.exitCode == null) put("exit_code", JSONObject.NULL) else put("exit_code", t.exitCode)
            put("stdout", t.stdout)
            put("stderr", t.stderr)
            put("started_at", t.startedAt)
            if (t.finishedAt == null) put("finished_at", JSONObject.NULL) else put("finished_at", t.finishedAt)
        }
    }

    fun cancel(params: JSONObject): JSONObject {
        val id = params.optString("task_id", "")
        if (id.isEmpty()) throw IllegalArgumentException("task_id required")
        val ok = TaskManager.cancel(id)
        val state = TaskManager.get(id)?.state?.name ?: "UNKNOWN"
        return JSONObject().apply {
            put("success", ok)
            put("task_id", id)
            put("state", state)
        }
    }

    fun list(params: JSONObject): JSONObject {
        val arr = JSONArray()
        for (t in TaskManager.list()) {
            arr.put(JSONObject().apply {
                put("task_id", t.id)
                put("state", t.state.name)
                put("command", t.command)
                put("started_at", t.startedAt)
            })
        }
        return JSONObject().apply {
            put("success", true)
            put("tasks", arr)
            put("count", arr.length())
        }
    }
}