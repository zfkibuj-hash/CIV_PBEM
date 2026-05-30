# Prompt for Claude: Build Civ4 PBEM Manager

Use this prompt to instruct Claude (or any LLM) to generate the complete application from scratch. The expected output is a ZIP archive containing all source files and a `build.bat` for one-click Windows build.

---

## PROMPT START

You are building a **Windows desktop application** called "Civ4 PBEM Manager" — a tool for managing Play-By-Email (PBEM) games of Civilization 4: Beyond the Sword.

Each player installs this same app on their PC. The app handles uploading/downloading save files between players via a shared transport (FTP, SFTP, WebDAV, Synology Sharing Links, or Email), and notifies the next player by email when it's their turn.

### Tech Stack
- **Python 3.10+**
- **PyQt5** for GUI (dark/light theme with runtime toggle)
- **paramiko** for SFTP transport
- **watchdog** for filesystem monitoring
- **smtplib/imaplib** (stdlib) for email transport and notifications
- **PyInstaller** for building a standalone `.exe`
- No database — game state stored as JSON files in AppData

### Project Structure
```
CIV_PBEM/
├── main.py                          # Entry point
├── build.bat                        # One-click Windows build (checks Python, installs deps, runs PyInstaller, shows result size)
├── build.spec                       # PyInstaller config (console=False, icon, datas, excludes for size optimization)
├── requirements.txt                 # PyQt5>=5.15, paramiko>=3.0, watchdog>=3.0, pyinstaller>=6.0
├── generate_icon.py                 # Generates icon.ico using Pillow (envelope + floppy disk)
├── icon.ico                         # App icon (multi-resolution: 16,24,32,48,64,128,256)
├── README.md
└── src/
    ├── __init__.py
    ├── config.py                    # AppConfig class, JSON-based, stored in %APPDATA%/Civ4PBEMManager/
    ├── models/
    │   ├── __init__.py
    │   └── game.py                  # Game, Player, Turn dataclasses + revert_to_turn()
    ├── transport/
    │   ├── __init__.py
    │   ├── base.py                  # BaseTransport ABC
    │   ├── ftp_transport.py         # FTP/FTPS (with ignore_ssl support)
    │   ├── sftp_transport.py        # SFTP via paramiko (AutoAddPolicy)
    │   ├── webdav_transport.py      # WebDAV via urllib (with ignore_ssl support)
    │   ├── synology_sharing_transport.py  # Synology File Request + GoFile sharing links
    │   └── email_transport.py       # SMTP upload + IMAP download of saves as attachments
    ├── notifier/
    │   ├── __init__.py
    │   └── email_notifier.py        # SMTP notifications (separate from transport)
    └── gui/
        ├── __init__.py
        ├── main_window.py           # MainWindow + SettingsDialog (tabbed) + NewGameDialog
        ├── app_controller.py        # AppController connecting GUI ↔ transport ↔ notifier
        ├── tray_icon.py             # QSystemTrayIcon with balloon notifications
        └── file_watcher.py          # Watchdog-based save folder monitor
```

### Core Features

#### 1. Multi-Game Support
- `Game` dataclass: name, players (ordered list), current_turn, current_player_index, history
- `Player` dataclass: name, email, order
- `Turn` dataclass: turn_number, player_name, timestamp, filename
- Games stored as individual JSON files in `%APPDATA%/Civ4PBEMManager/games/`
- Save filename convention: `{GameName}_T{turn:04d}_{SenderPlayerName}.CivBeyondSwordSave`
- The sender name is the **player who FINISHED their turn** (configured in settings as "Twoja nazwa")

#### 2. Turn Revert Feature
- `Game.revert_to_turn(history_index)`: removes all history after given index, resets current_turn and current_player_index to that point
- History displayed as clickable `QListWidget` (not readonly QTextEdit)
- "Przywroc zaznaczona ture" button with confirmation dialog
- `AppController.revert_turn(game, history_index)`:
  - Downloads old save from remote (if available)
  - Reverts local game state
  - Uploads reverted state JSON so all players sync
  - Sends email to ALL other players: "Gracz X przywrocil gre do tury N"

