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
├── MANUAL.md                        # Full user manual (PL/EN)
└── src/
    ├── __init__.py
    ├── config.py                    # AppConfig class, JSON-based, stored in %APPDATA%/Civ4PBEMManager/
    ├── crypto.py                    # AES-256 encryption (Fernet + PBKDF2), encrypt/decrypt/verify
    ├── i18n.py                      # Internationalization module (PL/EN, ~200 keys, runtime switching)
    ├── launcher.py                  # Civ4 BTS detection (Steam/GOG/registry) + launch with save
    ├── models/
    │   ├── __init__.py
    │   ├── game.py                  # Game, Player, Turn dataclasses + revert_to_turn() + delete_file()
    │   └── statistics.py            # GameStats, PlayerStats — calculated from turn history
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
        ├── main_window.py           # MainWindow + SettingsDialog + NewGameDialog + GameTransportDialog + GameStatsDialog
        ├── app_controller.py        # AppController (per-game transport, notifier, launch_civ4_with_save)
        ├── tray_icon.py             # QSystemTrayIcon with balloon notifications
        └── file_watcher.py          # Watchdog-based save folder monitor
```

### Core Features

#### 1. Multi-Game Support
- `Game` dataclass: name, players, current_turn, current_player_index, history, **transport_config**, **local_player_alias**
- `Player` dataclass: name, email, order
- `Turn` dataclass: turn_number, player_name, timestamp, filename
- Games stored as individual JSON files in `%APPDATA%/Civ4PBEMManager/games/`
- Save filename convention: `{GameName}_T{turn:04d}_{SenderPlayerName}.CivBeyondSwordSave`
- The sender name is the **game player name** (resolved via alias, NOT necessarily the local nick)
- `Game.local_player_alias`: maps local config.player_name → game player name (see section 19)
- `Game.delete_file(directory)` removes the JSON from disk

#### 2. Per-Game Transport Configuration
- **Each game has its own `transport_config` dict** — stored inside the game JSON
- `AppController._create_transport_for_game(game)` creates a transport instance from game's config
- No global transport on controller — each operation creates fresh transport for the specific game
- **GameTransportDialog**: full transport editor per game with:
  - Same fields as global settings (ftp/sftp/webdav/email panels)
  - **"Kopiuj ustawienia z..."** section at top: copy from defaults or another game
  - **"Testuj polaczenie"** button: creates temp transport from form, tests connect/disconnect
  - Orange warning in email panel: "Nie uzywaj prywatnego maila!"
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
- Then asks: "Czy usunac rowniez pliki save?"
  - If yes AND game has `admin_password` set: requires password input to proceed
  - If yes AND no admin_password: deletes directly
  - Deletes files matching `{game_name}_T*.*` from save folder
- `Game.admin_password`: set when creating game (optional field in NewGameDialog)
- `AppController.delete_game(game)`: removes JSON file + remote state cache

#### 5. Game Config Export/Import (.civ4pbem files)
- **Export**: "Eksportuj gre..." button in sidebar → saves `.civ4pbem` file (JSON) containing:
  - `civ4pbem_version`: "1.0"
  - `name`: game name
  - `players`: list of players with name, email, order
  - `transport_config`: full transport settings for this game
- **Import**: "Importuj gre..." button in sidebar → opens `.civ4pbem` file, creates game locally
  - Checks for duplicate game name (offers to overwrite)
  - **Player identity dialog**: asks "Which player are you?" from list + confirms email (see section 19)
  - Player who sets up the game exports the file and sends it (email, Discord, etc.) to all players
  - Each player imports, picks their identity, and has identical game config + transport ready to go

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
- `EmailNotifier` sends "Your turn!" to next player after upload
- Configurable independently from transport
- **Shared mailbox model**: if notification SMTP host is empty, automatically uses transport email SMTP credentials (one email account does everything)
- **Customizable templates** (`subject_template`, `body_template` in smtp config):
  - Variables: `{game}`, `{turn}`, `{from_player}`, `{to_player}`
  - Default: English template if not customized
  - Stored in config under `smtp.subject_template` and `smtp.body_template`
- **Credential fallback** (login/password ONLY, never host/port):
  - If notification login empty → uses email transport SMTP login
  - If password empty → uses email transport SMTP password
  - Host and port: fallback to transport email SMTP if notification host empty
- **Purge game emails** (`EmailTransport.purge_game(game_name)`):
  - Deletes ALL emails matching `[CIV4PBEM] {game_name}` from mailbox via IMAP
  - Uses IMAP search + `\Deleted` flag + `expunge()`
  - Only affects the specific game — other games on same mailbox are safe
  - `AppController.purge_game_emails(game)` → wrapper that checks transport type

#### 9. GUI (PyQt5)

##### Themes
- DARK_STYLE and LIGHT_STYLE (full stylesheets including QTabWidget, QTabBar, QCheckBox, sidebar)
- Toggle: "Tryb ciemny" checkbox in Settings → Ogolne
- Applies immediately (no restart). `apply_theme()` on main window.
- **All dialogs** (Settings, NewGame, GameTransport) use `get_style_for_theme(config)` — not hardcoded

##### Main Window
- Left sidebar (240px): game list, "+ Nowa gra", "Importuj gre...", "Eksportuj gre...", "Usun gre", "Transport gry...", "Ustawienia"
- Right panel: header, status banner, player order + time since last turn, action buttons, clickable turn history list
- Status bar at bottom
- **Time since last turn**: shows "PlayerName gra juz: X dni, Y godz." below player order

##### Action Buttons
- "Pobierz save" (green), "Wyslij moj save" (blue), "Otworz folder", "Sprawdz teraz"
- "Sprawdz teraz": checks remote + resets periodic timer

##### Settings Dialog (4 tabs: Ogolne, Transport, Powiadomienia, Bezpieczenstwo)
- **Ogolne** (scrollable): player name, email, save path, check interval, dark mode checkbox, **auto-send checkbox**, **language selector** (Polski/English), **Civ4 BTS path** (browse + auto-detect)
  - Auto-send: "Auto-wyslij save (bez pytania, dla fullscreen)" — when ON, watchdog uploads automatically with balloon only (no popup that would minimize Civ4 in fullscreen)
- **Transport**: global/default transport config (used as template for new games via "Kopiuj z domyslnych"). Orange warning: "Nie uzywaj prywatnego maila!" Shows lock icon if config encrypted and locked.
- **Powiadomienia**: SMTP for notifications. Placeholders: "puste = z transportu email". Shows lock icon if locked.
- **Bezpieczenstwo**: encryption status, set/change master password (with confirmation), info text
- After save: emits `settings_saved` signal → `controller.reload_config()` + `_refresh_ui_language()`
- All dialogs: `WindowContextHelpButtonHint` removed (no "?" button), sized generously, use `get_style_for_theme()`

#### 10. System Tray
- Context menu: "Pokaz okno", "Sprawdz teraz", "Zamknij"
- **X (close button) = quit application**. **Minimize (—) = goes to tray**.
- Double-click restores window.
- Balloon notifications + **system sound** (winsound.MessageBeep) on save download
- `_minimize_to_tray` and `_tray_icon` initialized in `__init__`
- `changeEvent` override: intercepts WindowMinimized state → hides window to tray
- Icon path via `_get_icon_path()` handling `sys._MEIPASS`

#### 11. File Watcher (Watchdog)
- Monitors save folder for new `.CivBeyondSwordSave` files
- Emits signal → behavior depends on `auto_send` setting:
  - **auto_send=False** (default): shows popup dialog asking to upload (can minimize fullscreen game!)
  - **auto_send=True**: uploads automatically, only balloon notification (safe for fullscreen play)
- 5-second deduplication cooldown per file. Daemon thread.
- **Ignore list** (`ignore_next(filepath)`): files downloaded BY THE APP are excluded from detection
  - Controller calls `watcher.ignore_next(path)` BEFORE writing a downloaded save
  - Prevents the "just downloaded turn → watchdog asks to re-upload" loop
  - Entries auto-expire after 30 seconds (safety against stale entries)
  - Path normalization (resolve()) ensures consistent matching
  - Only fires for saves that CIV4 itself creates (player finished turn)

#### 12. Windows Integration
- `SetCurrentProcessExplicitAppUserModelID` for taskbar icon
- `get_resource_path()` for dev vs frozen paths
- `setWindowIcon()` on both app and window
- `build.spec`: excludes ~25 unused Qt modules, filters heavy binaries, UPX enabled
- `build.bat`: checks Python/UPX, shows final size. Target: ~20-25MB (with UPX: ~15-18MB)

#### 13. Config
- `%APPDATA%/Civ4PBEMManager/config.json`
- Keys: save_path, check_interval_minutes, dark_mode, auto_send, player_name, player_email, transport (global/default), smtp, **language** ("pl"/"en"), **civ4_path** (path to .exe), **window_geometry** ({x, y, width, height})
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
- `closeEvent` on MainWindow: X = quit. `changeEvent` intercepts minimize → hides to tray.
- Auto-send mode: when enabled, watchdog uploads without popup (balloon only) — safe for fullscreen Civ4
- Notification sound: winsound.MessageBeep(MB_ICONASTERISK) on Windows after auto-download
- Delete saves requires admin_password (if set on game) — prevents accidental deletion
- Private email warning: orange label in both email transport panels
- Dark/light theme applies to ALL dialogs (not just main window)
- Exe optimized: exclude WebEngine/Multimedia/Quick/Qml/Svg/OpenGL + UPX
- Single-instance: only one copy of the app can run at a time
- "Uruchom Civ4" button: manual launch, loads latest save, prevents duplicate Civ4 instances
- Language stored in config, i18n.t() used for all UI strings
- Language change: after save, `_refresh_ui_language()` updates all button/label texts immediately (no restart)
- Player alias mapping: local nick ≠ game name → resolved transparently via Game.local_player_alias
- Remote {GameName}.config sync: first uploader establishes canonical config, all others auto-sync on periodic check
- Save filename always uses GAME player name (alias-resolved), not local nick
- Window geometry (position + size) saved on close, restored on start (clamped to screen bounds)
- All QDialog subclasses: remove `WindowContextHelpButtonHint` (the useless "?" button in title bar)
- Settings dialog: General tab wrapped in QScrollArea for small screens; default size 640×620
- Main window default size: 900×650 (minimum 800×600)

### NEW FEATURES (v1.1)

#### 14. Game Statistics (`src/models/statistics.py` + `GameStatsDialog`)
- **"Statystyki" button** in sidebar → opens `GameStatsDialog`
- `calculate_game_stats(game)` → `GameStats` dataclass with:
  - `total_turns`, `total_time_seconds`, `avg_turn_time_seconds`
  - `fastest_turn_seconds` + `fastest_turn_player`
  - `slowest_turn_seconds` + `slowest_turn_player`
  - `game_started`, `last_activity` (timestamps)
  - `player_stats`: list of `PlayerStats` per player
- `PlayerStats`: `name`, `total_turns`, `total_time_seconds`, `fastest_turn_seconds`, `slowest_turn_seconds`
- Turn duration = difference between consecutive history timestamps
- First turn duration = timestamp - game.created_at
- Dialog shows overview group (QFormLayout) + QTableWidget for per-player stats
- `format_duration(seconds)` helper → "5d 3h" / "2h 15m" / "42m" / "< 1m"

#### 15. Launch Civ4 (`src/launcher.py`)
- **"Uruchom Civ4" button** (orange) in action buttons row
- Button behavior (NOT auto-launch, only manual click):
  1. Checks `config.civ4_path` — if empty, shows error
  2. `is_civ4_running()` — if True, shows "already running" (prevents duplicate instances!)
  3. `get_latest_local_save(game)` — finds newest `{GameName}_T*.CivBeyondSwordSave` by mtime
  4. `launch_civ4(exe_path, save_file)` — launches with save as CLI argument
- **Detection**: `detect_civ4_path()` checks:
  - Common Steam paths (C/D/E drives)
  - GOG paths
  - Standard Firaxis install paths
  - Windows Registry: `HKLM\SOFTWARE\WOW6432Node\Valve\Steam` → InstallPath
  - Windows Registry: `HKLM\SOFTWARE\WOW6432Node\Firaxis Games\...` → INSTALLDIR
- **Settings UI**: "Sciezka do Civ4 BTS" field + "Przegladaj..." + "Wykryj automatycznie" buttons
- **Important**: NO auto-launch on download. Only manual button. Player decides when to launch.

#### 16. Multi-Language / i18n (`src/i18n.py`)
- Supported: `"pl"` (Polish, default), `"en"` (English)
- `_TRANSLATIONS` dict: key → {"pl": "...", "en": "..."}. ~200 keys covering full UI.
- ALL UI strings use `t()` — no hardcoded Polish/English anywhere in main_window.py
- `I18n` singleton class with `.t(key, **kwargs)` method
- Module-level shortcut: `from src.i18n import t` → `t("your_turn")`, `t("waiting_for", name="Bob")`
- `set_language(lang)` — changes global language at runtime
- **Settings**: language combo (Polski/English) in Ogolne tab
- **Startup**: `main.py` calls `set_language(config.language)` before creating window
- **Runtime refresh**: after language change, `MainWindow._refresh_ui_language()` updates all buttons, labels, status bar, game view — NO restart needed
- Format strings supported: `t("playing_since", name="Alice", time="2h 15m")`
- Missing key returns `"[key_name]"` for debugging

#### 17. Single-Instance Guard (`main.py`)
- `_ensure_single_instance()` called at very start of `main()`
- **Windows**: `CreateMutexW("Civ4PBEMManager_SingleInstance")` — kernel named mutex
  - GetLastError() == 183 → another instance exists
  - Mutex handle stored in function attribute (prevents GC)
- **Linux/Mac**: `fcntl.flock(LOCK_EX | LOCK_NB)` on `~/.config/Civ4PBEMManager/.lock`
- If duplicate detected: shows bilingual QMessageBox warning and calls `sys.exit(0)`
- Message: "Program jest juz uruchomiony! / Application is already running! / Sprawdz zasobnik systemowy (tray)."

#### 18. Encrypted Config / Master Password (`src/crypto.py` + config.py changes)
- **Problem solved**: transport credentials, SMTP passwords stored as plain text JSON → now AES-256 encrypted
- **Master password**: user sets in Settings → Bezpieczenstwo tab
- **Encryption**: Fernet (AES-128-CBC via cryptography lib) with key derived from PBKDF2-HMAC-SHA256 (600k iterations, random 16-byte salt)
- **Config split**:
  - PUBLIC (plain JSON): `save_path`, `check_interval_minutes`, `dark_mode`, `auto_send`, `language`, `civ4_path`, `player_name`, `player_email`
  - PRIVATE (encrypted blob): `transport` dict, `smtp` dict (all credentials)
  - On disk: `config.json` has `"encrypted": {"salt": "...", "data": "..."}` — no plain text secrets
- **Startup flow**:
  1. App loads config → public data available immediately
  2. If `config.has_master_password` → shows `QInputDialog` for password (3 attempts)
  3. Correct → `config.unlock(password)` → full access
  4. Wrong/cancel → app runs in "locked" mode (transport returns `{}`, buttons don't work)
- **Settings UI**:
  - Tab "Bezpieczenstwo": status display, set/change password (with confirm), info text
  - Transport tab: shows "🔒 Dane transportu sa zaszyfrowane" when locked
  - Notifications tab: same lock message when locked
- **AppConfig API**:
  - `config.is_unlocked` → bool
  - `config.has_master_password` → bool
  - `config.unlock(password)` → bool (True if correct)
  - `config.lock()` → clears private data from memory
  - `config.set_master_password(new_password)` → encrypts and saves
  - `config.transport_config` → returns `{}` if locked (safe default)
- **Backwards compatible**: if no encrypted section in config.json (legacy/first run), behaves as unlocked with plain data. Encryption activates only after user sets master password.
- **Crypto module** (`src/crypto.py`): `encrypt_data(dict, password) → blob`, `decrypt_data(blob, password) → dict|None`, `verify_password(blob, password) → bool`
- **Dependency**: `cryptography>=41.0` added to requirements.txt

#### 19. Player Alias Mapping (`Game.local_player_alias`)
- **Problem**: player's local nick (e.g. "kiroman") ≠ game player name (e.g. "K4arol"). Causes mismatches in is_my_turn(), save filenames, download logic.
- **Solution**: `Game.local_player_alias` field — stores the GAME player name this local user maps to
- **On import (.civ4pbem)**:
  1. `QInputDialog.getItem()`: "Ktorym graczem z listy jestes?" — shows all player names from game
  2. User picks their game identity (e.g. "K4arol")
  3. `QInputDialog.getText()`: "Potwierdz email" — confirms/updates notification email
  4. If chosen_name ≠ config.player_name → `game.local_player_alias = chosen_name`
  5. If names match → alias stays empty (no mapping needed)
- **`Game.get_game_player_name(local_name)`**: resolves local nick → game name via alias. If alias set, always returns alias. If empty, returns local_name as-is.
- **`Game.get_my_player(local_name)`**: returns the Player object for the local user (resolving alias)
- **`Game.is_my_turn(my_name)`**: uses `get_game_player_name()` to compare with `current_player.name`
- **`Game.get_save_filename(player_name)`**: uses resolved game name in filename (NOT local nick!)
- **Controller**: `download_save()`, `download_save_list()`, `upload_save()` all use alias-resolved name for finding player index, matching saves by sender name, generating filenames
- **Serialization**: `local_player_alias` saved in game JSON and restored via `from_dict()`
- **Important**: alias is per-game, per-machine. Same player can have different nicks on different PCs.

#### 20. Remote Config Sync (`{GameName}.config` on server)
- **Problem**: if players set different transport configs (wrong host, port, folder), saves end up in wrong places and game breaks after first round.
- **Solution**: shared `{GameName}.config` file uploaded to the remote transport (FTP/SFTP/WebDAV/Email folder)
- **File format** (JSON):
  ```json
  {
    "civ4pbem_config_version": "1.0",
    "name": "GameName",
    "players": [...],
    "transport_config": {...},
    "admin_password": "..."
  }
  ```
- **Upload**: `AppController.upload_game_config(game)` — serializes game config to temp file, uploads as `{GameName}.config`
- **Auto-upload**: first player to upload a save also creates `.config` if it doesn't exist yet (`transport.file_exists()` check in `upload_save()`)
- **Download**: `AppController.download_game_config(game)` → returns `(success, msg, data_dict)`
- **Auto-sync**: `_sync_game_state()` (called on every periodic check) also downloads `.config` and **auto-updates local transport_config** if remote version differs. This ensures all players converge on the same settings.
- **Verify**: `AppController.verify_game_config(game)` → downloads remote config, compares:
  - Player names (missing/extra players)
  - Transport type and host
  - Returns `(all_ok: bool, warnings: list[str])`
- **Design decisions**:
  - First uploader = authoritative config source (game creator)
  - Config is NOT encrypted on server (all players need to read it)
  - Transport config in .config overrides local on sync (remote wins)
  - Only transport_config synced, NOT local_player_alias (that's per-machine)

### Output Requirements
Generate ALL files listed in the project structure. The result should be:
1. Complete, runnable Python source code (all files, no placeholders, no TODOs)
2. A `build.bat` that checks Python, installs deps, builds standalone `.exe`
3. A `generate_icon.py` that creates `icon.ico` using Pillow
4. A `requirements.txt`
5. A `README.md` with usage and build instructions

Code: clean, well-commented (English), ready to use without modifications. Target: Python 3.10+, Windows 10/11.

## PROMPT END
