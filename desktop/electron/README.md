# Aria Desktop Avatar - Electron App

A transparent, frameless desktop overlay showing the Live2D maid avatar.

## Setup

```bash
cd desktop/electron
npm install
```

## Usage

1. **Start the Python backend first** (from project root):
   ```bash
   python -m desktop.agent
   ```

2. **Then start the Electron avatar** (from this folder):
   ```bash
   npm start
   ```

   Or with dev tools:
   ```bash
   npm run dev
   ```

## Features

- **Transparent window** - Only the avatar is visible, no background
- **Always on top** - Floats above other windows
- **Draggable** - Click and drag anywhere to move
- **Interactive** - Click on the avatar for reactions
- **Auto-reconnect** - Reconnects to backend if connection drops
- **Maid handoffs** - Avatar swaps when you summon different maids

## Controls

- **Drag** the window to reposition
- **Right-click tray icon** (if available) for menu:
  - Show/Hide Avatar
  - Toggle Always on Top
  - Reset Position
  - Quit

## Requirements

- Node.js 18+
- Python backend running (`python -m desktop.agent`)
- HTTP server on port 8080 (started by backend)
- WebSocket server on port 8765 (started by backend)

## Customization

Edit `main.js` to change:
- `DEFAULT_WIDTH` / `DEFAULT_HEIGHT` - Avatar window size
- `DEFAULT_POSITION` - Starting position (bottom-right, bottom-left, top-right, top-left)

## Troubleshooting

**Avatar not loading?**
- Make sure the Python backend is running first
- Check that http://localhost:8080 serves the Live2D models
- The app will show "Starting... (run: python -m desktop.agent)" if the server isn't detected

**Window not transparent?**
- Some Linux window managers don't support transparency
- Try running with a compositor enabled

**Can't interact with avatar?**
- The avatar area is interactive, background is click-through
- Drag from the edges if needed

## Debugging

Run with DevTools to see console logs and network requests:

```bash
npm run dev
```

Or add `--dev` flag:
```bash
npm start -- --dev
```

**Useful console logs to look for:**
- `✅ HTTP server is running` - Backend detected
- `⚠️ HTTP server not running on port 8080` - Backend not found, will try local files
- `🔄 Loading model from: ...` - Model load attempt
- `✅ Model loaded successfully` - Model loaded OK
- `❌ Failed to load ...` - Model load failed (check path/server)

**Check model paths:**
- HTTP: `http://localhost:8080/live2d/models/aria/长离.model3.json`
- Local fallback: `file:///path/to/live2d/models/aria/长离.model3.json`

**Network tab:** Look for failed requests to `localhost:8080` if models aren't loading.
