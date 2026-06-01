# Civ4 PBEM Manager v3.0

A desktop application for managing Play-By-Email (PBEM) games in Civilization 4: Beyond the Sword.

> **Note**: This application was entirely written by AI (Claude/Kiro LLM). It is free to use, modify, and redistribute. Contributions, bug reports, and feature requests are welcome!

## Features

- **Save transport**: FTP / SFTP / WebDAV / Email (per-game configuration)
- **Email notifications**: Automatic "your turn!" emails with customizable templates
- **Multi-game support**: Run multiple parallel PBEM games
- **Smart watchdog**: Auto-detects Civ4 saves by game name, uploads automatically
- **Launch Civ4**: One-click launch with any save from history
- **Game statistics**: Per-player turn times, averages, fastest/slowest turns
- **Turn calendar**: Displays in-game year (4000 BC → 2050 AD) based on game speed
- **Multi-language**: Polish / English with runtime switching
- **Encrypted config**: Master password protects credentials on disk (AES-256)
- **Single-instance**: Prevents multiple app copies from running
- **System tray**: Minimize to tray, balloon notifications, sound alerts
- **Dark/Light theme**: Runtime toggle

## Quick Start

1. Run the app, go to **Settings**
2. Set your player name, email, save folder path, Civ4 path
3. Create a new game (**+ New Game**), add players in turn order, select speed
4. Configure transport (**Game transport...**)
5. **Export** the `.civ4pbem` file and share with other players
6. Other players **Import** → pick their identity → done!

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

## Contributing

This project was created by AI and is maintained as an open experiment. Feel free to:
- Fork and modify
- Submit pull requests with fixes or new features
- Report issues
- Suggest improvements

No coding experience required to play — just download the release and follow the Quick Start above.

---

## 🇵🇱 Polski

Aplikacja desktopowa do obslugi gier Play-By-Email (PBEM) w Civilization 4: Beyond the Sword.

> **Uwaga**: Aplikacja zostala w calosci napisana przez AI (Claude/Kiro LLM). Jest darmowa, mozna ja dowolnie modyfikowac i rozpowszechniac. Poprawki i pomysly mile widziane!

### Glowne funkcje

- Transport save'ow (FTP/SFTP/WebDAV/Email)
- Powiadomienia email o turze
- Smart watchdog — automatyczne wykrywanie i wysylanie save'ow
- Uruchamianie Civ4 z wybranym save'em
- Statystyki gry i kalendarz turowy
- Szyfrowanie konfiguracji haslem glownym
- Interfejs PL/EN z przelaczaniem w runtime

### Szybki start

1. Uruchom → Ustawienia → podaj nick, email, folder save'ow, sciezke Civ4
2. Nowa gra → dodaj graczy → wybierz predkosc → skonfiguruj transport
3. Eksportuj `.civ4pbem` i wyslij innym graczom
4. Graj turę → watchdog automatycznie wysle save i powiadomi nastepnego gracza

Pelna instrukcja: **[MANUAL.md](MANUAL.md)**

## License

MIT
