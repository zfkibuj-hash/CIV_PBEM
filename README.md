# Civ4 PBEM Manager v4.0

A desktop application for managing Play-By-Email (PBEM) games in Civilization 4: Beyond the Sword.

> **Note**: This application was entirely written by AI (Claude/Kiro LLM). It is free to use, modify, and redistribute. Contributions, bug reports, and feature requests are welcome!

## Features

### Core
- **Save transport**: FTP / SFTP / WebDAV / Email (per-game configuration)
- **Multi-game support**: Run multiple parallel PBEM games
- **Smart watchdog**: Auto-detects Civ4 saves by game name, uploads automatically or asks
- **Auto-send mode**: Silent upload without popup — safe for fullscreen play
- **Game statistics**: Per-player turn times, averages, fastest/slowest turns
- **Turn calendar**: Displays in-game year (4000 BC → 2050 AD) based on game speed
- **Turn revert**: Roll back to any previous turn with full history
- **Multi-language**: Polish / English with runtime switching (no restart needed)
- **Encrypted config**: Master password protects credentials on disk (AES-256)
- **Single-instance guard**: Prevents multiple app copies from running
- **System tray**: Minimize to tray, balloon notifications, sound alerts
- **Dark/Light theme**: Runtime toggle

### Notifications
- **Email (SMTP)**: Automatic "your turn!" emails with fully customizable templates
- **In-app channel**: Flag files on transport server — no SMTP needed, works with any transport
- **Reminder button**: Manually nudge the current player via email and/or in-app
- **Auto-reminder**: Automatically remind after X days of inactivity
- **Master switch**: Enable/disable all notifications at once
- **Template editor**: Edit subject and body with one-click variable insertion (`{game}`, `{turn}`, `{from_player}`, `{to_player}`)

### Civ4 Launcher
- **Multi-edition support**: Steam, GOG, DVD — each with its own exe path
- **Direct save loading**: `/fxsload=` parameter loads save directly into Civ4 (confirmed working on Steam/GOG/DVD)
- **Edition picker dialog**: Colored buttons (Steam/GOG/DVD) when multiple editions installed
- **File association**: Set Windows `.CivBeyondSwordSave` association for any edition directly from app (no admin rights needed)
- **Remember choice**: Option to always use preferred edition

### Game Management
- **Export/Import** `.civ4pbem` files — share full game config with other players
- **Import → replace global settings**: Optionally overwrite transport + SMTP with game's settings
- **Player alias mapping**: Local nick ≠ game name — resolved transparently
- **Edit game**: Change player emails, game speed, alias at any time
- **Admin password**: Protect save deletion with a password

## Quick Start

1. Run the app → **Settings** → set player name, email, save folder
2. In **Settings → General**: configure your Civ4 installation (Steam/GOG/DVD)
3. **+ New Game** → add players in turn order → select speed → configure transport
4. **Export** the `.civ4pbem` file and share with other players
5. Other players **Import** → pick their identity → done!

After setup: play your turn in Civ4 → watchdog auto-detects → uploads → notifies next player.

## Installation

```bash
pip install -r requirements.txt
python main.py
```

### Build Windows .exe

```bash
build.bat
```

Output: `dist/Civ4PBEMManager.exe` (~20-25 MB, with UPX ~15-18 MB)

## Requirements

- Python 3.10+
- PyQt5 >= 5.15
- paramiko >= 3.0
- watchdog >= 3.0
- cryptography >= 41.0
- PyInstaller >= 6.0 (build only)

## Documentation

- **[MANUAL.md](MANUAL.md)** — Full user manual (Polish)
- **[CLAUDE_PROMPT.md](CLAUDE_PROMPT.md)** — Complete technical specification for AI/LLM regeneration

## Changelog

### v4.0.0
- Multi-edition Civ4 launcher (Steam/GOG/DVD) with edition picker dialog
- Direct save loading via `/fxsload=` for all editions
- Windows file association manager (no admin rights)
- In-app notifications via transport flag files (no SMTP needed)
- Notification master switch + two independent channels (SMTP / in-app)
- Reminder button + auto-reminder after X days
- Email template editor with variable-insert buttons
- Import game → optionally replace global transport/SMTP settings
- Simplified settings: one global direct-load checkbox, edition paths disabled until enabled

### v3.0.0
- Game statistics (per-player turn times, averages)
- Turn calendar (in-game year display)
- Auto-launch Civ4 with save
- Multi-language UI (PL/EN, runtime switching)
- Encrypted config (AES-256 master password)
- Single-instance guard
- Player alias mapping
- Turn revert with notifications
- Edit game dialog

---

## 🇵🇱 Polski

Aplikacja desktopowa do obslugi gier Play-By-Email (PBEM) w Civilization 4: Beyond the Sword.

> **Uwaga**: Aplikacja zostala w calosci napisana przez AI (Claude/Kiro LLM). Jest darmowa, mozna ja dowolnie modyfikowac i rozpowszechniac.

### Glowne funkcje

- Transport save'ow: FTP / SFTP / WebDAV / Email (konfiguracja per-gra)
- Powiadomienia email i przez aplikacje (bez SMTP)
- Przycisk ponaglenia gracza + automatyczne przypomnienia
- Edytor szablonow maili z przyciskami wstawiania zmiennych
- Obsluga wielu wersji Civ4 (Steam/GOG/DVD) z dialogiem wyboru
- Bezposrednie ladowanie save'a przez `/fxsload=`
- Ustawianie skojarzenia plikow `.CivBeyondSwordSave` bez uprawnien admina
- Smart watchdog — automatyczne wykrywanie i wysylanie save'ow
- Statystyki gry i kalendarz turowy
- Szyfrowanie konfiguracji haslem glownym (AES-256)
- Interfejs PL/EN z przelaczaniem w runtime

### Szybki start

1. Uruchom → Ustawienia → podaj nick, email, folder save'ow
2. Ustawienia → Ogolne → skonfiguruj wersje Civ4 (Steam/GOG/DVD)
3. Nowa gra → dodaj graczy → wybierz predkosc → skonfiguruj transport
4. Eksportuj `.civ4pbem` i wyslij innym graczom
5. Graj ture → watchdog automatycznie wysle save i powiadomi nastepnego gracza

Pelna instrukcja: **[MANUAL.md](MANUAL.md)**

## License

MIT
