# macOS AI Agent

A local macOS voice assistant with a PySide6 interface, a global hotkey, Groq speech-to-text and LLM calls, LangGraph orchestration, SQLite checkpoints, and persistent local memory.

## What is included

- A global hotkey: `Ctrl + Option + Space`
- Voice capture and Groq transcription
- LangGraph workflow with tool approval for high-risk actions
- A PySide6 status and approval UI
- SQLite checkpoints plus alias and recent-action memory
- A PyInstaller recipe for a distributable macOS `.app`

The app does **not** start automatically when you log in.

## Requirements

- macOS 12 or newer
- Python 3.11 or 3.12 for source builds
- A Groq API key
- A microphone

The generated `.app` must be built on macOS. Build separately on Apple Silicon and Intel Macs when distributing to both architectures.

## Run from source

```bash
git clone https://github.com/mozzam123/macos-ai-agent.git
cd macos-ai-agent
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
mkdir -p "$HOME/Library/Application Support/macOS AI Agent"
cp .env.example "$HOME/Library/Application Support/macOS AI Agent/.env"
# Edit that file and set GROQ_API_KEY.
python3 main.py
```

## Build the macOS app

From the repository root:

```bash
bash scripts/build_macos_app.sh
```

The completed bundle is:

```text
dist/macOS AI Agent.app
```

You can also run PyInstaller directly after installing dependencies:

```bash
python3 -m pip install -r requirements.txt -r requirements-dev.txt
python3 -m PyInstaller --noconfirm --clean macos_ai_agent.spec
```

To test the bundle before sharing it:

```bash
open "dist/macOS AI Agent.app"
```

## Configuration and local data

Secrets are intentionally **not** bundled. Before first launch, create:

```text
~/Library/Application Support/macOS AI Agent/.env
```

Copy the provided example and add your own key:

```bash
mkdir -p "$HOME/Library/Application Support/macOS AI Agent"
cp .env.example "$HOME/Library/Application Support/macOS AI Agent/.env"
```

The same folder stores each user's local state:

```text
~/Library/Application Support/macOS AI Agent/
├── .env
├── aliases.json
├── recent_memory.json
├── checkpoints.db
└── recording.wav
```

Set `MACOS_AI_AGENT_DATA_DIR` to use a different data directory. The repository ignores these files, so keys and user history cannot accidentally be committed or shipped in the app bundle.

## macOS permissions

On the first run, grant the application the permissions it needs:

1. **Microphone** — required for voice recording.
2. **Accessibility** — required by the global keyboard shortcut listener. Go to **System Settings → Privacy & Security → Accessibility** and enable **macOS AI Agent**.
3. **Automation** — macOS will ask when an approved action controls Finder, Cursor, or another application. Approve only requests you expect.

If the hotkey does not respond, quit the app, enable Accessibility, and open it again.

## Sharing the app

A locally built app is unsigned. Users may need to right-click the app, choose **Open**, and confirm the Gatekeeper prompt.

For a smoother public release, build and sign with an Apple Developer ID certificate, then notarize the distributed archive:

```bash
codesign --deep --force --options runtime --sign "Developer ID Application: Your Name (TEAMID)" "dist/macOS AI Agent.app"
ditto -c -k --keepParent "dist/macOS AI Agent.app" "dist/macOS AI Agent.zip"
xcrun notarytool submit "dist/macOS AI Agent.zip" --keychain-profile "notary-profile" --wait
xcrun stapler staple "dist/macOS AI Agent.app"
```

Do not use `--deep` as a substitute for testing nested dependencies; verify the signed app on a clean Mac before publishing a release. Notarization requires an Apple Developer Program membership and valid signing credentials.

## Security

- Never commit `.env`, API keys, checkpoints, or memory files.
- The assistant asks for approval before high-risk actions. Review each approval carefully.
- Each user should supply their own Groq API key.
