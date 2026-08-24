package com.example.androidmcp

import android.app.Application
import android.util.Log
import com.example.androidmcp.util.PrivilegeExecutor
import com.example.androidmcp.util.ShizukuHelper
import rikka.shizuku.Shizuku

class App : Application() {

    companion object {
        lateinit var instance: App
            private set
    }

    override fun onCreate() {
        super.onCreate()
        instance = this

        PrivilegeExecutor.init(this)

        try {
            Shizuku.addRequestPermissionResultListener { requestCode, grantResult ->
                Log.i("App", "Shizuku permission result: code=$requestCode grant=$grantResult")
                if (grantResult == android.content.pm.PackageManager.PERMISSION_GRANTED) {
                    PrivilegeExecutor.checkStatus()
                }
            }

            Shizuku.addBinderReceivedListener {
                Log.i("App", "Shizuku binder received")
                PrivilegeExecutor.checkStatus()
            }

            Shizuku.addBinderDeadListener {
                Log.w("App", "Shizuku binder dead")
                ShizukuHelper.resetStatus()
                PrivilegeExecutor.checkStatus()
            }
        } catch (e: Exception) {
            Log.w("App", "Shizuku init failed: ${e.message}", e)
        }
    }

    override fun onTerminate() {
        super.onTerminate()
    }
}