"""
Internationalization (i18n) module for Civ4 PBEM Manager.
Supports Polish (PL) and English (EN) with runtime language switching.
"""
from typing import Dict

# Supported languages
LANGUAGES = ["pl", "en"]
DEFAULT_LANGUAGE = "pl"

# Translation dictionary: key -> {lang: translation}
_TRANSLATIONS: Dict[str, Dict[str, str]] = {
    # --- Main Window ---
    "app_title": {
        "pl": "Civ4 PBEM Manager",
        "en": "Civ4 PBEM Manager",
    },
    "my_games": {
        "pl": "MOJE GRY",
        "en": "MY GAMES",
    },
    "new_game": {
        "pl": "+ Nowa gra",
        "en": "+ New Game",
    },
    "import_game": {
        "pl": "Importuj plik .civ4pbem...",
        "en": "Import .civ4pbem file...",
    },
    "export_game": {
        "pl": "Eksportuj plik .civ4pbem...",
        "en": "Export .civ4pbem file...",
    },
    "join_game": {
        "pl": "Dolacz do gry",
        "en": "Join game",
    },
    "join_game_hint": {
        "pl": "Import pliku .civ4pbem albo wklejenie kodu zaproszenia.",
        "en": "Import a .civ4pbem file or paste an invite code.",
    },
    "share_game": {
        "pl": "Udostepnij gre",
        "en": "Share game",
    },
    "share_game_hint": {
        "pl": "Eksport pliku .civ4pbem albo skopiowanie kodu zaproszenia (Discord).",
        "en": "Export a .civ4pbem file or copy an invite code (Discord).",
    },
    "game_list_hint": {
        "pl": "Prawy przycisk myszy: kod zaproszenia, import i eksport.",
        "en": "Right-click: invite code, import and export.",
    },
    "copy_invite_code": {
        "pl": "Kopiuj kod zaproszenia",
        "en": "Copy invite code",
    },
    "copy_invite_code_hint": {
        "pl": "Kopiuje ustawienia gry (transport, gracze) jako jeden ciag tekstu do wklejenia np. na Discordzie — zamiast wysylania pliku .civ4pbem.",
        "en": "Copies the game's settings (transport, players) as one text blob to paste e.g. on Discord — instead of sending a .civ4pbem file.",
    },
    "paste_invite_code": {
        "pl": "Wklej kod zaproszenia",
        "en": "Paste invite code",
    },
    "paste_invite_code_hint": {
        "pl": "Wklej kod otrzymany od innego gracza, zeby dolaczyc do jego gry.",
        "en": "Paste a code you received from another player to join their game.",
    },
    "paste_invite_code_prompt": {
        "pl": "Wklej tutaj caly kod zaproszenia:",
        "en": "Paste the whole invite code here:",
    },
    "invite_code_copied": {
        "pl": "Kod zaproszenia dla '{name}' skopiowany do schowka",
        "en": "Invite code for '{name}' copied to clipboard",
    },
    "invite_code_copied_body": {
        "pl": "Skopiowano do schowka ({chars} znakow).\n\nWklej to np. na Discordzie/Messengerze — druga osoba uzyje \"Wklej kod zaproszenia\", zeby dolaczyc do '{name}'.\n\nUwaga: kod zawiera haslo do FTP w jawnej postaci (tak samo jak plik .civ4pbem) — nie wklejaj go publicznie.",
        "en": "Copied to clipboard ({chars} chars).\n\nPaste this on Discord/Messenger — the other person uses \"Paste invite code\" to join '{name}'.\n\nNote: like the .civ4pbem file, this contains the FTP password in plain text — don't post it publicly.",
    },
    "invite_code_invalid": {
        "pl": "Nieprawidlowy kod zaproszenia: {error}",
        "en": "Invalid invite code: {error}",
    },
    "delete_game": {
        "pl": "Usun gre",
        "en": "Delete game",
    },
    "game_transport": {
        "pl": "Transport gry...",
        "en": "Game transport...",
    },
    "edit_game": {
        "pl": "Edytuj gre...",
        "en": "Edit game...",
    },
    "edit_queue": {
        "pl": "Kolejka i save'y...",
        "en": "Queue and saves...",
    },
    "edit_queue_title": {
        "pl": "Kolejka: {name}",
        "en": "Queue: {name}",
    },
    "edit_queue_hint": {
        "pl": "Recznie ustaw kto po kim gra i ktory plik jest ktorym w kolejce. "
              "Ostatni save w tabeli to plik do zaladowania. "
              "Usun duchy (zle nazwy), przestaw wiersze, wskaz kto czeka.",
        "en": "Manually set player order and which save file is which slot. "
              "The last row is the file to load. "
              "Delete ghost names, reorder rows, pick who is waiting.",
    },
    "edit_queue_order": {
        "pl": "Kolejnosc graczy",
        "en": "Player order",
    },
    "edit_queue_pointer": {
        "pl": "Czyj ruch",
        "en": "Whose turn",
    },
    "edit_queue_waiting": {
        "pl": "Czeka:",
        "en": "Waiting for:",
    },
    "edit_queue_turn": {
        "pl": "Numer tury (UI):",
        "en": "Turn number (UI):",
    },
    "edit_queue_next_seq": {
        "pl": "Nastepny upload (seq):",
        "en": "Next upload (seq):",
    },
    "edit_queue_sync_wait": {
        "pl": "Czeka = odbiorca ostatniego save'a",
        "en": "Waiting for = recipient of the last save",
    },
    "edit_queue_saves": {
        "pl": "Save'y w kolejce",
        "en": "Saves in the queue",
    },
    "edit_queue_saves_hint": {
        "pl": "Kazdy wiersz = jeden plik na serwerze. Seq / From / To / Turn musza "
              "pasowac do nazwy (albo kliknij Przebuduj nazwe). "
              "Ten wiersz jest biezacy = przenosi save na koniec i ustawia kto czeka.",
        "en": "Each row is one server file. Seq / From / To / Turn should match "
              "the filename (or click Rebuild name). "
              "Set as current moves that save to the end and sets who is waiting.",
    },
    "edit_queue_col_seq": {
        "pl": "Seq",
        "en": "Seq",
    },
    "edit_queue_col_turn": {
        "pl": "Tura",
        "en": "Turn",
    },
    "edit_queue_col_from": {
        "pl": "Od",
        "en": "From",
    },
    "edit_queue_col_to": {
        "pl": "Do",
        "en": "To",
    },
    "edit_queue_col_file": {
        "pl": "Plik",
        "en": "File",
    },
    "edit_queue_add": {
        "pl": "Dodaj",
        "en": "Add",
    },
    "edit_queue_remove": {
        "pl": "Usun wiersz",
        "en": "Remove row",
    },
    "edit_queue_up": {
        "pl": "W gore",
        "en": "Up",
    },
    "edit_queue_down": {
        "pl": "W dol",
        "en": "Down",
    },
    "edit_queue_pick": {
        "pl": "Wskaz plik...",
        "en": "Pick file...",
    },
    "edit_queue_rebuild": {
        "pl": "Przebuduj nazwe",
        "en": "Rebuild name",
    },
    "edit_queue_set_current": {
        "pl": "Ten wiersz jest biezacy",
        "en": "This row is current",
    },
    "edit_queue_publish": {
        "pl": "Wyslij poprawke na FTP (turns.json + state.json) — zeby inni tez to zobaczyli",
        "en": "Publish fix to FTP (turns.json + state.json) so everyone else sees it",
    },
    "edit_queue_confirm": {
        "pl": "Zapisac kolejke?\n\nCzeka: {player}\nTura: {turn}\nNastepny seq: {seq}\n"
              "Save'ow: {n}\nBiezacy plik:\n{filename}",
        "en": "Save this queue?\n\nWaiting: {player}\nTurn: {turn}\nNext seq: {seq}\n"
              "Saves: {n}\nCurrent file:\n{filename}",
    },
    "queue_published": {
        "pl": "Kolejka zapisana i wyslana na serwer.",
        "en": "Queue saved and published to the server.",
    },
    "queue_saved_local": {
        "pl": "Kolejka zapisana lokalnie (bez FTP).",
        "en": "Queue saved locally (not published).",
    },
    "queue_publish_failed": {
        "pl": "Kolejka zapisana lokalnie, ale wysylka na FTP nie wyszla. Sprobuj ponownie.",
        "en": "Queue saved locally, but FTP publish failed. Try again.",
    },
    "queue_err_no_players": {
        "pl": "Brak graczy w kolejce.",
        "en": "No players in the queue.",
    },
    "queue_err_player_count": {
        "pl": "Kolejnosc musi zawierac wszystkich graczy z gry (nikogo nie dodawaj i nie usuwaj).",
        "en": "Order must include every player in the game (do not add or drop anyone).",
    },
    "queue_err_unknown_player": {
        "pl": "Nieznany gracz w kolejce.",
        "en": "Unknown player in the queue.",
    },
    "queue_err_dup_player": {
        "pl": "Ten sam gracz jest w kolejce dwa razy.",
        "en": "The same player appears twice in the queue.",
    },
    "queue_err_empty_file": {
        "pl": "Jakis wiersz nie ma nazwy pliku.",
        "en": "A row is missing a filename.",
    },
    "queue_err_dup_file": {
        "pl": "Ten sam plik jest w tabeli dwa razy. Usun duplikat.",
        "en": "The same file is listed twice. Remove the duplicate.",
    },
    "queue_err_no_saves": {
        "pl": "Dodaj przynajmniej jeden save (wiersz w tabeli).",
        "en": "Add at least one save (a row in the table).",
    },
    "queue_err_waiting": {
        "pl": "Wybierz kto teraz czeka.",
        "en": "Pick who is waiting now.",
    },
    "edit_game_title": {
        "pl": "Edycja gry: {name}",
        "en": "Edit game: {name}",
    },
    "edit_alias": {
        "pl": "Tozsamosc w grze",
        "en": "Game identity",
    },
    "edit_alias_label": {
        "pl": "Jestem graczem:",
        "en": "I am player:",
    },
    "alias_claimed_title": {
        "pl": "Ten slot jest juz zajety",
        "en": "This slot is already claimed",
    },
    "alias_claimed_body": {
        "pl": "Gracz \"{player}\" jest juz ustawiony na innym komputerze "
              "(nick: {other}).\n\nJesli obie kopie wybiora te sama osobe, "
              "obie beda myslec ze to ich tura.\n\nUstawic sie mimo to?",
        "en": "Player \"{player}\" is already claimed on another PC "
              "(nick: {other}).\n\nIf both copies pick the same person, "
              "both will think it is their turn.\n\nClaim this slot anyway?",
    },
    "edit_players": {
        "pl": "Emaile graczy",
        "en": "Player emails",
    },
    "edit_player_color_tooltip": {
        "pl": "Kliknij aby zmienic kolor gracza w historii",
        "en": "Click to change player color in history",
    },
    "edit_player_color_title": {
        "pl": "Kolor gracza: {name}",
        "en": "Player color: {name}",
    },
    "edit_color_mode_group": {
        "pl": "Kolorowanie historii tur",
        "en": "Turn history coloring",
    },
    "color_mode_all": {
        "pl": "Koloruj wszystkich graczy",
        "en": "Color all players",
    },
    "color_mode_mine": {
        "pl": "Wyroznij tylko moje tury",
        "en": "Highlight only my turns",
    },
    "color_mode_hint": {
        "pl": "\"Koloruj wszystkich\" — kazdy gracz ma swoj kolor.\n\"Wyroznij moje\" — Twoje tury kolorowe, reszta szara.",
        "en": "\"Color all\" — each player has their own color.\n\"Highlight mine\" — your turns colored, others gray.",
    },
    "game_saved": {
        "pl": "Zapisano zmiany gry '{name}'",
        "en": "Game '{name}' changes saved",
    },
    "settings": {
        "pl": "Ustawienia",
        "en": "Settings",
    },
    "select_game": {
        "pl": "Wybierz gre z listy",
        "en": "Select a game from the list",
    },
    "your_turn": {
        "pl": "TWOJA KOLEJ!",
        "en": "YOUR TURN!",
    },
    "your_turn_banner": {
        "pl": "  TWOJA KOLEJ! Kliknij „Graj teraz” albo pobierz save.",
        "en": "  YOUR TURN! Click Play now or download the save.",
    },
    "play_now": {
        "pl": "Sprawdz i zagraj",
        "en": "Check & Play",
    },
    "play_now_working": {
        "pl": "Pobieranie save'a i uruchamianie Civ4...",
        "en": "Downloading save and launching Civ4...",
    },
    "play_now_launched": {
        "pl": "Civ4 uruchomiony — milej gry!",
        "en": "Civ4 launched — have fun!",
    },
    "play_now_launched_manual": {
        "pl": "Civ4 uruchomiony. Wczytaj save recznie: {filename}",
        "en": "Civ4 launched. Load the save manually: {filename}",
    },
    "play_now_not_your_turn": {
        "pl": "To nie Twoja tura w tej grze.",
        "en": "It is not your turn in this game.",
    },
    "play_now_no_save": {
        "pl": "Brak save'a dla Ciebie na serwerze. Kliknij „Sprawdz teraz”.",
        "en": "No save for you on the server. Click Check now.",
    },
    "play_now_no_direct_load": {
        "pl": "Wlacz „Laduj save bezposrednio (/fxsload)” w ustawieniach, zeby Graj teraz wczytalo ture automatycznie.",
        "en": "Enable direct save load (/fxsload) in settings for Play now to load your turn automatically.",
    },
    "waiting_for": {
        "pl": "  Czeka na: {name}",
        "en": "  Waiting for: {name}",
    },
    "download_save": {
        "pl": "Pobierz save",
        "en": "Download save",
    },
    "upload_save": {
        "pl": "Wyslij moj save",
        "en": "Upload my save",
    },
    "upload_not_your_turn": {
        "pl": "Nie Twoja kolej — teraz gra: {name}",
        "en": "Not your turn — now playing: {name}",
    },
    "upload_wrong_sender": {
        "pl": "Save wskazuje innego nadawce (from) niz Ty. Nie zakonczyles tury albo zly plik.",
        "en": "Save sender (from) is not you. You may not have ended your turn, or wrong file.",
    },
    "upload_wrong_recipient": {
        "pl": "Save nie jest dla nastepnego gracza (to). Sprawdz, czy zakonczyles ture w Civ4.",
        "en": "Save is not addressed to the next player (to). Check you ended your turn in Civ4.",
    },
    "upload_still_your_turn": {
        "pl": "Wyglada na to, ze nadal Twoja tura — w nazwie save'a jest Twoje imie po _to_.",
        "en": "Looks like it is still your turn — your name appears after _to_ in the save.",
    },
    "upload_wrong_leader": {
        "pl": "Save powinien byc dla lidera {leader} (nastepny gracz). Zakoncz ture i zapisz ponownie.",
        "en": "Save should be for leader {leader} (next player). End your turn and save again.",
    },
    "upload_native_no_to": {
        "pl": "Nierozpoznana nazwa save'a Civ4 (brak _to_).",
        "en": "Unrecognized Civ4 save name (missing _to_).",
    },
    "upload_unrecognized_name": {
        "pl": "Nierozpoznany format nazwy save'a dla tej gry.",
        "en": "Unrecognized save filename format for this game.",
    },
    "upload_not_this_game": {
        "pl": "Ten plik nie nalezy do wybranej gry.",
        "en": "This file does not belong to the selected game.",
    },
    "upload_already_sent": {
        "pl": "Ten ruch jest juz na serwerze ({filename}). Nie wysylam drugi raz.",
        "en": "This move is already on the server ({filename}). Not uploading again.",
    },
    "upload_seq_sync_failed": {
        "pl": "Nie udalo sie odczytac listy save'ow z serwera. Kliknij Sprawdz teraz i sprobuj ponownie — inaczej numer pliku sie powtorzy.",
        "en": "Could not list saves on the server. Click Check now and retry — otherwise the save number may collide.",
    },
    "upload_no_next_player": {
        "pl": "Brak nastepnego gracza w kolejce.",
        "en": "No next player in turn order.",
    },
    "open_folder": {
        "pl": "Otworz folder",
        "en": "Open folder",
    },
    "check_now": {
        "pl": "Sprawdz teraz",
        "en": "Check now",
    },
    "check_now_hint": {
        "pl": "Sciaga stan kolejki z serwera i — jesli Twoja tura — save do zagrania. "
              "Robi to tez automatycznie co kilka minut.",
        "en": "Pulls turn queue from the server and — if it’s your turn — the save to play. "
              "Also runs automatically every few minutes.",
    },
    "check_waiting": {
        "pl": "{game}: tura {turn}, kolej: {player}",
        "en": "{game}: turn {turn}, waiting: {player}",
    },
    "ftp_file_btn": {
        "pl": "Pobierz stan FTP",
        "en": "Pull FTP state",
    },
    "ftp_file_hint": {
        "pl": "Sciaga z FTP pliki {gra}_turns.json i _state.json (bez wpisywania). "
              "Ten sam kanal co upload save’a.",
        "en": "Downloads {game}_turns.json and _state.json from FTP (nothing to type). "
              "Same channel as save upload.",
    },
    "ftp_file_title": {
        "pl": "Stan z FTP",
        "en": "FTP state",
    },
    "ftp_file_prompt": {
        "pl": "Nazwa pliku w /civ4pbem/{game}/ (jak w FileZilli):\n"
              "np. {example} albo {game}_state.json",
        "en": "Filename in /civ4pbem/{game}/ (as in FileZilla):\n"
              "e.g. {example} or {game}_state.json",
    },
    "ftp_file_pulling": {
        "pl": "Pobieranie stanu {game} z FTP…",
        "en": "Pulling {game} state from FTP…",
    },
    "ftp_file_empty": {
        "pl": "Podaj nazwe pliku.",
        "en": "Enter a filename.",
    },
    "ftp_file_fail": {
        "pl": "Nie udalo sie pobrac „{file}”: {error}",
        "en": "Could not download “{file}”: {error}",
    },
    "history_group": {
        "pl": "Historia tur (wybierz aby przywrocic)",
        "en": "Turn history (select to revert)",
    },
    "history_filter": {
        "pl": "Filtr:",
        "en": "Filter:",
    },
    "history_filter_all": {
        "pl": "Wszyscy gracze",
        "en": "All players",
    },
    "history_filter_mine": {
        "pl": "Tylko moje",
        "en": "Mine only",
    },
    "history_download_this": {
        "pl": "Pobierz zaznaczona",
        "en": "Download selected",
    },
    "history_download_not_yours": {
        "pl": "To nie jest Twoj save (od {name}). Pobierasz awaryjnie, np. po wczytaniu zlej tury. Kontynuowac?",
        "en": "This is not your save (from {name}). Emergency download, e.g. after loading the wrong turn. Continue?",
    },
    "history_download_no_file": {
        "pl": "Ta pozycja nie ma pliku save do pobrania.",
        "en": "This entry has no save file to download.",
    },
    "choose_save_mine_hint": {
        "pl": "Zielone = save dla Ciebie. Pomaranczowe tez da sie pobrac (awaryjnie — np. ktos wczytal nie swoja ture).",
        "en": "Green = save for you. Orange rows can also be downloaded (emergency — e.g. someone loaded the wrong turn).",
    },
    "choose_save_can_download": {
        "pl": "[Twoja — mozna pobrac]",
        "en": "[Yours — can download]",
    },
    "choose_save_other_player": {
        "pl": "[awaryjne — mozna pobrac]",
        "en": "[emergency — can download]",
    },
    "choose_save_none_mine": {
        "pl": "Na serwerze nie ma teraz save'a dla Ciebie. Mozesz awaryjnie pobrac save innego gracza — potwierdz przy wyborze.",
        "en": "There is no save for you on the server right now. You can still download another player's save — confirm when you pick it.",
    },
    "choose_save_not_yours_confirm": {
        "pl": "To save od {from_name} dla {to_name}, nie Twoja tura.\n\nPobierz tylko jesli kolejnosc sie posypala i trzeba wrocic do wlasciwego pliku.\n\nKontynuowac?",
        "en": "This save is from {from_name} to {to_name}, not your turn.\n\nDownload only if turn order broke and you need the right file back.\n\nContinue?",
    },
    "choose_save_empty": {
        "pl": "Brak save'ow na serwerze dla tej gry.",
        "en": "No saves on the server for this game.",
    },
    "save_route": {
        "pl": "{from_name} -> {to_name}",
        "en": "{from_name} -> {to_name}",
    },
    "history_pending_prefix": {
        "pl": "DO ZAGRANIA",
        "en": "TO PLAY",
    },
    "history_pending_from": {
        "pl": "(save od {name})",
        "en": "(save from {name})",
    },
    "history_pending_no_revert": {
        "pl": "To jest tura, ktora dopiero bedzie zagrana. Przywrocic mozna tylko ture juz wyslana.",
        "en": "This is the turn that has not been played yet. You can only revert a turn that was already sent.",
    },
    "revert_selected": {
        "pl": "Przywroc zaznaczona ture",
        "en": "Revert to selected turn",
    },
    "launch_this_turn": {
        "pl": "Uruchom te ture",
        "en": "Launch this turn",
    },
    "launch_no_file": {
        "pl": "Ta tura nie ma skojarzonego pliku save.",
        "en": "This turn has no associated save file.",
    },
    "launch_file_missing": {
        "pl": "Plik save nie istnieje lokalnie:\n{filename}\n\nPobierz go najpierw z serwera.",
        "en": "Save file not found locally:\n{filename}\n\nDownload it from server first.",
    },
    "ready": {
        "pl": "Gotowy",
        "en": "Ready",
    },
    "statistics": {
        "pl": "Statystyki",
        "en": "Statistics",
    },

    # --- Game list items ---
    "turn": {
        "pl": "Tura",
        "en": "Turn",
    },
    "waiting": {
        "pl": "Czeka na",
        "en": "Waiting for",
    },
    "player_order": {
        "pl": "Kolejnosc graczy",
        "en": "Player order",
    },
    "you_marker": {
        "pl": "(Ty)",
        "en": "(You)",
    },
    "playing_since": {
        "pl": "{name} gra juz: {time}",
        "en": "{name} has been playing for: {time}",
    },
    "chip_play": {
        "pl": "GRAJ",
        "en": "PLAY",
    },
    "chip_waiting": {
        "pl": "Teraz gra: {name}",
        "en": "Now playing: {name}",
    },
    "chip_waiting_time": {
        "pl": "Teraz gra: {name} ({time})",
        "en": "Now playing: {name} ({time})",
    },

    # --- Time formatting ---
    "days_hours": {
        "pl": "{days} dni, {hours} godz.",
        "en": "{days} days, {hours} hrs.",
    },
    "hours_minutes": {
        "pl": "{hours} godz., {minutes} min.",
        "en": "{hours} hrs., {minutes} min.",
    },
    "minutes": {
        "pl": "{minutes} min.",
        "en": "{minutes} min.",
    },
    "less_than_minute": {
        "pl": "< 1 min.",
        "en": "< 1 min.",
    },

    # --- Settings Dialog ---
    "settings_title": {
        "pl": "Ustawienia",
        "en": "Settings",
    },
    "settings_appearance": {
        "pl": "Wyglad i jezyk",
        "en": "Appearance & language",
    },
    "tab_general": {
        "pl": "Ogolne",
        "en": "General",
    },
    "tab_transport": {
        "pl": "Transport",
        "en": "Transport",
    },
    "tab_notifications": {
        "pl": "Powiadomienia",
        "en": "Notifications",
    },
    "tab_security": {
        "pl": "Bezpieczenstwo",
        "en": "Security",
    },
    "player_name": {
        "pl": "Twoja nazwa:",
        "en": "Your name:",
    },
    "player_email": {
        "pl": "Twoj email:",
        "en": "Your email:",
    },
    "save_path": {
        "pl": "Folder save'ow Civ4 (wspolny dla wszystkich gier)",
        "en": "Civ4 save folder (shared by all games)",
    },
    "save_path_hint": {
        "pl": "Wykryj czyta ustawienia Civ4: skrot _Civ4Saves, CivilizationIV.ini i /ALTROOT. "
              "Wskaz folder Saves\\pbem — kazda gra ma w nim podfolder (np. „Mihau's game”). "
              "Jesli nie trafi, zawsze mozesz wskazac folder recznie.",
        "en": "Auto-detect reads Civ4's own settings: the _Civ4Saves shortcut, "
              "CivilizationIV.ini, and /ALTROOT. Point at Saves\\pbem — each game has "
              "its own subfolder there (e.g. \"Mihau's game\"). "
              "If detection misses, always pick the folder by hand.",
    },
    "browse_save_folder": {
        "pl": "Wskaz recznie...",
        "en": "Choose folder...",
    },
    "check_interval": {
        "pl": "Sprawdzanie co (min):",
        "en": "Check every (min):",
    },
    "dark_mode": {
        "pl": "Tryb ciemny",
        "en": "Dark mode",
    },
    "auto_send": {
        "pl": "Auto-wyslij save (bez pytania, dla fullscreen)",
        "en": "Auto-send save (no prompt, for fullscreen)",
    },
    "autostart": {
        "pl": "Uruchamiaj przy starcie komputera",
        "en": "Start at computer login",
    },
    "autostart_hint": {
        "pl": "Program wlaczy sie w tle (zasobnik) i bedzie sprawdzal save'y automatycznie.",
        "en": "App starts in the background (tray) and checks for saves automatically.",
    },
    "autostart_failed": {
        "pl": "Nie udalo sie ustawic autostartu: {msg}",
        "en": "Failed to set autostart: {msg}",
    },
    "language": {
        "pl": "Jezyk / Language:",
        "en": "Language / Jezyk:",
    },
    "auto_launch": {
        "pl": "Auto-uruchom Civ4 po pobraniu save'a (Graj teraz w tle)",
        "en": "Auto-launch Civ4 after downloading a save (background Play now)",
    },
    "auto_launch_hint": {
        "pl": "Dziala po automatycznym pobraniu tury. Wymaga wlaczonego /fxsload.",
        "en": "Runs after an automatic turn download. Requires /fxsload enabled.",
    },
    "try_direct_load": {
        "pl": "Probuj ladowac save bezposrednio (wymaga wyboru wersji gry)",
        "en": "Try to load save directly (requires game edition selection)",
    },
    "civ4_edition": {
        "pl": "Wersja gry:",
        "en": "Game edition:",
    },
    "civ4_edition_none": {
        "pl": "-- nie wybrano (tylko uruchom gre) --",
        "en": "-- not selected (just launch game) --",
    },
    "civ4_edition_steam": {
        "pl": "Steam",
        "en": "Steam",
    },
    "civ4_edition_gog": {
        "pl": "GOG",
        "en": "GOG",
    },
    "civ4_edition_dvd": {
        "pl": "DVD / CD (pudełkowa)",
        "en": "DVD / CD (retail)",
    },
    "steam_path": {
        "pl": "Sciezka do Steam.exe:",
        "en": "Path to Steam.exe:",
    },
    "steam_app_id": {
        "pl": "Steam App ID (domyslnie 8800):",
        "en": "Steam App ID (default 8800):",
    },
    "detect_steam": {
        "pl": "Wykryj Steam",
        "en": "Detect Steam",
    },
    "steam_detected": {
        "pl": "Wykryto Steam: {path}",
        "en": "Steam detected: {path}",
    },
    "steam_not_detected": {
        "pl": "Nie wykryto Steam automatycznie. Wskazz recznie.",
        "en": "Steam not auto-detected. Please set manually.",
    },
    "steam_not_found": {
        "pl": "Nie znaleziono Steam.exe. Ustaw sciezke w Ustawieniach.",
        "en": "Steam.exe not found. Set the path in Settings.",
    },
    "edition_hint_steam": {
        "pl": "Steam: uruchamia przez Steam.exe -applaunch 8800 /FXSLOAD=",
        "en": "Steam: launches via Steam.exe -applaunch 8800 /FXSLOAD=",
    },
    "edition_hint_gog": {
        "pl": "GOG/DVD: uruchamia Civ4BeyondSword.exe /fxsload= bezposrednio",
        "en": "GOG/DVD: launches Civ4BeyondSword.exe /fxsload= directly",
    },
    # --- Multi-edition installation config ---
    "civ4_installations_group": {
        "pl": "Zainstalowane wersje Civ4 BTS",
        "en": "Installed Civ4 BTS versions",
    },
    "edition_enabled": {
        "pl": "Mam te wersje",
        "en": "I have this version",
    },
    "edition_exe_path": {
        "pl": "Sciezka do Civ4BeyondSword.exe:",
        "en": "Path to Civ4BeyondSword.exe:",
    },
    "edition_direct_load": {
        "pl": "Laduj save bezposrednio (/fxsload=)",
        "en": "Load save directly (/fxsload=)",
    },
    "preferred_edition": {
        "pl": "Preferowana wersja Civ4 (PBEM):",
        "en": "Preferred Civ4 version (PBEM):",
    },
    "preferred_edition_hint": {
        "pl": "Steam (czesto OneDrive) i GOG/DVD maja osobne foldery Saves. "
              "Ta wersja decyduje, skad program wykrywa save'y i gdzie je kopiuje do Civ4.",
        "en": "Steam (often OneDrive) and GOG/DVD use separate Saves folders. "
              "This version controls save detection and where files are mirrored into Civ4.",
    },
    "preferred_edition_ask": {
        "pl": "-- pytaj za kazdym razem --",
        "en": "-- always ask --",
    },
    "choose_edition_title": {
        "pl": "Wybierz wersje gry",
        "en": "Choose game version",
    },
    "choose_edition_label": {
        "pl": "Masz kilka wersji Civ4 BTS. Ktora uruchomic?",
        "en": "You have multiple Civ4 BTS versions. Which one to launch?",
    },
    "remember_choice": {
        "pl": "Zapamietaj wybor (mozna zmienic w Ustawieniach)",
        "en": "Remember this choice (can be changed in Settings)",
    },
    "detect_for_edition": {
        "pl": "Wykryj",
        "en": "Detect",
    },
    "edition_steam_hint": {
        "pl": "Steam: wymaga Steam.exe do uruchomienia z save",
        "en": "Steam: requires Steam.exe to launch with save",
    },
    "edition_gog_dvd_hint": {
        "pl": "GOG/DVD: uruchamia exe bezposrednio",
        "en": "GOG/DVD: launches exe directly",
    },
    # --- Reminder ---
    "remind_player": {
        "pl": "Przypomnij o turze",
        "en": "Remind player",
    },
    "reminder_sent": {
        "pl": "Przypomnienie wyslane do {name}",
        "en": "Reminder sent to {name}",
    },
    "reminder_failed": {
        "pl": "Nie udalo sie wyslac przypomnienia",
        "en": "Failed to send reminder",
    },
    "notifier_not_configured": {
        "pl": "Powiadomienia nie sa skonfigurowane.",
        "en": "Notifications are not configured.",
    },
    "no_player_email": {
        "pl": "Gracz nie ma podanego adresu email.",
        "en": "Player has no email address.",
    },
    "reminder_auto_group": {
        "pl": "Automatyczne przypomnienia",
        "en": "Automatic reminders",
    },
    "reminder_auto_enabled": {
        "pl": "Wysylaj automatyczne przypomnienie po X dniach bezczynnosci",
        "en": "Send automatic reminder after X days of inactivity",
    },
    "reminder_auto_days": {
        "pl": "Dni bez ruchu przed przypomnieniem:",
        "en": "Days of inactivity before reminder:",
    },
    # --- Notification channels ---
    "notifications_master_switch": {
        "pl": "Wlacz powiadomienia",
        "en": "Enable notifications",
    },
    "notify_via_smtp": {
        "pl": "Przez email (SMTP)",
        "en": "Via email (SMTP)",
    },
    "notify_via_app": {
        "pl": "Przez aplikacje (plik na serwerze, bez SMTP)",
        "en": "Via app (flag file on server, no SMTP)",
    },
    "notify_via_app_hint": {
        "pl": "Aplikacja odbiorcy wykryje powiadomienie przy nastepnym sprawdzeniu serwera.",
        "en": "Recipient's app will detect the notification on next server check.",
    },
    # --- SMTP source for notifications ---
    "notif_smtp_same_as_transport": {
        "pl": "Uzyj tych samych danych co transport email",
        "en": "Use same credentials as email transport",
    },
    "notif_smtp_custom": {
        "pl": "Inny serwer SMTP (podaj recznie)",
        "en": "Different SMTP server (enter manually)",
    },
    "notif_smtp_same_hint": {
        "pl": "Powiadomienia beda wysylane z tego samego konta co save'y (konfiguracja z zakladki Transport).",
        "en": "Notifications will be sent from the same account as saves (configured in Transport tab).",
    },
    # --- Notification templates ---
    "notif_templates_group": {
        "pl": "Szablony wiadomosci email",
        "en": "Email message templates",
    },
    "notif_subject_template": {
        "pl": "Temat (tura):",
        "en": "Subject (turn):",
    },
    "notif_body_template": {
        "pl": "Tresc (tura):",
        "en": "Body (turn):",
    },
    "notif_template_hint": {
        "pl": "Puste = uzyj domyslnego szablonu. Zmienne:",
        "en": "Empty = use default template. Variables:",
    },
    "notif_reminder_subject_template": {
        "pl": "Temat (przypomnienie):",
        "en": "Subject (reminder):",
    },
    "notif_reminder_body_template": {
        "pl": "Tresc (przypomnienie):",
        "en": "Body (reminder):",
    },
    "insert_variable": {
        "pl": "Wstaw zmienna",
        "en": "Insert variable",
    },
    # --- Email autodiscover & presets ---
    "email_autodiscover": {
        "pl": "Automatyczne wykrywanie serwera",
        "en": "Automatic server detection",
    },
    "email_autodiscover_btn": {
        "pl": "Wykryj",
        "en": "Detect",
    },
    "email_autodiscover_invalid": {
        "pl": "Podaj prawidlowy adres email.",
        "en": "Enter a valid email address.",
    },
    "email_autodiscover_searching": {
        "pl": "Szukam ustawien serwera...",
        "en": "Detecting server settings...",
    },
    "email_autodiscover_ok": {
        "pl": "Wykryto ({source}): SMTP={smtp}, IMAP={imap}",
        "en": "Detected ({source}): SMTP={smtp}, IMAP={imap}",
    },
    "email_autodiscover_partial": {
        "pl": "Czescowo wykryto ({source}). Sprawdz pola recznie.",
        "en": "Partially detected ({source}). Check fields manually.",
    },
    "email_autodiscover_failed": {
        "pl": "Nie wykryto automatycznie. Wypelnij pola recznie.",
        "en": "Auto-detection failed. Fill in fields manually.",
    },
    "email_preset": {
        "pl": "Preset dostawcy:",
        "en": "Provider preset:",
    },
    "email_preset_custom": {
        "pl": "-- wlasny serwer --",
        "en": "-- custom server --",
    },
    "email_app_password_hint": {
        "pl": "Ten dostawca wymaga hasla aplikacji (App Password), nie zwyklego hasla konta.\nWygeneruj je w ustawieniach bezpieczenstwa swojego konta.",
        "en": "This provider requires an App Password, not your regular account password.\nGenerate it in your account security settings.",
    },
    "email_incoming": {
        "pl": "Poczta przychodząca (IMAP / POP3)",
        "en": "Incoming mail (IMAP / POP3)",
    },
    "email_protocol": {
        "pl": "Protokol:",
        "en": "Protocol:",
    },
    "email_imap_recommended": {
        "pl": "(zalecany)",
        "en": "(recommended)",
    },
    "email_delete_after_download": {
        "pl": "Usun wiadomosci po pobraniu save'a",
        "en": "Delete messages after downloading save",
    },
    "security_label": {
        "pl": "Zabezpieczenie",
        "en": "Security",
    },
    "security_none": {
        "pl": "Brak",
        "en": "None",
    },
    # --- Import: replace global settings ---
    "import_replace_settings": {
        "pl": "Zastap globalne ustawienia transportu i powiadomien ustawieniami z tej gry",
        "en": "Replace global transport and notification settings with those from this game",
    },
    "import_settings_replaced": {
        "pl": "Ustawienia globalne zastapione ustawieniami gry '{name}'",
        "en": "Global settings replaced with settings from game '{name}'",
    },
    # --- Export: password prompt ---
    "export_password_prompt_title": {
        "pl": "Zabezpieczenie eksportu",
        "en": "Export protection",
    },
    "export_password_prompt_text": {
        "pl": "Czy chcesz zabezpieczyc plik eksportu haslem?\n"
              "(Chroni dane transportu przed nieautoryzowanym odczytem)",
        "en": "Do you want to protect the export file with a password?\n"
              "(Protects transport credentials from unauthorized access)",
    },
    "export_skip_prompt": {
        "pl": "Nie pytaj ponownie",
        "en": "Don't ask again",
    },
    "export_password_label": {
        "pl": "Haslo do pliku eksportu:",
        "en": "Export file password:",
    },

    # --- File association ---
    "file_assoc_group": {
        "pl": "Skojarzenie plikow .CivBeyondSwordSave",
        "en": ".CivBeyondSwordSave file association",
    },
    "file_assoc_current": {
        "pl": "Obecne skojarzenie:",
        "en": "Current association:",
    },
    "file_assoc_none": {
        "pl": "brak / nieznane",
        "en": "none / unknown",
    },
    "file_assoc_set": {
        "pl": "Ustaw skojarzenie dla tej wersji",
        "en": "Set association for this version",
    },
    "file_assoc_ok": {
        "pl": "Skojarzenie ustawione!\nKomenda: {cmd}",
        "en": "Association set!\nCommand: {cmd}",
    },
    "file_assoc_error": {
        "pl": "Blad ustawiania skojarzenia:\n{error}",
        "en": "Error setting association:\n{error}",
    },
    "registry_windows_only": {
        "pl": "Skojarzenia plikow dostepne tylko na Windows.",
        "en": "File associations are only available on Windows.",
    },
    "registry_permission_error": {
        "pl": "Brak uprawnien do zapisu rejestru.",
        "en": "No permission to write to registry.",
    },
    "civ4_path": {
        "pl": "Sciezka do Civ4 BTS (.exe):",
        "en": "Civ4 BTS path (.exe):",
    },
    "browse": {
        "pl": "Przegladaj...",
        "en": "Browse...",
    },
    "detect_civ4": {
        "pl": "Wykryj automatycznie",
        "en": "Auto-detect",
    },
    "notification_empty_hint": {
        "pl": "puste = z transportu email",
        "en": "empty = from email transport",
    },
    "email_warning": {
        "pl": "Nie uzywaj prywatnego maila!",
        "en": "Do not use your personal email!",
    },
    # --- Transport tab labels ---
    "transport_method": {
        "pl": "Metoda transportu",
        "en": "Transport method",
    },
    "transport_type_label": {
        "pl": "Typ:",
        "en": "Type:",
    },
    "ssl_ignore": {
        "pl": "Ignoruj bledy SSL (self-signed certs)",
        "en": "Ignore SSL errors (self-signed certs)",
    },
    "ftp_use_tls": {
        "pl": "FTP przez TLS (FTPS)",
        "en": "FTP over TLS (FTPS)",
    },
    "ftp_use_tls_hint": {
        "pl": "Wylaczone = zwykly FTP (jak FileZilla na porcie 21). "
              "Wlacz tylko gdy serwer wymaga FTPS — inaczej check wisi na polaczeniu.",
        "en": "Off = plain FTP (like FileZilla on port 21). "
              "Enable only if the server requires FTPS — otherwise check hangs on connect.",
    },
    "file_transport_group": {
        "pl": "Serwer plikow (FTP/SFTP/WebDAV)",
        "en": "File server (FTP/SFTP/WebDAV)",
    },
    "email_transport_group": {
        "pl": "Transport email (SMTP + IMAP)",
        "en": "Email transport (SMTP + IMAP)",
    },
    "field_host": {
        "pl": "Host:",
        "en": "Host:",
    },
    "field_port": {
        "pl": "Port:",
        "en": "Port:",
    },
    "field_login": {
        "pl": "Login:",
        "en": "Login:",
    },
    "field_password": {
        "pl": "Haslo:",
        "en": "Password:",
    },
    "field_remote_dir": {
        "pl": "Folder zdalny:",
        "en": "Remote folder:",
    },
    "field_mode": {
        "pl": "Tryb:",
        "en": "Mode:",
    },
    "field_shared_mailbox": {
        "pl": "Skrzynka wspolna:",
        "en": "Shared mailbox:",
    },
    "field_from": {
        "pl": "Od (nadawca):",
        "en": "From (sender):",
    },
    "transport_locked": {
        "pl": "Dane transportu sa zaszyfrowane.\n\nOdblokuj aplikacje haslem glownym\naby wyswietlic i edytowac te ustawienia.",
        "en": "Transport data is encrypted.\n\nUnlock the app with master password\nto view and edit these settings.",
    },
    # --- Notifications tab labels ---
    "notifications_group": {
        "pl": "Powiadomienia email (SMTP)",
        "en": "Email notifications (SMTP)",
    },
    "notifications_info": {
        "pl": "Host i port musisz podac recznie.\nLogin i haslo: jesli puste, beda uzyte dane\nz zakladki Transport (jesli typ = email).",
        "en": "Host and port must be set manually.\nLogin and password: if empty, credentials\nfrom Transport tab will be used (if type = email).",
    },
    "smtp_locked": {
        "pl": "Dane SMTP sa zaszyfrowane.\n\nOdblokuj aplikacje haslem glownym\naby wyswietlic i edytowac te ustawienia.",
        "en": "SMTP data is encrypted.\n\nUnlock the app with master password\nto view and edit these settings.",
    },
    "subject_template": {
        "pl": "Szablon tematu:",
        "en": "Subject template:",
    },
    "body_template": {
        "pl": "Szablon tresci:",
        "en": "Body template:",
    },
    # --- Security tab labels ---
    "security_status_unlocked": {
        "pl": "Odblokowane — dane widoczne",
        "en": "Unlocked — data visible",
    },
    "security_status_locked": {
        "pl": "Zablokowane — dane zaszyfrowane",
        "en": "Locked — data encrypted",
    },
    "security_no_password": {
        "pl": "Brak hasla — dane niezaszyfrowane",
        "en": "No password — data not encrypted",
    },
    "master_password_group": {
        "pl": "Haslo glowne",
        "en": "Master password",
    },
    "new_password": {
        "pl": "Nowe haslo:",
        "en": "New password:",
    },
    "confirm_password": {
        "pl": "Potwierdz haslo:",
        "en": "Confirm password:",
    },
    "new_password_placeholder": {
        "pl": "Nowe haslo",
        "en": "New password",
    },
    "confirm_password_placeholder": {
        "pl": "Potwierdz haslo",
        "en": "Confirm password",
    },
    "set_password_btn": {
        "pl": "Ustaw / Zmien haslo",
        "en": "Set / Change password",
    },
    "security_info": {
        "pl": "Haslo glowne szyfruje dane transportu (FTP/SFTP/WebDAV/Email),\nloginy i hasla SMTP.\n\nBez hasla dane beda widoczne w pliku konfiguracyjnym.\nUWAGA: Jesli zapomnisz hasla, musisz usunac config i ustawic od nowa!",
        "en": "Master password encrypts transport credentials (FTP/SFTP/WebDAV/Email)\nand SMTP passwords.\n\nWithout a password, credentials are stored in plain text.\nWARNING: If you forget the password, you must delete config and set up again!",
    },
    "password_mismatch": {
        "pl": "Hasla nie sa identyczne.",
        "en": "Passwords do not match.",
    },
    "password_empty": {
        "pl": "Haslo nie moze byc puste.",
        "en": "Password cannot be empty.",
    },
    "password_set_ok": {
        "pl": "Haslo ustawione! Dane zostaly zaszyfrowane.\nOd teraz przy starcie program bedzie pytac o haslo.",
        "en": "Password set! Data has been encrypted.\nFrom now on the app will ask for password on startup.",
    },
    "password_locked_error": {
        "pl": "Nie mozna zmienic hasla gdy config jest zablokowany.\nNajpierw odblokuj przy starcie aplikacji.",
        "en": "Cannot change password while config is locked.\nUnlock the app on startup first.",
    },
    # --- GameTransportDialog ---
    "game_transport_copy_group": {
        "pl": "Kopiuj ustawienia z...",
        "en": "Copy settings from...",
    },
    "transport_test_btn": {
        "pl": "Testuj polaczenie",
        "en": "Test connection",
    },
    "transport_not_configured_short": {
        "pl": "Transport nie jest skonfigurowany.",
        "en": "Transport is not configured.",
    },
    "tray_minimized_msg": {
        "pl": "Zminimalizowano do tray. Kliknij dwukrotnie aby otworzyc.",
        "en": "Minimized to tray. Double-click to open.",
    },

    # --- New Game Dialog ---
    "new_game_title": {
        "pl": "Nowa gra",
        "en": "New Game",
    },
    "game_name": {
        "pl": "Nazwa gry:",
        "en": "Game name:",
    },
    "game_speed": {
        "pl": "Predkosc gry:",
        "en": "Game speed:",
    },
    "game_name_placeholder": {
        "pl": "np. ClashOfRome (unikalna — jest w nazwie save'a)",
        "en": "e.g. ClashOfRome (unique — used in save filenames)",
    },
    "random_game_name": {
        "pl": "Losuj",
        "en": "Random",
    },
    "game_name_taken": {
        "pl": "Gra o nazwie '{name}' juz istnieje. Wybierz inna (albo wcisnij Losuj).",
        "en": "A game named '{name}' already exists. Pick another (or click Random).",
    },
    "admin_password": {
        "pl": "Haslo admina:",
        "en": "Admin password:",
    },
    "admin_password_placeholder": {
        "pl": "haslo do usuwania save'ow (opcjonalne)",
        "en": "password for deleting saves (optional)",
    },
    "players_group": {
        "pl": "Gracze (w kolejnosci tur)",
        "en": "Players (in turn order)",
    },
    "player_name_placeholder": {
        "pl": "Nazwa gracza",
        "en": "Player name",
    },
    "player_email_placeholder": {
        "pl": "Email gracza",
        "en": "Player email",
    },
    "add": {
        "pl": "Dodaj",
        "en": "Add",
    },
    "remove_selected": {
        "pl": "Usun zaznaczonego",
        "en": "Remove selected",
    },
    "error_min_players": {
        "pl": "Podaj nazwe gry i minimum 2 graczy.",
        "en": "Enter a game name and at least 2 players.",
    },

    # --- Transport Dialog ---
    "transport_title": {
        "pl": "Transport gry: {name}",
        "en": "Game transport: {name}",
    },
    "copy_from": {
        "pl": "Kopiuj ustawienia z...",
        "en": "Copy settings from...",
    },
    "copy_defaults": {
        "pl": "Kopiuj z domyslnych",
        "en": "Copy from defaults",
    },
    "test_connection": {
        "pl": "Testuj polaczenie",
        "en": "Test connection",
    },
    "connection_ok": {
        "pl": "Polaczenie OK!",
        "en": "Connection OK!",
    },
    "connection_failed": {
        "pl": "Nie mozna polaczyc",
        "en": "Cannot connect",
    },

    # --- Status messages ---
    "checking_saves": {
        "pl": "Sprawdzanie nowych save'ow...",
        "en": "Checking for new saves...",
    },
    "status_connecting": {
        "pl": "Laczenie z serwerem ({game})...",
        "en": "Connecting to server ({game})...",
    },
    "status_connect_failed": {
        "pl": "Nie udalo sie polaczyc ({game})",
        "en": "Could not connect ({game})",
    },
    "status_searching_saves": {
        "pl": "Szukanie save'ow na serwerze ({game})...",
        "en": "Searching for saves on server ({game})...",
    },
    "status_found_save": {
        "pl": "Znaleziono save: {game} — {filename}",
        "en": "Found save: {game} — {filename}",
    },
    "status_looking_for_turn": {
        "pl": "Sprawdzanie Twojej tury ({game})...",
        "en": "Checking your turn ({game})...",
    },
    "status_downloading_save": {
        "pl": "Pobieranie: {game} — {filename}",
        "en": "Downloading: {game} — {filename}",
    },
    "status_health_check": {
        "pl": "Diagnostyka zdrowia gier...",
        "en": "Running health check...",
    },
    "status_check_summary": {
        "pl": "Sprawdzono {n} gier — pobrano: {downloaded}, lokalnie OK: {local}",
        "en": "Checked {n} games — downloaded: {downloaded}, already local: {local}",
    },
    "no_new_saves": {
        "pl": "Sprawdzono — brak nowych save'ow",
        "en": "Checked — no new saves found",
    },
    "found_new_save": {
        "pl": "Znaleziono nowy save — pobrano",
        "en": "Found new save — downloaded",
    },
    "downloading": {
        "pl": "Pobieranie save'a...",
        "en": "Downloading save...",
    },
    "uploading": {
        "pl": "Wysylanie: {filename}...",
        "en": "Uploading: {filename}...",
    },
    "uploaded": {
        "pl": "Wyslano: {filename}",
        "en": "Sent: {filename}",
    },
    "downloaded": {
        "pl": "Pobrano: {filename}",
        "en": "Downloaded: {filename}",
    },
    "save_exists": {
        "pl": "Save juz istnieje: {filename}",
        "en": "Save already exists: {filename}",
    },
    "no_save_from": {
        "pl": "Brak save'a od {name}",
        "en": "No save from {name}",
    },
    "transport_not_configured": {
        "pl": "Transport nie jest skonfigurowany dla tej gry",
        "en": "Transport is not configured for this game",
    },
    "player_not_in_game": {
        "pl": "Gracz '{name}' nie jest w tej grze",
        "en": "Player '{name}' is not in this game",
    },
    "upload_error": {
        "pl": "Blad wysylania",
        "en": "Upload error",
    },
    "download_error": {
        "pl": "Blad pobierania",
        "en": "Download error",
    },
    "auto_sent": {
        "pl": "Auto-wyslano!",
        "en": "Auto-sent!",
    },
    "new_save_detected": {
        "pl": "Nowy save wykryty: {filename}",
        "en": "New save detected: {filename}",
    },
    "new_save_dialog_title": {
        "pl": "Nowy save wykryty!",
        "en": "New save detected!",
    },
    "new_save_dialog_text": {
        "pl": "Wykryto nowy plik save:\n{filename}\n\nCzy chcesz go wyslac do gry '{game}'?",
        "en": "New save file detected:\n{filename}\n\nDo you want to send it to game '{game}'?",
    },

    # --- Delete game ---
    "delete_game_title": {
        "pl": "Usuwanie gry",
        "en": "Delete game",
    },
    "delete_game_confirm": {
        "pl": "Czy na pewno chcesz usunac gre '{name}'?\n\nTa operacja jest nieodwracalna!",
        "en": "Are you sure you want to delete game '{name}'?\n\nThis action is irreversible!",
    },
    "delete_saves_title": {
        "pl": "Usuwanie save'ow",
        "en": "Delete saves",
    },
    "delete_saves_confirm": {
        "pl": "Czy chcesz rowniez usunac pliki save skojarzone z gra '{name}'?",
        "en": "Do you also want to delete save files associated with game '{name}'?",
    },
    "delete_remote_saves_title": {
        "pl": "Usuwanie z serwera",
        "en": "Delete from server",
    },
    "delete_remote_saves_confirm": {
        "pl": "Czy usunac tez pliki tej gry z serwera (FTP/SFTP/WebDAV/email)?\n\n"
              "Znikna save'y, stan gry i flagi powiadomien.",
        "en": "Also delete this game's files from the server (FTP/SFTP/WebDAV/email)?\n\n"
              "Saves, game state, and notification flags will be removed.",
    },
    "delete_remote_one_confirm": {
        "pl": "Usunac z serwera plik:\n{filename}\n\nTej operacji nie cofniesz.",
        "en": "Delete from server:\n{filename}\n\nThis cannot be undone.",
    },
    "delete_remote_not_game_file": {
        "pl": "Ten plik nie wyglada na save tej gry.",
        "en": "This file does not look like a save for this game.",
    },
    "history_delete_remote": {
        "pl": "Usun z serwera",
        "en": "Delete from server",
    },
    "delete_all_remote": {
        "pl": "Usun cala gre z serwera",
        "en": "Delete entire game from server",
    },
    "danger_zone_open": {
        "pl": "Strefa niebezpieczna…",
        "en": "Danger zone…",
    },
    "danger_zone_title": {
        "pl": "Strefa niebezpieczna — {name}",
        "en": "Danger zone — {name}",
    },
    "danger_zone_group": {
        "pl": "Usuwanie (tylko swiadomie)",
        "en": "Deletion (intentional only)",
    },
    "danger_zone_hint": {
        "pl": "Tu sa operacje, ktore kasuja pliki na FTP albo lokalna gre. "
              "Nie leza na glownym ekranie, zeby uniknac przypadkowego klikniecia.",
        "en": "These actions wipe FTP files or remove the local game. "
              "They are kept off the main screen to avoid accidental clicks.",
    },
    "danger_zone_no_selection": {
        "pl": "Najpierw zaznacz wiersz historii z plikiem save.",
        "en": "Select a history row with a save file first.",
    },
    "danger_type_name_prompt": {
        "pl": "Aby potwierdzic, wpisz DOKLADNIE nazwe gry:\n{name}",
        "en": "To confirm, type the game name EXACTLY:\n{name}",
    },
    "danger_type_name_mismatch": {
        "pl": "Nazwa nie pasuje — anulowano.",
        "en": "Name did not match — cancelled.",
    },
    "revert_remote_cleanup_hint": {
        "pl": "Na serwerze zostana usuniete nowsze save'y i flagi powiadomien.",
        "en": "Newer saves and notification flags will be removed from the server.",
    },
    "admin_password_prompt": {
        "pl": "Haslo admina gry (puste = bez hasla):",
        "en": "Game admin password (leave empty if none set):",
    },
    "wrong_password": {
        "pl": "Nieprawidlowe haslo. Save'y nie zostana usuniete.",
        "en": "Wrong password. Saves will not be deleted.",
    },
    "edit_status_needs_admin": {
        "pl": "Zmiana statusu gracza wymaga hasla admina gry. Zmiany nie zostaly zapisane.",
        "en": "Changing a player's status requires the game admin password. Changes were not saved.",
    },
    "game_deleted": {
        "pl": "Gra '{name}' usunieta",
        "en": "Game '{name}' deleted",
    },
    "saves_deleted": {
        "pl": "Usunieto pliki save gry '{name}'",
        "en": "Deleted save files for game '{name}'",
    },

    # --- Revert ---
    "revert_title": {
        "pl": "Przywrocenie tury",
        "en": "Revert turn",
    },
    "revert_confirm": {
        "pl": "Czy na pewno chcesz przywrocic gre do tury {turn} (gracz: {player})?\n\n"
              "Wszystkie pozniejsze tury zostana usuniete.\nWszyscy gracze otrzymaja powiadomienie.",
        "en": "Are you sure you want to revert to turn {turn} (player: {player})?\n\n"
              "All later turns will be removed.\nAll players will be notified.",
    },
    "revert_success": {
        "pl": "Przywrocono do tury {turn} ({player})",
        "en": "Reverted to turn {turn} ({player})",
    },
    "revert_select_hint": {
        "pl": "Zaznacz ture z listy aby ja przywrocic.",
        "en": "Select a turn from the list to revert to.",
    },

    # --- Upload confirmation ---
    "not_your_turn_title": {
        "pl": "Nie Twoja kolej",
        "en": "Not your turn",
    },
    "not_your_turn_text": {
        "pl": "Wedlug stanu gry, teraz gra: {name}\n\nCzy na pewno chcesz wyslac save?\n"
              "(np. powtorzenie tury po przywroceniu)",
        "en": "According to game state, it's now {name}'s turn.\n\nAre you sure you want to upload?\n"
              "(e.g. replay after revert)",
    },

    # --- Tray ---
    "tray_show": {
        "pl": "Pokaz okno",
        "en": "Show window",
    },
    "tray_check": {
        "pl": "Sprawdz teraz",
        "en": "Check now",
    },
    "tray_quit": {
        "pl": "Zamknij",
        "en": "Quit",
    },
    "tray_minimized": {
        "pl": "Zminimalizowano do tray. Kliknij dwukrotnie aby otworzyc.",
        "en": "Minimized to tray. Double-click to open.",
    },
    "tray_your_turn_title": {
        "pl": "Civ4 PBEM — Twoja kolej!",
        "en": "Civ4 PBEM — Your turn!",
    },
    "tray_your_turn_body": {
        "pl": "Gra: {game}\nTura: {turn}\n\nKliknij, aby otworzyc.",
        "en": "Game: {game}\nTurn: {turn}\n\nClick to open.",
    },
    "tray_tooltip_pending_one": {
        "pl": "Civ4 PBEM — Twoja tura: {game}",
        "en": "Civ4 PBEM — Your turn: {game}",
    },
    "tray_tooltip_pending_many": {
        "pl": "Civ4 PBEM — Twoja tura w {n} grach",
        "en": "Civ4 PBEM — Your turn in {n} games",
    },
    "tray_new_save_title": {
        "pl": "Civ4 PBEM — Nowy save",
        "en": "Civ4 PBEM — New save",
    },
    "tray_new_save_body": {
        "pl": "Plik: {filename}\n\nKliknij, aby wyslac.",
        "en": "File: {filename}\n\nClick to send.",
    },

    # --- Statistics ---
    "stats_title": {
        "pl": "Statystyki gry: {name}",
        "en": "Game statistics: {name}",
    },
    "stats_total_turns": {
        "pl": "Laczna liczba tur:",
        "en": "Total turns:",
    },
    "stats_total_time": {
        "pl": "Laczny czas gry:",
        "en": "Total game time:",
    },
    "stats_avg_turn_time": {
        "pl": "Sredni czas tury:",
        "en": "Average turn time:",
    },
    "stats_fastest_turn": {
        "pl": "Najszybsza tura:",
        "en": "Fastest turn:",
    },
    "stats_slowest_turn": {
        "pl": "Najwolniejsza tura:",
        "en": "Slowest turn:",
    },
    "stats_per_player": {
        "pl": "Statystyki graczy",
        "en": "Player statistics",
    },
    "stats_player_name": {
        "pl": "Gracz",
        "en": "Player",
    },
    "stats_player_turns": {
        "pl": "Tur",
        "en": "Turns",
    },
    "stats_player_avg_time": {
        "pl": "Sredni czas",
        "en": "Avg. time",
    },
    "stats_player_total_time": {
        "pl": "Laczny czas",
        "en": "Total time",
    },
    "stats_game_started": {
        "pl": "Gra rozpoczeta:",
        "en": "Game started:",
    },
    "stats_last_activity": {
        "pl": "Ostatnia aktywnosc:",
        "en": "Last activity:",
    },
    "stats_current_round": {
        "pl": "Obecna runda:",
        "en": "Current round:",
    },
    "stats_no_game": {
        "pl": "Wybierz gre aby wyswietlic statystyki.",
        "en": "Select a game to view statistics.",
    },

    # --- Auto-launch ---
    "launch_civ4": {
        "pl": "Uruchom Civ4",
        "en": "Launch Civ4",
    },
    "launching_civ4": {
        "pl": "Uruchamianie Civ4 Beyond the Sword...",
        "en": "Launching Civ4 Beyond the Sword...",
    },
    "civ4_launched": {
        "pl": "Civ4 uruchomiony",
        "en": "Civ4 launched",
    },
    "civ4_not_found": {
        "pl": "Nie znaleziono Civ4 BTS. Ustaw sciezke w Ustawieniach.",
        "en": "Civ4 BTS not found. Set the path in Settings.",
    },
    "civ4_already_running": {
        "pl": "Civ4 juz jest uruchomiony",
        "en": "Civ4 is already running",
    },
    "civ4_leader_name": {
        "pl": "Lider / frakcja (z save)",
        "en": "Leader / civ (from save)",
    },
    "civ4_leader_placeholder": {
        "pl": "np. Alexander, Frederick, Wang Kon",
        "en": "e.g. Alexander, Frederick, Wang Kon",
    },
    "civ4_leaders_from_save": {
        "pl": "Liderzy i frakcje z pliku save",
        "en": "Leaders and civs from save file",
    },
    "civ4_leaders_no_save": {
        "pl": "Brak odczytanego save — kliknij „Wczytaj z save…”, albo zostaw puste.",
        "en": "No save loaded yet — click “Load from save…”, or leave empty.",
    },
    "civ4_leaders_load_save": {
        "pl": "Wczytaj z save…",
        "en": "Load from save…",
    },
    "civ4_leaders_pick_save": {
        "pl": "Wybierz save Civ4",
        "en": "Choose Civ4 save",
    },
    "civ4_leaders_loaded": {
        "pl": "Odczytano {n} slot(y) z: {path}",
        "en": "Read {n} slot(s) from: {path}",
    },
    "civ4_leaders_parse_fail": {
        "pl": "Nie udalo sie odczytac liderow z tego save.",
        "en": "Could not read leaders from that save.",
    },
    "edit_player_nick": {
        "pl": "Gracz",
        "en": "Player",
    },
    "edit_player_status": {
        "pl": "Status",
        "en": "Status",
    },
    "edit_player_status_hint": {
        "pl": "Pokonany/zrezygnowany gracz jest pomijany w kolejce tur — kolejny save trafi automatycznie do nastepnego aktywnego gracza.",
        "en": "A defeated/resigned player is skipped in the turn order — the next save automatically routes to the next active player.",
    },
    "player_status_active": {
        "pl": "Aktywny",
        "en": "Active",
    },
    "player_status_defeated": {
        "pl": "Pokonany",
        "en": "Defeated",
    },
    "winner_group": {
        "pl": "Zwycięzca",
        "en": "Winner",
    },
    "winner_label": {
        "pl": "Wygral:",
        "en": "Won by:",
    },
    "winner_none": {
        "pl": "(gra w toku)",
        "en": "(game in progress)",
    },
    "winner_hint": {
        "pl": "Ustaw recznie, albo zostaw puste — gdy zostanie jeden aktywny gracz, "
              "aplikacja uzna go za zwyciezce sama. Reszta stolu dostanie powiadomienie.",
        "en": "Set manually, or leave empty — when one active player remains, "
              "the app declares them the winner. Everyone else with the game in the app is notified.",
    },
    "banner_winner": {
        "pl": "Koniec gry — wygral {player}",
        "en": "Game over — {player} won",
    },
    "game_list_winner": {
        "pl": "Wygral: {player}",
        "en": "Won by: {player}",
    },
    "chip_winner": {
        "pl": "WYGRAL",
        "en": "WON",
    },
    "chip_defeated": {
        "pl": "pokonany",
        "en": "defeated",
    },
    "chip_resigned": {
        "pl": "zrezygnowal",
        "en": "resigned",
    },
    "chip_winner_tooltip": {
        "pl": "{name} wygral te gre",
        "en": "{name} won this game",
    },
    "chip_defeated_tooltip": {
        "pl": "{name} zostal wyeliminowany",
        "en": "{name} was eliminated",
    },
    "chip_resigned_tooltip": {
        "pl": "{name} zrezygnowal",
        "en": "{name} resigned",
    },
    "event_defeated": {
        "pl": "{game}: {player} zostal wyeliminowany",
        "en": "{game}: {player} was eliminated",
    },
    "event_resigned": {
        "pl": "{game}: {player} zrezygnowal",
        "en": "{game}: {player} resigned",
    },
    "event_won": {
        "pl": "{game}: {player} wygral gre!",
        "en": "{game}: {player} won the game!",
    },
    "event_revived": {
        "pl": "{game}: {player} wraca do gry",
        "en": "{game}: {player} is back in the game",
    },
    "event_revert": {
        "pl": "{game}: {player} cofnal ture",
        "en": "{game}: {player} reverted a turn",
    },
    "event_email_subject": {
        "pl": "[Civ4 PBEM] {game} — zmiana w grze",
        "en": "[Civ4 PBEM] {game} — game update",
    },
    "event_email_footer": {
        "pl": "Otworz Civ4 PBEM Manager, zeby zobaczyc aktualny stan.",
        "en": "Open Civ4 PBEM Manager to see the current state.",
    },
    "tray_roster_title": {
        "pl": "Civ4 PBEM — wydarzenie",
        "en": "Civ4 PBEM — game event",
    },
    "civ4_detected": {
        "pl": "Wykryto Civ4: {path}",
        "en": "Civ4 detected: {path}",
    },
    "civ4_not_detected": {
        "pl": "Nie wykryto Civ4 automatycznie. Wskazz reczne.",
        "en": "Civ4 not auto-detected. Please set manually.",
    },
    "save_path_detected": {
        "pl": "Wykryto folder save: {path}",
        "en": "Save folder detected: {path}",
    },
    "save_path_detected_from_civ4": {
        "pl": "Folder z ustawien Civ4 (_Civ4Saves / ini / ALTROOT):\n{path}",
        "en": "Folder from Civ4 settings (_Civ4Saves / ini / ALTROOT):\n{path}",
    },
    "save_path_not_detected": {
        "pl": "Nie wykryto folderu save automatycznie. Uzyj 'Wskaz recznie' i wybierz np. "
              "...\\My Games\\beyond the sword\\Saves",
        "en": "Save folder was not auto-detected. Use 'Choose folder' and pick e.g. "
              "...\\My Games\\beyond the sword\\Saves",
    },
    "choose_save_path_title": {
        "pl": "Wykryte foldery save",
        "en": "Detected save folders",
    },
    "choose_save_path_hint": {
        "pl": "Program uzywa folderu Saves\\pbem. Kazda gra ma w nim podfolder "
              "(np. „Mihau's game”) z plikami .CivBeyondSwordSave. Civ4 Load Game "
              "widzi folder nadrzedny Saves — kopie ida tam automatycznie.",
        "en": "The app uses Saves\\pbem. Each game has a subfolder there "
              "(e.g. \"Mihau's game\") with .CivBeyondSwordSave files. Civ4 Load Game "
              "uses the parent Saves folder — saves are mirrored there automatically.",
    },
    "choose_save_path_use": {
        "pl": "Uzyj tego",
        "en": "Use this",
    },
    "choose_save_path_check_saves": {
        "pl": "Sprawdz czy sa juz save'y w folderze",
        "en": "Check if the folder already has saves",
    },
    "choose_save_path_pick_one": {
        "pl": "Wybierz folder z listy.",
        "en": "Pick a folder from the list.",
    },
    "save_path_from_civ4_badge": {
        "pl": "Wskazany przez Civ4 (ini / skrot / ALTROOT)",
        "en": "Pointed to by Civ4 (ini / shortcut / ALTROOT)",
    },
    "save_path_load_game": {
        "pl": "Civ4 Load Game: {path}",
        "en": "Civ4 Load Game: {path}",
    },
    "save_path_has_saves": {
        "pl": "{count} save(ow) w folderze",
        "en": "{count} save(s) in folder",
    },
    "save_path_no_saves": {
        "pl": "Brak save'ow — OK przy pierwszej instalacji",
        "en": "No saves yet — normal on first install",
    },
    "cancel": {
        "pl": "Anuluj",
        "en": "Cancel",
    },
    "health_ok": {
        "pl": "Wszystko gotowe",
        "en": "All good",
    },
    "health_ok_your_turn": {
        "pl": "Wszystko gotowe — twoja tura",
        "en": "All good — your turn",
    },
    "health_ok_waiting": {
        "pl": "Wszystko gotowe — czeka: {player}",
        "en": "All good — waiting for {player}",
    },
    "health_not_synced": {
        "pl": "{game}: brak synchronizacji z serwerem (pusta historia)",
        "en": "{game}: not synced with server (empty history)",
    },
    "health_not_synced_hint": {
        "pl": "Kliknij „Check now”. Jesli wyskoczy timeout FTP — sprawdz firewall / Game transport.",
        "en": "Click Check now. If you get an FTP timeout — check firewall / Game transport.",
    },
    "health_ok_detail": {
        "pl": "Nick, folder save i polaczenie z serwerem wygladaja OK.",
        "en": "Nickname, save folder and server connection look OK.",
    },
    "health_click_hint": {
        "pl": "Kliknij aby zobaczyc szczegoly",
        "en": "Click for details",
    },
    "health_dialog_title": {
        "pl": "Stan PBEM",
        "en": "PBEM status",
    },
    "health_dialog_hint": {
        "pl": "Program sprawdza to przy starcie i przy kazdym 'Sprawdz teraz'.",
        "en": "Checked at startup and on every 'Check now'.",
    },
    "health_no_nick": {
        "pl": "Brak nicku gracza",
        "en": "Player nickname missing",
    },
    "health_no_nick_hint": {
        "pl": "Ustawienia → Twoj nick (ten sam co w grze)",
        "en": "Settings → Your nickname (same as in the game)",
    },
    "health_save_missing": {
        "pl": "Folder save nie istnieje: {path}",
        "en": "Save folder does not exist: {path}",
    },
    "health_save_missing_hint": {
        "pl": "Ustawienia → Folder save lub 'Wskaz recznie'",
        "en": "Settings → Save folder or 'Choose folder'",
    },
    "health_no_games": {
        "pl": "Brak skonfigurowanych gier",
        "en": "No games configured",
    },
    "health_no_games_hint": {
        "pl": "Dodaj gre lub zaimportuj plik .civ4pbem",
        "en": "Add a game or import a .civ4pbem file",
    },
    "health_locked": {
        "pl": "Program zablokowany — brak hasla glownego",
        "en": "App locked — master password required",
    },
    "health_locked_hint": {
        "pl": "Uruchom ponownie i podaj haslo, albo wylacz szyfrowanie w ustawieniach",
        "en": "Restart and enter password, or disable encryption in settings",
    },
    "health_not_in_game": {
        "pl": "{game}: nie jestes na liscie graczy",
        "en": "{game}: you are not on the player list",
    },
    "health_not_in_game_hint": {
        "pl": "Edytuj gre → tozsamosc / alias dla nicku {nick}",
        "en": "Edit game → identity / alias for nickname {nick}",
    },
    "health_alias_claimed": {
        "pl": "{game}: slot \"{player}\" jest tez ustawiony na innym PC ({other})",
        "en": "{game}: slot \"{player}\" is also claimed on another PC ({other})",
    },
    "health_alias_claimed_hint": {
        "pl": "Edytuj gre → tozsamosc. Dwie kopie z tym samym graczem obie widza \"twoja tura\".",
        "en": "Edit game → identity. Two copies claiming the same player both see \"your turn\".",
    },
    "health_no_transport": {
        "pl": "{game}: brak transportu (FTP/email)",
        "en": "{game}: no transport (FTP/email)",
    },
    "health_no_transport_hint": {
        "pl": "Transport gry → ustaw FTP, SFTP, WebDAV lub email",
        "en": "Game transport → set FTP, SFTP, WebDAV or email",
    },
    "health_transport_fail": {
        "pl": "{game}: nie laczy sie z serwerem",
        "en": "{game}: cannot connect to server",
    },
    "health_transport_fail_hint": {
        "pl": "Sprawdz host, login, haslo i internet",
        "en": "Check host, login, password and internet",
    },
    "health_no_remote_save": {
        "pl": "{game}: twoja tura, ale brak save na serwerze",
        "en": "{game}: your turn but no save on server",
    },
    "health_no_remote_save_hint": {
        "pl": "Poczekaj az poprzedni gracz wysle, albo sprawdz czy to naprawde twoja tura",
        "en": "Wait for the previous player to upload, or verify it is really your turn",
    },
    "health_save_not_local": {
        "pl": "{game}: save na serwerze — kliknij Pobierz save",
        "en": "{game}: save on server — click Download save",
    },
    "health_save_not_local_hint": {
        "pl": "Przycisk 'Pobierz save' lub 'Sprawdz teraz' zrobi to automatycznie",
        "en": "'Download save' or 'Check now' will do this automatically",
    },
    "health_config_mismatch": {
        "pl": "{game}: ustawienia roznia sie od serwera",
        "en": "{game}: settings differ from server",
    },
    "health_tray_title": {
        "pl": "Civ4 PBEM — uwaga",
        "en": "Civ4 PBEM — attention",
    },
    "close": {
        "pl": "Zamknij",
        "en": "Close",
    },
    "save_path_other_candidates": {
        "pl": "Inne znalezione foldery:\n{paths}",
        "en": "Other folders found:\n{paths}",
    },
    "mirror_saves": {
        "pl": "Dubluj save do folderu Civ4 (Load Game)",
        "en": "Also copy saves into the Civ4 Load Game folder",
    },
    "mirror_saves_hint": {
        "pl": (
            "Program trzyma save'y we wlasnym folderze, a kopia idzie tam, "
            "gdzie Civ4 otwiera Load Game. Wpisz folder z gry jesli ma zepsute "
            "ń (np. Jagiello˙ski) albo otwiera Saves zamiast pbem. "
            "Puste = wykryj automatycznie i kopiuj tez do Saves."
        ),
        "en": (
            "The app keeps saves in its own folder and copies them to wherever "
            "Civ4 Load Game opens. Set this if the game mangles ń (e.g. Jagiello˙ski) "
            "or opens Saves instead of pbem. Leave empty to auto-detect and also "
            "copy into Saves."
        ),
    },
    "civ4_save_path": {
        "pl": "Folder Load Game Civ4:",
        "en": "Civ4 Load Game folder:",
    },
    "civ4_save_path_placeholder": {
        "pl": "pusty = wykryj sam (Saves / pbem / OneDrive)",
        "en": "empty = auto-detect (Saves / pbem / OneDrive)",
    },
    "use_civ4_as_primary": {
        "pl": "Wymus jako glowny",
        "en": "Use as primary",
    },
    "wizard_saves_onedrive_hint": {
        "pl": (
            "Jesli w Civ4 nie widac save'a, a w Eksploratorze tak — to dwa rozne "
            "foldery (czesto OneDrive). Wskaz ten, w ktorym gra pokazuje auto/pitboss."
        ),
        "en": (
            "If Civ4 cannot see a save that Explorer shows, they are two different "
            "folders (often OneDrive). Pick the one where the game lists auto/pitboss."
        ),
    },

    # --- Import/Export ---
    "export_title": {
        "pl": "Eksportuj konfiguracje gry",
        "en": "Export game configuration",
    },
    "import_title": {
        "pl": "Importuj konfiguracje gry",
        "en": "Import game configuration",
    },
    "exported": {
        "pl": "Wyeksportowano: {path}",
        "en": "Exported: {path}",
    },
    "imported": {
        "pl": "Zaimportowano gre: {name}",
        "en": "Imported game: {name}",
    },
    "import_choose_player_title": {
        "pl": "Wybierz swojego gracza",
        "en": "Choose your player",
    },
    "import_choose_player_body": {
        "pl": "Gra: {game}\nTwoj lokalny nick: '{nick}'\n\n"
              "Ktorym graczem z listy jestes?\n"
              "(Jesli obok jest lider/frakcja — to odczyt z lokalnego save.)",
        "en": "Game: {game}\nYour local nick: '{nick}'\n\n"
              "Which player on the list are you?\n"
              "(Leader/civ next to a name comes from a local save, if found.)",
    },
    "import_sync_ok": {
        "pl": "Zsynchronizowano z serwerem — tura {turn}, kolej: {player}",
        "en": "Synced from server — turn {turn}, next: {player}",
    },
    "import_sync_unchanged": {
        "pl": "Import OK. Kolej: {player}. Kliknij „Sprawdz teraz” jesli wyglada zle.",
        "en": "Import OK. Waiting for: {player}. Click Check now if this looks wrong.",
    },
    "import_sync_no_transport": {
        "pl": "Zaimportowano, ale brak transportu — ustaw FTP/email i kliknij „Sprawdz teraz”.",
        "en": "Imported, but no transport — set FTP/email and click Check now.",
    },
    "import_sync_failed": {
        "pl": "Zaimportowano, ale nie udalo sie pobrac stanu z serwera. Kliknij „Sprawdz teraz”.",
        "en": "Imported, but could not fetch state from server. Click Check now.",
    },
    "import_sync_no_saves": {
        "pl": "Zaimportowano „{game}”, ale na FTP nie ma managed save’ow (plikow: {n}). "
              "Sprawdz Game transport (host/katalog) i kliknij „Sprawdz teraz”.",
        "en": "Imported “{game}”, but no managed saves on FTP ({n} files listed). "
              "Check Game transport (host/folder) and click Check now.",
    },
    "import_sync_keep_export": {
        "pl": "FTP nie zwrocil save’ow ({tip}). Zostawiam stan z pliku .civ4pbem — "
              "tura {turn}, kolej: {player}. Pozniej kliknij Check now.",
        "en": "FTP returned no saves ({tip}). Keeping .civ4pbem state — "
              "turn {turn}, next: {player}. Click Check now later.",
    },
    "check_watchdog_abandoned": {
        "pl": "Sprawdzanie wisialo zbyt dlugo (FTP). Sprobuj ponownie za chwile.",
        "en": "Check hung too long (FTP). Try again in a moment.",
    },
    "check_ftp_timeout_hint": {
        "pl": "FTP: {error}",
        "en": "FTP: {error}",
    },
    "load_state_btn": {
        "pl": "Pobierz stan",
        "en": "Pull state",
    },
    "load_state_hint": {
        "pl": "Sciaga z FTP plik {gra}_turns.json (albo _state.json) i uzupelnia historie. "
              "Bez listowania katalogu — ten sam kanal co download save’a.",
        "en": "Downloads {game}_turns.json (or _state.json) from FTP and fills history. "
              "No directory listing — same channel as save download.",
    },
    "load_state_title": {
        "pl": "Stan z serwera",
        "en": "State from server",
    },
    "load_state_pulling": {
        "pl": "Pobieranie stanu {game} z FTP…",
        "en": "Pulling {game} state from FTP…",
    },
    "load_state_filter": {
        "pl": "Stan gry (*.json);;Wszystkie (*.*)",
        "en": "Game state (*.json);;All (*.*)",
    },
    "load_state_ok": {
        "pl": "Wczytano stan — tura {turn}, kolej: {player} ({n} wpisow historii).",
        "en": "State loaded — turn {turn}, next: {player} ({n} history entries).",
    },
    "load_state_missing": {
        "pl": "Brak pliku: {path}",
        "en": "File missing: {path}",
    },
    "load_state_bad_json": {
        "pl": "Niepoprawny JSON: {error}",
        "en": "Bad JSON: {error}",
    },
    "load_state_no_history": {
        "pl": "Ten plik nie ma historii tur (puste history). "
              "Potrzebujesz *_turns.json albo *_state.json z niepustym history.",
        "en": "This file has no turn history (empty history). "
              "Need *_turns.json or *_state.json with non-empty history.",
    },
    "load_state_select_game": {
        "pl": "Najpierw wybierz gre po lewej.",
        "en": "Select a game in the sidebar first.",
    },
    "list_server_btn": {
        "pl": "Lista FTP",
        "en": "List FTP",
    },
    "list_server_hint": {
        "pl": "Pokaz surowa liste plikow na serwerze i uzupelnij historie, jesli sa save’y.",
        "en": "Show raw server file list and repair history if saves are there.",
    },
    "list_server_title": {
        "pl": "Pliki na serwerze",
        "en": "Files on server",
    },
    "list_server_done": {
        "pl": "FTP {game}: {n} plik(ow)",
        "en": "FTP {game}: {n} file(s)",
    },
    "list_server_repaired": {
        "pl": "Uzupelniono historie z {n} save’ow. Kolej: {player}",
        "en": "Repaired history from {n} saves. Next: {player}",
    },
    "import_syncing": {
        "pl": "Pobieranie stanu gry z serwera...",
        "en": "Downloading game state from server...",
    },
    "banner_no_server_state": {
        "pl": "BRAK STANU Z SERWERA — pusta historia. Kliknij „Sprawdz teraz”. "
              "Dopoki nie ma historii, to NIE jest Twoja tura.",
        "en": "NO SERVER STATE — empty history. Click Check now. "
              "Until history exists, this is NOT your turn.",
    },
    "history_empty_hint": {
        "pl": "Historia pusta — brak stanu kolejki z serwera. Kliknij „Sprawdz teraz”. "
              "Po imporcie gry raz wystarczy Check na kazdym PC (bez eksportu).",
        "en": "Empty history — no turn queue from the server yet. Click Check now. "
              "After importing the game once, Check is enough on every PC (no re-export).",
    },
    "game_list_needs_sync": {
        "pl": "BRAK SYNC Z SERWERA — kliknij Check",
        "en": "NOT SYNCED — click Check",
    },
    "check_no_saves_found": {
        "pl": "Check „{game}”: na FTP jest {n} plikow, ale ZERO managed save’ow. "
              "Widoczne: {sample}. Sprawdz Game transport → remote_dir / nazwe folderu gry.",
        "en": "Check “{game}”: FTP listed {n} files but ZERO managed saves. "
              "Seen: {sample}. Check Game transport → remote_dir / game folder name.",
    },
    "check_server_inventory": {
        "pl": "Check „{game}”: FTP plikow={files}, save’y={saves}, "
              "state.json={state}, config={config}, najnowszy={tip}",
        "en": "Check “{game}”: FTP files={files}, saves={saves}, "
              "state.json={state}, config={config}, latest={tip}",
    },
    "check_state_fallback": {
        "pl": "Check „{game}”: brak save’ow — pobieram {game}_state.json jako zapas…",
        "en": "Check “{game}”: no saves — downloading {game}_state.json as fallback…",
    },
    "check_state_empty_history": {
        "pl": "Check „{game}”: state.json jest, ale historia nadal pusta. "
              "Plik stanu na serwerze jest uszkodzony/stary — wgraj save’y albo popraw state.",
        "en": "Check “{game}”: state.json present but history still empty. "
              "Server state file is bad/stale — upload saves or fix state.",
    },
    "check_no_saves_or_state": {
        "pl": "Check „{game}”: na FTP ({n} plikow) NIE MA ani managed save’ow, "
              "ani {game}_state.json. Widoczne: {sample}. "
              "Zly katalog gry albo puste konto — otworz Game transport.",
        "en": "Check “{game}”: FTP ({n} files) has neither managed saves nor "
              "{game}_state.json. Seen: {sample}. Wrong game folder or empty — open Game transport.",
    },
    "game_exists_overwrite": {
        "pl": "Gra '{name}' juz istnieje. Nadpisac?",
        "en": "Game '{name}' already exists. Overwrite?",
    },
    "import_error": {
        "pl": "Nie udalo sie zaimportowac:\n{error}",
        "en": "Failed to import:\n{error}",
    },

    # --- Misc ---
    "info": {
        "pl": "Info",
        "en": "Info",
    },
    "error": {
        "pl": "Blad",
        "en": "Error",
    },
    "select_game_to_export": {
        "pl": "Zaznacz gre do eksportu.",
        "en": "Select a game to export.",
    },
    "select_game_to_delete": {
        "pl": "Zaznacz gre do usuniecia.",
        "en": "Select a game to delete.",
    },
    "select_game_for_transport": {
        "pl": "Zaznacz gre aby skonfigurowac transport.",
        "en": "Select a game to configure transport.",
    },
    "transport_saved": {
        "pl": "Transport gry '{name}' zapisany.",
        "en": "Game transport '{name}' saved.",
    },
    "shared_config_pushed": {
        "pl": "Ustawienia gry '{name}' wyslane na serwer — reszta stolika dostanie je przy sprawdzaniu.",
        "en": "Settings for '{name}' uploaded — other players will get them on the next check.",
    },
    "shared_config_failed": {
        "pl": "Nie udalo sie wyslac ustawien gry '{name}' na serwer: {msg}",
        "en": "Could not upload settings for '{name}': {msg}",
    },
    "choose_save_title": {
        "pl": "Wybierz save do pobrania",
        "en": "Choose save to download",
    },
    "choose_save_label": {
        "pl": "Dostepne save'y dla '{name}':\n(najnowszy na dole)",
        "en": "Available saves for '{name}':\n(newest at bottom)",
    },
    "choose_save_to_upload": {
        "pl": "Wybierz save do wyslania",
        "en": "Choose save to upload",
    },
    "civ4_saves_filter": {
        "pl": "Civ4 Saves (*.CivBeyondSwordSave);;Wszystkie pliki (*)",
        "en": "Civ4 Saves (*.CivBeyondSwordSave);;All Files (*)",
    },

    # --- First-run setup wizard ---
    "wizard_title": {
        "pl": "Civ4 PBEM Manager — konfiguracja",
        "en": "Civ4 PBEM Manager — setup",
    },
    "wizard_step": {
        "pl": "Krok {current} z {total}",
        "en": "Step {current} of {total}",
    },
    "wizard_next": {
        "pl": "Dalej",
        "en": "Next",
    },
    "wizard_back": {
        "pl": "Wstecz",
        "en": "Back",
    },
    "wizard_skip": {
        "pl": "Pomin (ustawie pozniej)",
        "en": "Skip (I'll set this later)",
    },
    "wizard_finish": {
        "pl": "Zakoncz i uruchom",
        "en": "Finish and start",
    },
    "wizard_rerun": {
        "pl": "Uruchom kreator konfiguracji ponownie...",
        "en": "Run setup wizard again...",
    },
    "wizard_welcome_title": {
        "pl": "Witaj. Poprowadzimy Cie przez ustawienia.",
        "en": "Welcome. We'll walk you through setup.",
    },
    "wizard_welcome_body": {
        "pl": "Krok po kroku:\n"
              "1. Nick i email\n"
              "2. Wykrycie Civ4, folder save i /fxsload (dwuklik laduje ture)\n"
              "3. Import gry od hosta albo nowa gra + transport\n\n"
              "Zajmie to minute.",
        "en": "Step by step:\n"
              "1. Nickname and email\n"
              "2. Detect Civ4, save folder and /fxsload (double-click loads a turn)\n"
              "3. Import from host or new game + transport\n\n"
              "This takes about a minute.",
    },
    "wizard_identity_title": {
        "pl": "Kim jestes w grach PBEM?",
        "en": "Who are you in PBEM games?",
    },
    "wizard_identity_hint": {
        "pl": "Nick musi zgadzac sie z nazwa gracza w save'ach (albo ustawisz alias przy imporcie gry). "
              "Email jest opcjonalny — do powiadomien o turze.",
        "en": "Your nick should match the player name in saves (or set an alias when you import a game). "
              "Email is optional — used for turn notifications.",
    },
    "wizard_name_placeholder": {
        "pl": "np. Mihau",
        "en": "e.g. Mihau",
    },
    "wizard_email_placeholder": {
        "pl": "opcjonalnie, np. gracz@example.com",
        "en": "optional, e.g. player@example.com",
    },
    "wizard_name_required": {
        "pl": "Podaj nick — bez niego aplikacja nie wie, ktora tura jest Twoja.",
        "en": "Enter a nick — without it the app cannot tell when it is your turn.",
    },
    "wizard_detect_title": {
        "pl": "Szukamy Civ4 na tym komputerze",
        "en": "Looking for Civ4 on this PC",
    },
    "wizard_detect_hint": {
        "pl": "Najpierw Civ4 (Steam / GOG / plyta), potem folder save. "
              "Jesli cos nie wstalo samo — wskaz recznie.",
        "en": "Civ4 first (Steam / GOG / DVD), then the save folder. "
              "Browse manually if something was not found.",
    },
    "wizard_detect_civ4": {
        "pl": "Szukaj Civ4 na tym komputerze",
        "en": "Search for Civ4 on this PC",
    },
    "wizard_preferred_edition": {
        "pl": "Wersja do /fxsload i uruchamiania:",
        "en": "Edition for /fxsload and launch:",
    },
    "wizard_save_section": {
        "pl": "Folder save'ow",
        "en": "Save folder",
    },
    "wizard_saves_missing": {
        "pl": "Nie wybrano folderu — kliknij Wykryj automatycznie.",
        "en": "No folder selected — click Auto-detect.",
    },
    "wizard_save_required": {
        "pl": "Wybierz folder save'ow zanim przejdziesz dalej.",
        "en": "Pick a save folder before continuing.",
    },
    "wizard_no_civ4_continue": {
        "pl": "Nie znaleziono Civ4BeyondSword.exe. Mozesz kontynuowac i wskazac "
              "gre pozniej w Ustawieniach. Kontynuowac?",
        "en": "Civ4BeyondSword.exe was not found. You can continue and set it "
              "later in Settings. Continue?",
    },
    "wizard_saves_found": {
        "pl": "Folder save'ow: {path}",
        "en": "Save folder: {path}",
    },
    "wizard_saves_found_layout": {
        "pl": "PBEM: {pbem}\nCiv4 Load Game: {load_game}",
        "en": "PBEM: {pbem}\nCiv4 Load Game: {load_game}",
    },
    "wizard_browse_saves": {
        "pl": "Wskaz folder save'ow...",
        "en": "Choose save folder...",
    },
    "wizard_browse_exe": {
        "pl": "Wskaz Civ4BeyondSword.exe",
        "en": "Locate Civ4BeyondSword.exe",
    },
    "wizard_edition_found": {
        "pl": "{name}: znaleziono\n{path}",
        "en": "{name}: found\n{path}",
    },
    "wizard_edition_missing": {
        "pl": "{name}: nie znaleziono — wskaz exe, jesli masz te wersje",
        "en": "{name}: not found — browse if you have this edition",
    },
    "wizard_fxsload": {
        "pl": "Laduj save bezposrednio w Civ4 (/fxsload)",
        "en": "Load saves directly in Civ4 (/fxsload)",
    },
    "wizard_assoc": {
        "pl": "Powiaz pliki .CivBeyondSwordSave z Civ4 (dwuklik otwiera ture)",
        "en": "Associate .CivBeyondSwordSave with Civ4 (double-click opens the turn)",
    },
    "wizard_assoc_hint": {
        "pl": "Zapisuje w Twoim profilu Windows komende: Civ4BeyondSword.exe /fxsload=\"%1\". "
              "Bez uprawnien administratora.",
        "en": "Writes to your Windows user profile: Civ4BeyondSword.exe /fxsload=\"%1\". "
              "No administrator rights needed.",
    },
    "wizard_done_title": {
        "pl": "Gotowe. Mozesz grac.",
        "en": "Done. You can play.",
    },
    "wizard_done_next": {
        "pl": "Co dalej? Wybierz jedna opcje — albo wejdz do programu przyciskiem na dole.",
        "en": "What's next? Pick an option — or open the app with the button below.",
    },
    "wizard_open_app": {
        "pl": "Wejdz do programu",
        "en": "Open app",
    },
    "wizard_action_import": {
        "pl": "Importuj gre (.civ4pbem od hosta)",
        "en": "Import game (.civ4pbem from host)",
    },
    "wizard_action_new_game": {
        "pl": "Utworz nowa gre (jestes hostem)",
        "en": "Create new game (you are the host)",
    },
    "wizard_action_settings": {
        "pl": "Ustawienia transportu i powiadomien",
        "en": "Transport and notification settings",
    },
    "wizard_summary_name": {
        "pl": "Nick: {name}",
        "en": "Nick: {name}",
    },
    "wizard_summary_saves": {
        "pl": "Save'y: {path}",
        "en": "Saves: {path}",
    },
    "wizard_summary_civ4": {
        "pl": "Civ4: {editions}",
        "en": "Civ4: {editions}",
    },
    "wizard_summary_civ4_preferred": {
        "pl": "Civ4 ({edition}): {path}",
        "en": "Civ4 ({edition}): {path}",
    },
    "wizard_summary_civ4_none": {
        "pl": "Civ4: nie wskazano — ustawisz w Ustawieniach",
        "en": "Civ4: not set — you can add it in Settings",
    },
    "wizard_summary_fxsload": {
        "pl": "Bezposrednie ladowanie save'ow: wlaczone",
        "en": "Direct save loading: on",
    },
    "wizard_summary_assoc": {
        "pl": "Skojarzenie .CivBeyondSwordSave: ustawione",
        "en": ".CivBeyondSwordSave association: set",
    },
}


