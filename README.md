# Civ4 PBEM Manager

Desktopowa aplikacja do obslugi gier Play-By-Email (PBEM) w Civilization 4: Beyond the Sword.

## Funkcje

- **Transport plikow**: FTP / SFTP / WebDAV / Email (per-game config)
- **Powiadomienia email**: Automatyczne maile do nastepnego gracza
- **Wiele gier**: Obsluga wielu rownoczesnych gier PBEM
- **Automatyczne sprawdzanie**: Cykliczne sprawdzanie nowych save'ow + watchdog
- **Uruchom Civ4**: Przycisk "Uruchom Civ4" odpala gre z ostatnim pobranym save'em
- **Statystyki gry**: Czas tur, srednie, najszybsza/najwolniejsza tura, per-player stats
- **Multi-language**: Polski / English (przelaczanie w runtime)
- **Single-instance**: Ochrona przed wielokrotnym uruchomieniem
- **System tray**: Minimalizacja do zasobnika, powiadomienia balloon
- **Ciemny/jasny motyw**: Przelaczanie w ustawieniach

## Instalacja

### Z kodu zrodlowego

```bash
pip install -r requirements.txt
python main.py
```

### Budowanie .exe (Windows)

```bash
build.bat
```

Wynikowy plik: `dist/Civ4PBEMManager.exe` (~20-25 MB, z UPX ~15-18 MB)

## Szybki start

1. Uruchom aplikacje
2. Przejdz do **Ustawienia** (lewy sidebar)
3. Podaj nazwe gracza, email, folder save'ow
4. Ustaw sciezke do Civ4 BTS (przycisk "Wykryj automatycznie" lub "Przegladaj")
5. Skonfiguruj transport (zakladka Transport)
6. Utworz gre: **+ Nowa gra** → dodaj graczy w kolejnosci tur
7. Kazdy gracz importuje plik `.civ4pbem` (eksport/import w sidebar)

Pelna instrukcja: **[MANUAL.md](MANUAL.md)**

## Architektura

```
CIV_PBEM/
├── main.py                 # Entry point + single-instance guard
├── src/
│   ├── config.py           # AppConfig (JSON, %APPDATA%)
│   ├── i18n.py             # Internationalization PL/EN
│   ├── launcher.py         # Civ4 detection + launch
│   ├── models/
│   │   ├── game.py         # Game, Player, Turn dataclasses
│   │   └── statistics.py   # Game statistics calculations
│   ├── transport/
│   │   ├── base.py         # BaseTransport ABC
│   │   ├── ftp_transport.py
│   │   ├── sftp_transport.py
│   │   ├── webdav_transport.py
│   │   └── email_transport.py
│   ├── notifier/
│   │   └── email_notifier.py
│   └── gui/
│       ├── main_window.py  # MainWindow + dialogs + GameStatsDialog
│       ├── app_controller.py
│       ├── tray_icon.py
│       └── file_watcher.py
├── build.bat / build.spec  # Windows build
└── MANUAL.md               # User manual
```

## Wymagania

- Python 3.10+
- PyQt5 >= 5.15
- paramiko >= 3.0 (SFTP)
- watchdog >= 3.0 (file monitoring)
- PyInstaller >= 6.0 (build)

## Licencja

MIT
