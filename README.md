# Civ4 PBEM Manager

Desktopowa aplikacja Windows do obslugi gier Play-By-Email (PBEM) w Civilization 4: Beyond the Sword.

## Funkcje

- **Transport plikow**: FTP / SFTP / WebDAV (Synology Cloud)
- **Powiadomienia email**: Automatyczne maile do nastepnego gracza
- **Wiele gier**: Obsluga wielu rownoczesnych gier PBEM
- **Automatyczne sprawdzanie**: Cykliczne sprawdzanie nowych save'ow
- **Synchronizacja stanu**: Automatyczna synchronizacja stanu gry miedzy graczami
- **Nowoczesny interfejs**: PyQt5, ciemny motyw

## Instalacja

### Z kodu zrodlowego

```bash
pip install -r requirements.txt
python main.py
```

### Budowanie .exe (Windows)

```bash
pip install -r requirements.txt
pyinstaller build.spec
```

Wynikowy plik: `dist/Civ4PBEMManager.exe`

## Konfiguracja

Przy pierwszym uruchomieniu:

1. Przejdz do **Ustawienia**
2. Podaj swoja nazwe gracza i email
3. Wskaz folder save'ow Civ4 (domyslnie: `Documents\My Games\Beyond the Sword\Saves\pbem`)
4. Skonfiguruj transport (FTP/SFTP/WebDAV)
5. Skonfiguruj SMTP do powiadomien email

## Uzytkowanie

1. **Nowa gra**: Kliknij "+ Nowa gra", podaj nazwe i dodaj graczy w kolejnosci tur
2. **Pobierz save**: Gdy jest Twoja kolej, kliknij "Pobierz save"
3. **Zagraj ture**: Otworz Civ4, zagraj, zapisz
4. **Wyslij save**: Kliknij "Wyslij moj save" - aplikacja uploaduje plik i powiadomi nastepnego gracza

## Architektura

```
src/
  config.py          - Zarzadzanie konfiguracja (JSON)
  models/
    game.py          - Modele danych: Game, Player, Turn
  transport/
    base.py          - Interfejs bazowy transportu
    ftp_transport.py - Transport FTP
    sftp_transport.py - Transport SFTP (paramiko)
    webdav_transport.py - Transport WebDAV (Synology/Nextcloud)
  notifier/
    email_notifier.py - Powiadomienia SMTP
  gui/
    main_window.py   - Glowne okno aplikacji (PyQt5)
    app_controller.py - Kontroler laczacy GUI z logika
main.py              - Punkt wejscia
build.spec           - Konfiguracja PyInstaller
```

## Wymagania

- Python 3.10+
- PyQt5
- paramiko (dla SFTP)
- watchdog (planowane: monitoring folderu)
- keyring (planowane: bezpieczne przechowywanie hasel)

## Licencja

MIT
