# Aria Maid System — Android App Guide

This guide explains how to build an Android app that connects to the Aria voice agent using LiveKit.

## Overview

The Android app uses the [LiveKit Android SDK](https://github.com/livekit/client-sdk-android) to connect to your Aria agent running on the server. Users can talk to Aria and the maids through their phone.

## Prerequisites

- Android Studio (latest stable version)
- Android device or emulator (API 24+, Android 7.0+)
- LiveKit Cloud account (or self-hosted LiveKit server)
- Aria agent running and connected to LiveKit

## Quick Start

### Option 1: Using LiveKit CLI (Recommended)

```bash
# Install LiveKit CLI if not already installed
# macOS
brew install livekit-cli

# Windows (via scoop)
scoop install livekit-cli

# Create a Sandbox Token Server in LiveKit Cloud first
# https://cloud.livekit.io/projects/p_/sandbox/templates/token-server

# Clone and configure the app automatically
lk app create --template agent-starter-android --sandbox <your_sandbox_id>
```

### Option 2: Manual Setup

1. Clone the starter template:
```bash
git clone https://github.com/livekit-examples/agent-starter-android.git
cd agent-starter-android
```

2. Open in Android Studio

3. Configure your LiveKit connection (see Configuration section below)

4. Build and run on device/emulator

## Configuration

### TokenExt.kt

Edit `app/src/main/java/io/livekit/android/example/voiceassistant/TokenExt.kt`:

```kotlin
package io.livekit.android.example.voiceassistant

// Option 1: Use LiveKit Sandbox (easiest for testing)
const val sandboxID = "your-sandbox-id-here"

// Option 2: Use hardcoded URL and token (for development)
const val hardcodedUrl = "wss://your-project.livekit.cloud"
const val hardcodedToken = "your-jwt-token-here"
```

### Getting Your LiveKit Credentials

#### For LiveKit Cloud:

1. Go to [LiveKit Cloud](https://cloud.livekit.io)
2. Create or select a project
3. Go to **Settings > Keys** to get your API credentials
4. For testing, create a **Sandbox Token Server**:
   - Go to **Sandbox > Templates > Token Server**
   - Copy the Sandbox ID

#### For Self-Hosted LiveKit:

Use your LiveKit server URL and generate tokens using your API key/secret.

## Project Structure

```
agent-starter-android/
├── app/
│   ├── src/main/
│   │   ├── java/io/livekit/android/example/voiceassistant/
│   │   │   ├── MainActivity.kt          # App entry point
│   │   │   ├── TokenExt.kt              # LiveKit credentials
│   │   │   ├── Permissions.kt           # Audio permissions
│   │   │   ├── screen/
│   │   │   │   ├── ConnectScreen.kt     # Connection UI
│   │   │   │   └── VoiceAssistantScreen.kt  # Voice chat UI
│   │   │   ├── viewmodel/
│   │   │   │   └── VoiceAssistantViewModel.kt
│   │   │   └── ui/theme/                # App theming
│   │   ├── res/                         # Resources
│   │   └── AndroidManifest.xml
│   └── build.gradle.kts
├── gradle/
│   └── libs.versions.toml               # Dependencies
└── build.gradle.kts
```

## Key Dependencies

From `gradle/libs.versions.toml`:

```toml
[libraries]
livekit-lib = { group = "io.livekit", name = "livekit-android", version = "2.23.1" }
livekit-components = { group = "io.livekit", name = "livekit-android-compose-components", version = "2.1.1" }
```

## Required Permissions

The app needs microphone permission. Add to `AndroidManifest.xml`:

```xml
<uses-permission android:name="android.permission.RECORD_AUDIO" />
<uses-permission android:name="android.permission.INTERNET" />
```

## Customizing for Aria

### App Name and Branding

1. Update `app/src/main/res/values/strings.xml`:
```xml
<string name="app_name">Aria Maid</string>
```

2. Replace app icons in `app/src/main/res/mipmap-*/`

3. Update theme colors in `app/src/main/java/.../ui/theme/Color.kt`

### Custom UI

The main voice interface is in `VoiceAssistantScreen.kt`. You can customize:
- Audio visualizer appearance
- Button styles
- Transcript display
- Connection status indicators

## Building for Release

1. Create a signing key:
```bash
keytool -genkey -v -keystore aria-release.keystore -alias aria -keyalg RSA -keysize 2048 -validity 10000
```

2. Configure signing in `app/build.gradle.kts`:
```kotlin
android {
    signingConfigs {
        create("release") {
            storeFile = file("aria-release.keystore")
            storePassword = "your-store-password"
            keyAlias = "aria"
            keyPassword = "your-key-password"
        }
    }
    buildTypes {
        release {
            signingConfig = signingConfigs.getByName("release")
            isMinifyEnabled = true
            proguardFiles(...)
        }
    }
}
```

3. Build release APK:
```bash
./gradlew assembleRelease
```

Output: `app/build/outputs/apk/release/app-release.apk`

## Production Token Generation

For production, you need a backend server to generate tokens. Do NOT hardcode tokens in the app.

Example token server endpoint:
```
POST /api/livekit/token
Body: { "identity": "user-123", "room": "aria-room" }
Response: { "url": "wss://...", "token": "eyJ..." }
```

Update the app to fetch tokens from your server instead of using hardcoded values.

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "No agent found" | Make sure Aria agent is running and connected to LiveKit |
| Audio not working | Check microphone permissions in Android settings |
| Connection timeout | Verify LiveKit URL and token are correct |
| App crashes on start | Check logcat for errors, ensure API 24+ device |

## Testing with Aria

1. Start Aria agent on your server:
```bash
cd ~/friday_jarvis2
source .venv/bin/activate
python agent.py dev
```

2. Verify agent is connected (check logs for "registered worker")

3. Launch Android app and tap "START CALL"

4. Speak to Aria!

## Resources

- [LiveKit Android SDK](https://github.com/livekit/client-sdk-android)
- [LiveKit Agents Docs](https://docs.livekit.io/agents/overview/)
- [LiveKit Cloud](https://cloud.livekit.io)
- [Voice AI Quickstart](https://docs.livekit.io/agents/start/voice-ai/)

## Related Starters

- [iOS Starter](https://github.com/livekit-examples/agent-starter-swift)
- [Web Starter](https://github.com/livekit-examples/agent-starter-web)
- [Flutter Starter](https://github.com/livekit-examples/agent-starter-flutter)
