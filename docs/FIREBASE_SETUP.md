# Firebase Cloud Messaging Setup Guide

**GoodPlay Backend - Push Notifications**

---

## Overview

This guide explains how to set up Firebase Cloud Messaging (FCM) for push notifications in the GoodPlay backend. FCM enables sending push notifications to both Android and iOS devices when users are offline.

---

## 1. Create Firebase Project

### Step 1: Go to Firebase Console
- Visit: https://console.firebase.google.com/
- Sign in with your Google account

### Step 2: Create New Project
1. Click **"Add project"**
2. Enter project name: `goodplay` (or your preferred name)
3. Enable Google Analytics (recommended)
4. Click **"Create project"**

---

## 2. Generate Service Account Key

### Step 1: Access Service Accounts
1. In Firebase Console, click **⚙️ Settings** (top-left)
2. Select **"Project settings"**
3. Go to **"Service accounts"** tab

### Step 2: Generate Private Key
1. Click **"Generate new private key"**
2. Confirm by clicking **"Generate key"**
3. A JSON file will be downloaded: `goodplay-xyz-firebase-adminsdk-xxxxx.json`

### Step 3: Store Securely
```bash
# On server, create secure directory
mkdir -p /etc/goodplay/secrets
chmod 700 /etc/goodplay/secrets

# Copy service account file
cp goodplay-xyz-firebase-adminsdk-xxxxx.json /etc/goodplay/secrets/firebase-admin.json
chmod 600 /etc/goodplay/secrets/firebase-admin.json

# Set ownership
chown goodplay-user:goodplay-user /etc/goodplay/secrets/firebase-admin.json
```

---

## 3. Enable Firebase Cloud Messaging API

### Step 1: Go to Google Cloud Console
1. In Firebase Console, click **"Project settings"**
2. Under **"Your apps"**, note the **Project ID** (e.g., `goodplay-xyz`)
3. Click on **"Cloud Console"** link to open Google Cloud Console

### Step 2: Enable FCM API
1. In Cloud Console, search for **"Firebase Cloud Messaging API"**
2. Click on the API
3. Click **"Enable"**

---

## 4. Configure Android App

### Step 1: Register Android App
1. In Firebase Console, go to **Project settings**
2. Under **"Your apps"**, click **Android icon**
3. Enter Android package name: `com.goodplay.app`
4. Enter app nickname: `GoodPlay Android`
5. Click **"Register app"**

### Step 2: Download google-services.json
1. Download `google-services.json`
2. Provide to Android frontend team
3. File should be placed in `android/app/google-services.json`

### Step 3: Add SHA-256 Certificate Fingerprint
```bash
# Generate debug fingerprint (for development)
keytool -list -v -keystore ~/.android/debug.keystore -alias androiddebugkey -storepass android -keypass android

# Copy SHA-256 fingerprint and add to Firebase Console
# Firebase Console > Project settings > Your apps > Android app > Add fingerprint
```

For production, repeat with release keystore:
```bash
keytool -list -v -keystore /path/to/release.keystore -alias release
```

---

## 5. Configure iOS App

### Step 1: Register iOS App
1. In Firebase Console, go to **Project settings**
2. Under **"Your apps"**, click **iOS icon**
3. Enter iOS bundle ID: `com.goodplay.app`
4. Enter app nickname: `GoodPlay iOS`
5. Click **"Register app"**

### Step 2: Download GoogleService-Info.plist
1. Download `GoogleService-Info.plist`
2. Provide to iOS frontend team
3. File should be added to Xcode project

### Step 3: Upload APNs Authentication Key
1. Go to Apple Developer Portal: https://developer.apple.com/account/
2. **Certificates, Identifiers & Profiles** > **Keys**
3. Create new key with **Apple Push Notifications service (APNs)** enabled
4. Download `.p8` file (e.g., `AuthKey_ABC123XYZ.p8`)
5. Note the **Key ID** and **Team ID**

### Step 4: Upload to Firebase
1. In Firebase Console: **Project settings** > **Cloud Messaging** tab
2. Under **"Apple app configuration"**, click **"Upload"**
3. Upload `.p8` file
4. Enter **Key ID** and **Team ID**
5. Click **"Upload"**

---

## 6. Configure Backend Environment

### Step 1: Set Environment Variables

Add to `.env` file:
```bash
# Firebase Cloud Messaging
FIREBASE_CREDENTIALS_PATH=/etc/goodplay/secrets/firebase-admin.json
FIREBASE_PROJECT_ID=goodplay-xyz

# Background Scheduler
SCHEDULER_ENABLED=true

# Notification System
NOTIFICATION_CLEANUP_DAYS=90
```

### Step 2: Verify File Permissions
```bash
# Check file exists and is readable
ls -la /etc/goodplay/secrets/firebase-admin.json

# Should show: -rw------- 1 goodplay-user goodplay-user
```

---

## 7. Test Push Notifications

### Step 1: Start Backend
```bash
python app.py
```

Check logs for Firebase initialization:
```
INFO:app:Firebase Cloud Messaging initialized successfully
INFO:app:Scheduler initialized with 5 tasks
```

### Step 2: Register Test Device
```bash
# Get FCM token from mobile app
# Then register via API:

curl -X POST http://localhost:5000/api/devices/register \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "device_token": "FCM_DEVICE_TOKEN_FROM_APP",
    "platform": "android",
    "device_info": {
      "model": "Pixel 5",
      "os_version": "Android 12",
      "app_version": "1.0.0"
    }
  }'
```

