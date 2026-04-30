from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Gestion de camiones")
        self.resize(1180, 760)
        self.setMinimumSize(980, 620)

        self._build_menu()
        self.setCentralWidget(self._build_shell())
        self.setStyleSheet(APP_STYLES)

    def _build_menu(self) -> None:
        file_menu = self.menuBar().addMenu("Archivo")
        exit_action = QAction("Salir", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        view_menu = self.menuBar().addMenu("Vista")
        view_menu.addAction(QAction("Tablero", self))
        view_menu.addAction(QAction("Camiones", self))
        view_menu.addAction(QAction("Turnos", self))

    def _build_shell(self) -> QWidget:
        shell = QWidget()
        layout = QHBoxLayout(shell)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        layout.addWidget(self._build_sidebar())
        layout.addWidget(self._build_main_area(), stretch=1)
        return shell

    def _build_sidebar(self) -> QWidget:
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(236)

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(18, 22, 18, 18)
        layout.setSpacing(8)

        brand = QLabel("Gestion Camiones")
        brand.setObjectName("brand")
        subtitle = QLabel("Laboratorio y produccion")
        subtitle.setObjectName("sidebarSubtitle")

        layout.addWidget(brand)
        layout.addWidget(subtitle)
        layout.addSpacing(24)

        for index, item in enumerate(
            ["Tablero", "Camiones", "Turnos", "Documentacion", "Reportes", "Configuracion"]
        ):
            button = QPushButton(item)
            button.setObjectName("navButtonActive" if index == 0 else "navButton")
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            layout.addWidget(button)

        layout.addStretch()
        return sidebar

    def _build_main_area(self) -> QWidget:
        main = QWidget()
        main.setObjectName("main")
        layout = QVBoxLayout(main)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        layout.addWidget(self._build_topbar())
        content = QWidget()
        content.setObjectName("content")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(24, 24, 24, 24)
        content_layout.setSpacing(20)

        content_layout.addLayout(self._build_metrics())
        content_layout.addWidget(self._build_table_panel(), stretch=1)

        layout.addWidget(content, stretch=1)
        return main

    def _build_topbar(self) -> QWidget:
        topbar = QFrame()
        topbar.setObjectName("topbar")
        topbar.setFixedHeight(76)

        layout = QHBoxLayout(topbar)
        layout.setContentsMargins(24, 0, 24, 0)
        layout.setSpacing(14)

        title_block = QVBoxLayout()
        title_block.setSpacing(2)
        title = QLabel("Tablero operativo")
        title.setObjectName("pageTitle")
        subtitle = QLabel("Resumen diario de camiones, estados y demoras.")
        subtitle.setObjectName("muted")
        title_block.addWidget(title)
        title_block.addWidget(subtitle)

        search = QLineEdit()
        search.setPlaceholderText("Buscar patente o proveedor")
        search.setFixedWidth(260)

        new_button = QPushButton("Nuevo camion")
        new_button.setObjectName("primaryButton")
        new_button.setCursor(Qt.CursorShape.PointingHandCursor)

        layout.addLayout(title_block)
        layout.addStretch()
        layout.addWidget(search)
        layout.addWidget(new_button)
        return topbar

    def _build_metrics(self) -> QGridLayout:
        grid = QGridLayout()
        grid.setSpacing(14)
        metrics = [
            ("Programados hoy", "18"),
            ("En planta", "7"),
            ("Observados", "2"),
            ("Finalizados", "9"),
        ]

        for column, (label, value) in enumerate(metrics):
            grid.addWidget(MetricCard(label, value), 0, column)

        return grid

    def _build_table_panel(self) -> QWidget:
        panel = QFrame()
        panel.setObjectName("panel")
        panel.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        header = QFrame()
        header.setObjectName("panelHeader")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(16, 0, 16, 0)
        header_title = QLabel("Camiones activos")
        header_title.setObjectName("sectionTitle")
        export_button = QPushButton("Exportar")
        header_layout.addWidget(header_title)
        header_layout.addStretch()
        header_layout.addWidget(export_button)

        table = QTableWidget(4, 7)
        table.setHorizontalHeaderLabels(
            ["Patente", "Proveedor", "Operacion", "Estado", "Ingreso", "Responsable", "Accion"]
        )
        rows = [
            ["AB123CD", "Romero e hijos", "Descarga", "En laboratorio", "08:25", "Laboratorio", "Ver"],
            ["AE456FG", "Proveedor Norte", "Carga", "En espera", "09:10", "Porteria", "Ver"],
            ["AD789HI", "Cliente Sur", "Retiro", "Observado", "09:45", "Calidad", "Ver"],
            ["AC321JK", "Transporte Oeste", "Descarga", "Autorizado", "10:05", "Produccion", "Ver"],
        ]
        for row_index, row in enumerate(rows):
            for column_index, value in enumerate(row):
                item = QTableWidgetItem(value)
                item.setFlags(item.flags() ^ Qt.ItemFlag.ItemIsEditable)
                table.setItem(row_index, column_index, item)

        table.verticalHeader().setVisible(False)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.setAlternatingRowColors(True)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)

        layout.addWidget(header)
        layout.addWidget(table, stretch=1)
        return panel


