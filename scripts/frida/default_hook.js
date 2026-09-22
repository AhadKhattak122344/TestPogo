// Default Frida hook script for Pokémon GO analysis
// This script hooks common functions to detect injection points

Java.perform(function() {
    console.log("[*] Starting Pokémon GO analysis script");
    
    // Hook Activity.onCreate to detect app launch
    try {
        var Activity = Java.use("android.app.Activity");
        Activity.onCreate.overload("android.os.Bundle").implementation = function(bundle) {
            console.log("[+] Activity.onCreate called: " + this.getClass().getName());
            return this.onCreate(bundle);
        };
    } catch (e) {
        console.log("[-] Could not hook Activity.onCreate: " + e);
    }
    
    // Try to hook Niantic-specific classes
    try {
        var NianticManager = Java.use("com.nianticlabs.nia.manager.NianticManager");
        console.log("[+] Found NianticManager class");
        
        NianticManager.init.implementation = function() {
            console.log("[+] NianticManager.init called");
            return this.init();
        };
    } catch (e) {
        console.log("[-] NianticManager not found or hook failed: " + e);
    }
    
    // Hook location services
    try {
        var LocationManager = Java.use("android.location.LocationManager");
        console.log("[+] Found LocationManager");
        
        LocationManager.getLastKnownLocation.overload("java.lang.String").implementation = function(provider) {
            console.log("[+] getLastKnownLocation called with provider: " + provider);
            var result = this.getLastKnownLocation(provider);
            if (result) {
                console.log("[+] Location: lat=" + result.getLatitude() + ", lng=" + result.getLongitude());
            }
            return result;
        };
    } catch (e) {
        console.log("[-] LocationManager hook failed: " + e);
    }
    
    // Hook Unity player if present
    try {
        var UnityPlayer = Java.use("com.unity3d.player.UnityPlayer");
        console.log("[+] Found UnityPlayer");
        
        UnityPlayer.$init.implementation = function(context) {
            console.log("[+] UnityPlayer initialized");
            return this.$init(context);
        };
    } catch (e) {
        console.log("[-] UnityPlayer not found: " + e);
    }
    
    // Detect SSL pinning implementations
    try {
        var OkHttpClient = Java.use("okhttp3.OkHttpClient");
        console.log("[+] Found OkHttpClient - potential SSL pinning target");
    } catch (e) {
        console.log("[-] OkHttpClient not found: " + e);
    }
    
    console.log("[*] Script initialization complete");
});

// Native function hooks (for IL2CPP/Unity)
Interceptor.attach(Module.findExportByName(null, "JNI_OnLoad"), {
    onEnter: function(args) {
        console.log("[*] JNI_OnLoad called");
    },
    onLeave: function(retval) {
        console.log("[*] JNI_OnLoad returned: " + retval);
    }
});

// Log native method registration
try {
    var jniRegisterNativeMethods = Module.findExportByName("libart.so", "_ZN3art3jni16RegisterNativeMethodsEP7_JNIEnvPK7_JClassPK15JNINativeMethodibb");
    if (jniRegisterNativeMethods) {
        Interceptor.attach(jniRegisterNativeMethods, {
            onEnter: function(args) {
                console.log("[*] RegisterNativeMethods called");
            }
        });
    }
} catch (e) {
    console.log("[-] Could not find RegisterNativeMethods: " + e);
}

console.log("[*] All hooks installed");