### Step 3: Send Test Notification
```bash
# Send invitation to trigger notification
curl -X POST http://localhost:5000/api/multiplayer/rooms/ROOM_ID/invitations \
  -H "Authorization: Bearer SENDER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "recipient_user_id": "TEST_USER_ID"
  }'
```

Check logs:
```
INFO:app:Push notification sent successfully
INFO:app:Notification sent to user USER_ID (type: invitation_received)
```

---

## 8. Production Deployment

### On Heroku

#### Step 1: Add Config Vars
```bash
heroku config:set FIREBASE_PROJECT_ID=goodplay-xyz
heroku config:set SCHEDULER_ENABLED=true
heroku config:set NOTIFICATION_CLEANUP_DAYS=90
```

#### Step 2: Upload Firebase Credentials
```bash
# Option 1: Base64 encode and store as env var
cat firebase-admin.json | base64 > firebase-admin.txt
heroku config:set FIREBASE_CREDENTIALS_BASE64="$(cat firebase-admin.txt)"

# Update code to decode base64 if using this approach
```

```bash
# Option 2: Upload as file (if supported by hosting)
heroku ps:copy firebase-admin.json /app/secrets/firebase-admin.json
heroku config:set FIREBASE_CREDENTIALS_PATH=/app/secrets/firebase-admin.json
```

### On AWS/Digital Ocean

#### Step 1: Upload Service Account File
```bash
scp firebase-admin.json user@server:/etc/goodplay/secrets/
```

#### Step 2: Set Permissions
```bash
ssh user@server
sudo chown goodplay:goodplay /etc/goodplay/secrets/firebase-admin.json
sudo chmod 600 /etc/goodplay/secrets/firebase-admin.json
```

#### Step 3: Update Environment Variables
Add to systemd service or Docker environment:
```bash
FIREBASE_CREDENTIALS_PATH=/etc/goodplay/secrets/firebase-admin.json
FIREBASE_PROJECT_ID=goodplay-xyz
SCHEDULER_ENABLED=true
```

---

## 9. Monitoring & Troubleshooting

### Check Firebase Console
1. Go to **Cloud Messaging** tab in Firebase Console
2. View delivery statistics
3. Monitor quota usage (free tier: 10 GB/month)

### Check Backend Logs
```bash
# Successful initialization
grep "Firebase Cloud Messaging initialized" logs/app.log

# Push notification delivery
grep "Push notification sent" logs/app.log

# Failed tokens
grep "Device token unregistered" logs/app.log
```

### Common Issues

#### Issue: "Firebase not initialized"
**Solution:**
- Check `FIREBASE_CREDENTIALS_PATH` is set correctly
- Verify file exists and is readable
- Check file permissions

#### Issue: "Invalid credentials"
**Solution:**
- Re-download service account JSON from Firebase Console
- Ensure JSON file is not corrupted
- Verify project ID matches

#### Issue: "Unregistered device token"
**Solution:**
- Token expired or invalid
- App was uninstalled
- Backend automatically deletes these tokens

#### Issue: "Quota exceeded"
**Solution:**
- Check Firebase Console for usage
- Consider upgrading to Blaze plan if needed
- Free tier allows 10 GB/month

---

## 10. Security Best Practices

### 1. Protect Service Account File
```bash
# Never commit to git
echo "firebase-admin.json" >> .gitignore

# Restrict permissions
chmod 600 firebase-admin.json

# Use secrets manager in production
# - AWS Secrets Manager
# - Google Secret Manager
# - HashiCorp Vault
```

### 2. Rotate Service Account Keys
- Rotate keys every 90 days
- Generate new key in Firebase Console
- Update production servers
- Delete old key

### 3. Monitor API Usage
- Set up billing alerts in Google Cloud Console
- Monitor quota usage regularly
- Review logs for unusual activity

### 4. Restrict API Access
- Use VPC/firewall rules to restrict access
- Only allow backend server IP addresses
- Use Cloud Armor for DDoS protection (production)

---

## 11. Testing Checklist

- [ ] Firebase project created
- [ ] Service account JSON downloaded and secured
- [ ] FCM API enabled in Google Cloud Console
- [ ] Android app registered with SHA-256 fingerprint
- [ ] iOS app registered with APNs key uploaded
- [ ] Backend environment variables configured
- [ ] Backend logs show Firebase initialization success
- [ ] Test device registered successfully
- [ ] Test notification sent and received on Android
- [ ] Test notification sent and received on iOS
- [ ] Scheduler tasks running successfully
- [ ] Expired tokens cleaned up automatically

---

## 12. Support & Resources

### Documentation
- Firebase Admin SDK: https://firebase.google.com/docs/admin/setup
- FCM Documentation: https://firebase.google.com/docs/cloud-messaging
- APNs Setup: https://firebase.google.com/docs/cloud-messaging/ios/certs

### Troubleshooting
- Firebase Status Dashboard: https://status.firebase.google.com/
- Stack Overflow: https://stackoverflow.com/questions/tagged/firebase-cloud-messaging
- GitHub Issues: https://github.com/firebase/firebase-admin-python/issues

### Quotas & Pricing
- Free Tier: 10 GB/month
- Blaze Plan: $0.12/GB after free tier
- Full pricing: https://firebase.google.com/pricing

---

## 🎉 Setup Complete!

Your Firebase Cloud Messaging is now configured and ready to send push notifications to GoodPlay users!

**Next Steps:**
1. Integrate FCM in mobile apps (see `FRONTEND_NOTIFICATION_GUIDE.md`)
2. Test end-to-end notification flow
3. Monitor delivery rates in Firebase Console
4. Set up billing alerts in Google Cloud Console