class MetricCard(QFrame):
    def __init__(self, label: str, value: str) -> None:
        super().__init__()
        self.setObjectName("metric")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(8)

        label_widget = QLabel(label)
        label_widget.setObjectName("muted")
        value_widget = QLabel(value)
        value_widget.setObjectName("metricValue")

        layout.addWidget(label_widget)
        layout.addWidget(value_widget)


APP_STYLES = """
QWidget {
    background: #f5f7f8;
    color: #182026;
    font-family: "Segoe UI", "San Francisco", Arial, sans-serif;
    font-size: 14px;
}

QMenuBar {
    background: #ffffff;
    border-bottom: 1px solid #d9e0e5;
}

QPushButton {
    min-height: 34px;
    border: 1px solid #d9e0e5;
    border-radius: 8px;
    background: #ffffff;
    padding: 0 12px;
}

QPushButton:hover {
    border-color: #1f6f8b;
}

QLineEdit {
    min-height: 34px;
    border: 1px solid #d9e0e5;
    border-radius: 8px;
    background: #ffffff;
    padding: 0 12px;
}

QFrame#sidebar {
    background: #24333a;
}

QLabel#brand {
    background: transparent;
    color: #ffffff;
    font-size: 15px;
    font-weight: 700;
}

QLabel#sidebarSubtitle {
    background: transparent;
    color: rgba(255, 255, 255, 0.68);
    font-size: 12px;
}

QPushButton#navButton,
QPushButton#navButtonActive {
    min-height: 36px;
    border: none;
    border-radius: 8px;
    color: rgba(255, 255, 255, 0.84);
    text-align: left;
    padding-left: 12px;
    background: transparent;
}

QPushButton#navButton:hover,
QPushButton#navButtonActive {
    background: rgba(255, 255, 255, 0.12);
    color: #ffffff;
}

QFrame#topbar,
QFrame#panel,
QFrame#metric {
    background: #ffffff;
    border: 1px solid #d9e0e5;
}

QFrame#topbar {
    border-left: none;
    border-right: none;
    border-top: none;
}

QFrame#panel,
QFrame#metric {
    border-radius: 8px;
}

QFrame#panelHeader {
    min-height: 56px;
    background: #ffffff;
    border-bottom: 1px solid #d9e0e5;
}

QLabel#pageTitle {
    background: transparent;
    font-size: 20px;
    font-weight: 700;
}

QLabel#sectionTitle {
    background: transparent;
    font-size: 16px;
    font-weight: 700;
}

QLabel#muted {
    background: transparent;
    color: #63707a;
    font-size: 12px;
}

QLabel#metricValue {
    background: transparent;
    font-size: 24px;
    font-weight: 700;
}

QPushButton#primaryButton {
    border-color: #1f6f8b;
    background: #1f6f8b;
    color: #ffffff;
}

QTableWidget {
    background: #ffffff;
    alternate-background-color: #f8fafb;
    border: none;
    gridline-color: #d9e0e5;
}

QHeaderView::section {
    background: #eef3f5;
    color: #63707a;
    border: none;
    border-bottom: 1px solid #d9e0e5;
    padding: 10px;
    font-size: 12px;
    font-weight: 700;
}
"""
