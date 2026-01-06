# 🎣 Fisch Streak Monitor

A desktop application for monitoring and tracking streaks in the **Fisch** Roblox game. The app automatically detects the orange streak number above your character and sends screenshots to Discord when the streak changes a specified number of times.

## ✨ Features

- **🎯 Streak Detection** - Automatically detects and tracks the orange streak number above your character
- **📸 Auto Screenshot** - Takes a full-screen screenshot when streak changes reach your target
- **🔗 Discord Webhook** - Sends screenshots directly to your Discord channel via webhook
- **⏱️ Delay Settings** - Configure delay before taking screenshot
- **🖥️ Zone Selection** - Select the exact area on screen where the streak number appears
- **🌙 Dark/Light Mode** - Beautiful UI with theme switching
- **📌 Always On Top** - Keep the app visible while playing
- **💾 Auto-Save Settings** - Your configuration is saved automatically

## 🚀 How to Use

1. **Set Discord Webhook** - Paste your Discord webhook URL
2. **Select Zone** - Click "Select Zone" and drag to select the area with the streak number
3. **Set Changes Count** - Enter how many streak changes should trigger a screenshot (use `-` to disable)
4. **Set Delay** - Configure delay in seconds before screenshot is taken
5. **Start Monitoring** - Press `F1` or click "Start" button
6. **Stop Monitoring** - Press `F3` or click "Stop" button

## ⌨️ Hotkeys

| Key | Action |
|-----|--------|
| `F1` | Start monitoring |
| `F3` | Stop monitoring |

## 📋 Requirements

- Windows 10/11
- [Tesseract OCR](https://github.com/UB-Mannheim/tesseract/wiki) - Required for text recognition

## 🛠️ Installation

1. Download and install [Tesseract OCR](https://github.com/UB-Mannheim/tesseract/wiki)
2. Run `ScreenMonitor.exe` or use `run.bat` for development

## 📁 Files

- `ScreenMonitor.exe` - Main application (in `dist` folder after build)
- `config.json` - Auto-saved settings (webhook, zone, etc.)
- `run.bat` - Run from source code
- `build.bat` - Build executable

## 🎮 About Fisch

Fisch is a popular Roblox fishing game where players can build up streaks by catching fish consecutively. This tool helps you track and document your streak achievements!

---

## Made by Sayson

🔔 [Subscribe on YouTube](https://www.youtube.com/@sayson6129)
