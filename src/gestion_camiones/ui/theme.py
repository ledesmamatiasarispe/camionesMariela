from __future__ import annotations

import json
from pathlib import Path

from PySide6.QtGui import QColor, QPalette

DEFAULT_THEME: dict[str, str | int] = {
    "app_background": "#f5f7f8",
    "text_color": "#182026",
    "menu_background": "#ffffff",
    "panel_background": "#ffffff",
    "panel_header_background": "#ffffff",
    "input_background": "#ffffff",
    "border_color": "#d9e0e5",
    "muted_text": "#63707a",
    "sidebar_background": "#24333a",
    "brand_text": "#ffffff",
    "sidebar_subtitle_text": "#adb8bd",
    "nav_text": "#d6dde1",
    "nav_active_text": "#ffffff",
    "nav_active_background": "#3b4a51",
    "page_title_text": "#182026",
    "section_title_text": "#182026",
    "metric_value_text": "#182026",
    "accent_color": "#1f6f8b",
    "primary_button_text": "#ffffff",
    "danger_color": "#b42318",
    "table_alt_background": "#f8fafb",
    "table_header_background": "#eef3f5",
    "table_header_text": "#63707a",
    "font_family": "Segoe UI",
    "base_font_size": 14,
}

THEME_COLOR_FIELDS: tuple[tuple[str, str], ...] = (
    ("app_background", "Fondo general"),
    ("text_color", "Texto principal"),
    ("menu_background", "Barra menu"),
    ("panel_background", "Paneles"),
    ("panel_header_background", "Cabecera panel"),
    ("input_background", "Campos"),
    ("border_color", "Bordes"),
    ("muted_text", "Texto secundario"),
    ("sidebar_background", "Sidebar fondo"),
    ("brand_text", "Marca sidebar"),
    ("sidebar_subtitle_text", "Sidebar subtitulo"),
    ("nav_text", "Sidebar texto"),
    ("nav_active_text", "Sidebar activo texto"),
    ("nav_active_background", "Sidebar activo fondo"),
    ("page_title_text", "Titulo pagina"),
    ("section_title_text", "Titulo seccion"),
    ("metric_value_text", "Valor metricas"),
    ("accent_color", "Color primario"),
    ("primary_button_text", "Texto primario"),
    ("danger_color", "Color peligro"),
    ("table_alt_background", "Tabla alterna"),
    ("table_header_background", "Cabecera tabla"),
    ("table_header_text", "Texto cabecera"),
)

