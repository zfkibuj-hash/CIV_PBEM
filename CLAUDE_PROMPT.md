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
    │   ├── statistics.py            # GameStats, PlayerStats — calculated from turn history
    │   └── turn_calendar.py         # Turn-to-year mapping for all 4 game speeds (Quick/Normal/Epic/Marathon)
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
- Save filename convention on server: `{GameName}_T{turn:04d}_{SenderPlayerName}.CivBeyondSwordSave`
  - The sender name is the **game player name** (resolved via alias)
  - Upload RENAMES the file from Civ4's native naming to our pattern
  - Civ4 locally saves as `GameName_BC-4000_to_NextLeader.CivBeyondSwordSave` — we don't care, we rename on upload
  - Download matches by `_{prev_player_name}.` in filename
- `Game.local_player_alias`: maps local config.player_name → game player name (see section 19)
- `Game.game_speed`: "quick" / "normal" / "epic" / "marathon" — determines turn-to-year mapping
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
  - `civ4pbem_version`: "1.1"
  - `name`: game name
  - `players`: list of players with name, email, order
  - `transport_config`: full transport settings for this game
  - `game_speed`: quick/normal/epic/marathon
  - `smtp`: SMTP notification config (so all players get working notifications on import)
- **Import**: "Importuj gre..." button in sidebar → opens `.civ4pbem` file, creates game locally
  - Checks for duplicate game name (offers to overwrite)
  - **Player identity dialog**: asks "Which player are you?" from list + confirms email (see section 19)
  - **Auto-imports SMTP** if user hasn't configured their own (notifications work without manual setup)
  - Player who sets up the game exports the file and sends it (email, Discord, etc.) to all players
  - Each player imports, picks their identity, and has identical game config + transport + notifications ready to go

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
- Left sidebar (240px): game list, "+ Nowa gra", "Importuj gre...", "Eksportuj gre...", "Edytuj gre...", "Usun gre", "Transport gry...", "Statystyki", "Ustawienia"
- Right panel: header (game name + turn + game year), status banner, player order + time since last turn, action buttons, **filterable** turn history list
- Status bar at bottom
- **Time since last turn**: shows "PlayerName gra juz: X dni, Y godz." below player order
- **History list**: player filter dropdown (all/specific player), shows up to 50 turns, "Uruchom tę turę" button (visible only when any enabled edition has `direct_load=True`)
- **`_clear_game_view()`**: clears right panel when no game selected (e.g. after delete — fixes stale history bug)
- **All sidebar buttons have `self.` references** so they update immediately on language change without restart
- **`_refresh_ui_language()`** updates: all sidebar buttons, action buttons, history group title, filter label, filter combo first item, status bar — NO restart needed

##### Action Buttons
- "Pobierz save" (green), "Wyslij moj save" (blue), "Otworz folder", "Sprawdz teraz"
- "Sprawdz teraz": checks remote + resets periodic timer

##### History panel buttons (under history list)
- "Przywroc zaznaczona ture" (orange)
- "Uruchom te ture" (blue) — visible only when `direct_load_global=True`
- **"Przypomnij o turze"** (purple) — sends reminder to current player via enabled channels
- **"Uruchom Civ4"** (orange) — launches game, moved here from action buttons

##### Settings Dialog (4 tabs: Ogolne, Transport, Powiadomienia, Bezpieczenstwo)
- **Ogolne** (scrollable): player name, email, save path (browse + auto-detect), check interval, dark mode, **auto-send checkbox**, **language selector** (Polski/English), **multi-edition Civ4 installation section**
  - Auto-send: "Auto-wyslij save (bez pytania, dla fullscreen)" — when ON, watchdog uploads automatically with balloon only
  - **Multi-edition section** ("Zainstalowane wersje Civ4 BTS"): three independent groups — Steam, GOG, DVD — each with:
    - "Mam te wersje" checkbox — gdy odznaczony, pola ścieżki i przyciski są wyszarzone (disabled)
    - Path to Civ4BeyondSword.exe + Browse + Auto-detect buttons (active only when checkbox ticked)
  - **Global direct load checkbox** ("Laduj save bezposrednio") — jeden dla wszystkich wersji; gdy zaznaczony, "Uruchom te ture" pojawia się pod historią
  - **Preferred edition** dropdown (ask / Steam / GOG / DVD) — used when multiple editions enabled
  - **File association section**: 3 colored buttons (Steam green / GOG blue / DVD purple) — sets `HKCU\Software\Classes\CivBeyondSwordSave\shell\open\command` to `"exe" /fxsload="%1"` for chosen edition. Shows current association. No admin rights needed (HKCU).
