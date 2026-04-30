from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QDate, Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QDoubleSpinBox,
    QFormLayout,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from gestion_camiones.data.models import ViajeCreate, ViajeResumen
from gestion_camiones.data.repositories import (
    CargaRepository,
    ChoferRepository,
    ClienteRepository,
    LugarRepository,
    PeajeRepository,
    VehiculoRepository,
    ViajeRepository,
)


TAB_LABELS = [
    "Cargar viaje",
    "Historial viajes",
    "Clientes",
    "Lugares",
    "Chofer",
    "T.Carga",
    "Vehiculos",
    "Peajes",
    "Estadisticas",
    "Opciones",
]

TAB_HEADERS = {
    "Cargar viaje": (
        "Cargar viaje",
        "Alta de viaje con cliente, carga, lugares, chofer, vehiculos e importes.",
    ),
    "Historial viajes": (
        "Historial viajes",
        "Listado operativo de viajes cargados y busqueda rapida.",
    ),
    "Clientes": (
        "Clientes",
        "Datos fiscales y de contacto de clientes.",
    ),
    "Lugares": (
        "Lugares",
        "Puntos de carga y descarga con roles variables.",
    ),
    "Chofer": (
        "Chofer",
        "Datos de choferes y vencimiento de registro.",
    ),
    "T.Carga": (
        "T.Carga",
        "Tipos de carga disponibles para cada viaje.",
    ),
    "Vehiculos": (
        "Vehiculos",
        "Camiones y semis registrados.",
    ),
    "Peajes": (
        "Peajes",
        "Peajes disponibles y costos asociados.",
    ),
    "Estadisticas": (
        "Estadisticas",
        "Resumen de viajes e importes cobrados al cliente.",
    ),
    "Opciones": (
        "Opciones",
        "Configuracion general de la aplicacion.",
    ),
}