class I18n:
    """Internationalization manager with runtime language switching."""

    def __init__(self, language: str = DEFAULT_LANGUAGE):
        self._language = language if language in LANGUAGES else DEFAULT_LANGUAGE

    @property
    def language(self) -> str:
        return self._language

    @language.setter
    def language(self, value: str):
        if value in LANGUAGES:
            self._language = value

    def t(self, key: str, **kwargs) -> str:
        """Get translated string by key. Supports format kwargs.

        Usage:
            i18n.t("waiting_for", name="PlayerName")
            i18n.t("your_turn")
        """
        translations = _TRANSLATIONS.get(key)
        if not translations:
            return f"[{key}]"

        text = translations.get(self._language, translations.get("pl", f"[{key}]"))

        if kwargs:
            try:
                text = text.format(**kwargs)
            except (KeyError, IndexError):
                pass

        return text

    def get_language_display_name(self, lang: str) -> str:
        """Get display name for a language code."""
        names = {
            "pl": "Polski",
            "en": "English",
        }
        return names.get(lang, lang)


# Global singleton instance
_instance: I18n = I18n()


def get_i18n() -> I18n:
    """Get the global I18n instance."""
    return _instance


def set_language(language: str):
    """Set the global language."""
    _instance.language = language


def t(key: str, **kwargs) -> str:
    """Shortcut for global translation lookup."""
    return _instance.t(key, **kwargs)
