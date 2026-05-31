# Civ4 PBEM Manager — Instrukcja / User Manual

---

## Spis tresci / Table of Contents

1. [Pierwsze uruchomienie / First Launch](#1-pierwsze-uruchomienie)
2. [Ustawienia / Settings](#2-ustawienia)
3. [Tworzenie gry / Creating a Game](#3-tworzenie-gry)
4. [Obsluga gry / Playing](#4-obsluga-gry)
5. [Uruchom Civ4 / Launch Civ4](#5-uruchom-civ4)
6. [Statystyki / Statistics](#6-statystyki)
7. [Transport — konfiguracja](#7-transport)
8. [Powiadomienia email](#8-powiadomienia-email)
9. [Eksport/Import gry](#9-eksportimport-gry)
10. [Przywracanie tury / Revert](#10-przywracanie-tury)
11. [System tray i zachowanie okna](#11-system-tray)
12. [FAQ / Rozwiazywanie problemow](#12-faq)

---

## 1. Pierwsze uruchomienie

Przy pierwszym uruchomieniu aplikacja:
- Tworzy folder konfiguracji: `%APPDATA%\Civ4PBEMManager\`
- Tworzy domyslny `config.json`
- Wymaga jednorazowej konfiguracji w Ustawieniach

**Single-instance**: Nie mozna uruchomic dwoch kopii programu.
Jesli sprobejsuz, zobaczysz komunikat "Program jest juz uruchomiony"
i powinienes sprawdzic zasobnik systemowy (tray).

---

## 2. Ustawienia

Przycisk **"Ustawienia"** w lewym sidebar. Trzy zakladki:

### Zakladka: Ogolne

| Opcja | Opis |
|-------|------|
| **Twoja nazwa** | Nazwa gracza wyswietlana w grze (musi byc taka sama jak w Civ4) |
| **Twoj email** | Email do powiadomien (inni gracze wysla Ci maila gdy bedzie Twoja kolej) |
| **Folder save'ow** | Gdzie Civ4 zapisuje pliki PBEM. Domyslnie: `Documents\My Games\Beyond the Sword\Saves\pbem` |
| **Sprawdzaj co X min** | Jak czesto sprawdzac serwer (domyslnie 5 min) |
| **Tryb ciemny** | Dark/Light theme (natychmiastowe przelaczanie) |
| **Auto-wyslij save** | Gdy ON: watchdog automatycznie wysle nowy save bez pytania (dla gry fullscreen) |
| **Jezyk / Language** | Polski / English — przelacza caly interfejs w runtime |
| **Sciezka do Civ4 BTS** | Sciezka do `Civ4BeyondSword.exe`. Potrzebna dla przycisku "Uruchom Civ4" |

#### Ustawianie sciezki Civ4:
- **Wykryj automatycznie** — szuka w typowych lokalizacjach (Steam, GOG, standardowe)
- **Przegladaj** — reczny wybor pliku .exe
- Jesli nie ustawisz sciezki, przycisk "Uruchom Civ4" bedzie nieaktywny

### Zakladka: Transport

Domyslna (globalna) konfiguracja transportu. Sluzy jako **szablon** dla nowych gier
(przycisk "Kopiuj z domyslnych" w oknie transportu per-game).

Typy:
- **FTP** — port 21, opcjonalnie FTPS
- **SFTP** — port 22, paramiko
- **WebDAV** — Synology WebDAV Server, Nextcloud, itp.
- **Email** — SMTP upload + IMAP download (tryb shared/individual)

**"Ignoruj bledy SSL"** — zaznacz jesli serwer ma self-signed cert.

### Zakladka: Powiadomienia

Konfiguracja SMTP do powiadomien "Twoja kolej!":
- Host i port musisz podac recznie
- Login i haslo: jesli puste, beda uzyte dane z transportu email
- Powiadomienia sa **niezalezne** od transportu (inny serwer SMTP)

---

## 3. Tworzenie gry

1. Kliknij **"+ Nowa gra"** w sidebar
2. Podaj nazwe gry (bez spacji, np. `WojnaSwiatowa`)
3. Opcjonalnie: haslo admina (wymagane do kasowania save'ow)
4. Dodaj graczy **w kolejnosci tur** (pierwszy gracz = host)
5. Ty jestes dodany automatycznie jako pierwszy

Po utworzeniu: **Eksportuj gre** i wyslij plik `.civ4pbem` innym graczom.
Kazdy importuje i ma gotowa konfiguracje.

---

## 4. Obsluga gry

### Gdy jest Twoja kolej:
1. Banner "TWOJA KOLEJ!" pojawi sie na gorze
2. Kliknij **"Pobierz save"** — sciaga najnowszy save z serwera
3. Kliknij **"Uruchom Civ4"** — odpala gre z tym save'em
4. Zagraj ture w Civ4, zapisz (PBEM save)
5. Kliknij **"Wyslij moj save"** — upload + powiadomienie nastepnego gracza

### Gdy czekasz:
- Aplikacja sprawdza automatycznie co X minut
- Mozesz kliknac **"Sprawdz teraz"** (resetuje timer)
- Przy nowym save: dzwiek + balloon notification w tray

### Auto-send (tryb fullscreen):
Jesli grasz w fullscreen i nie chcesz popupow:
1. Wlacz "Auto-wyslij save" w Ustawieniach
2. Watchdog wykryje nowy save i wysle automatycznie
3. Tylko balloon notification (nie minimalizuje gry)

---

## 5. Uruchom Civ4

Przycisk **"Uruchom Civ4"** (pomaranczowy) w pasku akcji:

- **Sprawdza czy Civ4 juz chodzi** — jesli tak, nie odpala drugiej instancji
- **Znajduje najnowszy save** dla aktywnej gry (po dacie modyfikacji pliku)
- **Odpala Civ4 BTS** z tym save'em jako argument (gra wczyta go automatycznie)

Wymaga ustawienia sciezki do Civ4 w Ustawieniach (zakladka Ogolne).

---

## 6. Statystyki

Przycisk **"Statystyki"** w sidebar. Pokazuje:

| Pole | Opis |
|------|------|
| Gra rozpoczeta | Data i godzina utworzenia gry |
| Ostatnia aktywnosc | Timestamp ostatniej tury |
| Obecna runda | Numer aktualnej rundy |
| Laczna liczba tur | Ile tur zagrali wszyscy gracze |
| Laczny czas gry | Suma czasow wszystkich tur |
| Sredni czas tury | Srednia arytmetyczna |
| Najszybsza tura | Kto i ile (player name) |
| Najwolniejsza tura | Kto i ile |

Plus **tabela per-player**: kazdy gracz — ile tur, sredni czas, laczny czas.

---

## 7. Transport

Kazda gra ma **wlasna konfiguracje transportu** (niezalezna od innych gier).

### Konfiguracja per-game:
1. Zaznacz gre w sidebar
2. Kliknij **"Transport gry..."**
3. Wybierz typ, podaj dane
4. **"Testuj polaczenie"** — sprawdza czy dziala
5. Zapisz

### Kopiowanie konfiguracji:
- **"Kopiuj z domyslnych"** — bierze z globalnych ustawien
- Rozwijana lista — kopiuj z innej gry

### Typy transportu:

#### FTP/SFTP
- Host, port, login, haslo, folder zdalny
- SFTP wymaga portu 22 (paramiko, auto-accept key)

#### WebDAV
- Dziala z Synology WebDAV Server, Nextcloud
- SSL/TLS, ignorowanie bledow certyfikatu

#### Email
- **Tryb shared**: wspolna skrzynka, IMAP filtruje po tagu gry
- **Tryb individual**: SMTP bezposrednio do nastepnego gracza
- UWAGA: **Nie uzywaj prywatnego maila** — program modyfikuje/kasuje maile!

---

## 8. Powiadomienia email

Niezalezne od transportu. Wysylaja "Twoja kolej!" po uploadzie save'a.

- Skonfiguruj w Ustawieniach → Powiadomienia
- Jesli login/haslo puste: uzyje danych z transportu email (ale host/port nigdy!)
- Revert powiadamia WSZYSTKICH graczy
- Upload powiadamia tylko nastepnego gracza

---

## 9. Eksport/Import gry

### Eksport (host gry):
1. Zaznacz gre → **"Eksportuj gre..."**
2. Zapisz plik `.civ4pbem`
3. Wyslij graczom (email, Discord, itp.)

### Import (pozostali gracze):
1. **"Importuj gre..."** w sidebar
2. Wybierz plik `.civ4pbem`
3. Gotowe — gra z pelna konfiguracja transportu

Plik zawiera: nazwe gry, liste graczy, konfiguracje transportu.

---

## 10. Przywracanie tury

Gdy cos poszlo nie tak (crash, blad w turze):

1. Zaznacz ture w "Historii tur" (dolna lista)
2. Kliknij **"Przywroc zaznaczona ture"**
3. Potwierdz — gra wroci do tamtego stanu
4. Wszyscy gracze dostana maila o przywroceniu
5. Stan gry zsynchronizuje sie automatycznie

---

## 11. System tray

- **Przycisk X (zamknij)** = zamyka program
- **Przycisk — (minimalizuj)** = chowa do tray
- **Dwuklik na ikone tray** = przywraca okno
- **Menu kontekstowe tray**: Pokaz okno / Sprawdz teraz / Zamknij
- **Balloon notifications**: informacja o nowym save, Twojej kolei, itp.
- **Dzwiek**: winsound.MessageBeep po auto-pobraniu save'a

---

## 12. FAQ

### Program nie uruchamia sie / "Juz uruchomiony"
Sprawdz tray (zasobnik systemowy obok zegara). Jesli nie ma ikony,
zabij proces `Civ4PBEMManager.exe` w Menedzerze zadan.

### Civ4 nie uruchamia sie z przyciskiem
- Sprawdz sciezke w Ustawieniach → "Sciezka do Civ4 BTS"
- Uzyj "Wykryj automatycznie" lub wskazz reczne
- Jesli gra juz chodzi, przycisk pokaze "Civ4 juz jest uruchomiony"

### Save nie jest pobierany
- Sprawdz transport gry (przycisk "Transport gry..." → "Testuj polaczenie")
- Sprawdz czy folder zdalny istnieje na serwerze
- Sprawdz logi: `%APPDATA%\Civ4PBEMManager\logs\app.log`

### Zmiana jezyka
Ustawienia → Ogolne → Jezyk/Language. Zmiana natychmiastowa (bez restartu).
Niektore elementy (np. tytuly otwartych okien) zmienia sie po zamknieciu/otwarciu.

### Wielokrotne instancje
Program blokuje uruchamianie wiecej niz jednej kopii.
Na Windows: named mutex. Na Linux: file lock.

### Zapomnialem hasla glownego
Musisz usunac plik konfiguracji i ustawic wszystko od nowa:
- Windows: usun `%APPDATA%\Civ4PBEMManager\config.json`
- Linux: usun `~/.config/Civ4PBEMManager/config.json`
Pliki gier (JSONy w `games/`) nie sa zaszyfrowane — pozostana nienaruszone.
Ale transport kazdej gry bedzie wymagal ponownej konfiguracji.

---

## 13. Szyfrowanie danych / Encryption

### Problem
Bez szyfrowania plik `config.json` zawiera w plain text:
- Loginy i hasla do FTP/SFTP/WebDAV
- Hasla SMTP
- Adresy serwerow

Kazdy kto ma dostep do dysku moze je odczytac.

### Rozwiazanie
Dane wrazliwe (transport, SMTP) sa szyfrowane AES-256 z haslem glownym:
- Algorytm: Fernet (AES-128-CBC) z kluczem z PBKDF2-HMAC-SHA256
- Iteracje: 600 000 (ochrona przed brute-force)
- Sol: losowa 16 bajtow (unikalna per-zapis)

### Jak ustawic

1. Otworz **Ustawienia** → zakladka **Bezpieczenstwo**
2. Wpisz nowe haslo + potwierdzenie
3. Kliknij **"Ustaw / zmien haslo"**
4. Gotowe — dane zostaly zaszyfrowane

### Jak to dziala

- **Przy starcie**: program pyta o haslo glowne (3 proby)
- **Poprawne haslo**: pelny dostep do wszystkich funkcji
- **Bledne / anulowanie**: program dziala w trybie "zablokowanym":
  - Pobieranie/wysylanie save'ow **nie dziala** (brak dostepu do danych transportu)
  - Zakladki Transport/Powiadomienia w Ustawieniach pokazuja ikone klodki
  - Reszta aplikacji (przeglad gier, statystyki, Civ4) dziala normalnie
- **Na dysku**: `config.json` zawiera `"encrypted": {"salt": "...", "data": "..."}` — nieczytelne bez hasla

### Co jest szyfrowane, a co nie

| Zaszyfrowane | Niezaszyfrowane |
|---|---|
| Transport (host, login, haslo) | Sciezka save'ow |
| SMTP (host, login, haslo) | Tryb ciemny/jasny |
| Konfiguracja email | Jezyk |
| | Nazwa gracza |
| | Sciezka Civ4 |
| | Interwale sprawdzania |

### Wsteczna kompatybilnosc
Jesli nie ustawisz hasla — config dziala jak wczesniej (plain text).
Szyfrowanie aktywuje sie dopiero po ustawieniu hasla w Bezpieczenstwo.

---

*Wersja dokumentu: 1.2 — odpowiada feature/stats-autolaunch-i18n*
