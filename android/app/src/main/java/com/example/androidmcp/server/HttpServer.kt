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
    private val router: Router
) {
    private val tag = "HttpServer"
    private var serverSocket: ServerSocket? = null
    private val threadPool = Executors.newFixedThreadPool(8)
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

                val responseJson = if (path == "/mcp" && requestJson != null) {
                    router.handle(requestJson)
                } else if (path == "/health") {
                    JSONObject().apply {
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

                val responseBody = responseJson.toString()
                val httpResponse = buildString {
                    append("HTTP/1.1 200 OK\r\n")
                    append("Content-Type: application/json\r\n")
                    append("Content-Length: ${responseBody.toByteArray().size}\r\n")
                    append("Connection: close\r\n")
                    append("Access-Control-Allow-Origin: *\r\n")
                    append("\r\n")
                    append(responseBody)
                }

                writer.write(httpResponse)
                writer.flush()
            }
        } catch (e: Exception) {
            Log.e(tag, "Client handler error: ${e.message}")
        }
    }
}
