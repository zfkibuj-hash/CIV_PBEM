# Prompt for Claude: Build Civ4 PBEM Manager

Use this prompt to instruct Claude (or any LLM) to generate the complete application from scratch. The expected output is a ZIP archive containing all source files and a `build.bat` for one-click Windows build.

---

## PROMPT START

You are building a **Windows desktop application** called "Civ4 PBEM Manager" — a tool for managing Play-By-Email (PBEM) games of Civilization 4: Beyond the Sword.

Each player installs this same app on their PC. The app handles uploading/downloading save files between players via a shared transport (FTP, SFTP, WebDAV, or Email), and notifies the next player by email when it's their turn.

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
├── main.py                          # Entry point, wires GUI ↔ controller ↔ tray ↔ watcher
├── build.bat                        # One-click Windows build (checks Python, UPX, installs deps, shows size)
├── build.spec                       # PyInstaller config (excludes unused Qt modules for smaller exe)
├── requirements.txt                 # PyQt5>=5.15, paramiko>=3.0, watchdog>=3.0, pyinstaller>=6.0
├── generate_icon.py                 # Generates icon.ico using Pillow (envelope + floppy disk)
├── icon.ico                         # App icon (multi-resolution: 16,24,32,48,64,128,256)
├── README.md
└── src/
    ├── __init__.py
    ├── config.py                    # AppConfig class, JSON-based, stored in %APPDATA%/Civ4PBEMManager/
    ├── models/
    │   ├── __init__.py
    │   └── game.py                  # Game, Player, Turn dataclasses + revert_to_turn() + delete_file()
    ├── transport/
    │   ├── __init__.py
    │   ├── base.py                  # BaseTransport ABC
    │   ├── ftp_transport.py         # FTP/FTPS (with ignore_ssl support)
    │   ├── sftp_transport.py        # SFTP via paramiko (AutoAddPolicy)
    │   ├── webdav_transport.py      # WebDAV via urllib (with ignore_ssl support, works with Synology WebDAV Server)
    │   └── email_transport.py       # SMTP upload + IMAP download of saves as attachments
    ├── notifier/
    │   ├── __init__.py
    │   └── email_notifier.py        # SMTP notifications (separate from transport)
    └── gui/
        ├── __init__.py
        ├── main_window.py           # MainWindow + SettingsDialog + NewGameDialog + GameTransportDialog
        ├── app_controller.py        # AppController (per-game transport, notifier)
        ├── tray_icon.py             # QSystemTrayIcon with balloon notifications
        └── file_watcher.py          # Watchdog-based save folder monitor