STYLE_TEMPLATE = """
QWidget {{
    background: __APP_BACKGROUND__;
    color: __TEXT_COLOR__;
    font-family: "__FONT_FAMILY__", "San Francisco", Arial, sans-serif;
    font-size: __BASE_FONT_SIZE__px;
}}

QMenuBar {{
    background: __MENU_BACKGROUND__;
    border-bottom: 1px solid __BORDER_COLOR__;
}}

QPushButton {{
    min-height: 34px;
    border: 1px solid __BORDER_COLOR__;
    border-radius: 8px;
    background: __PANEL_BACKGROUND__;
    padding: 0 12px;
}}

QPushButton:hover {{
    border-color: __ACCENT_COLOR__;
}}

QLineEdit {{
    min-height: 34px;
    border: 1px solid __BORDER_COLOR__;
    border-radius: 8px;
    background: __INPUT_BACKGROUND__;
    padding: 0 12px;
}}

QComboBox,
QDateEdit,
QDoubleSpinBox,
QTextEdit,
QListWidget,
QFontComboBox,
QSpinBox {{
    border: 1px solid __BORDER_COLOR__;
    border-radius: 8px;
    background: __INPUT_BACKGROUND__;
    padding: 6px 8px;
}}

QComboBox,
QDateEdit,
QDoubleSpinBox,
QFontComboBox,
QSpinBox {{
    min-height: 34px;
}}

QTabWidget::pane {{
    border: none;
}}

QScrollArea {{
    border: none;
    background: transparent;
}}

QFrame#sidebar {{
    background: __SIDEBAR_BACKGROUND__;
}}

QLabel#brand {{
    background: transparent;
    color: __BRAND_TEXT__;
    font-size: 15px;
    font-weight: 700;
}}

QLabel#sidebarSubtitle {{
    background: transparent;
    color: __SIDEBAR_SUBTITLE_TEXT__;
    font-size: 12px;
}}

QPushButton#navButton,
QPushButton#navButtonActive {{
    min-height: 36px;
    border: none;
    border-radius: 8px;
    color: __SIDEBAR_TEXT__;
    text-align: left;
    padding-left: 12px;
    background: transparent;
}}

QPushButton#navButton:hover,
QPushButton#navButtonActive {{
    background: __SIDEBAR_HOVER_BACKGROUND__;
    color: __SIDEBAR_ACTIVE_TEXT__;
}}

QFrame#topbar,
QFrame#panel,
QFrame#metric {{
    background: __PANEL_BACKGROUND__;
    border: 1px solid __BORDER_COLOR__;
}}

QFrame#topbar {{
    border-left: none;
    border-right: none;
    border-top: none;
}}

QFrame#panel,
QFrame#metric {{
    border-radius: 8px;
}}

QFrame#viajeFieldGroup {{
    background: #f6f9fb;
    border: 1px solid __BORDER_COLOR__;
    border-radius: 8px;
}}

QLabel#viajeFieldGroupTitle {{
    background: transparent;
    color: __SECTION_TITLE_TEXT__;
    font-size: 13px;
    font-weight: 700;
}}

QFrame#panelHeader {{
    min-height: 56px;
    background: __PANEL_HEADER_BACKGROUND__;
    border-bottom: 1px solid __BORDER_COLOR__;
}}

QLabel#pageTitle {{
    background: transparent;
    color: __PAGE_TITLE_TEXT__;
    font-size: 20px;
    font-weight: 700;
}}

QLabel#sectionTitle {{
    background: transparent;
    color: __SECTION_TITLE_TEXT__;
    font-size: 16px;
    font-weight: 700;
}}

QLabel#muted {{
    background: transparent;
    color: __MUTED_TEXT__;
    font-size: 12px;
}}

QLabel#metricValue {{
    background: transparent;
    color: __METRIC_VALUE_TEXT__;
    font-size: 24px;
    font-weight: 700;
}}

QCheckBox {{
    background: transparent;
    spacing: 8px;
}}

QCheckBox::indicator {{
    width: 18px;
    height: 18px;
    border: 2px solid #52616b;
    border-radius: 4px;
    background: #ffffff;
}}

QCheckBox::indicator:hover {{
    border-color: __ACCENT_COLOR__;
}}

QCheckBox::indicator:checked {{
    border-color: __ACCENT_COLOR__;
    background: __ACCENT_COLOR__;
}}

QCheckBox::indicator:checked:hover {{
    border-color: __ACCENT_COLOR__;
    background: __ACCENT_COLOR__;
}}

QCheckBox::indicator:disabled {{
    border-color: #aeb8bf;
    background: #edf1f4;
}}

QPushButton#primaryButton {{
    border-color: __ACCENT_COLOR__;
    background: __ACCENT_COLOR__;
    color: __PRIMARY_BUTTON_TEXT__;
}}

QPushButton#dangerButton {{
    border-color: __DANGER_COLOR__;
    color: __DANGER_COLOR__;
}}

QWidget#actionButtons {{
    background: transparent;
}}

QTableWidget {{
    background: __PANEL_BACKGROUND__;
    alternate-background-color: __TABLE_ALT_BACKGROUND__;
    border: none;
    gridline-color: __BORDER_COLOR__;
}}

QHeaderView::section {{
    background: __TABLE_HEADER_BACKGROUND__;
    color: __TABLE_HEADER_TEXT__;
    border: none;
    border-bottom: 1px solid __BORDER_COLOR__;
    padding: 10px;
    font-size: 12px;
    font-weight: 700;
}}
"""


def default_theme(font_family: str | None = None) -> dict[str, str | int]:
    theme = DEFAULT_THEME.copy()
    if font_family:
        theme["font_family"] = font_family
    return theme


