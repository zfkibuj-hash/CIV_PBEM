# Prompt for Claude: Build Civ4 PBEM Manager

Use this prompt to instruct Claude (or any LLM) to generate the complete application from scratch. The expected output is a ZIP archive containing all source files and a `build.bat` for one-click Windows build.

---

## PROMPT START

You are building a **Windows desktop application** called "Civ4 PBEM Manager" — a tool for managing Play-By-Email (PBEM) games of Civilization 4: Beyond the Sword.

Each player installs this same app on their PC. The app handles uploading/downloading save files between players via a shared transport (FTP, SFTP, WebDAV, or Email), and notifies the next player by email when it's their turn.

### Tech Stack
- **Python 3.10+**
- **PyQt5** for GUI (modern dark/light theme)
- **paramiko** for SFTP transport
- **watchdog** for filesystem monitoring
- **smtplib/imaplib** (stdlib) for email transport and notifications
- **PyInstaller** for building a standalone `.exe`
- No database — game state stored as JSON files in AppData

### Project Structure
```
CIV_PBEM/
├── main.py                     # Entry point
├── build.bat                   # One-click Windows build script
├── build.spec                  # PyInstaller config (console=False, icon=icon.ico)
├── requirements.txt            # PyQt5>=5.15, paramiko>=3.0, watchdog>=3.0, pyinstaller>=6.0
├── generate_icon.py            # Generates icon.ico (envelope + floppy disk)
├── icon.ico                    # App icon (multi-resolution)
├── README.md
└── src/
    ├── __init__.py
    ├── config.py               # AppConfig class, JSON-based, stored in %APPDATA%/Civ4PBEMManager/
    ├── models/
    │   ├── __init__.py
    │   └── game.py             # Game, Player, Turn dataclasses
    ├── transport/
    │   ├── __init__.py
    │   ├── base.py             # BaseTransport ABC
    │   ├── ftp_transport.py    # FTP/FTPS
    │   ├── sftp_transport.py   # SFTP via paramiko
    │   ├── webdav_transport.py # WebDAV via urllib (Synology/Nextcloud)
    │   └── email_transport.py  # SMTP upload + IMAP download of saves as attachments
    ├── notifier/
    │   ├── __init__.py
    │   └── email_notifier.py   # SMTP notifications (separate from transport)
    └── gui/
        ├── __init__.py
        ├── main_window.py      # MainWindow + SettingsDialog + NewGameDialog
        ├── app_controller.py   # AppController connecting GUI ↔ transport ↔ notifier
        ├── tray_icon.py        # QSystemTrayIcon with balloon notifications
        └── file_watcher.py     # Watchdog-based save folder monitor
```

### Core Features

#### 1. Multi-Game Support
- `Game` dataclass: name, players (ordered list), current_turn, current_player_index, history
- `Player` dataclass: name, email, order
- `Turn` dataclass: turn_number, player_name, timestamp, filename
- Games stored as individual JSON files in `%APPDATA%/Civ4PBEMManager/games/`
- Save filename convention: `{GameName}_T{turn:04d}_{SenderPlayerName}.CivBeyondSwordSave`

#### 2. Transport Layer (abstract base + 4 implementations)
- `BaseTransport` ABC with methods: `connect()`, `disconnect()`, `upload()`, `download()`, `list_files()`, `file_exists()`, `is_connected`, `get_latest_save()`
- **FTP**: plain FTP and FTP_TLS, auto-creates remote directories
- **SFTP**: paramiko-based, supports key or password auth
- **WebDAV**: HTTP-based via urllib (PROPFIND/PUT/GET/MKCOL), works with Synology/Nextcloud
- **Email**: SMTP to send saves as attachments, IMAP to retrieve them. Two modes:
  - `shared`: all players send to/read from one shared mailbox
  - `individual`: saves sent directly to next player's inbox
  - Subject format: `[CIV4PBEM] {GameName} | {filename}`

#### 3. Email Notifications (separate from transport)
- `EmailNotifier` class sends "Twoja kolej!" emails to the next player after upload
- Uses SMTP with STARTTLS or SSL
- Configurable independently from transport (you might use FTP for files but Gmail for notifications)

