# Sabbak APK builder 📱
Workflow: Actions → "Build APK" → Run workflow → url + app name (+ icon url).
Result: public Release `apk-<id>` with `app.apk`, plus an Artifact.
Optional secrets for a permanent signing key: KEYSTORE_BASE64, KEYSTORE_PASSWORD (alias must be `sabbak`, key password = store password).
# sabbak-apk
