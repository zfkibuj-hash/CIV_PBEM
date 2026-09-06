"""
Theme stylesheets for Civ4 PBEM Manager.
Exports DARK_STYLE, LIGHT_STYLE and get_style_for_theme().
"""

DARK_STYLE = """
QMainWindow, QWidget {
    background-color: #1e1e1e;
    color: #e0e0e0;
    font-family: "Segoe UI", sans-serif;
    font-size: 10pt;
}
QWidget#sidebar {
    background-color: #252536;
}
QGroupBox {
    border: 1px solid #555;
    border-radius: 4px;
    margin-top: 8px;
    padding-top: 12px;
    font-weight: bold;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 5px;
}
QPushButton {
    background-color: #2d2d2d;
    border: 1px solid #555;
    border-radius: 4px;
    padding: 6px 16px;
    min-height: 24px;
}
QPushButton:hover {
    background-color: #383838;
    border-color: #42a5f5;
}
QPushButton:pressed {
    background-color: #1a1a2e;
}
QPushButton#btn_play_now {
    background-color: #2e7d32;
    border-color: #66bb6a;
    color: white;
    font-weight: bold;
    font-size: 12pt;
}
QPushButton#btn_play_now:hover {
    background-color: #388e3c;
}
QPushButton#btn_play_now:disabled {
    background-color: #1b3d1f;
    border-color: #336633;
    color: #888;
}
QPushButton#btn_download {
    background-color: #1b5e20;
    border-color: #4caf50;
    color: white;
    font-weight: bold;
}
QPushButton#btn_download:hover {
    background-color: #2e7d32;
}
QPushButton#btn_upload {
    background-color: #0d47a1;
    border-color: #42a5f5;
    color: white;
    font-weight: bold;
}
QPushButton#btn_upload:hover {
    background-color: #1565c0;
}
QListWidget {
    background-color: #252536;
    border: 1px solid #555;
    border-radius: 4px;
    padding: 4px;
}
QListWidget::item {
    padding: 8px;
    border-radius: 3px;
}
QListWidget::item:selected {
    background-color: #1a3a1a;
    border-left: 3px solid #66bb6a;
}
QListWidget::item:hover {
    background-color: #2d2d3d;
}
QLineEdit, QSpinBox, QComboBox {
    background-color: #2d2d2d;
    border: 1px solid #555;
    border-radius: 3px;
    padding: 4px 8px;
    min-height: 20px;
}
QLineEdit:focus, QSpinBox:focus, QComboBox:focus {
    border-color: #42a5f5;
}
QLabel#status_bar {
    background-color: #1a1a2e;
    padding: 4px 12px;
    font-size: 9pt;
    color: #9e9e9e;
}
QLabel#banner_your_turn {
    background-color: #1b5e20;
    color: white;
    padding: 8px 16px;
    font-weight: bold;
    font-size: 11pt;
}
QLabel#banner_waiting {
    background-color: #2d2d2d;
    color: #9e9e9e;
    padding: 8px 16px;
    font-size: 10pt;
}
QLabel#banner_winner {
    background-color: #b8860b;
    color: white;
    padding: 8px 16px;
    font-weight: bold;
    font-size: 11pt;
}
QLabel#health_ok {
    background-color: #1b5e20;
    color: #c8e6c9;
    padding: 6px 16px;
    font-size: 10pt;
}
QLabel#health_info {
    background-color: #263238;
    color: #b0bec5;
    padding: 6px 16px;
    font-size: 10pt;
}
QLabel#health_warn {
    background-color: #e65100;
    color: white;
    padding: 6px 16px;
    font-size: 10pt;
    font-weight: bold;
}
QLabel#health_error {
    background-color: #b71c1c;
    color: white;
    padding: 6px 16px;
    font-size: 10pt;
    font-weight: bold;
}
QLabel#status_banner[state="your_turn"] {
    background-color: #1b5e20;
    color: white;
    padding: 8px 16px;
    font-weight: bold;
    font-size: 11pt;
}
QLabel#status_banner[state="waiting"] {
    background-color: #2d2d2d;
    color: #9e9e9e;
    padding: 8px 16px;
    font-size: 10pt;
}
QLabel#game_header {
    background-color: #2d2d2d;
    color: #e0e0e0;
    padding: 12px 20px;
    font-size: 12pt;
    font-weight: bold;
}
QTextEdit {
    background-color: #252536;
    border: 1px solid #555;
    border-radius: 4px;
    color: #9e9e9e;
    font-size: 9pt;
}
QSplitter::handle {
    background-color: #555;
}
QTabWidget::pane {
    border: 1px solid #555;
    background-color: #1e1e1e;
}
QTabBar::tab {
    background-color: #2d2d2d;
    color: #e0e0e0;
    border: 1px solid #555;
    border-bottom: none;
    padding: 8px 20px;
    margin-right: 2px;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
}
QTabBar::tab:selected {
    background-color: #1e1e1e;
    color: #42a5f5;
    border-bottom: 2px solid #42a5f5;
}
QTabBar::tab:hover:!selected {
    background-color: #383838;
}
QTableWidget {
    background-color: #252536;
    border: 1px solid #555;
    border-radius: 4px;
    gridline-color: #444;
    color: #e0e0e0;
}
QTableWidget::item {
    padding: 4px 8px;
    color: #e0e0e0;
}
QTableWidget::item:selected {
    background-color: #1a3a1a;
    color: #e0e0e0;
}
QHeaderView::section {
    background-color: #333350;
    color: #e0e0e0;
    border: 1px solid #555;
    padding: 4px 8px;
    font-weight: bold;
}
QHeaderView::section:horizontal {
    border-top: none;
}
"""