#### 3. Transport Layer (abstract base + 5 implementations)
- `BaseTransport` ABC with methods: `connect()`, `disconnect()`, `upload()`, `download()`, `list_files()`, `file_exists()`, `is_connected` property, `get_latest_save()`
- All transports that use HTTPS/TLS respect a global `ignore_ssl` flag (checkbox in settings, default ON)

##### FTP (`ftp_transport.py`)
- Plain FTP and FTP_TLS (FTPS)
- When `ignore_ssl=True` and TLS: creates `ssl.SSLContext` with `CERT_NONE` so self-signed certs work
- Auto-creates remote directories via `_ensure_dir()`

##### SFTP (`sftp_transport.py`)
- paramiko-based, supports key or password auth
- Uses `AutoAddPolicy()` — accepts any host key (no SSL issue here, it's SSH)

##### WebDAV (`webdav_transport.py`)
- HTTP-based via urllib (PROPFIND/PUT/GET/MKCOL)
- Works with Synology WebDAV Server, Nextcloud, etc.
- All `urlopen()` calls pass `context=self._ssl_ctx` when `ignore_ssl=True`

##### Synology Sharing Links (`synology_sharing_transport.py`)
- Uses Synology DSM's web sharing links — NO NAS user account needed
- **Upload**: via File Request link (multipart POST with password to `/webapi/entry.cgi` or fallback to direct POST)
- **Download**: via shared folder link (direct GET with password, or via Synology API endpoint)
- **Separate passwords** for upload and download (they can be different!)
- Credential fallback: if download_password is empty, uses upload_password
- Config: `upload_url`, `upload_password`, `download_url`, `download_password`
- Handles self-signed certs via permissive SSL context
- `list_files()` not available (sharing links don't expose directory listing) — relies on game state sync
- Example URLs:
  - Upload: `https://your.synology.me:5001/sharing/XXXXXXX`
  - Download: `https://gofile.me/XXXXX/XXXXXXX`

##### Email (`email_transport.py`)
- SMTP to send saves as email attachments, IMAP to retrieve them
- Two modes:
  - `shared`: all players send to/read from one shared mailbox (e.g. `civ4pbem@gmail.com`)
  - `individual`: saves sent directly to next player's inbox, each player checks own inbox
- Subject format: `[CIV4PBEM] {GameName} | {filename}`
- IMAP search filters by `[CIV4PBEM]` tag + game name
- Handles encoded headers via `email.header.decode_header()`

#### 4. Email Notifications (separate from transport)
- `EmailNotifier` class sends "Twoja kolej!" emails to the next player after upload
- Uses SMTP with STARTTLS or SSL
- Configurable **independently** from transport (you might use Synology for files but Gmail for notifications)
- `test_connection()` method for testing SMTP config
- **Credential fallback** (login/password ONLY, never host/port):
  - If notification SMTP login is empty → uses email transport SMTP login
  - If notification SMTP password is empty → uses email transport SMTP password
  - If from_address is empty → uses SMTP login
  - Host and port are NEVER inherited — must be set explicitly

#### 5. GUI (PyQt5)

##### Themes
- **Two full stylesheets**: DARK_STYLE and LIGHT_STYLE
- Toggle via checkbox "Tryb ciemny" in Settings → Ogolne tab
- Theme applies immediately on save (calls `window.apply_theme()` — no restart needed)
- **Both SettingsDialog and NewGameDialog** use `get_style_for_theme(config)` — NOT hardcoded DARK_STYLE
- Dark theme: `#1e1e1e` background, `#e0e0e0` text, blue accents (`#42a5f5`)
- Light theme: `#f5f5f5` background, `#212121` text, blue accents (`#1976d2`)
- Sidebar uses `QWidget#sidebar` objectName for theme-aware background color
- QTabWidget/QTabBar fully styled in both themes
- QCheckBox color styled for light theme

##### Main Window
- Left sidebar (240px fixed width): game list with color-coded status
- Right panel: header, status banner, player order, action buttons, turn history (clickable list)
- Status bar at bottom

##### Action Buttons
- "Pobierz save" (green), "Wyslij moj save" (blue), "Otworz folder", "Sprawdz teraz"
- "Sprawdz teraz": immediately checks remote AND resets periodic timer (full interval from now)

##### Turn History Panel
- `QListWidget` (clickable, not QTextEdit) showing last 20 turns
- Each item shows: date, player name, turn number, filename
- "Przywroc zaznaczona ture" button (orange styled) below the list
- Confirmation dialog before reverting

##### Settings Dialog (QDialog with QTabWidget — 3 tabs)
- **Ogolne** tab: player name, email, save folder path (with browse button), check interval (SpinBox 1-60 min), "Tryb ciemny" checkbox
- **Transport** tab:
  - Type selector ComboBox: `ftp`, `sftp`, `webdav`, `email`, `synology`
  - "Ignoruj bledy SSL (self-signed certs)" checkbox (default: checked)
  - Panels auto-show/hide based on selected type (ONLY the relevant panel is visible):
    - FTP/SFTP/WebDAV: host, port, login, password, remote_dir
    - Email: mode (shared/individual), shared_email, SMTP host/port/user/pass, IMAP host/port/user/pass, from_address
    - Synology: upload_url, upload_password, download_url, download_password (with placeholder: "puste = takie samo jak uploadu")
  - Transport tab uses `QScrollArea` to prevent overflow on 1080p screens
- **Powiadomienia** tab: SMTP host/port/user/pass/from_address for notification emails
  - Placeholder texts: "puste = z transportu email" on login/password fields
  - Info label explaining the fallback behavior
- Dialog minimum size: 520×480, default: 540×520
- After save: emits `settings_saved` signal → `controller.reload_config()` reinitializes transport/notifier

##### New Game Dialog
- Game name, add players with name+email, ordered list with add/remove buttons
- Pre-adds current player (from config) as first entry

#### 6. System Tray (`tray_icon.py`)
- `QSystemTrayIcon` with context menu: "Pokaz okno", "Sprawdz teraz", separator, "Zamknij"
- Double-click on tray icon shows/activates window
- Balloon notifications: `notify_your_turn()`, `notify_new_save_detected()`, `notify_status()`
- **Window close (X button) minimizes to tray** instead of quitting
  - `closeEvent()` calls `event.ignore()` + `self.hide()` + shows balloon "Aplikacja dziala w tle"
  - `_minimize_to_tray` and `_tray_icon` initialized in `MainWindow.__init__` (not via hasattr!)
  - Set to True by `main.py` after tray is confirmed available
- `app.setQuitOnLastWindowClosed(False)` to keep running in background
- Icon loaded via `_get_icon_path()` which handles both dev (`Path(__file__)`) and frozen (`sys._MEIPASS`)

#### 7. File Watcher — Watchdog (`file_watcher.py`)
- `SaveFileWatcher` class using `watchdog.observers.Observer`
- Monitors configured save folder for new/modified `.CivBeyondSwordSave` files
- On detection: emits `new_save_detected(str)` signal with full file path
- Main.py handler: shows tray balloon, updates status, if player's turn offers upload via QMessageBox.question
- 5-second per-file deduplication cooldown (filesystem can fire multiple events for one save)
- `start()`, `stop()`, `restart(new_path)` methods
- Observer runs as daemon thread

#### 8. AppController (`app_controller.py`)
- Connects GUI signals to transport and notifier logic
- `_init_transport()`: creates appropriate transport based on config type + passes `ignore_ssl`
- `_init_notifier()`: creates EmailNotifier from SMTP config with credential fallback (login/pass only, not host/port)
- `reload_config()`: re-initializes transport and notifier after settings change. Connected via `window.settings_saved` signal.
- `download_save(game)` → `get_latest_save()` + `download()` to local save folder
- `upload_save(game, path)`:
  - Validates it's player's turn
  - Uploads save file
  - For email transport individual mode: passes `to_email=next_player.email`
  - Advances turn (game.advance_turn)
  - Uploads game state JSON so other instances can sync
  - Sends notification email to next player
- `revert_turn(game, history_index)`:
  - Downloads old save (if available on remote)
  - Calls `game.revert_to_turn()`
  - Uploads reverted state JSON
  - Emails ALL other players about the revert
- `check_for_new_saves(games)`: iterates all games, syncs remote state, returns notifications
- `_sync_game_state(game)`: downloads `{game}_state.json`, updates local if remote is ahead
- `test_transport()` / `test_smtp()` for connection testing

#### 9. Icon (`generate_icon.py`)
- Generated programmatically with Pillow
- Visual: white envelope (with flap/fold lines) in motion, blue floppy disk inside labeled "CIV", speed lines on left, motion particles
- Multi-resolution .ico: sizes `[16, 24, 32, 48, 64, 128, 256]`
- Also outputs `icon_preview.png` (256×256)
- Used for: taskbar, window title bar, system tray, .exe file icon

#### 10. Windows Integration (`main.py`)
- `ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("Civ4PBEMManager.1.0")` for proper taskbar icon grouping
- `get_resource_path(relative_path)` helper:
  - If `sys.frozen`: uses `sys._MEIPASS` (PyInstaller temp directory)
  - Else: uses `Path(__file__).parent` (source directory)
- `app.setWindowIcon(icon)` + `window.setWindowIcon(icon)` for taskbar/title display
- `build.spec`:
  - `datas=[('icon.ico', '.')]` to bundle icon inside .exe
  - `excludes=` list of ~25 unused Qt modules (WebEngine, Multimedia, Quick, Qml, Svg, OpenGL, etc.) + unused stdlib (tkinter, unittest, etc.) to reduce size by 15-20MB
  - Filters heavy binaries: opengl32sw.dll, d3dcompiler, libGLESv2, libEGL
  - UPX compression enabled (if UPX is in PATH)
- `build.bat`: checks Python, installs requirements, checks for UPX, runs pyinstaller, shows final file size

#### 11. Config (`config.py`)
- JSON file at `%APPDATA%/Civ4PBEMManager/config.json`
- Properties with defaults:
  - `save_path`: `Documents\My Games\Beyond the Sword\Saves\pbem`
  - `check_interval_minutes`: 5
  - `dark_mode`: True
  - `player_name`: ""
  - `player_email`: ""
  - `transport`: dict with `type`, `ignore_ssl_errors`, `host`, `port`, `username`, `password`, `remote_dir`, nested `email` dict, nested `synology` dict
  - `smtp`: dict with `host`, `port`, `username`, `password`, `use_tls`, `from_address`
- `AppConfig` class with getters/setters that auto-save on change
- `get_config_dir()`, `get_games_dir()` helpers

### Important Design Decisions
- Save filename includes the **sender's** name (player who finished their turn), not the recipient
- Turn advancement: `current_player_index` increments modulo number of players; `current_turn` increments only when wrapping back to index 0
- Game state sync: after uploading a save, also upload `{game}_state.json` so other players' apps detect turn changes even when `list_files()` isn't available (Synology sharing case)
- Notifications are **independent** from transport — you can use Synology for files and Gmail for notifications
- The app **never auto-uploads** — always asks the user (via dialog or manual button click)
- Timer reset: "Sprawdz teraz" stops the QTimer and restarts it with a fresh full interval
- SSL errors ignored by default (checkbox ON) — handles self-signed certs, Synology without domain, no public IP
- Synology sharing has **separate upload and download passwords** (download falls back to upload if empty)
- Credential fallback for notifications: only login/password inherit from email transport. Host and port are NEVER inherited (IMAP port ≠ SMTP port!)
- `closeEvent` uses `_minimize_to_tray` flag (initialized in `__init__`, set by `main.py`)
- Tray icon path resolution uses `sys._MEIPASS` for frozen executables
- Dark/light theme change is immediate — `apply_theme()` called on parent window + dialogs use `get_style_for_theme()` based on config
- Settings save emits `settings_saved` signal → `controller.reload_config()` — without this, transport stays None after first configuration!
- Turn revert sends notification to ALL players (not just next one)
- Exe size optimized by excluding unused Qt modules — target ~20-25MB without UPX, ~15-18MB with UPX

### Output Requirements
Generate all files listed in the project structure above. The result should be:
1. Complete, runnable Python source code (all files, no placeholders)
2. A `build.bat` that checks for Python, installs deps, and builds a standalone Windows `.exe`
3. A `generate_icon.py` that creates `icon.ico` using Pillow (run it once before building)
4. A `requirements.txt` with: PyQt5>=5.15, paramiko>=3.0, watchdog>=3.0, pyinstaller>=6.0
5. A `README.md` with usage and build instructions

The code should be clean, well-commented (in English), and ready to use. All files must work together without modifications. Target: Python 3.10+, Windows 10/11.

## PROMPT END
