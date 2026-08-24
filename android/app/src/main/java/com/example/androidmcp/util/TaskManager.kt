package com.example.androidmcp.util

import android.util.Log
import java.util.UUID
import java.util.concurrent.ConcurrentHashMap
import java.util.concurrent.Executors
import java.util.concurrent.Semaphore

/**
 * Long-running command task manager.
 *
 * Turns the blocking "execute shell command" model into an asynchronous
 * "submit → poll → collect result" model so a single command is no longer
 * bounded by the HTTP 30s timeout. Commands run on a dedicated background
 * thread pool via [PrivilegeExecutor.exec] (root/su or Shizuku).
 */
object TaskManager {

    private const val TAG = "MCP_Task"

    /** In-memory output cap per task (older output is truncated). */
    private const val MAX_OUTPUT = 256 * 1024

    /** Concurrency limit — never starve the HTTP server's own thread pool. */
    private const val MAX_CONCURRENT = 10

    /** Upper bound on retained tasks (finished tasks are evicted first). */
    private const val MAX_TASKS = 200

    /** Finished tasks are evicted after this TTL. */
    private const val TTL_MS = 60 * 60 * 1000L

    enum class State { QUEUED, RUNNING, DONE, ERROR, TIMEOUT, CANCELLED }

    data class Task(
        val id: String,
        val command: String,
        @Volatile var state: State = State.QUEUED,
        @Volatile var exitCode: Int? = null,
        @Volatile var stdout: String = "",
        @Volatile var stderr: String = "",
        val startedAt: Long = System.currentTimeMillis(),
        @Volatile var finishedAt: Long? = null,
        @Volatile var process: Process? = null
    )

    private val tasks = ConcurrentHashMap<String, Task>()
    private val pool = Executors.newCachedThreadPool { r ->
        Thread(r, "mcp-task").apply { isDaemon = true }
    }
    private val semaphore = Semaphore(MAX_CONCURRENT)

    fun submit(command: String, timeoutMs: Long): Task {
        val task = Task(UUID.randomUUID().toString().substring(0, 8), command)
        tasks[task.id] = task

        pool.execute {
            semaphore.acquire()
            try {
                task.state = State.RUNNING
                val r = PrivilegeExecutor.exec(command, timeoutMs) { p -> task.process = p }
                task.exitCode = r.exitCode
                task.stdout = r.stdout.take(MAX_OUTPUT)
                task.stderr = r.stderr.take(MAX_OUTPUT)

                task.state = if (task.state == State.CANCELLED) {
                    State.CANCELLED
                } else when {
                    r.timedOut -> State.TIMEOUT
                    r.isSuccess -> State.DONE
                    else -> State.ERROR
                }
            } catch (e: Exception) {
                if (task.state != State.CANCELLED) {
                    task.state = State.ERROR
                    task.stderr = (e.message ?: "unknown").take(MAX_OUTPUT)
                }
            } finally {
                task.finishedAt = System.currentTimeMillis()
                if (task.state == State.RUNNING) task.state = State.DONE
                task.process = null
                semaphore.release()
            }
        }

        cleanup()
        return task
    }

    fun get(id: String): Task? = tasks[id]

    fun cancel(id: String): Boolean {
        val task = tasks[id] ?: return false
        if (task.state == State.DONE || task.state == State.ERROR ||
            task.state == State.TIMEOUT || task.state == State.CANCELLED
        ) {
            return false
        }
        task.state = State.CANCELLED
        try {
            task.process?.destroyForcibly()
        } catch (_: Exception) {
        }
        return true
    }

    fun list(): List<Task> = tasks.values.toList()

    /** Evict finished tasks past their TTL and cap total task count. */
    private fun cleanup() {
        val now = System.currentTimeMillis()
        val iter = tasks.entries.iterator()
        while (iter.hasNext()) {
            val t = iter.next().value
            val done = t.state == State.DONE || t.state == State.ERROR ||
                t.state == State.TIMEOUT || t.state == State.CANCELLED
            if (done && t.finishedAt != null && now - t.finishedAt!! > TTL_MS) {
                iter.remove()
            }
        }
        if (tasks.size > MAX_TASKS) {
            val finished = tasks.values
                .filter { it.finishedAt != null }
                .sortedBy { it.finishedAt }
            val overflow = tasks.size - MAX_TASKS
            for (t in finished.take(overflow)) {
                tasks.remove(t.id)
            }
        }
    }

    fun taskCount(): Int = tasks.size
}