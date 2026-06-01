# Civ4 PBEM Manager v4.0

<p align="center">
  <img src="icon_preview.png" alt="Civ4 PBEM Manager" width="512"/>
</p>

<p align="center">
  <strong>Stop clicking through menus. Start playing.</strong>
</p>

---

## What is this?

Civilization 4: Beyond the Sword is a 20-year-old game with no built-in online multiplayer infrastructure worth speaking of. Yet thousands of people still play it — passing save files back and forth by email, Discord, or shared folders, manually tracking whose turn it is, manually launching the game, manually notifying the next player.

**Civ4 PBEM Manager** automates all of that.

You play your turn. The app detects the save, uploads it to your shared server, and emails (or pings via the app itself) the next player. They download it, launch Civ4, and play. No spreadsheets. No "hey did you get my save?" messages. No forgotten turns sitting in someone's inbox for a week.

It was built entirely by AI (Claude / Kiro) as pure vibecoding for fun. The human provided the vision, tested the builds, and kept the AI on track. The AI wrote every line of code.

---

## What it does

### The core loop
- Watches your Civ4 save folder for new saves
- Uploads them to a shared server (FTP, SFTP, WebDAV, or Email)
- Notifies the next player — via email (SMTP) or directly through the app (no SMTP needed)
- Downloads saves when it's your turn
- Launches Civ4 with the right save, optionally loading it directly

### Everything else
- **Multi-game**: manage as many parallel PBEM games as you want
- **Multi-edition**: Steam, GOG, DVD — each with its own path and launch method
- **Direct save loading**: `/fxsload=` parameter skips the main menu entirely
- **File association**: set Windows to open `.CivBeyondSwordSave` files with your preferred edition
- **Turn history**: full log of every turn, with revert capability
- **Game statistics**: who plays fastest, who takes the longest, average turn times
- **Turn calendar**: shows in-game year (4000 BC → 2050 AD) everywhere in the UI
- **Reminder system**: nudge the current player manually or automatically after X days
- **In-app notifications**: flag files on the transport server — works without any email setup
- **Encrypted config**: master password protects your server credentials on disk (AES-256)
- **Export/Import**: share a `.civ4pbem` file with other players — they import it and are ready to go
- **Polish / English UI**: runtime language switching, no restart needed
- **Dark / Light theme**: because some of us play at night

---

## What it does NOT do

This is important. The app is a **coordinator**, not a game client.

- ❌ It does not modify Civ4 in any way
- ❌ It does not host a game server
- ❌ It does not handle simultaneous turns (hotseat only, not true multiplayer)
- ❌ It does not work with mods that change the save format in incompatible ways
- ❌ It does not guarantee `/fxsload=` works on your system — this depends on your Windows version, Civ4 version, and registry state. It works on most setups but not all.
- ❌ It does not send notifications if you haven't configured a transport (you need somewhere to put the files)
- ❌ It does not replace the need for all players to have the same mods installed
- ❌ It is not a replacement for Pitboss or any real multiplayer infrastructure

---

## Download