```

### Core Features

#### 1. Multi-Game Support
- `Game` dataclass: name, players, current_turn, current_player_index, history, **transport_config**
- `Player` dataclass: name, email, order
- `Turn` dataclass: turn_number, player_name, timestamp, filename
- Games stored as individual JSON files in `%APPDATA%/Civ4PBEMManager/games/`
- Save filename convention: `{GameName}_T{turn:04d}_{SenderPlayerName}.CivBeyondSwordSave`
- The sender name is the **player who FINISHED their turn** (configured in settings as "Twoja nazwa")
- `Game.delete_file(directory)` removes the JSON from disk

#### 2. Per-Game Transport Configuration
- **Each game has its own `transport_config` dict** — stored inside the game JSON
- `AppController._create_transport_for_game(game)` creates a transport instance from game's config
- No global transport on controller — each operation creates fresh transport for the specific game
- **GameTransportDialog**: full transport editor per game with:
  - Same fields as global settings (ftp/sftp/webdav/email panels)
  - **"Kopiuj ustawienia z..."** section at top:
    - "Domyślne (globalne)" button — copies from app-wide Settings → Transport tab
    - Dropdown of other games + "Kopiuj" button — copies from another game's config
  - Uses QScrollArea, auto-shows/hides panels based on type
- Button **"Transport gry..."** in sidebar opens this dialog for selected game

#### 3. Turn Revert Feature
- `Game.revert_to_turn(history_index)`: removes all history after given index, resets current_turn and current_player_index
- History displayed as clickable `QListWidget` (each item stores history_index in UserRole data)
- "Przywroc zaznaczona ture" button with confirmation dialog
- `AppController.revert_turn(game, history_index)`:
  - Downloads old save from remote (if available)
  - Reverts local game state
  - Uploads reverted state JSON so all players sync
  - Emails ALL other players about the revert

#### 4. Delete Game
- "Usun gre" button in sidebar (styled red)
- Confirmation dialog
- `AppController.delete_game(game)`: removes JSON file + remote state cache

#### 5. Game Config Export/Import (.civ4pbem files)
- **Export**: "Eksportuj gre..." button in sidebar → saves `.civ4pbem` file (JSON) containing:
  - `civ4pbem_version`: "1.0"
  - `name`: game name
  - `players`: list of players with name, email, order
  - `transport_config`: full transport settings for this game
- **Import**: "Importuj gre..." button in sidebar → opens `.civ4pbem` file, creates game locally
  - Checks for duplicate game name (offers to overwrite)
  - Player who sets up the game exports the file and sends it (email, Discord, etc.) to all players
  - Each player imports and has identical game config + transport ready to go

#### 5. Upload Confirmation (Turn Order Advisory)
- Upload does NOT block based on turn order — user decides when to send
- BUT: if `game.is_my_turn(my_name)` is False AND game has history, shows warning popup:
  - "Wedlug stanu gry, teraz gra: {name}. Czy na pewno chcesz wyslac save?"
  - User can confirm (e.g. after revert) or cancel
- New game (empty history) skips the check entirely

#### 6. Duplicate Save Handling on Download
- `controller.download_save_list(game)`: gets all `.CivBeyondSwordSave` files from remote
- If **one** save: downloads automatically
- If **multiple** saves: shows `QInputDialog.getItem()` with list, newest pre-selected
- Already-existing local files: reports "Save juz istnieje lokalnie" without re-downloading
- `controller.download_specific_save(game, filename)`: downloads a chosen file by name

#### 7. Transport Layer (abstract base + 4 implementations)
- `BaseTransport` ABC: `connect()`, `disconnect()`, `upload()`, `download()`, `list_files()`, `file_exists()`, `is_connected`, `get_latest_save()`
- All HTTPS/TLS transports respect `ignore_ssl` flag (per-game config, default ON)

##### FTP
- Plain FTP and FTP_TLS. When `ignore_ssl=True`: `ssl.SSLContext` with `CERT_NONE`
- Auto-creates remote directories

##### SFTP
- paramiko, `AutoAddPolicy()`, supports key or password auth

##### WebDAV
- urllib-based (PROPFIND/PUT/GET/MKCOL). All `urlopen()` pass `context=ssl_ctx`
- Works with Synology WebDAV Server, Nextcloud, etc.

##### Email
- SMTP send + IMAP receive. Two modes: `shared` (one mailbox) or `individual` (direct to player)
- Subject: `[CIV4PBEM] {GameName} | {filename}`. IMAP filters by tag + game name

#### 8. Email Notifications (separate from transport)
- `EmailNotifier` sends "Twoja kolej!" to next player after upload
- Configurable independently from transport
- **Credential fallback** (login/password ONLY, never host/port):
  - If notification login empty → uses email transport SMTP login
  - If password empty → uses email transport SMTP password
  - Host and port: NEVER inherited, must be set explicitly

#### 9. GUI (PyQt5)

##### Themes
- DARK_STYLE and LIGHT_STYLE (full stylesheets including QTabWidget, QTabBar, QCheckBox, sidebar)
- Toggle: "Tryb ciemny" checkbox in Settings → Ogolne
- Applies immediately (no restart). `apply_theme()` on main window.
- **All dialogs** (Settings, NewGame, GameTransport) use `get_style_for_theme(config)` — not hardcoded

##### Main Window
- Left sidebar (240px): game list, "+ Nowa gra", "Usun gre", "Transport gry...", "Ustawienia"
- Right panel: header, status banner, player order, action buttons, clickable turn history list
- Status bar at bottom

##### Action Buttons
- "Pobierz save" (green), "Wyslij moj save" (blue), "Otworz folder", "Sprawdz teraz"
- "Sprawdz teraz": checks remote + resets periodic timer

##### Settings Dialog (3 tabs: Ogolne, Transport, Powiadomienia)
- **Ogolne**: player name, email, save path, check interval, dark mode checkbox
- **Transport**: global/default transport config (used as template for new games via "Kopiuj z domyslnych")
- **Powiadomienia**: SMTP for notifications. Placeholders: "puste = z transportu email"
- After save: emits `settings_saved` signal → `controller.reload_config()`

#### 10. System Tray
- Context menu: "Pokaz okno", "Sprawdz teraz", "Zamknij"
- Close (X) minimizes to tray + shows balloon. Double-click restores.
- `_minimize_to_tray` and `_tray_icon` initialized in `__init__`
- Icon path via `_get_icon_path()` handling `sys._MEIPASS`

#### 11. File Watcher (Watchdog)
- Monitors save folder for new `.CivBeyondSwordSave` files
- Emits signal → tray balloon + optional upload dialog
- 5-second deduplication cooldown per file. Daemon thread.

#### 12. Windows Integration
- `SetCurrentProcessExplicitAppUserModelID` for taskbar icon
- `get_resource_path()` for dev vs frozen paths
- `setWindowIcon()` on both app and window
- `build.spec`: excludes ~25 unused Qt modules, filters heavy binaries, UPX enabled
- `build.bat`: checks Python/UPX, shows final size. Target: ~20-25MB (with UPX: ~15-18MB)

#### 13. Config
- `%APPDATA%/Civ4PBEMManager/config.json`
- Keys: save_path, check_interval_minutes, dark_mode, player_name, player_email, transport (global/default), smtp
- `AppConfig` class with auto-save on change
- Games dir: `%APPDATA%/Civ4PBEMManager/games/`

### Important Design Decisions
- Save filename = sender's name (who finished turn), not recipient
- Turn tracking is **advisory** not enforced — upload shows warning popup if not your turn, but allows it
- Per-game transport: each game is independent. Global settings serve as template for "copy from defaults"
- Game state sync: upload `{game}_state.json` after each turn so other players' apps detect changes
- Credential fallback for notifications: only login/password (never host/port — IMAP port ≠ SMTP port!)
- Settings save → `settings_saved` signal → `controller.reload_config()` — critical for first-time setup!
- Revert notifies ALL players. Upload only notifies next player.
- Download with duplicates: user chooses which save via dialog
- `closeEvent` on MainWindow: minimize to tray (not quit). Flag initialized in `__init__`.
- Dark/light theme applies to ALL dialogs (not just main window)
- Exe optimized: exclude WebEngine/Multimedia/Quick/Qml/Svg/OpenGL + UPX

### Output Requirements
Generate ALL files listed in the project structure. The result should be:
1. Complete, runnable Python source code (all files, no placeholders, no TODOs)
2. A `build.bat` that checks Python, installs deps, builds standalone `.exe`
3. A `generate_icon.py` that creates `icon.ico` using Pillow
4. A `requirements.txt`
5. A `README.md` with usage and build instructions

Code: clean, well-commented (English), ready to use without modifications. Target: Python 3.10+, Windows 10/11.

## PROMPT END
