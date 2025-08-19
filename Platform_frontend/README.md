# Vue + Vite + Capacitor Cross-Platform App

A proof of concept cross-platform application built with Vue 3, Vite, Ionic, and Capacitor that runs on web, Android, and iOS platforms.

## 🚀 Features

- **Cross-Platform**: Single codebase for web, Android, and iOS
- **Vue 3**: Modern Vue with Composition API and `<script setup>` syntax
- **Vite**: Lightning-fast development server and build tool
- **Ionic Vue**: Beautiful, cross-platform UI components
- **Capacitor**: Native device capabilities and platform integration
- **Platform Detection**: Automatic platform-specific feature detection
- **Native Features**: Haptic feedback, alerts, toasts, and more

## 🛠️ Technology Stack

- **Frontend**: Vue 3 + Vite
- **UI Framework**: Ionic Vue
- **Mobile Runtime**: Capacitor
- **Icons**: Ionicons
- **Routing**: Vue Router with Ionic integration

## 📦 Installation

```bash
# Install dependencies
npm install

# Start development server (web)
npm run dev

# Build for web
npm run build
```

## 📱 Mobile Development

### Android
```bash
# Build and sync for Android
npm run build:android

# Open in Android Studio
npm run open:android

# Run on Android device/emulator
npm run run:android
```

### iOS
```bash
# Build and sync for iOS
npm run build:ios

# Open in Xcode
npm run open:ios

# Run on iOS device/simulator
npm run run:ios
```

## 🌐 Available Scripts

- `npm run dev` - Start development server for web
- `npm run build` - Build for production (web)
- `npm run preview` - Preview production build
- `npm run build:android` - Build and sync for Android
- `npm run build:ios` - Build and sync for iOS
- `npm run open:android` - Open Android project in Android Studio
- `npm run open:ios` - Open iOS project in Xcode
- `npm run sync` - Sync web assets to native platforms

## 📖 Project Structure

```
src/
├── components/
│   ├── Home.vue          # Main home page with platform demo
│   └── About.vue         # About page with tech stack info
├── App.vue               # Root Ionic app component
└── main.js               # App entry point with Ionic setup
```

## 🎯 Demo Features

The app demonstrates:

1. **Platform Detection** - Shows current platform (web/mobile/desktop)
2. **Native Alerts** - Cross-platform alert dialogs
3. **Toast Notifications** - Native toast messages
4. **Haptic Feedback** - Device vibration (mobile only)
5. **Navigation** - Multi-page routing
6. **Responsive Design** - Adapts to different screen sizes

## 🔧 Development Requirements

- **Node.js** 16+ 
- **npm** or **yarn**
- **Android Studio** (for Android development)
- **Xcode** (for iOS development, macOS only)

## 📝 Notes

- Web version runs in any modern browser
- Android requires Android Studio and Android SDK
- iOS requires Xcode and is only available on macOS
- All platforms share the same Vue.js codebase
- Native features gracefully degrade on web platform

## 🤝 Contributing

This is a proof of concept project. Feel free to explore and extend it with additional Capacitor plugins and native features!