- **Transport**: transport type (ftp/sftp/webdav/email) + SSL ignore checkbox. File group (Host/Port/Login/Password/Remote folder). Email group (Mode/Shared mailbox/SMTP+IMAP fields/From/warning). Shows lock message when config encrypted and locked. All labels via `t()`.
- **Powiadomienia**: przepisana na QScrollArea. **Main switch** "Włącz powiadomienia" — gdy odznaczony, cała sekcja wyszarzona. **Dwa kanały** (niezależne checkboxy):
  - "Przez email (SMTP)" — gdy odznaczony, sekcja SMTP + szablony wyszarzone
  - "Przez aplikację" — tworzy `{GameName}_notify_{PlayerName}.flag` na serwerze transportu; aplikacja odbiorcy wykrywa przy następnym sprawdzeniu, pokazuje popup w tray, usuwa plik. Działa bez SMTP.
  - SMTP settings: Host/Port/Login/Password/From
  - **Szablony wiadomości**: każde pole (subject/body dla tury i przypomnienia) ma etykietę nad polem + rząd przycisków `{game}` `{turn}` `{from_player}` `{to_player}` wstawiających zmienną w miejsce kursora
  - **Auto-reminder**: checkbox + spinner dni
  - Wszystko via `t()`, shows lock message when locked.
- **Bezpieczenstwo**: encryption status (unlocked/locked/no password — each with distinct color), set/change master password (New password + Confirm fields + button), info text. All labels via `t()` — fully translated, no bilingual hardcoded strings.
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
- **Smart game matching**: matches filename prefix to game name (e.g. `Wojna5_BC-3955_to_Alexander...` → game "Wojna5")
- **Skips our own files**: regex `_T\d{4}_` in filename = our pattern (downloaded/uploaded by app) → ignored
- **Only fires on Civ4 native saves**: files Civ4 itself creates after playing a turn
- Emits signal → behavior depends on `auto_send` setting:
  - **auto_send=False** (default): shows popup dialog asking to upload (can minimize fullscreen game!)
  - **auto_send=True**: uploads automatically, only balloon notification (safe for fullscreen play)
- 5-second deduplication cooldown per file. Daemon thread.
- **Ignore list** (`ignore_next(filepath)`): files downloaded BY THE APP are excluded from detection
  - Controller calls `watcher.ignore_next(path)` BEFORE writing a downloaded save
  - Entries auto-expire after 30 seconds (safety against stale entries)
  - Path normalization (resolve()) ensures consistent matching

#### 12. Windows Integration
- `SetCurrentProcessExplicitAppUserModelID` for taskbar icon
- `get_resource_path()` for dev vs frozen paths
- `setWindowIcon()` on both app and window
- `build.spec`: excludes ~25 unused Qt modules, filters heavy binaries, UPX enabled
- `build.bat`: checks Python/UPX, shows final size. Target: ~20-25MB (with UPX: ~15-18MB)

#### 13. Config
- `%APPDATA%/Civ4PBEMManager/config.json`
- Keys: save_path, check_interval_minutes, dark_mode, auto_send, player_name, player_email, transport, smtp, **language**, **window_geometry**, **preferred_edition**, **civ4_installations**, **direct_load_global** (bool), **notifications_enabled** (bool, default True), **notify_via_smtp** (bool, default True), **notify_via_app** (bool, default False), **reminder_auto_enabled** (bool), **reminder_auto_days** (int), **export_skip_password_prompt** (bool)
- **`civ4_installations`**: `{"steam": {"enabled", "exe_path"}, "gog": {...}, "dvd": {...}}` — no per-edition direct_load (replaced by global `direct_load_global`)
- **`smtp`** includes: host, port, username, password, use_tls, from_address, **subject_template**, **body_template**, **reminder_subject_template**, **reminder_body_template**
- `AppConfig.get_enabled_editions()` → list of enabled edition keys with exe_path set
- `AppConfig.civ4_path` → legacy property, returns first enabled exe_path
- App version: **v4.0.0**

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
- Turn calendar: game year displayed alongside turn number everywhere in UI (header, sidebar, history, stats)
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
  1. `_resolve_edition_for_launch()` — picks which edition to use (see below)
  2. `is_civ4_running()` — if True, shows "already running" (prevents duplicate instances!)
  3. `get_latest_local_save(game)` — finds newest `{GameName}_T*.CivBeyondSwordSave` by mtime (only if `direct_load=True` for chosen edition)
  4. `launch_civ4(exe_path, save_file, edition)` — launches with `/fxsload=` if save provided