**Windows .exe** is available in [Releases](https://github.com/zfkibuj-hash/CIV_PBEM/releases) -- no Python installation needed.

Just download `Civ4PBEMManager.exe` and run it.

1. Run the app → **Settings → General**
2. Set your player name, email, save folder path
3. Configure your Civ4 installation (Steam / GOG / DVD)
4. **+ New Game** → add players in turn order → select game speed
5. **Game transport...** → configure your shared server
6. **Export** the `.civ4pbem` file → send it to other players
7. Other players **Import** → pick their identity → done

After setup: play your turn in Civ4 → watchdog detects the save → uploads → notifies next player → they download and play.

---

## Installation

```bash
pip install -r requirements.txt
python main.py
```

### Build standalone .exe (Windows)

```bash
build.bat
```

Output: `dist/Civ4PBEMManager.exe` (~28 MB)

### Requirements

- Python 3.10+
- PyQt5 >= 5.15
- paramiko >= 3.0
- watchdog >= 3.0
- cryptography >= 41.0
- PyInstaller >= 6.0 (build only)

---

## Features at a glance

| Feature | Details |
|---|---|
| Transport | FTP, SFTP, WebDAV, Email (per-game) |
| Notifications | SMTP email + in-app flag files |
| Launcher | Steam / GOG / DVD, direct save load |
| Languages | Polish, English (runtime switch) |
| Security | AES-256 encrypted credentials |
| History | Full turn log, revert to any turn |
| Statistics | Per-player times, averages |
| Calendar | In-game year display |
| Reminders | Manual + auto after X days |

---

## Changelog

### v4.0.0
- Multi-edition launcher (Steam/GOG/DVD) with colored picker dialog
- Direct save loading via `/fxsload=` — confirmed working on Steam, GOG, DVD
- Windows file association manager (no admin rights needed)
- In-app notifications via transport flag files — no SMTP required
- Notification master switch + two independent channels
- Reminder button + auto-reminder after X days of inactivity
- Email template editor with one-click variable insertion
- Import game → optionally replace global transport/SMTP settings
- Simplified settings: one global direct-load checkbox

### v3.0.0
- Game statistics and turn calendar
- Auto-launch Civ4 with save
- Polish/English UI with runtime switching
- AES-256 encrypted config
- Single-instance guard
- Player alias mapping
- Turn revert with player notifications
- Edit game dialog

---

## 🇵🇱 Polski

### Po co to powstało?

Civilization 4 to gra sprzed 20 lat, która nie ma żadnej sensownej infrastruktury do gry przez internet. A mimo to tysiące ludzi nadal w nią gra — przesyłając save'y mailem, przez Discorda albo współdzielone foldery, ręcznie śledząc czyja tura, ręcznie uruchamiając grę, ręcznie powiadamiając następnego gracza.

**Civ4 PBEM Manager** automatyzuje to wszystko.

Grasz swoją turę. Aplikacja wykrywa save, wysyła go na serwer i powiadamia następnego gracza — mailem albo bezpośrednio przez aplikację. Oni pobierają save, uruchamiają Civ4 i grają. Bez arkuszy kalkulacyjnych. Bez "hej, dostałeś mój save?". Bez tur leżących zapomniane w czyjejś skrzynce przez tydzień.

### Czego to nie ogarnia?

Aplikacja jest **koordynatorem**, nie klientem gry.

- ❌ Nie modyfikuje Civ4 w żaden sposób
- ❌ Nie hostuje serwera gry
- ❌ Nie obsługuje jednoczesnych tur (tylko kolejkowe PBEM)
- ❌ Nie gwarantuje że `/fxsload=` zadziała na Twoim systemie — zależy od wersji Windows, wersji Civ4 i stanu rejestru
- ❌ Nie zastępuje konieczności posiadania tych samych modów przez wszystkich graczy
- ❌ Nie działa bez skonfigurowanego transportu (potrzebujesz miejsca na pliki)

### Szybki start

1. Uruchom → Ustawienia → podaj nick, email, folder save'ów
2. Ustawienia → Ogólne → skonfiguruj wersję Civ4 (Steam/GOG/DVD)
3. Nowa gra → dodaj graczy → wybierz prędkość → skonfiguruj transport
4. Eksportuj `.civ4pbem` i wyślij innym graczom
5. Graj turę → watchdog automatycznie wyśle save i powiadomi następnego gracza

Pełna instrukcja: **[MANUAL.md](MANUAL.md)**

---

## About

Built entirely by AI (Claude / Kiro LLM) as pure vibecoding for fun. The human provided the vision, tested the builds, and kept the AI on track. The AI wrote every line of code. The human has zero programming knowledge and cannot fix bugs or implement feature requests on their own.

You are welcome to report bugs and suggest features in the Issues tab. Just know that fixes depend on AI assistance, not a developer sitting behind the keyboard. If you know Python and want to contribute, pull requests are very welcome.

Free to use, modify, and redistribute. MIT License.
