package com.example.androidmcp.util

import android.content.Context
import android.content.SharedPreferences
import java.security.SecureRandom

/** Generates and persists the bridge auth token shared with the Python gateway. */
object TokenStore {

    private const val PREFS_NAME = "android_mcp_prefs"
    private const val KEY_TOKEN = "auth_token"

    private fun prefs(context: Context): SharedPreferences =
        context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)

    /** Return the current token, generating and persisting a random one if absent. */
    fun getOrCreate(context: Context): String {
        val p = prefs(context)
        val existing = p.getString(KEY_TOKEN, null)
        if (!existing.isNullOrBlank()) return existing
        val token = generateToken()
        p.edit().putString(KEY_TOKEN, token).apply()
        return token
    }

    /** Generate a fresh random token and persist it. */
    fun regenerate(context: Context): String {
        val token = generateToken()
        prefs(context).edit().putString(KEY_TOKEN, token).apply()
        return token
    }

    private fun generateToken(): String {
        val bytes = ByteArray(16)
        SecureRandom().nextBytes(bytes)
        return bytes.joinToString("") { "%02x".format(it) }
    }
}