- **Edition resolution** (`_resolve_edition_for_launch()`):
  - 0 enabled editions → error "civ4_not_found"
  - 1 enabled edition → use it directly, no dialog
  - 2-3 enabled editions + preferred set → use preferred
  - 2-3 enabled editions + no preference → shows **button dialog** with colored buttons (Steam=green, GOG=blue, DVD=purple) + "Remember choice" checkbox
- **Launch command** (ALL editions use same syntax — confirmed from Windows registry):
  - With save: `"Civ4BeyondSword.exe" /fxsload="C:\...\save.CivBeyondSwordSave"`
  - Without save: `"Civ4BeyondSword.exe"` (plain launch)
  - Note: Steam BTS also supports `/fxsload=` directly via exe (no Steam.exe needed)
- **Per-edition detection** (`detect_civ4_for_edition(edition)`):
  - Steam: checks `...\Beyond the Sword\Civ4BeyondSword.exe` subfolder + registry
  - GOG: checks GOG paths + registry INSTALLDIR
  - DVD: checks Firaxis paths + registry INSTALLDIR
  - Generic `detect_civ4_path()` tries all three editions
- **Save path detection**: `detect_save_path()` checks Documents, OneDrive, Dokumenty
- **File association** (`set_file_association(edition, exe_path)`):
  - Writes `HKCU\Software\Classes\CivBeyondSwordSave\shell\open\command`
  - Command: `"exe_path" /fxsload="%1"` (same for all editions)
  - No admin rights needed (HKCU). Shows current association in UI.
  - `get_current_file_association()` reads current command from HKCU or HKLM
- **"Uruchom tę turę" button**: visible in history panel when any enabled edition has `direct_load=True`
- **Important**: NO auto-launch on download. Only manual button. Player decides when to launch.

#### 16. Multi-Language / i18n (`src/i18n.py`)
- Supported: `"pl"` (Polish, default), `"en"` (English)
- `_TRANSLATIONS` dict: key → {"pl": "...", "en": "..."}. ~250 keys covering full UI.
- ALL UI strings use `t()` — no hardcoded Polish/English anywhere in main_window.py
- `I18n` singleton class with `.t(key, **kwargs)` method
- Module-level shortcut: `from src.i18n import t` → `t("your_turn")`, `t("waiting_for", name="Bob")`
- `set_language(lang)` — changes global language at runtime
- **Settings**: language combo (Polski/English) in Ogolne tab
- **Startup**: `main.py` calls `set_language(config.language)` before creating window
- **Runtime refresh**: after language change, `MainWindow._refresh_ui_language()` updates all buttons, labels, status bar, game view — NO restart needed
- Format strings supported: `t("playing_since", name="Alice", time="2h 15m")`
- Missing key returns `"[key_name]"` for debugging
- **Key corrections**: `history_group` = "wybierz aby przywrocic" (not "kliknij"), `waiting` = "Czeka na" / "Waiting for"
- **Full coverage**: Transport tab (transport_method, file_transport_group, email_transport_group, field_host/port/login/password/remote_dir/mode/shared_mailbox/from, ssl_ignore, transport_locked), Notifications tab (notifications_group, notifications_info, smtp_locked), Security tab (security_status_unlocked/locked/no_password, master_password_group, new_password, confirm_password, set_password_btn, security_info, password_mismatch/empty/set_ok/locked_error), GameTransportDialog (game_transport_copy_group, transport_test_btn, transport_not_configured_short), tray_minimized_msg, edition keys (civ4_edition, civ4_edition_none/steam/gog/dvd), Steam keys (steam_path, steam_app_id, detect_steam, steam_detected/not_detected/not_found)

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
  - Tab "Bezpieczenstwo": status (🔓 unlocked / 🔒 locked / ⚠ no password — each with distinct color), set/change password (New password + Confirm fields + button), info text — all via `t()`
  - Transport tab: shows `t("transport_locked")` lock message when locked
  - Notifications tab: shows `t("smtp_locked")` lock message when locked
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

#### 21. Turn Calendar / Game Year Display (`src/models/turn_calendar.py`)
- **Problem**: Civ4 displays game year (e.g. "4000 BC", "1200 AD") but our app only showed turn numbers
- **Solution**: `turn_calendar.py` maps turn number → game year based on selected speed
- **Game speed** stored in `Game.game_speed` field, selected in NewGameDialog (QComboBox):
  - Quick: 330 turns
  - Normal: 500 turns (default)
  - Epic: 750 turns
  - Marathon: 1500 turns