class MainWindow(QMainWindow):
    def __init__(self, viaje_repository: ViajeRepository, database_path: Path) -> None:
        super().__init__()
        self.viaje_repository = viaje_repository
        self.database_path = database_path
        self.cliente_repository = ClienteRepository(database_path)
        self.carga_repository = CargaRepository(database_path)
        self.lugar_repository = LugarRepository(database_path)
        self.chofer_repository = ChoferRepository(database_path)
        self.vehiculo_repository = VehiculoRepository(database_path)
        self.peaje_repository = PeajeRepository(database_path)
        self.metric_cards: dict[str, MetricCard] = {}
        self.search_input: QLineEdit | None = None
        self.table: QTableWidget | None = None
        self.tabs: QTabWidget | None = None
        self.nav_buttons: dict[str, QPushButton] = {}
        self.page_title_label: QLabel | None = None
        self.page_subtitle_label: QLabel | None = None
        self.new_button: QPushButton | None = None
        self.form_widgets: dict[str, QWidget] = {}

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
        for label in TAB_LABELS:
            action = QAction(label, self)
            action.triggered.connect(
                lambda checked=False, tab_label=label: self._go_to_tab_by_label(
                    tab_label
                )
            )
            view_menu.addAction(action)

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

        for index, item in enumerate(TAB_LABELS):
            button = QPushButton(item)
            button.setObjectName("navButtonActive" if index == 0 else "navButton")
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            self.nav_buttons[item] = button
            button.clicked.connect(
                lambda checked=False, tab_label=item: self._go_to_tab_by_label(
                    tab_label
                )
            )
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

        self.tabs = QTabWidget()
        self.tabs.setUsesScrollButtons(True)
        self.tabs.setElideMode(Qt.TextElideMode.ElideRight)
        self.tabs.addTab(self._build_viaje_form_tab(), TAB_LABELS[0])
        self.tabs.addTab(self._build_history_tab(), TAB_LABELS[1])
        self.tabs.addTab(self._build_clients_tab(), TAB_LABELS[2])
        self.tabs.addTab(self._build_lugares_tab(), TAB_LABELS[3])
        self.tabs.addTab(self._build_choferes_tab(), TAB_LABELS[4])
        self.tabs.addTab(self._build_tipo_carga_tab(), TAB_LABELS[5])
        self.tabs.addTab(self._build_vehiculos_tab(), TAB_LABELS[6])
        self.tabs.addTab(self._build_peajes_tab(), TAB_LABELS[7])
        self.tabs.addTab(self._build_statistics_tab(), TAB_LABELS[8])
        self.tabs.addTab(self._build_options_tab(), TAB_LABELS[9])
        self.tabs.currentChanged.connect(self._sync_tab_header)
        content_layout.addWidget(self.tabs, stretch=1)
        self._sync_tab_header(0)

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
        title = QLabel("Cargar viaje")
        title.setObjectName("pageTitle")
        subtitle = QLabel(
            "Alta de viaje con cliente, carga, lugares, chofer, vehiculos e importes."
        )
        subtitle.setObjectName("muted")
        self.page_title_label = title
        self.page_subtitle_label = subtitle
        title_block.addWidget(title)
        title_block.addWidget(subtitle)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar cliente, chofer, vehiculo, lugar o peaje")
        self.search_input.setFixedWidth(300)
        self.search_input.textChanged.connect(self._refresh_table)

        new_button = QPushButton("Nuevo viaje")
        new_button.setObjectName("primaryButton")
        new_button.setCursor(Qt.CursorShape.PointingHandCursor)
        new_button.clicked.connect(self._go_to_create_tab)
        self.new_button = new_button

        layout.addLayout(title_block)
        layout.addStretch()
        layout.addWidget(self.search_input)
        layout.addWidget(new_button)
        return topbar

    def _build_viaje_form_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        panel = QFrame()
        panel.setObjectName("panel")
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(18, 18, 18, 18)
        panel_layout.setSpacing(14)

        title = QLabel("Cargar viaje")
        title.setObjectName("sectionTitle")
        panel_layout.addWidget(title)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        form.setFormAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        form.setHorizontalSpacing(16)
        form.setVerticalSpacing(10)

        fecha = QDateEdit()
        fecha.setCalendarPopup(True)
        fecha.setDisplayFormat("yyyy-MM-dd")
        fecha.setDate(QDate.currentDate())

        cliente = self._build_combo(
            [(item.nombre, item.id) for item in self.cliente_repository.list_all()]
        )
        carga = self._build_combo(
            [
                (item.codigo_contenedor, item.id)
                for item in self.carga_repository.list_all()
            ]
        )
        lugar_carga = self._build_lugar_combo("CARGA")
        lugar_descarga = self._build_lugar_combo("DESCARGA")

        observaciones = QTextEdit()
        observaciones.setFixedHeight(72)

        chofer = self._build_combo(
            [(f"{item.nombre_completo} - DNI {item.dni}", item.id)
             for item in self.chofer_repository.list_all()]
        )
        tipo_carga = self._build_combo(
            [("General", "GENERAL"), ("Carga peligrosa", "PELIGROSA")]
        )
        camion = self._build_combo(
            [(item.etiqueta, item.id)
             for item in self.vehiculo_repository.list_all("CAMION")]
        )
        semi = self._build_combo(
            [("Sin semi", None)]
            + [(item.etiqueta, item.id)
               for item in self.vehiculo_repository.list_all("SEMI")]
        )

        tarifa = self._money_input()
        fecha_descarga_tarifa = QDateEdit()
        fecha_descarga_tarifa.setCalendarPopup(True)
        fecha_descarga_tarifa.setDisplayFormat("yyyy-MM-dd")
        fecha_descarga_tarifa.setDate(QDate.currentDate())

        demora = self._money_input()
        fecha_descarga_demora = QDateEdit()
        fecha_descarga_demora.setCalendarPopup(True)
        fecha_descarga_demora.setDisplayFormat("yyyy-MM-dd")
        fecha_descarga_demora.setDate(QDate.currentDate())

        vacio = self._money_input()
        peajes = QListWidget()
        peajes.setFixedHeight(92)
        for item in self.peaje_repository.list_all():
            peaje_item = QListWidgetItem(
                f"{item.nombre} - {_format_money(item.costo)}"
            )
            peaje_item.setFlags(
                peaje_item.flags() | Qt.ItemFlag.ItemIsUserCheckable
            )
            peaje_item.setCheckState(Qt.CheckState.Unchecked)
            peaje_item.setData(Qt.ItemDataRole.UserRole, item.id)
            peajes.addItem(peaje_item)

        self.form_widgets = {
            "fecha": fecha,
            "cliente": cliente,
            "carga": carga,
            "lugar_carga": lugar_carga,
            "lugar_descarga": lugar_descarga,
            "observaciones": observaciones,
            "chofer": chofer,
            "tipo_carga": tipo_carga,
            "camion": camion,
            "semi": semi,
            "tarifa": tarifa,
            "fecha_descarga_tarifa": fecha_descarga_tarifa,
            "demora": demora,
            "fecha_descarga_demora": fecha_descarga_demora,
            "vacio": vacio,
            "peajes": peajes,
        }

        form.addRow("Fecha", fecha)
        form.addRow("Cliente", cliente)
        form.addRow("Carga", carga)
        form.addRow("Lugar carga", lugar_carga)
        form.addRow("L.Descarga", lugar_descarga)
        form.addRow("Observaciones", observaciones)
        form.addRow("Chofer", chofer)
        form.addRow("T.Carga", tipo_carga)
        form.addRow("Camion", camion)
        form.addRow("Semi", semi)
        form.addRow("Tarifa", tarifa)
        form.addRow("F.Desc tarifa", fecha_descarga_tarifa)
        form.addRow("Demora", demora)
        form.addRow("F.Desc demora", fecha_descarga_demora)
        form.addRow("Vacio", vacio)
        form.addRow("Peajes", peajes)
        panel_layout.addLayout(form)

        actions = QHBoxLayout()
        actions.addStretch()
        save_button = QPushButton("Guardar viaje")
        save_button.setObjectName("primaryButton")
        save_button.clicked.connect(self._save_viaje)
        actions.addWidget(save_button)
        panel_layout.addLayout(actions)

        scroll = QScrollArea()
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setWidgetResizable(True)
        scroll.setWidget(panel)

        layout.addWidget(scroll, stretch=1)
        return tab

    def _build_history_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(20)

        layout.addWidget(self._build_table_panel(), stretch=1)
        return tab

    def _build_clients_tab(self) -> QWidget:
        rows = [
            [
                item.nombre,
                item.domicilio_fiscal,
                item.email,
                item.numero_contacto,
            ]
            for item in self.cliente_repository.list_all()
        ]
        return self._build_static_table_tab(
            "Clientes",
            ["Nombre", "Domicilio fiscal", "Email", "Contacto"],
            rows,
        )

    def _build_lugares_tab(self) -> QWidget:
        roles_by_lugar: dict[int, list[str]] = {}
        for role in self.lugar_repository.list_roles():
            roles_by_lugar.setdefault(role.lugar_id, []).append(role.rol.title())

        rows = [
            [
                item.nombre,
                item.direccion,
                ", ".join(roles_by_lugar.get(item.id, [])),
                item.observaciones,
            ]
            for item in self.lugar_repository.list_all()
        ]
        return self._build_static_table_tab(
            "Lugares",
            ["Nombre", "Direccion", "Roles", "Observaciones"],
            rows,
        )

    def _build_choferes_tab(self) -> QWidget:
        rows = [
            [
                item.dni,
                item.nombre,
                item.apellido,
                item.numero_telefono,
                item.fecha_vencimiento_registro,
            ]
            for item in self.chofer_repository.list_all()
        ]
        return self._build_static_table_tab(
            "Chofer",
            ["DNI", "Nombre", "Apellido", "Telefono", "Vencimiento registro"],
            rows,
        )

    def _build_tipo_carga_tab(self) -> QWidget:
        return self._build_static_table_tab(
            "T.Carga",
            ["Nombre", "Codigo interno"],
            [["General", "GENERAL"], ["Carga peligrosa", "PELIGROSA"]],
        )

    def _build_vehiculos_tab(self) -> QWidget:
        rows = [
            [
                item.tipo.title(),
                item.nombre_identificatorio,
                item.patente,
                item.observaciones,
            ]
            for item in self.vehiculo_repository.list_all()
        ]
        return self._build_static_table_tab(
            "Vehiculos",
            ["Tipo", "Nombre identificatorio", "Patente", "Observaciones"],
            rows,
        )

    def _build_peajes_tab(self) -> QWidget:
        rows = [
            [item.nombre, item.direccion, _format_money(item.costo)]
            for item in self.peaje_repository.list_all()
        ]
        return self._build_static_table_tab(
            "Peajes",
            ["Nombre", "Direccion", "Costo"],
            rows,
        )

    def _build_statistics_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(20)

        layout.addLayout(self._build_metrics())
        layout.addStretch()
        return tab

    def _build_options_tab(self) -> QWidget:
        return self._build_static_table_tab(
            "Opciones",
            ["Opcion", "Valor"],
            [
                ["Base de datos", str(self.database_path)],
                ["Actualizaciones", "GitHub Releases"],
                ["Modo", "Cliente sin servidor"],
            ],
        )

    def _build_static_table_tab(
        self,
        title: str,
        headers: list[str],
        rows: list[list[str]],
    ) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(20)

        layout.addWidget(self._build_readonly_table_panel(title, headers, rows), stretch=1)
        return tab

    def _build_readonly_table_panel(
        self,
        title: str,
        headers: list[str],
        rows: list[list[str]],
    ) -> QWidget:
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
        header_title = QLabel(title)
        header_title.setObjectName("sectionTitle")
        header_layout.addWidget(header_title)
        header_layout.addStretch()

        table = QTableWidget(len(rows), len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.verticalHeader().setVisible(False)
        table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.ResizeToContents
        )
        table.setAlternatingRowColors(True)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)

        for row_index, row in enumerate(rows):
            for column_index, value in enumerate(row):
                item = QTableWidgetItem(value)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                table.setItem(row_index, column_index, item)

        layout.addWidget(header)
        layout.addWidget(table, stretch=1)
        return panel

    def _build_metrics(self) -> QGridLayout:
        grid = QGridLayout()
        grid.setSpacing(14)
        metrics = self.viaje_repository.dashboard_metrics()

        for column, (label, value) in enumerate(metrics.items()):
            display_value = (
                str(value)
                if label == "Viajes cargados"
                else _format_money(value)
            )
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

        self.table = QTableWidget(0, 17)
        self.table.setHorizontalHeaderLabels(
            [
                "Fecha",
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
                "F.Desc tarifa",
                "Demora $",
                "F.Desc demora",
                "Vacio $",
                "Peajes $",
                "Estado",
            ]
        )
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.ResizeToContents
        )
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
            viaje.fecha,
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
            viaje.fecha_descarga_tarifa,
            _format_money(viaje.demora),
            viaje.fecha_descarga_demora,
            _format_money(viaje.vacio),
            _format_money(viaje.peajes),
            viaje.estado,
        ]

    def _save_viaje(self) -> None:
        try:
            viaje = self._collect_viaje_form()
            self.viaje_repository.create(viaje)
        except ValueError as exc:
            QMessageBox.warning(self, "Datos incompletos", str(exc))
            return
        except Exception as exc:
            QMessageBox.critical(self, "Error", f"No se pudo guardar el viaje.\n{exc}")
            return

        QMessageBox.information(self, "Viaje guardado", "El viaje se cargo correctamente.")
        self._refresh_table()
        self._refresh_metrics()
        self._clear_viaje_form()
        self._go_to_history_tab()

    def _collect_viaje_form(self) -> ViajeCreate:
        fecha = self._date_value("fecha")
        fecha_descarga_tarifa = self._date_value("fecha_descarga_tarifa")
        fecha_descarga_demora = self._date_value("fecha_descarga_demora")

        return ViajeCreate(
            fecha=fecha,
            cliente_id=self._required_combo_int("cliente"),
            carga_id=self._required_combo_int("carga"),
            lugar_carga_id=self._required_combo_int("lugar_carga"),
            lugar_descarga_id=self._required_combo_int("lugar_descarga"),
            observaciones=self._text_value("observaciones"),
            chofer_id=self._required_combo_int("chofer"),
            tipo_carga=str(self._combo_value("tipo_carga") or "GENERAL"),
            camion_id=self._required_combo_int("camion"),
            semi_id=self._optional_combo_int("semi"),
            tarifa=self._money_value("tarifa"),
            fecha_descarga_tarifa=fecha_descarga_tarifa,
            demora=self._money_value("demora"),
            fecha_descarga_demora=fecha_descarga_demora,
            vacio=self._money_value("vacio"),
            peaje_ids=self._checked_peaje_ids(),
        )

    def _clear_viaje_form(self) -> None:
        for key in ("tarifa", "demora", "vacio"):
            widget = self.form_widgets[key]
            if isinstance(widget, QDoubleSpinBox):
                widget.setValue(0)

        observaciones = self.form_widgets["observaciones"]
        if isinstance(observaciones, QTextEdit):
            observaciones.clear()

        for key in ("fecha", "fecha_descarga_tarifa", "fecha_descarga_demora"):
            widget = self.form_widgets[key]
            if isinstance(widget, QDateEdit):
                widget.setDate(QDate.currentDate())

        peajes = self.form_widgets["peajes"]
        if isinstance(peajes, QListWidget):
            for row in range(peajes.count()):
                peajes.item(row).setCheckState(Qt.CheckState.Unchecked)

    def _refresh_metrics(self) -> None:
        metrics = self.viaje_repository.dashboard_metrics()
        for label, value in metrics.items():
            card = self.metric_cards.get(label)
            if card is None:
                continue
            display_value = (
                str(value)
                if label == "Viajes cargados"
                else _format_money(value)
            )
            card.set_value(display_value)

    def _go_to_create_tab(self) -> None:
        self._go_to_tab_by_label("Cargar viaje")

    def _go_to_history_tab(self) -> None:
        self._go_to_tab_by_label("Historial viajes")

    def _go_to_dashboard_tab(self) -> None:
        self._go_to_history_tab()

    def _go_to_tab_by_label(self, label: str) -> None:
        if self.tabs is None:
            return

        for index in range(self.tabs.count()):
            if self.tabs.tabText(index) == label:
                self.tabs.setCurrentIndex(index)
                return

    def _sync_tab_header(self, index: int) -> None:
        if self.tabs is None:
            return

        active_label = self.tabs.tabText(index)
        title, subtitle = TAB_HEADERS.get(active_label, (active_label, ""))
        if self.page_title_label is not None:
            self.page_title_label.setText(title)
        if self.page_subtitle_label is not None:
            self.page_subtitle_label.setText(subtitle)
        if self.search_input is not None:
            self.search_input.setVisible(active_label == "Historial viajes")
        if self.new_button is not None:
            self.new_button.setVisible(active_label != "Cargar viaje")

        for label, button in self.nav_buttons.items():
            object_name = "navButtonActive" if label == active_label else "navButton"
            button.setObjectName(object_name)
            button.style().unpolish(button)
            button.style().polish(button)

    def _build_combo(self, items: list[tuple[str, object]]) -> QComboBox:
        combo = QComboBox()
        for label, value in items:
            combo.addItem(label, value)
        return combo

    def _build_lugar_combo(self, rol: str) -> QComboBox:
        roles = self.lugar_repository.list_roles(rol)
        if roles:
            return self._build_combo([(item.lugar, item.lugar_id) for item in roles])
        return self._build_combo(
            [(item.nombre, item.id) for item in self.lugar_repository.list_all()]
        )

    def _money_input(self) -> QDoubleSpinBox:
        spin = QDoubleSpinBox()
        spin.setRange(0, 999_999_999)
        spin.setDecimals(2)
        spin.setSingleStep(1000)
        spin.setPrefix("$ ")
        return spin

    def _combo_value(self, key: str) -> object:
        widget = self.form_widgets[key]
        if not isinstance(widget, QComboBox):
            raise ValueError("Campo invalido.")
        return widget.currentData()

    def _required_combo_int(self, key: str) -> int:
        value = self._combo_value(key)
        if value is None:
            raise ValueError("Faltan datos obligatorios del viaje.")
        return int(value)

    def _optional_combo_int(self, key: str) -> int | None:
        value = self._combo_value(key)
        return None if value is None else int(value)

    def _date_value(self, key: str) -> str:
        widget = self.form_widgets[key]
        if not isinstance(widget, QDateEdit):
            raise ValueError("Campo de fecha invalido.")
        return widget.date().toString("yyyy-MM-dd")

    def _text_value(self, key: str) -> str:
        widget = self.form_widgets[key]
        if not isinstance(widget, QTextEdit):
            raise ValueError("Campo de texto invalido.")
        return widget.toPlainText().strip()

    def _money_value(self, key: str) -> float:
        widget = self.form_widgets[key]
        if not isinstance(widget, QDoubleSpinBox):
            raise ValueError("Campo de importe invalido.")
        return float(widget.value())

    def _checked_peaje_ids(self) -> tuple[int, ...]:
        widget = self.form_widgets["peajes"]
        if not isinstance(widget, QListWidget):
            raise ValueError("Campo de peajes invalido.")

        peaje_ids = []
        for row in range(widget.count()):
            item = widget.item(row)
            if item.checkState() == Qt.CheckState.Checked:
                peaje_ids.append(int(item.data(Qt.ItemDataRole.UserRole)))
        return tuple(peaje_ids)


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
        self.value_widget = value_widget

    def set_value(self, value: str) -> None:
        self.value_widget.setText(value)


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

QComboBox,
QDateEdit,
QDoubleSpinBox,
QTextEdit,
QListWidget {
    border: 1px solid #d9e0e5;
    border-radius: 8px;
    background: #ffffff;
    padding: 6px 8px;
}

QComboBox,
QDateEdit,
QDoubleSpinBox {
    min-height: 34px;
}

QTabWidget::pane {
    border: none;
}

QScrollArea {
    border: none;
    background: transparent;
}

QTabBar::tab {
    min-height: 34px;
    border: 1px solid #d9e0e5;
    border-bottom: none;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    background: #eef3f5;
    padding: 0 14px;
}

QTabBar::tab:selected {
    background: #ffffff;
    color: #1f6f8b;
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