LIGHT_STYLE = """
QMainWindow, QWidget {
    background-color: #f5f5f5;
    color: #212121;
    font-family: "Segoe UI", sans-serif;
    font-size: 10pt;
}
QWidget#sidebar {
    background-color: #e0e0e0;
}
QGroupBox {
    border: 1px solid #bdbdbd;
    border-radius: 4px;
    margin-top: 8px;
    padding-top: 12px;
    font-weight: bold;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 5px;
}
QPushButton {
    background-color: #ffffff;
    border: 1px solid #bdbdbd;
    border-radius: 4px;
    padding: 6px 16px;
    min-height: 24px;
    color: #212121;
}
QPushButton:hover {
    background-color: #e3f2fd;
    border-color: #1976d2;
}
QPushButton:pressed {
    background-color: #bbdefb;
}
QPushButton#btn_play_now {
    background-color: #2e7d32;
    border-color: #66bb6a;
    color: white;
    font-weight: bold;
    font-size: 12pt;
}
QPushButton#btn_play_now:hover {
    background-color: #388e3c;
}
QPushButton#btn_play_now:disabled {
    background-color: #1b3d1f;
    border-color: #336633;
    color: #888;
}
QPushButton#btn_download {
    background-color: #4caf50;
    border-color: #388e3c;
    color: white;
    font-weight: bold;
}
QPushButton#btn_download:hover {
    background-color: #66bb6a;
}
QPushButton#btn_upload {
    background-color: #1976d2;
    border-color: #1565c0;
    color: white;
    font-weight: bold;
}
QPushButton#btn_upload:hover {
    background-color: #42a5f5;
}
QListWidget {
    background-color: #ffffff;
    border: 1px solid #bdbdbd;
    border-radius: 4px;
    padding: 4px;
}
QListWidget::item {
    padding: 8px;
    border-radius: 3px;
}
QListWidget::item:selected {
    background-color: #e8f5e9;
    border-left: 3px solid #4caf50;
}
QListWidget::item:hover {
    background-color: #f5f5f5;
}
QLineEdit, QSpinBox, QComboBox {
    background-color: #ffffff;
    border: 1px solid #bdbdbd;
    border-radius: 3px;
    padding: 4px 8px;
    min-height: 20px;
    color: #212121;
}
QLineEdit:focus, QSpinBox:focus, QComboBox:focus {
    border-color: #1976d2;
}
QLabel#status_bar {
    background-color: #e0e0e0;
    padding: 4px 12px;
    font-size: 9pt;
    color: #616161;
}
QLabel#banner_your_turn {
    background-color: #4caf50;
    color: white;
    padding: 8px 16px;
    font-weight: bold;
    font-size: 11pt;
}
QLabel#banner_waiting {
    background-color: #eeeeee;
    color: #616161;
    padding: 8px 16px;
    font-size: 10pt;
}
QLabel#banner_winner {
    background-color: #ffc107;
    color: #111111;
    padding: 8px 16px;
    font-weight: bold;
    font-size: 11pt;
}
QLabel#status_banner[state="your_turn"] {
    background-color: #4caf50;
    color: white;
    padding: 8px 16px;
    font-weight: bold;
    font-size: 11pt;
}
QLabel#status_banner[state="waiting"] {
    background-color: #eeeeee;
    color: #616161;
    padding: 8px 16px;
    font-size: 10pt;
}
QLabel#game_header {
    background-color: #e0e0e0;
    color: #212121;
    padding: 12px 20px;
    font-size: 12pt;
    font-weight: bold;
}
QTextEdit {
    background-color: #ffffff;
    border: 1px solid #bdbdbd;
    border-radius: 4px;
    color: #616161;
    font-size: 9pt;
}
QSplitter::handle {
    background-color: #bdbdbd;
}
QTabWidget::pane {
    border: 1px solid #bdbdbd;
    background-color: #f5f5f5;
}
QTabBar::tab {
    background-color: #e0e0e0;
    color: #212121;
    border: 1px solid #bdbdbd;
    border-bottom: none;
    padding: 8px 20px;
    margin-right: 2px;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
}
QTabBar::tab:selected {
    background-color: #f5f5f5;
    color: #1976d2;
    border-bottom: 2px solid #1976d2;
}
QTabBar::tab:hover:!selected {
    background-color: #eeeeee;
}
QCheckBox {
    color: #212121;
}
QTableWidget {
    background-color: #ffffff;
    border: 1px solid #bdbdbd;
    border-radius: 4px;
    gridline-color: #e0e0e0;
    color: #212121;
}
QTableWidget::item {
    padding: 4px 8px;
    color: #212121;
}
QTableWidget::item:selected {
    background-color: #e8f5e9;
    color: #212121;
}
QHeaderView::section {
    background-color: #e0e0e0;
    color: #212121;
    border: 1px solid #bdbdbd;
    padding: 4px 8px;
    font-weight: bold;
}
QHeaderView::section:horizontal {
    border-top: none;
}
"""


def get_style_for_theme(dark: bool) -> str:
    """Return the appropriate stylesheet."""
    return DARK_STYLE if dark else LIGHT_STYLE
