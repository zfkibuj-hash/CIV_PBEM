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
        "pl": "Civ4 PBEM Manager v1.1",
        "en": "Civ4 PBEM Manager v1.1",
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
        "pl": "Historia tur (kliknij aby przywrocic)",
        "en": "Turn history (click to revert)",
    },
    "revert_selected": {
        "pl": "Przywroc zaznaczona ture",
        "en": "Revert to selected turn",
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
        "pl": "Czeka",
        "en": "Waiting",
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

    # --- New Game Dialog ---
    "new_game_title": {
        "pl": "Nowa gra",
        "en": "New Game",
    },
    "game_name": {
        "pl": "Nazwa gry:",
        "en": "Game name:",
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
