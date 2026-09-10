[app]
# (str) Title of your application
title = Instaling

# (str) Package name
package.name = instaling

# (str) Package domain (needed for android/ios packaging)
package.domain = org.kait65

# (str) Source files where the main.py lives
source.dir = .

# (list) Source files to include (let empty to include all the files)
source.include_exts = py,png,jpg,kv,atlas,json,csv

# (str) Application versioning (method 1)
version = 1.0

# (list) Application requirements
requirements = python3,kivy==2.3.0

# (str) Presplash filename
presplash.filename = %(source.dir)s/data/presplash.png

# (str) Icon filename
icon.filename = %(source.dir)s/data/icon.png

# (str) Supported orientation (one of 'landscape', 'portrait' or 'sensor')
orientation = portrait

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 0

# (list) List of allowed (x, y) tuples for the orientation
android.permissions = INTERNET

# (int) Target Android API, should be as high as possible.
android.api = 33

# (int) Minimum Android API, this is the minimum API your application will support.
android.minapi = 21

# (int) Android NDK version to use
android.ndk = 25b

# (int) Android SDK version to use
android.sdk = 33

# (str) Android arch to build for (choices: arm64-v8a, armeabi-v7a)
android.archs = arm64-v8a, armeabi-v7a

# (bool) Enables Android NDK's debug mode to build native code with debug symbols
android.debuggable = False

# (str) Python-for-android branch to use, defaults to master
p4a.branch = master

# (str) Python-for-android specific recipes to use
p4a.recipes =

# (str) Bootstrap to use for android builds
android.bootstrap = sdl2

# (str) Android entry point, default is 'main'
android.entrypoint = main

# (str) Android app theme, default is 'Theme_Main'
android.theme = Theme_Main

# (list) Android library project to add (will be added in the
# project.properties automatically.)
android.library_references =

# (str) Android logcat filters to use
android.logcat_filters = *:S Python:D

# (bool) Copy library instead of making a libpymodules.so
android.copy_libs = 1

# (str) The Android arch to build for, choices: arm64-v8a, armeabi-v7a
android.arch = arm64-v8a

[buildozer]
# (int) Log level (0 = error only, 1 = info, 2 = debug (with command output))
log_level = 2

# (int) Display warning if buildozer is run as root (0 = False, 1 = True)
warn_on_root = 1