#### 4. GUI (PyQt5)
- **Dark and Light themes** — full stylesheets for both, toggle via checkbox in settings
- **Main window layout**: left sidebar (game list) + right panel (game details, actions, history)
- **Sidebar**: lists all games, shows "TWOJA KOLEJ!" in green for active games
- **Game detail view**: header with game name + turn, status banner (green=your turn, grey=waiting), player order display, action buttons, turn history
- **Action buttons**: "Pobierz save", "Wyslij moj save", "Otworz folder", "Sprawdz teraz"
- **"Sprawdz teraz" button**: immediately checks remote for new saves AND resets the periodic timer
- **Settings dialog with 3 tabs** (QTabWidget):
  - **Ogolne**: player name, email, save folder path (with browse button), check interval (SpinBox, minutes), dark mode checkbox
  - **Transport**: type selector (ftp/sftp/webdav/email), file-based config OR email config panel (auto-shows/hides based on type). Email tab uses QScrollArea to avoid overflow on 1080p.
  - **Powiadomienia**: SMTP config for notifications (independent from transport)
- **New Game dialog**: game name, add players with name+email, ordered list

#### 5. System Tray
- `QSystemTrayIcon` with context menu: "Pokaz okno", "Sprawdz teraz", separator, "Zamknij"
- Double-click shows window
- Balloon notifications: "Twoja kolej!", "Nowy save wykryty!", generic status
- Window close (X button) minimizes to tray instead of quitting
- `app.setQuitOnLastWindowClosed(False)` to keep running in background

#### 6. File Watcher (Watchdog)
- Monitors the Civ4 save folder for new `.CivBeyondSwordSave` files
- On detection: shows tray balloon, updates status bar, if it's player's turn asks "Czy chcesz wyslac?"
- 5-second deduplication cooldown per file (filesystem events can fire multiple times)

#### 7. AppController
- Connects GUI signals to transport and notifier logic
- `download_save(game)`: gets latest from remote, saves to local folder
- `upload_save(game, path)`: uploads file, advances turn, uploads game state, sends notification
- `check_for_new_saves(games)`: checks all games, syncs remote state, returns notification list
- `_sync_game_state(game)`: downloads `{game}_state.json` from remote, updates local if remote is ahead
- For email transport in individual mode, passes next player's email to upload()

#### 8. Icon
- Generated programmatically with Pillow: a white envelope in motion with a blue floppy disk inside labeled "CIV", speed lines on the left
- Multi-resolution .ico (16,24,32,48,64,128,256)
- Used for: taskbar, window title, system tray, .exe file icon

#### 9. Windows Integration
- `ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("Civ4PBEMManager.1.0")` for proper taskbar icon
- `get_resource_path()` helper handles `sys._MEIPASS` (PyInstaller frozen path) vs source path
- `icon.ico` bundled as data in build.spec: `datas=[('icon.ico', '.')]`
- `build.bat`: checks Python, installs requirements, runs pyinstaller, outputs to `dist/`

#### 10. Config
- JSON file at `%APPDATA%/Civ4PBEMManager/config.json`
- Properties: save_path, check_interval_minutes, dark_mode, player_name, player_email, transport (dict), smtp (dict)
- `AppConfig` class with getters/setters that auto-save on change

### Important Design Decisions
- Save filename includes the **sender's** name (player who finished their turn), not the recipient
- Turn advancement: `current_player_index` increments modulo number of players; `current_turn` increments when wrapping to index 0
- Game state sync: after uploading a save, also upload `{game}_state.json` so other players' apps can detect turn changes even without the save file itself
- Notifications are independent from transport — you can use FTP for files and any SMTP for notifications
- The app never auto-uploads — it always asks the user (via dialog or manual button click)
- Timer reset: "Sprawdz teraz" stops and restarts the QTimer with fresh interval

### Output Requirements
Generate all files listed in the project structure above. The result should be:
1. Complete, runnable Python source code
2. A `build.bat` that installs deps and builds a standalone Windows `.exe`
3. A `generate_icon.py` that creates `icon.ico` using Pillow
4. A `requirements.txt`
5. A `README.md` with usage instructions

The code should be clean, well-commented, and ready to use. All files should work together without modifications. Target: Python 3.10+, Windows 10/11.

## PROMPT END
