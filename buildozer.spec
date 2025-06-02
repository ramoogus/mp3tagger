
[app]

title = MP3Tagger
package.name = mp3tagger
package.domain = org.example
source.include_exts = py,png,jpg,kv,atlas

# Your main.py file
source.main = main.py

version = 0.1
requirements = python3,kivy,mutagen,requests
orientation = portrait
android.api = 33
android.minapi = 21
android.sdk = 33
android.ndk = 25b
android.arch = armeabi-v7a

# Permissions to access storage and internet
android.permissions = INTERNET, READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE, MANAGE_EXTERNAL_STORAGE

# This lets you access storage on Android 11+ using scoped storage APIs
android.manifest_xml =

# (Optional) Enable for debug
#log_level = 2
