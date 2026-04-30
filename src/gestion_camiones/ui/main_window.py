from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from PySide6.QtCore import QDate, Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDateEdit,
    QDialog,
    QDialogButtonBox,
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
    TipoCargaRepository,
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
        self.tipo_carga_repository = TipoCargaRepository(database_path)
        self.metric_cards: dict[str, MetricCard] = {}
        self.search_input: QLineEdit | None = None
        self.table: QTableWidget | None = None
        self.object_tables: dict[str, QTableWidget] = {}
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
        self.tabs.tabBar().hide()
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
        new_button.clicked.connect(self._prepare_new_viaje)
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

        header = QHBoxLayout()
        title = QLabel("Cargar viaje")
        title.setObjectName("sectionTitle")
        header.addWidget(title)
        header.addStretch()
        panel_layout.addLayout(header)

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
        carga.setEditable(True)
        carga.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        if carga.lineEdit() is not None:
            carga.lineEdit().setPlaceholderText("Codigo provisto por el cliente")

        lugar_carga = self._build_lugar_combo("CARGA")
        lugar_descarga = self._build_lugar_combo("DESCARGA")

        observaciones = QTextEdit()
        observaciones.setFixedHeight(72)

        chofer = self._build_combo(
            [(f"{item.nombre_completo} - DNI {item.dni}", item.id)
             for item in self.chofer_repository.list_all()]
        )
        tipo_carga = self._build_tipo_carga_combo()
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
        fecha_descarga_vacio = QDateEdit()
        fecha_descarga_vacio.setCalendarPopup(True)
        fecha_descarga_vacio.setDisplayFormat("yyyy-MM-dd")
        fecha_descarga_vacio.setDate(QDate.currentDate())

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
            "fecha_descarga_vacio": fecha_descarga_vacio,
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
        form.addRow("F.Desc vacio", fecha_descarga_vacio)
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
        return self._build_static_table_tab(
            "Clientes",
            ["Nombre", "Domicilio fiscal", "Email", "Contacto"],
            self._cliente_rows(),
            create_callback=self._create_cliente,
            edit_callback=self._edit_cliente,
            delete_callback=self._delete_cliente,
        )

    def _build_lugares_tab(self) -> QWidget:
        return self._build_static_table_tab(
            "Lugares",
            ["Nombre", "Direccion", "Roles", "Observaciones"],
            self._lugar_rows(),
            create_callback=self._create_lugar,
            edit_callback=self._edit_lugar,
            delete_callback=self._delete_lugar,
        )

    def _build_choferes_tab(self) -> QWidget:
        return self._build_static_table_tab(
            "Chofer",
            ["DNI", "Nombre", "Apellido", "Telefono", "Vencimiento registro"],
            self._chofer_rows(),
            create_callback=self._create_chofer,
            edit_callback=self._edit_chofer,
            delete_callback=self._delete_chofer,
        )

    def _build_tipo_carga_tab(self) -> QWidget:
        return self._build_static_table_tab(
            "T.Carga",
            ["Nombre", "Codigo interno"],
            self._tipo_carga_rows(),
            create_callback=self._create_tipo_carga,
            edit_callback=self._edit_tipo_carga,
            delete_callback=self._delete_tipo_carga,
        )

    def _build_vehiculos_tab(self) -> QWidget:
        return self._build_static_table_tab(
            "Vehiculos",
            ["Tipo", "Nombre identificatorio", "Patente", "Observaciones"],
            self._vehiculo_rows(),
            create_callback=self._create_vehiculo,
            edit_callback=self._edit_vehiculo,
            delete_callback=self._delete_vehiculo,
        )

    def _build_peajes_tab(self) -> QWidget:
        return self._build_static_table_tab(
            "Peajes",
            ["Nombre", "Direccion", "Costo"],
            self._peaje_rows(),
            create_callback=self._create_peaje,
            edit_callback=self._edit_peaje,
            delete_callback=self._delete_peaje,
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
                (1, ["Base de datos", str(self.database_path)]),
                (2, ["Actualizaciones", "GitHub Releases"]),
                (3, ["Modo", "Cliente sin servidor"]),
            ],
            show_actions=False,
        )

    def _cliente_rows(self) -> list[tuple[int, list[str]]]:
        return [
            (
                item.id,
                [
                    item.nombre,
                    item.domicilio_fiscal,
                    item.email,
                    item.numero_contacto,
                ],
            )
            for item in self.cliente_repository.list_all()
        ]

    def _lugar_rows(self) -> list[tuple[int, list[str]]]:
        roles_by_lugar: dict[int, list[str]] = {}
        for role in self.lugar_repository.list_roles():
            roles_by_lugar.setdefault(role.lugar_id, []).append(role.rol.title())

        return [
            (
                item.id,
                [
                    item.nombre,
                    item.direccion,
                    ", ".join(roles_by_lugar.get(item.id, [])),
                    item.observaciones,
                ],
            )
            for item in self.lugar_repository.list_all()
        ]

    def _chofer_rows(self) -> list[tuple[int, list[str]]]:
        return [
            (
                item.id,
                [
                    item.dni,
                    item.nombre,
                    item.apellido,
                    item.numero_telefono,
                    item.fecha_vencimiento_registro,
                ],
            )
            for item in self.chofer_repository.list_all()
        ]

    def _tipo_carga_rows(self) -> list[tuple[int, list[str]]]:
        return [
            (item.id, [item.nombre, item.codigo])
            for item in self.tipo_carga_repository.list_all()
        ]

    def _vehiculo_rows(self) -> list[tuple[int, list[str]]]:
        return [
            (
                item.id,
                [
                    item.tipo.title(),
                    item.nombre_identificatorio,
                    item.patente,
                    item.observaciones,
                ],
            )
            for item in self.vehiculo_repository.list_all()
        ]

    def _peaje_rows(self) -> list[tuple[int, list[str]]]:
        return [
            (item.id, [item.nombre, item.direccion, _format_money(item.costo)])
            for item in self.peaje_repository.list_all()
        ]

    def _build_static_table_tab(
        self,
        title: str,
        headers: list[str],
        rows: list[tuple[int, list[str]]],
        *,
        show_actions: bool = True,
        create_callback: Callable[[], None] | None = None,
        edit_callback: Callable[[], None] | None = None,
        delete_callback: Callable[[], None] | None = None,
    ) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(20)

        panel = self._build_readonly_table_panel(
            title,
            headers,
            rows,
            show_actions=show_actions,
            create_callback=create_callback,
            edit_callback=edit_callback,
            delete_callback=delete_callback,
        )
        layout.addWidget(panel, stretch=1)
        return tab

    def _build_readonly_table_panel(
        self,
        title: str,
        headers: list[str],
        rows: list[tuple[int, list[str]]],
        *,
        show_actions: bool = True,
        create_callback: Callable[[], None] | None = None,
        edit_callback: Callable[[], None] | None = None,
        delete_callback: Callable[[], None] | None = None,
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
        if show_actions:
            header_layout.addWidget(
                self._build_crud_actions(
                    title,
                    create_callback=create_callback,
                    edit_callback=edit_callback,
                    delete_callback=delete_callback,
                )
            )

        table = QTableWidget(len(rows), len(headers) + 1)
        table.setHorizontalHeaderLabels(["ID", *headers])
        table.setColumnHidden(0, True)
        table.verticalHeader().setVisible(False)
        table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.ResizeToContents
        )
        table.setAlternatingRowColors(True)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)

        for row_index, (row_id, row) in enumerate(rows):
            id_item = QTableWidgetItem(str(row_id))
            id_item.setFlags(id_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            table.setItem(row_index, 0, id_item)
            for column_index, value in enumerate(row, start=1):
                item = QTableWidgetItem(value)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                table.setItem(row_index, column_index, item)

        self.object_tables[title] = table
        layout.addWidget(header)
        layout.addWidget(table, stretch=1)
        return panel

    def _populate_object_table(
        self,
        title: str,
        rows: list[tuple[int, list[str]]],
    ) -> None:
        table = self.object_tables.get(title)
        if table is None:
            return

        table.setRowCount(len(rows))
        for row_index, (row_id, row) in enumerate(rows):
            id_item = QTableWidgetItem(str(row_id))
            id_item.setFlags(id_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            table.setItem(row_index, 0, id_item)
            for column_index, value in enumerate(row, start=1):
                item = QTableWidgetItem(value)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                table.setItem(row_index, column_index, item)
        table.resizeColumnsToContents()

    def _refresh_object_table(self, title: str) -> None:
        loaders = {
            "Clientes": self._cliente_rows,
            "Lugares": self._lugar_rows,
            "Chofer": self._chofer_rows,
            "T.Carga": self._tipo_carga_rows,
            "Vehiculos": self._vehiculo_rows,
            "Peajes": self._peaje_rows,
        }
        loader = loaders.get(title)
        if loader is not None:
            self._populate_object_table(title, loader())

    def _selected_object_id(self, title: str) -> int | None:
        table = self.object_tables.get(title)
        if table is None:
            return None

        row = table.currentRow()
        if row < 0:
            QMessageBox.warning(
                self,
                "Seleccion requerida",
                f"Selecciona un registro de {title} primero.",
            )
            return None

        item = table.item(row, 0)
        return None if item is None else int(item.text())

    def _selected_viaje_id(self) -> int | None:
        if self.table is None:
            return None

        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(
                self,
                "Seleccion requerida",
                "Selecciona un viaje primero.",
            )
            return None

        item = self.table.item(row, 0)
        return None if item is None else int(item.text())

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
        header_layout.addWidget(header_title)
        header_layout.addStretch()
        header_layout.addWidget(
            self._build_crud_actions(
                "viaje",
                create_callback=self._go_to_create_tab,
                edit_callback=self._edit_viaje,
                delete_callback=self._delete_viaje,
            )
        )

        self.table = QTableWidget(0, 19)
        self.table.setHorizontalHeaderLabels(
            [
                "ID",
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
                "F.Desc vacio",
                "Peajes $",
                "Estado",
            ]
        )
        self.table.setColumnHidden(0, True)
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
            str(viaje.id),
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
            viaje.fecha_descarga_vacio,
            _format_money(viaje.peajes),
            viaje.estado,
        ]

    def _build_crud_actions(
        self,
        section_label: str,
        *,
        create_callback: Callable[[], None] | None = None,
        edit_callback: Callable[[], None] | None = None,
        delete_callback: Callable[[], None] | None = None,
    ) -> QWidget:
        actions = QWidget()
        actions.setObjectName("actionButtons")
        layout = QHBoxLayout(actions)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        create_button = QPushButton("Crear")
        create_button.setObjectName("primaryButton")
        create_button.clicked.connect(
            create_callback
            if create_callback is not None
            else lambda: self._show_pending_action(section_label, "Crear")
        )

        edit_button = QPushButton("Editar")
        edit_button.clicked.connect(
            edit_callback
            if edit_callback is not None
            else lambda: self._show_pending_action(section_label, "Editar")
        )

        delete_button = QPushButton("Eliminar")
        delete_button.setObjectName("dangerButton")
        delete_button.clicked.connect(
            delete_callback
            if delete_callback is not None
            else lambda: self._show_pending_action(section_label, "Eliminar")
        )

        layout.addWidget(create_button)
        layout.addWidget(edit_button)
        layout.addWidget(delete_button)
        return actions

    def _show_pending_action(self, section_label: str, action: str) -> None:
        QMessageBox.information(
            self,
            f"{action} {section_label}",
            f"La accion {action.lower()} para {section_label} queda lista para implementar.",
        )

    def _record_values(
        self,
        title: str,
        fields: list[dict[str, object]],
    ) -> dict[str, object] | None:
        dialog = RecordDialog(self, title, fields)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return None

        values = dialog.values()
        missing = [
            str(field["label"])
            for field in fields
            if field.get("required", True)
            and not str(values.get(str(field["key"]), "")).strip()
        ]
        if missing:
            QMessageBox.warning(
                self,
                "Datos incompletos",
                "Completa los campos obligatorios: " + ", ".join(missing),
            )
            return None
        return values

    def _run_data_action(
        self,
        success_message: str,
        callback: Callable[[], None],
    ) -> None:
        try:
            callback()
        except Exception as exc:
            QMessageBox.critical(self, "Error", f"No se pudo completar la accion.\n{exc}")
            return
        QMessageBox.information(self, "Listo", success_message)

    def _create_cliente(self) -> None:
        values = self._record_values("Crear cliente", self._cliente_fields())
        if values is None:
            return

        def save() -> None:
            self.cliente_repository.create(
                nombre=str(values["nombre"]).strip(),
                domicilio_fiscal=str(values["domicilio_fiscal"]).strip(),
                email=str(values["email"]).strip(),
                numero_contacto=str(values["numero_contacto"]).strip(),
            )
            self._refresh_object_table("Clientes")
            self._refresh_viaje_form_options()

        self._run_data_action("Cliente creado.", save)

    def _edit_cliente(self) -> None:
        cliente_id = self._selected_object_id("Clientes")
        if cliente_id is None:
            return
        cliente = self._find_by_id(self.cliente_repository.list_all(), cliente_id)
        if cliente is None:
            return
        values = self._record_values(
            "Editar cliente",
            self._cliente_fields(
                {
                    "nombre": cliente.nombre,
                    "domicilio_fiscal": cliente.domicilio_fiscal,
                    "email": cliente.email,
                    "numero_contacto": cliente.numero_contacto,
                }
            ),
        )
        if values is None:
            return

        def save() -> None:
            self.cliente_repository.update(
                cliente_id,
                nombre=str(values["nombre"]).strip(),
                domicilio_fiscal=str(values["domicilio_fiscal"]).strip(),
                email=str(values["email"]).strip(),
                numero_contacto=str(values["numero_contacto"]).strip(),
            )
            self._refresh_object_table("Clientes")
            self._refresh_table()
            self._refresh_viaje_form_options()

        self._run_data_action("Cliente actualizado.", save)

    def _delete_cliente(self) -> None:
        cliente_id = self._selected_object_id("Clientes")
        if cliente_id is not None:
            self._soft_delete_object(
                "cliente",
                lambda: self.cliente_repository.delete(cliente_id),
                lambda: self._refresh_object_table("Clientes"),
            )

    def _create_lugar(self) -> None:
        values = self._record_values("Crear lugar", self._lugar_fields())
        if values is None:
            return

        def save() -> None:
            self.lugar_repository.create(
                nombre=str(values["nombre"]).strip(),
                direccion=str(values["direccion"]).strip(),
                observaciones=str(values["observaciones"]).strip(),
                roles=tuple(values["roles"]),
            )
            self._refresh_object_table("Lugares")
            self._refresh_viaje_form_options()

        self._run_data_action("Lugar creado.", save)

    def _edit_lugar(self) -> None:
        lugar_id = self._selected_object_id("Lugares")
        if lugar_id is None:
            return
        lugar = self._find_by_id(self.lugar_repository.list_all(), lugar_id)
        if lugar is None:
            return
        roles = tuple(
            role.rol
            for role in self.lugar_repository.list_roles()
            if role.lugar_id == lugar_id
        )
        values = self._record_values(
            "Editar lugar",
            self._lugar_fields(
                {
                    "nombre": lugar.nombre,
                    "direccion": lugar.direccion,
                    "observaciones": lugar.observaciones,
                    "roles": roles,
                }
            ),
        )
        if values is None:
            return

        def save() -> None:
            self.lugar_repository.update(
                lugar_id,
                nombre=str(values["nombre"]).strip(),
                direccion=str(values["direccion"]).strip(),
                observaciones=str(values["observaciones"]).strip(),
                roles=tuple(values["roles"]),
            )
            self._refresh_object_table("Lugares")
            self._refresh_table()
            self._refresh_viaje_form_options()

        self._run_data_action("Lugar actualizado.", save)

    def _delete_lugar(self) -> None:
        lugar_id = self._selected_object_id("Lugares")
        if lugar_id is not None:
            self._soft_delete_object(
                "lugar",
                lambda: self.lugar_repository.delete(lugar_id),
                lambda: self._refresh_object_table("Lugares"),
            )

    def _create_chofer(self) -> None:
        values = self._record_values("Crear chofer", self._chofer_fields())
        if values is None:
            return

        def save() -> None:
            self.chofer_repository.create(
                dni=str(values["dni"]).strip(),
                nombre=str(values["nombre"]).strip(),
                apellido=str(values["apellido"]).strip(),
                numero_telefono=str(values["numero_telefono"]).strip(),
                fecha_vencimiento_registro=str(values["fecha_vencimiento_registro"]),
            )
            self._refresh_object_table("Chofer")
            self._refresh_viaje_form_options()

        self._run_data_action("Chofer creado.", save)

    def _edit_chofer(self) -> None:
        chofer_id = self._selected_object_id("Chofer")
        if chofer_id is None:
            return
        chofer = self._find_by_id(self.chofer_repository.list_all(), chofer_id)
        if chofer is None:
            return
        values = self._record_values(
            "Editar chofer",
            self._chofer_fields(
                {
                    "dni": chofer.dni,
                    "nombre": chofer.nombre,
                    "apellido": chofer.apellido,
                    "numero_telefono": chofer.numero_telefono,
                    "fecha_vencimiento_registro": chofer.fecha_vencimiento_registro,
                }
            ),
        )
        if values is None:
            return

        def save() -> None:
            self.chofer_repository.update(
                chofer_id,
                dni=str(values["dni"]).strip(),
                nombre=str(values["nombre"]).strip(),
                apellido=str(values["apellido"]).strip(),
                numero_telefono=str(values["numero_telefono"]).strip(),
                fecha_vencimiento_registro=str(values["fecha_vencimiento_registro"]),
            )
            self._refresh_object_table("Chofer")
            self._refresh_table()
            self._refresh_viaje_form_options()

        self._run_data_action("Chofer actualizado.", save)

    def _delete_chofer(self) -> None:
        chofer_id = self._selected_object_id("Chofer")
        if chofer_id is not None:
            self._soft_delete_object(
                "chofer",
                lambda: self.chofer_repository.delete(chofer_id),
                lambda: self._refresh_object_table("Chofer"),
            )

    def _create_tipo_carga(self) -> None:
        values = self._record_values("Crear tipo de carga", self._tipo_carga_fields())
        if values is None:
            return

        def save() -> None:
            self.tipo_carga_repository.create(
                codigo=str(values["codigo"]).strip().upper(),
                nombre=str(values["nombre"]).strip(),
            )
            self._refresh_object_table("T.Carga")
            self._refresh_viaje_form_options()

        self._run_data_action("Tipo de carga creado.", save)

    def _edit_tipo_carga(self) -> None:
        tipo_id = self._selected_object_id("T.Carga")
        if tipo_id is None:
            return
        tipo = self._find_by_id(self.tipo_carga_repository.list_all(), tipo_id)
        if tipo is None:
            return
        values = self._record_values(
            "Editar tipo de carga",
            self._tipo_carga_fields({"codigo": tipo.codigo, "nombre": tipo.nombre}),
        )
        if values is None:
            return

        def save() -> None:
            self.tipo_carga_repository.update(
                tipo_id,
                codigo=str(values["codigo"]).strip().upper(),
                nombre=str(values["nombre"]).strip(),
            )
            self._refresh_object_table("T.Carga")
            self._refresh_table()
            self._refresh_viaje_form_options()

        self._run_data_action("Tipo de carga actualizado.", save)

    def _delete_tipo_carga(self) -> None:
        tipo_id = self._selected_object_id("T.Carga")
        if tipo_id is not None:
            self._soft_delete_object(
                "tipo de carga",
                lambda: self.tipo_carga_repository.delete(tipo_id),
                lambda: self._refresh_object_table("T.Carga"),
            )

    def _create_vehiculo(self) -> None:
        values = self._record_values("Crear vehiculo", self._vehiculo_fields())
        if values is None:
            return

        def save() -> None:
            self.vehiculo_repository.create(
                tipo=str(values["tipo"]),
                nombre_identificatorio=str(values["nombre_identificatorio"]).strip(),
                patente=str(values["patente"]).strip().upper(),
                observaciones=str(values["observaciones"]).strip(),
            )
            self._refresh_object_table("Vehiculos")
            self._refresh_viaje_form_options()

        self._run_data_action("Vehiculo creado.", save)

    def _edit_vehiculo(self) -> None:
        vehiculo_id = self._selected_object_id("Vehiculos")
        if vehiculo_id is None:
            return
        vehiculo = self._find_by_id(self.vehiculo_repository.list_all(), vehiculo_id)
        if vehiculo is None:
            return
        values = self._record_values(
            "Editar vehiculo",
            self._vehiculo_fields(
                {
                    "tipo": vehiculo.tipo,
                    "nombre_identificatorio": vehiculo.nombre_identificatorio,
                    "patente": vehiculo.patente,
                    "observaciones": vehiculo.observaciones,
                }
            ),
        )
        if values is None:
            return

        def save() -> None:
            self.vehiculo_repository.update(
                vehiculo_id,
                tipo=str(values["tipo"]),
                nombre_identificatorio=str(values["nombre_identificatorio"]).strip(),
                patente=str(values["patente"]).strip().upper(),
                observaciones=str(values["observaciones"]).strip(),
            )
            self._refresh_object_table("Vehiculos")
            self._refresh_table()
            self._refresh_viaje_form_options()

        self._run_data_action("Vehiculo actualizado.", save)

    def _delete_vehiculo(self) -> None:
        vehiculo_id = self._selected_object_id("Vehiculos")
        if vehiculo_id is not None:
            self._soft_delete_object(
                "vehiculo",
                lambda: self.vehiculo_repository.delete(vehiculo_id),
                lambda: self._refresh_object_table("Vehiculos"),
            )

    def _create_peaje(self) -> None:
        values = self._record_values("Crear peaje", self._peaje_fields())
        if values is None:
            return

        def save() -> None:
            self.peaje_repository.create(
                nombre=str(values["nombre"]).strip(),
                direccion=str(values["direccion"]).strip(),
                costo=float(values["costo"]),
            )
            self._refresh_object_table("Peajes")
            self._refresh_viaje_form_options()

        self._run_data_action("Peaje creado.", save)

    def _edit_peaje(self) -> None:
        peaje_id = self._selected_object_id("Peajes")
        if peaje_id is None:
            return
        peaje = self._find_by_id(self.peaje_repository.list_all(), peaje_id)
        if peaje is None:
            return
        values = self._record_values(
            "Editar peaje",
            self._peaje_fields(
                {
                    "nombre": peaje.nombre,
                    "direccion": peaje.direccion,
                    "costo": peaje.costo,
                }
            ),
        )
        if values is None:
            return

        def save() -> None:
            self.peaje_repository.update(
                peaje_id,
                nombre=str(values["nombre"]).strip(),
                direccion=str(values["direccion"]).strip(),
                costo=float(values["costo"]),
            )
            self._refresh_object_table("Peajes")
            self._refresh_table()
            self._refresh_viaje_form_options()

        self._run_data_action("Peaje actualizado.", save)

    def _delete_peaje(self) -> None:
        peaje_id = self._selected_object_id("Peajes")
        if peaje_id is not None:
            self._soft_delete_object(
                "peaje",
                lambda: self.peaje_repository.delete(peaje_id),
                lambda: self._refresh_object_table("Peajes"),
            )

    def _edit_viaje(self) -> None:
        viaje_id = self._selected_viaje_id()
        if viaje_id is None or self.table is None:
            return

        row = self.table.currentRow()
        values = self._record_values(
            "Editar viaje",
            self._viaje_fields_from_row(row),
        )
        if values is None:
            return

        def save() -> None:
            self.viaje_repository.update_basic(
                viaje_id,
                fecha=str(values["fecha"]),
                observaciones=str(values["observaciones"]).strip(),
                tarifa=float(values["tarifa"]),
                fecha_descarga_tarifa=str(values["fecha_descarga_tarifa"]),
                demora=float(values["demora"]),
                fecha_descarga_demora=str(values["fecha_descarga_demora"]),
                vacio=float(values["vacio"]),
                fecha_descarga_vacio=str(values["fecha_descarga_vacio"]),
                estado=str(values["estado"]).strip(),
            )
            self._refresh_table()
            self._refresh_metrics()

        self._run_data_action("Viaje actualizado.", save)

    def _delete_viaje(self) -> None:
        viaje_id = self._selected_viaje_id()
        if viaje_id is None:
            return
        if self._confirm_delete("viaje"):
            self._run_data_action(
                "Viaje eliminado.",
                lambda: self._delete_viaje_and_refresh(viaje_id),
            )

    def _delete_viaje_and_refresh(self, viaje_id: int) -> None:
        self.viaje_repository.delete(viaje_id)
        self._refresh_table()
        self._refresh_metrics()

    def _soft_delete_object(
        self,
        label: str,
        delete_callback: Callable[[], None],
        refresh_callback: Callable[[], None],
    ) -> None:
        if not self._confirm_delete(label):
            return

        def delete_and_refresh() -> None:
            delete_callback()
            refresh_callback()
            self._refresh_table()
            self._refresh_viaje_form_options()

        self._run_data_action(f"{label.title()} eliminado.", delete_and_refresh)

    def _confirm_delete(self, label: str) -> bool:
        response = QMessageBox.question(
            self,
            "Confirmar eliminacion",
            f"Eliminar {label} seleccionado?",
        )
        return response == QMessageBox.StandardButton.Yes

    def _cliente_fields(
        self,
        values: dict[str, object] | None = None,
    ) -> list[dict[str, object]]:
        values = values or {}
        return [
            {"key": "nombre", "label": "Nombre", "value": values.get("nombre", "")},
            {
                "key": "domicilio_fiscal",
                "label": "Domicilio fiscal",
                "value": values.get("domicilio_fiscal", ""),
                "required": False,
            },
            {
                "key": "email",
                "label": "Email",
                "value": values.get("email", ""),
                "required": False,
            },
            {
                "key": "numero_contacto",
                "label": "Numero contacto",
                "value": values.get("numero_contacto", ""),
                "required": False,
            },
        ]

    def _lugar_fields(
        self,
        values: dict[str, object] | None = None,
    ) -> list[dict[str, object]]:
        values = values or {}
        return [
            {"key": "nombre", "label": "Nombre", "value": values.get("nombre", "")},
            {
                "key": "direccion",
                "label": "Direccion",
                "value": values.get("direccion", ""),
                "required": False,
            },
            {
                "key": "observaciones",
                "label": "Observaciones",
                "type": "multiline",
                "value": values.get("observaciones", ""),
                "required": False,
            },
            {
                "key": "roles",
                "label": "Roles",
                "type": "checks",
                "value": values.get("roles", ()),
                "options": [("Carga", "CARGA"), ("Descarga", "DESCARGA")],
                "required": False,
            },
        ]

    def _chofer_fields(
        self,
        values: dict[str, object] | None = None,
    ) -> list[dict[str, object]]:
        values = values or {}
        return [
            {"key": "dni", "label": "DNI", "value": values.get("dni", "")},
            {"key": "nombre", "label": "Nombre", "value": values.get("nombre", "")},
            {"key": "apellido", "label": "Apellido", "value": values.get("apellido", "")},
            {
                "key": "numero_telefono",
                "label": "Telefono",
                "value": values.get("numero_telefono", ""),
                "required": False,
            },
            {
                "key": "fecha_vencimiento_registro",
                "label": "Vencimiento registro",
                "type": "date",
                "value": values.get("fecha_vencimiento_registro", ""),
            },
        ]

    def _tipo_carga_fields(
        self,
        values: dict[str, object] | None = None,
    ) -> list[dict[str, object]]:
        values = values or {}
        return [
            {"key": "nombre", "label": "Nombre", "value": values.get("nombre", "")},
            {
                "key": "codigo",
                "label": "Codigo interno",
                "value": values.get("codigo", ""),
            },
        ]

    def _vehiculo_fields(
        self,
        values: dict[str, object] | None = None,
    ) -> list[dict[str, object]]:
        values = values or {}
        return [
            {
                "key": "tipo",
                "label": "Tipo",
                "type": "combo",
                "value": values.get("tipo", "CAMION"),
                "options": [("Camion", "CAMION"), ("Semi", "SEMI")],
            },
            {
                "key": "nombre_identificatorio",
                "label": "Nombre identificatorio",
                "value": values.get("nombre_identificatorio", ""),
            },
            {"key": "patente", "label": "Patente", "value": values.get("patente", "")},
            {
                "key": "observaciones",
                "label": "Observaciones",
                "type": "multiline",
                "value": values.get("observaciones", ""),
                "required": False,
            },
        ]

    def _peaje_fields(
        self,
        values: dict[str, object] | None = None,
    ) -> list[dict[str, object]]:
        values = values or {}
        return [
            {"key": "nombre", "label": "Nombre", "value": values.get("nombre", "")},
            {
                "key": "direccion",
                "label": "Direccion",
                "value": values.get("direccion", ""),
                "required": False,
            },
            {
                "key": "costo",
                "label": "Costo",
                "type": "money",
                "value": values.get("costo", 0),
            },
        ]

    def _viaje_fields_from_row(self, row: int) -> list[dict[str, object]]:
        return [
            {"key": "fecha", "label": "Fecha", "type": "date", "value": self._cell(row, 1)},
            {
                "key": "observaciones",
                "label": "Observaciones",
                "type": "multiline",
                "value": self._cell(row, 6),
                "required": False,
            },
            {
                "key": "tarifa",
                "label": "Tarifa",
                "type": "money",
                "value": self._money_from_display(self._cell(row, 11)),
            },
            {
                "key": "fecha_descarga_tarifa",
                "label": "F.Desc tarifa",
                "type": "date",
                "value": self._cell(row, 12),
                "required": False,
            },
            {
                "key": "demora",
                "label": "Demora",
                "type": "money",
                "value": self._money_from_display(self._cell(row, 13)),
            },
            {
                "key": "fecha_descarga_demora",
                "label": "F.Desc demora",
                "type": "date",
                "value": self._cell(row, 14),
                "required": False,
            },
            {
                "key": "vacio",
                "label": "Vacio",
                "type": "money",
                "value": self._money_from_display(self._cell(row, 15)),
            },
            {
                "key": "fecha_descarga_vacio",
                "label": "F.Desc vacio",
                "type": "date",
                "value": self._cell(row, 16),
                "required": False,
            },
            {"key": "estado", "label": "Estado", "value": self._cell(row, 18)},
        ]

    def _find_by_id(self, items: list[object], item_id: int) -> object | None:
        for item in items:
            if getattr(item, "id", None) == item_id:
                return item
        return None

    def _cell(self, row: int, column: int) -> str:
        if self.table is None:
            return ""
        item = self.table.item(row, column)
        return "" if item is None else item.text()

    def _money_from_display(self, value: str) -> float:
        clean = value.replace("$", "").replace(".", "").replace(",", ".").strip()
        return float(clean or 0)

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
        self._refresh_viaje_form_options()
        self._refresh_table()
        self._refresh_metrics()
        self._clear_viaje_form()
        self._go_to_history_tab()

    def _prepare_new_viaje(self) -> None:
        self._clear_viaje_form()
        self._go_to_create_tab()

    def _collect_viaje_form(self) -> ViajeCreate:
        fecha = self._date_value("fecha")
        fecha_descarga_tarifa = self._date_value("fecha_descarga_tarifa")
        fecha_descarga_demora = self._date_value("fecha_descarga_demora")
        fecha_descarga_vacio = self._date_value("fecha_descarga_vacio")
        cliente_id = self._required_combo_int("cliente")
        lugar_carga_id = self._required_combo_int("lugar_carga")
        lugar_descarga_id = self._required_combo_int("lugar_descarga")
        chofer_id = self._required_combo_int("chofer")
        camion_id = self._required_combo_int("camion")
        semi_id = self._optional_combo_int("semi")
        peaje_ids = self._checked_peaje_ids()
        carga_id = self._carga_id_from_form()

        return ViajeCreate(
            fecha=fecha,
            cliente_id=cliente_id,
            carga_id=carga_id,
            lugar_carga_id=lugar_carga_id,
            lugar_descarga_id=lugar_descarga_id,
            observaciones=self._text_value("observaciones"),
            chofer_id=chofer_id,
            tipo_carga=str(self._combo_value("tipo_carga") or "GENERAL"),
            camion_id=camion_id,
            semi_id=semi_id,
            tarifa=self._money_value("tarifa"),
            fecha_descarga_tarifa=fecha_descarga_tarifa,
            demora=self._money_value("demora"),
            fecha_descarga_demora=fecha_descarga_demora,
            vacio=self._money_value("vacio"),
            fecha_descarga_vacio=fecha_descarga_vacio,
            peaje_ids=peaje_ids,
        )

    def _clear_viaje_form(self) -> None:
        for key in ("tarifa", "demora", "vacio"):
            widget = self.form_widgets[key]
            if isinstance(widget, QDoubleSpinBox):
                widget.setValue(0)

        observaciones = self.form_widgets["observaciones"]
        if isinstance(observaciones, QTextEdit):
            observaciones.clear()

        carga = self.form_widgets["carga"]
        if isinstance(carga, QComboBox) and carga.isEditable():
            carga.setCurrentText("")

        for key in (
            "fecha",
            "fecha_descarga_tarifa",
            "fecha_descarga_demora",
            "fecha_descarga_vacio",
        ):
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
            self.new_button.setVisible(active_label == "Cargar viaje")

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

    def _build_tipo_carga_combo(self) -> QComboBox:
        items = [
            (item.nombre, item.codigo)
            for item in self.tipo_carga_repository.list_all()
        ]
        if not items:
            items = [("General", "GENERAL"), ("Carga peligrosa", "PELIGROSA")]
        return self._build_combo(items)

    def _refresh_viaje_form_options(self) -> None:
        combo_sources = {
            "cliente": [(item.nombre, item.id) for item in self.cliente_repository.list_all()],
            "carga": [
                (item.codigo_contenedor, item.id)
                for item in self.carga_repository.list_all()
            ],
            "lugar_carga": self._lugar_options("CARGA"),
            "lugar_descarga": self._lugar_options("DESCARGA"),
            "chofer": [
                (f"{item.nombre_completo} - DNI {item.dni}", item.id)
                for item in self.chofer_repository.list_all()
            ],
            "tipo_carga": [
                (item.nombre, item.codigo)
                for item in self.tipo_carga_repository.list_all()
            ],
            "camion": [
                (item.etiqueta, item.id)
                for item in self.vehiculo_repository.list_all("CAMION")
            ],
            "semi": [("Sin semi", None)]
            + [
                (item.etiqueta, item.id)
                for item in self.vehiculo_repository.list_all("SEMI")
            ],
        }
        if not combo_sources["tipo_carga"]:
            combo_sources["tipo_carga"] = [
                ("General", "GENERAL"),
                ("Carga peligrosa", "PELIGROSA"),
            ]

        for key, items in combo_sources.items():
            widget = self.form_widgets.get(key)
            if isinstance(widget, QComboBox):
                was_editable = widget.isEditable()
                widget.clear()
                for label, value in items:
                    widget.addItem(label, value)
                if was_editable:
                    widget.setCurrentText("")

        peajes = self.form_widgets.get("peajes")
        if isinstance(peajes, QListWidget):
            peajes.clear()
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

    def _lugar_options(self, rol: str) -> list[tuple[str, object]]:
        roles = self.lugar_repository.list_roles(rol)
        if roles:
            return [(item.lugar, item.lugar_id) for item in roles]
        return [(item.nombre, item.id) for item in self.lugar_repository.list_all()]

    def _build_lugar_combo(self, rol: str) -> QComboBox:
        return self._build_combo(self._lugar_options(rol))

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

    def _carga_id_from_form(self) -> int:
        widget = self.form_widgets["carga"]
        if not isinstance(widget, QComboBox):
            raise ValueError("Campo de carga invalido.")

        codigo = widget.currentText().strip()
        if not codigo:
            raise ValueError("Completa el codigo de carga provisto por el cliente.")

        selected_text = widget.itemText(widget.currentIndex()).strip()
        selected_id = widget.currentData()
        if selected_id is not None and codigo == selected_text:
            return int(selected_id)

        carga_id = self.carga_repository.get_or_create(codigo_contenedor=codigo)
        return carga_id

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


class RecordDialog(QDialog):
    def __init__(
        self,
        parent: QWidget,
        title: str,
        fields: list[dict[str, object]],
    ) -> None:
        super().__init__(parent)
        self.fields = fields
        self.widgets: dict[str, QWidget] = {}
        self.check_groups: dict[str, list[tuple[QCheckBox, object]]] = {}

        self.setWindowTitle(title)
        self.setMinimumWidth(420)

        layout = QVBoxLayout(self)
        form = QFormLayout()
        form.setHorizontalSpacing(14)
        form.setVerticalSpacing(10)

        for field in fields:
            key = str(field["key"])
            label = str(field["label"])
            field_type = str(field.get("type", "text"))
            value = field.get("value", "")

            if field_type == "date":
                widget = QDateEdit()
                widget.setCalendarPopup(True)
                widget.setDisplayFormat("yyyy-MM-dd")
                date = QDate.fromString(str(value), "yyyy-MM-dd")
                widget.setDate(date if date.isValid() else QDate.currentDate())
            elif field_type == "money":
                widget = QDoubleSpinBox()
                widget.setRange(0, 999_999_999)
                widget.setDecimals(2)
                widget.setSingleStep(1000)
                widget.setPrefix("$ ")
                widget.setValue(float(value or 0))
            elif field_type == "combo":
                widget = QComboBox()
                for option_label, option_value in field.get("options", []):
                    widget.addItem(str(option_label), option_value)
                selected = field.get("value")
                index = widget.findData(selected)
                if index >= 0:
                    widget.setCurrentIndex(index)
            elif field_type == "multiline":
                widget = QTextEdit()
                widget.setFixedHeight(84)
                widget.setPlainText(str(value or ""))
            elif field_type == "checks":
                widget = QWidget()
                check_layout = QHBoxLayout(widget)
                check_layout.setContentsMargins(0, 0, 0, 0)
                check_layout.setSpacing(12)
                selected_values = set(value or ())
                checks: list[tuple[QCheckBox, object]] = []
                for option_label, option_value in field.get("options", []):
                    check = QCheckBox(str(option_label))
                    check.setChecked(option_value in selected_values)
                    check_layout.addWidget(check)
                    checks.append((check, option_value))
                check_layout.addStretch()
                self.check_groups[key] = checks
            else:
                widget = QLineEdit()
                widget.setText(str(value or ""))

            self.widgets[key] = widget
            form.addRow(label, widget)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout.addLayout(form)
        layout.addWidget(buttons)

    def values(self) -> dict[str, object]:
        values: dict[str, object] = {}
        for field in self.fields:
            key = str(field["key"])
            widget = self.widgets[key]
            if key in self.check_groups:
                values[key] = tuple(
                    option_value
                    for check, option_value in self.check_groups[key]
                    if check.isChecked()
                )
            elif isinstance(widget, QLineEdit):
                values[key] = widget.text().strip()
            elif isinstance(widget, QTextEdit):
                values[key] = widget.toPlainText().strip()
            elif isinstance(widget, QDateEdit):
                values[key] = widget.date().toString("yyyy-MM-dd")
            elif isinstance(widget, QDoubleSpinBox):
                values[key] = float(widget.value())
            elif isinstance(widget, QComboBox):
                values[key] = widget.currentData()
        return values


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

QPushButton#dangerButton {
    border-color: #b42318;
    color: #b42318;
}

QWidget#actionButtons {
    background: transparent;
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
