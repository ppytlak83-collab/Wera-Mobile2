[app]
title = Wera Mobile
package.name = weramobile
package.domain = org.inzynierpawel
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 3.1

# KLUCZOWE WYMAGANIA (Zgodnie z naszą architekturą)
requirements = python3,kivy==2.3.0,cryptography,openssl,requests,urllib3

orientation = portrait
fullscreen = 1
android.archs = arm64-v8a, armeabi-v7a
android.allow_backup = False

# Uprawnienia (Internet dla naszego łącza danych)
android.permissions = INTERNET

[buildozer]
log_level = 2
warn_on_root = 1
