from __future__ import annotations

from pathlib import Path

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

from gestion_camiones.data.models import ViajeResumen
from gestion_camiones.data.repositories import ViajeRepository


class MainWindow(QMainWindow):
    def __init__(self, viaje_repository: ViajeRepository, database_path: Path) -> None:
        super().__init__()
        self.viaje_repository = viaje_repository
        self.database_path = database_path
        self.metric_cards: dict[str, MetricCard] = {}
        self.search_input: QLineEdit | None = None
        self.table: QTableWidget | None = None

        self.setWindowTitle("Gestion de viajes")
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
        view_menu.addAction(QAction("Viajes", self))
        view_menu.addAction(QAction("Maestros", self))

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

        brand = QLabel("Gestion Viajes")
        brand.setObjectName("brand")
        subtitle = QLabel("Transporte")
        subtitle.setObjectName("sidebarSubtitle")

        layout.addWidget(brand)
        layout.addWidget(subtitle)
        layout.addSpacing(24)

        for index, item in enumerate(
            ["Tablero", "Viajes", "Clientes", "Choferes", "Vehiculos", "Reportes"]
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
        subtitle = QLabel("Resumen de viajes e importes cobrados al cliente.")
        subtitle.setObjectName("muted")
        title_block.addWidget(title)
        title_block.addWidget(subtitle)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar cliente, chofer, vehiculo o lugar")
        self.search_input.setFixedWidth(300)
        self.search_input.textChanged.connect(self._refresh_table)

        new_button = QPushButton("Nuevo viaje")
        new_button.setObjectName("primaryButton")
        new_button.setCursor(Qt.CursorShape.PointingHandCursor)

        layout.addLayout(title_block)
        layout.addStretch()
        layout.addWidget(self.search_input)
        layout.addWidget(new_button)
        return topbar

    def _build_metrics(self) -> QGridLayout:
        grid = QGridLayout()
        grid.setSpacing(14)
        metrics = self.viaje_repository.dashboard_metrics()

        for column, (label, value) in enumerate(metrics.items()):
            display_value = str(value) if label == "Viajes cargados" else _format_money(value)
            card = MetricCard(label, display_value)
            self.metric_cards[label] = card
            grid.addWidget(card, 0, column)

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
        header_title = QLabel("Viajes")
        header_title.setObjectName("sectionTitle")
        export_button = QPushButton("Exportar")
        header_layout.addWidget(header_title)
        header_layout.addStretch()
        header_layout.addWidget(export_button)

        self.table = QTableWidget(0, 16)
        self.table.setHorizontalHeaderLabels(
            [
                "Cliente",
                "Carga",
                "Lugar carga",
                "L.Descarga",
                "Observaciones",
                "Chofer",
                "T.Carga",
                "Camion",
                "Semi",
                "Tarifa $",
                "F.Desc prog.",
                "Demora $",
                "F.Desc real",
                "Vacio $",
                "Peajes",
                "Estado",
            ]
        )
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._refresh_table()

        layout.addWidget(header)
        layout.addWidget(self.table, stretch=1)
        return panel

    def _refresh_table(self) -> None:
        if self.table is None:
            return

        search = self.search_input.text() if self.search_input is not None else ""
        rows = self.viaje_repository.list_resumen(search)
        self.table.setRowCount(len(rows))

        for row_index, viaje in enumerate(rows):
            for column_index, value in enumerate(self._viaje_to_row(viaje)):
                item = QTableWidgetItem(value)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.table.setItem(row_index, column_index, item)

        self.table.resizeColumnsToContents()

    def _viaje_to_row(self, viaje: ViajeResumen) -> list[str]:
        return [
            viaje.cliente,
            viaje.carga,
            viaje.lugar_carga,
            viaje.lugar_descarga,
            viaje.observaciones,
            viaje.chofer,
            viaje.tipo_carga,
            viaje.camion,
            viaje.semi,
            _format_money(viaje.tarifa),
            viaje.fecha_descarga_programada,
            _format_money(viaje.demora),
            viaje.fecha_descarga_real,
            _format_money(viaje.vacio),
            _format_money(viaje.peajes),
            viaje.estado,
        ]


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


def _format_money(value: float) -> str:
    return f"$ {value:,.0f}".replace(",", ".")


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