- **Data structure**: `SPEED_DATA[speed]` = list of `(num_turns, years_per_turn)` tuples per iteration
  - All speeds start at 4000 BC and end at 2050 AD
  - Fractional years_per_turn for later eras (0.5 = 2 turns/year, 0.25 = 4 turns/year)
- **API**:
  - `turn_to_year(turn, speed)` → float (negative=BC, positive=AD)
  - `format_game_year(year)` → "4000 BC" / "100 AD"
  - `turn_to_year_str(turn, speed)` → combined helper
  - `get_total_turns(speed)` → int
- **Displayed in UI** (always alongside turn number):
  - Game view header: "GameName - Turn 50 (1000 BC)"
  - Sidebar game list: "[Turn 50, 1000 BC]"
  - History list: "... → Turn 50 (1000 BC) [filename]"
  - Statistics dialog: "Current round: 50 (1000 BC)"
- **NewGameDialog**: speed selector dropdown with total turns shown
- **Export (.civ4pbem)**: game_speed included so imported games show correct years

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

#### 22. Edit Game Dialog (`EditGameDialog`)
- **"Edytuj gre..." button** in sidebar → opens dialog for currently selected game
- **Editable fields**:
  - Game speed (Quick/Normal/Epic/Marathon dropdown)
  - Player alias ("I am player:" dropdown — change game identity)
  - Player emails (one text field per player, editable)
- **No game rename** — name is immutable (used as filename on server and in save pattern)
- Saves changes directly to game JSON on Accept
- Refreshes game view and sidebar after save

#### 23. Player Reminder (`src/notifier/email_notifier.py` + `AppController`)
- **"Przypomnij o turze" button** (purple) under history list, next to "Przywroc" and "Uruchom Civ4"
- `EmailNotifier.send_reminder(to_email, game_name, turn_number, to_player, from_player)` — uses reminder templates
- `AppController.send_reminder(game)` — sends via all enabled channels (SMTP + in-app), returns `(success, message_key)`
- **Auto-reminder**: `check_for_new_saves()` checks elapsed time; if `reminder_auto_enabled=True` and elapsed >= `reminder_auto_days * 86400s`, sends reminder once per threshold (tracked via `Game.last_reminder_sent`)
- `Game.last_reminder_sent` — float timestamp, persisted in game JSON

#### 24. Notification Templates (Settings → Powiadomienia)
- Editable fields for subject/body of turn notification and reminder
- Each field has label above + row of variable-insert buttons: `{game}` `{turn}` `{from_player}` `{to_player}` — click inserts at cursor position (works for both QLineEdit and QTextEdit)
- Empty = use built-in default template
- Saved in `smtp` config dict

#### 25. Import Game → Replace Global Settings
- During `.civ4pbem` import: if file contains `transport_config` or `smtp`, shows dialog asking to replace global transport + SMTP settings
- Yes → overwrites global `transport` and `smtp` config
- No → keeps existing (old behaviour)

#### 26. In-App Notifications (via transport flag files)
- **Channel**: `notify_via_app` — works without SMTP, uses same transport as saves
- **Upload** (`_upload_notify_flag`): after `upload_save()` or `send_reminder()`, creates `{GameName}_notify_{ToPlayer}.flag` on server with JSON: `{game, to_player, from_player, turn, timestamp, kind}`
  - `kind`: `"turn"` (new save uploaded) or `"reminder"` (manual/auto reminder)
- **Download** (`check_for_new_saves`): checks for `{GameName}_notify_{MyGameName}.flag` on server; if found → downloads, shows tray notification, deletes flag from server
- **No SMTP needed** — purely transport-based; all players must have `notify_via_app` enabled
- **Coexists with SMTP**: both channels can be active simultaneously (independent checkboxes)
- `BaseTransport.delete(filename, game_name)` — used to remove flag after reading

### Output Requirements
Generate ALL files listed in the project structure. The result should be:
1. Complete, runnable Python source code (all files, no placeholders, no TODOs)
2. A `build.bat` that checks Python, installs deps, builds standalone `.exe`
3. A `generate_icon.py` that creates `icon.ico` using Pillow
4. A `requirements.txt`
5. A `README.md` with usage and build instructions

Code: clean, well-commented (English), ready to use without modifications. Target: Python 3.10+, Windows 10/11.

## PROMPT END
