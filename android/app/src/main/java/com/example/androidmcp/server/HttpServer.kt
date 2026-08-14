package com.example.androidmcp.server

import android.util.Log
import org.json.JSONObject
import java.io.BufferedReader
import java.io.InputStreamReader
import java.io.OutputStreamWriter
import java.net.ServerSocket
import java.net.Socket
import java.util.concurrent.Executors

class HttpServer(
    private val port: Int = 18080,
    private val router: Router,
    private val authToken: String = "",
    private val maxBodySize: Int = 10 * 1024 * 1024  // 10MB limit
) {
    private val tag = "HttpServer"
    private var serverSocket: ServerSocket? = null
    private val threadPool = Executors.newFixedThreadPool(8)
    private val maxConnections = 50
    private val activeConnections = java.util.concurrent.atomic.AtomicInteger(0)
    private var running = false

    val isRunning: Boolean get() = running

    fun start() {
        if (running) return
        running = true

        Thread {
            try {
                serverSocket = ServerSocket(port)
                Log.i(tag, "HTTP Server started on port $port")

                while (running) {
                    try {
                        val client = serverSocket?.accept() ?: break
                        threadPool.execute { handleClient(client) }
                    } catch (e: Exception) {
                        if (running) {
                            Log.e(tag, "Accept error: ${e.message}")
                        }
                    }
                }
            } catch (e: Exception) {
                Log.e(tag, "Server error: ${e.message}")
                running = false
            }
        }.start()
    }

    fun stop() {
        running = false
        try {
            serverSocket?.close()
        } catch (_: Exception) {}
        serverSocket = null
        threadPool.shutdownNow()
        Log.i(tag, "HTTP Server stopped")
    }

    private fun handleClient(socket: Socket) {
        if (activeConnections.incrementAndGet() > maxConnections) {
            activeConnections.decrementAndGet()
            try { socket.close() } catch (_: Exception) {}
            Log.w(tag, "Connection rejected: max connections ($maxConnections) reached")
            return
        }
        try {
            socket.use { client ->
                client.soTimeout = 30000
                val reader = BufferedReader(InputStreamReader(client.getInputStream()))
                val writer = OutputStreamWriter(client.getOutputStream())

                val requestLine = reader.readLine() ?: return
                val parts = requestLine.split(" ")
                if (parts.size < 2) return

                val method = parts[0]
                val path = parts[1]

                val headers = mutableMapOf<String, String>()
                var line = reader.readLine()
                while (!line.isNullOrEmpty()) {
                    val colonIndex = line.indexOf(':')
                    if (colonIndex > 0) {
                        val key = line.substring(0, colonIndex).trim().lowercase()
                        val value = line.substring(colonIndex + 1).trim()
                        headers[key] = value
                    }
                    line = reader.readLine()
                }

                var body = ""
                if (method == "POST" && headers.containsKey("content-length")) {
                    val contentLength = headers["content-length"]?.toIntOrNull() ?: 0
                    if (contentLength > maxBodySize) {
                        val errorResponse = JSONObject().apply {
                            put("jsonrpc", "2.0")
                            put("error", JSONObject().apply {
                                put("code", -32000)
                                put("message", "Request body too large: $contentLength bytes (max $maxBodySize)")
                            })
                            put("id", null)
                        }
                        writer.write(buildHttpResponse(errorResponse.toString()))
                        writer.flush()
                        return
                    }
                    if (contentLength > 0) {
                        val charBuffer = CharArray(contentLength)
                        reader.read(charBuffer, 0, contentLength)
                        body = String(charBuffer)
                    }
                }

                val requestJson = if (body.isNotEmpty()) {
                    try {
                        JSONObject(body)
                    } catch (_: Exception) {
                        null
                    }
                } else {
                    null
                }

                // CORS preflight
                if (method == "OPTIONS") {
                    val preflightResponse = buildString {
                        append("HTTP/1.1 204 No Content\r\n")
                        append("Access-Control-Allow-Origin: *\r\n")
                        append("Access-Control-Allow-Methods: GET, POST, OPTIONS\r\n")
                        append("Access-Control-Allow-Headers: Content-Type, Authorization\r\n")
                        append("Access-Control-Max-Age: 86400\r\n")
                        append("Connection: close\r\n")
                        append("\r\n")
                    }
                    writer.write(preflightResponse)
                    writer.flush()
                    return
                }

                // Auth check: when a token is configured, require the X-MCP-Token header.
                if (authToken.isNotBlank() && !isAuthorized(headers)) {
                    val errorResponse = JSONObject().apply {
                        put("jsonrpc", "2.0")
                        put("error", JSONObject().apply {
                            put("code", -32001)
                            put("message", "Unauthorized: missing or invalid X-MCP-Token")
                        })
                        put("id", null)
                    }
                    writer.write(buildHttpResponse(errorResponse.toString(), 401))
                    writer.flush()
                    return
                }

                val responseJson = if (path == "/mcp" && requestJson != null) {
                    router.handle(requestJson)
                } else if (path == "/health") {
                    JSONObject().apply {
                        put("result", "ok")
                        put("connected", true)
                        put("shizuku_running", true)
                    }
                } else {
                    JSONObject().apply {
                        put("jsonrpc", "2.0")
                        put("error", JSONObject().apply {
                            put("code", -32601)
                            put("message", "Method not found: $method $path")
                        })
                        put("id", requestJson?.opt("id"))
                    }
                }

                writer.write(buildHttpResponse(responseJson.toString()))
                writer.flush()
            }
        } catch (e: Exception) {
            Log.e(tag, "Client handler error: ${e.message}")
        } finally {
            activeConnections.decrementAndGet()
        }
    }

    private fun isAuthorized(headers: Map<String, String>): Boolean =
        headers["x-mcp-token"] == authToken

    private fun buildHttpResponse(body: String, statusCode: Int = 200): String {
        val statusText = when (statusCode) {
            200 -> "OK"
            204 -> "No Content"
            400 -> "Bad Request"
            401 -> "Unauthorized"
            413 -> "Payload Too Large"
            500 -> "Internal Server Error"
            else -> "OK"
        }
        return buildString {
            append("HTTP/1.1 $statusCode $statusText\r\n")
            append("Content-Type: application/json\r\n")
            append("Content-Length: ${body.toByteArray().size}\r\n")
            append("Connection: close\r\n")
            append("Access-Control-Allow-Origin: *\r\n")
            append("\r\n")
            append(body)
        }
    }
}