def load_theme_settings(
    theme_path: Path,
    *,
    fallback_font_family: str | None = None,
) -> dict[str, str | int]:
    theme = default_theme(fallback_font_family)
    if not theme_path.exists():
        return theme

    try:
        data = json.loads(theme_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return theme

    for key, value in data.items():
        if key not in theme:
            continue
        if key == "base_font_size":
            theme[key] = int(value)
        else:
            theme[key] = str(value)

    if fallback_font_family:
        saved_font = str(theme["font_family"]).strip()
        if saved_font.lower().startswith("segoe ui") and saved_font != fallback_font_family:
            theme["font_family"] = fallback_font_family
    return theme


def save_theme_settings(theme_path: Path, theme: dict[str, str | int]) -> None:
    theme_path.parent.mkdir(parents=True, exist_ok=True)
    theme_path.write_text(
        json.dumps(theme, indent=2, ensure_ascii=True),
        encoding="utf-8",
    )


def build_app_styles(theme: dict[str, str | int]) -> str:
    replacements = {
        "__APP_BACKGROUND__": str(theme["app_background"]),
        "__TEXT_COLOR__": str(theme["text_color"]),
        "__MENU_BACKGROUND__": str(theme["menu_background"]),
        "__PANEL_BACKGROUND__": str(theme["panel_background"]),
        "__PANEL_HEADER_BACKGROUND__": str(theme["panel_header_background"]),
        "__INPUT_BACKGROUND__": str(theme["input_background"]),
        "__BORDER_COLOR__": str(theme["border_color"]),
        "__MUTED_TEXT__": str(theme["muted_text"]),
        "__SIDEBAR_BACKGROUND__": str(theme["sidebar_background"]),
        "__BRAND_TEXT__": str(theme["brand_text"]),
        "__SIDEBAR_SUBTITLE_TEXT__": str(theme["sidebar_subtitle_text"]),
        "__SIDEBAR_TEXT__": str(theme["nav_text"]),
        "__SIDEBAR_ACTIVE_TEXT__": str(theme["nav_active_text"]),
        "__SIDEBAR_HOVER_BACKGROUND__": str(theme["nav_active_background"]),
        "__PAGE_TITLE_TEXT__": str(theme["page_title_text"]),
        "__SECTION_TITLE_TEXT__": str(theme["section_title_text"]),
        "__METRIC_VALUE_TEXT__": str(theme["metric_value_text"]),
        "__ACCENT_COLOR__": str(theme["accent_color"]),
        "__PRIMARY_BUTTON_TEXT__": str(theme["primary_button_text"]),
        "__DANGER_COLOR__": str(theme["danger_color"]),
        "__TABLE_ALT_BACKGROUND__": str(theme["table_alt_background"]),
        "__TABLE_HEADER_BACKGROUND__": str(theme["table_header_background"]),
        "__TABLE_HEADER_TEXT__": str(theme["table_header_text"]),
        "__FONT_FAMILY__": str(theme["font_family"]),
        "__BASE_FONT_SIZE__": str(theme["base_font_size"]),
    }

    stylesheet = STYLE_TEMPLATE
    for placeholder, value in replacements.items():
        stylesheet = stylesheet.replace(placeholder, value)
    return stylesheet


def build_app_palette(theme: dict[str, str | int]) -> QPalette:
    palette = QPalette()
    window = QColor(str(theme["app_background"]))
    base = QColor(str(theme["input_background"]))
    alternate = QColor(str(theme["table_alt_background"]))
    text = QColor(str(theme["text_color"]))
    button = QColor(str(theme["panel_background"]))
    border = QColor(str(theme["border_color"]))
    accent = QColor(str(theme["accent_color"]))
    button_text = QColor(str(theme["primary_button_text"]))

    palette.setColor(QPalette.ColorRole.Window, window)
    palette.setColor(QPalette.ColorRole.WindowText, text)
    palette.setColor(QPalette.ColorRole.Base, base)
    palette.setColor(QPalette.ColorRole.AlternateBase, alternate)
    palette.setColor(QPalette.ColorRole.ToolTipBase, base)
    palette.setColor(QPalette.ColorRole.ToolTipText, text)
    palette.setColor(QPalette.ColorRole.Text, text)
    palette.setColor(QPalette.ColorRole.Button, button)
    palette.setColor(QPalette.ColorRole.ButtonText, text)
    palette.setColor(QPalette.ColorRole.BrightText, button_text)
    palette.setColor(QPalette.ColorRole.Highlight, accent)
    palette.setColor(QPalette.ColorRole.HighlightedText, button_text)
    palette.setColor(QPalette.ColorRole.Light, border)
    return palette
