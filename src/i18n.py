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
        "pl": "Civ4 PBEM Manager v4.1",
        "en": "Civ4 PBEM Manager v4.1",
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
        "pl": "Importuj gre...",
        "en": "Import game...",
    },
    "export_game": {
        "pl": "Eksportuj gre...",
        "en": "Export game...",
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
    "edit_players": {
        "pl": "Emaile graczy",
        "en": "Player emails",
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
        "pl": "  TWOJA KOLEJ! Save jest gotowy do pobrania.",
        "en": "  YOUR TURN! Save is ready to download.",
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
    "open_folder": {
        "pl": "Otworz folder",
        "en": "Open folder",
    },
    "check_now": {
        "pl": "Sprawdz teraz",
        "en": "Check now",
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
        "pl": "Kolejnosc graczy: ",
        "en": "Player order: ",
    },
    "you_marker": {
        "pl": " (Ty)",
        "en": " (You)",
    },
    "playing_since": {
        "pl": "{name} gra juz: {time}",
        "en": "{name} has been playing for: {time}",
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
        "pl": "Folder save'ow:",
        "en": "Save folder:",
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
    "language": {
        "pl": "Jezyk / Language:",
        "en": "Language / Jezyk:",
    },
    "auto_launch": {
        "pl": "Auto-uruchom Civ4 po pobraniu save'a",
        "en": "Auto-launch Civ4 after downloading save",
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
        "pl": "Preferowana wersja (gdy wiecej niz jedna):",
        "en": "Preferred version (when more than one):",
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
        "pl": "np. WojnaSwiatowa",
        "en": "e.g. WorldWar",
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
    "no_new_saves": {
        "pl": "Sprawdzono - brak nowych save'ow",
        "en": "Checked - no new saves found",
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
    "admin_password_prompt": {
        "pl": "Podaj haslo admina gry aby usunac pliki save:",
        "en": "Enter game admin password to delete save files:",
    },
    "wrong_password": {
        "pl": "Nieprawidlowe haslo. Save'y nie zostana usuniete.",
        "en": "Wrong password. Saves will not be deleted.",
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
        "pl": "Nazwa lidera Civ4 (jak w save):",
        "en": "Civ4 leader name (as in save file):",
    },
    "civ4_leader_placeholder": {
        "pl": "np. Zara_Yaqob, Montezuma, Washington",
        "en": "e.g. Zara_Yaqob, Montezuma, Washington",
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
    "save_path_not_detected": {
        "pl": "Nie wykryto folderu save automatycznie. Wskazz reczne.",
        "en": "Save folder not auto-detected. Please set manually.",
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
