from __future__ import annotations

import platform
from collections.abc import Callable
from pathlib import Path
from threading import Thread

from PySide6.QtCore import QDate, QObject, Qt, QTimer, QUrl, Signal
from PySide6.QtGui import QAction, QDesktopServices
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFileDialog,
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
    QProgressDialog,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from gestion_camiones import __version__
from gestion_camiones.config import GITHUB_OWNER, GITHUB_REPO
from gestion_camiones.data.models import AppAlert, ViajeCreate, ViajeResumen
from gestion_camiones.data.paths import get_app_data_dir, get_settings_path
from gestion_camiones.data.repositories import (
    AlertRepository,
    CargaRepository,
    ChoferRepository,
    ClienteRepository,
    LugarRepository,
    PeajeRepository,
    TipoCargaRepository,
    VehiculoRepository,
    ViajeRepository,
)
from gestion_camiones.data.schema import clear_database
from gestion_camiones.services.app_settings import (
    load_app_settings,
    normalize_company_name,
    save_app_settings,
)
from gestion_camiones.services.report_exporter import (
    build_monthly_report_summary,
    build_ricco_export_filename,
    export_monthly_report_excel,
    export_monthly_report_pdf,
    export_ricco_report_excel,
    find_ricco_template_path,
)
from gestion_camiones.services.updater import (
    ReleaseAsset,
    ReleaseInfo,
    UpdateCheckError,
    UpdateDownloadError,
    UpdateInstallError,
    backups_dir,
    check_latest_release,
    create_database_backup,
    download_release_asset,
    launch_update_installer,
    select_checksum_asset,
    select_release_asset,
    updates_dir,
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
    "Imprimir",
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
    "Imprimir": (
        "Imprimir",
        "Exportacion mensual de viajes en Excel y PDF.",
    ),
    "Opciones": (
        "Opciones",
        "Configuracion general de la aplicacion.",
    ),
}

MONTH_NAMES = (
    "Enero",
    "Febrero",
    "Marzo",
    "Abril",
    "Mayo",
    "Junio",
    "Julio",
    "Agosto",
    "Septiembre",
    "Octubre",
    "Noviembre",
    "Diciembre",
)

VIAJE_FORM_FIELDS = (
    ("fecha", "Fecha"),
    ("cliente", "Cliente"),
    ("carta_porte", "N° Carta de Porte"),
    ("carga", "Carga"),
    ("lugar_carga", "Lugar carga"),
    ("lugar_descarga", "L.Descarga"),
    ("observaciones", "Observaciones"),
    ("chofer", "Chofer"),
    ("tipo_carga", "T.Carga"),
    ("camion", "Camion"),
    ("semi", "Semi"),
    ("tarifa", "Tarifa"),
    ("fecha_descarga_tarifa", "F.Desc tarifa"),
    ("demora", "Demora"),
    ("fecha_descarga_demora", "F.Desc demora"),
    ("vacio", "Vacio"),
    ("fecha_descarga_vacio", "F.Desc vacio"),
    ("gas_oil_lts", "Gas oil (lts)"),
    ("peaje_empresa", "Empresa peajes"),
    ("peajes", "Peajes"),
)
VIAJE_FORM_LABELS = dict(VIAJE_FORM_FIELDS)
VIAJE_CONFIGURABLE_FIELD_KEYS = tuple(
    key for key, _label in VIAJE_FORM_FIELDS if key != "cliente"
)


class UpdateSignals(QObject):
    finished = Signal(object, bool)
    failed = Signal(str, bool)
    download_progress = Signal(int, int)
    download_finished = Signal(object, object, object)
    download_failed = Signal(str)


class MainWindow(QMainWindow):
    def __init__(self, viaje_repository: ViajeRepository, database_path: Path) -> None:
        super().__init__()
        self.viaje_repository = viaje_repository
        self.database_path = database_path
        self.settings_path = get_settings_path()
        self.app_settings = load_app_settings(self.settings_path)
        self.company_name = str(self.app_settings["company_name"])
        self.update_signals = UpdateSignals()
        self.update_signals.finished.connect(self._handle_update_check_finished)
        self.update_signals.failed.connect(self._handle_update_check_failed)
        self.update_signals.download_progress.connect(self._handle_update_download_progress)
        self.update_signals.download_finished.connect(self._handle_update_download_finished)
        self.update_signals.download_failed.connect(self._handle_update_download_failed)
        self.update_check_in_progress = False
        self.update_download_in_progress = False
        self.update_progress_dialog: QProgressDialog | None = None
        self.cliente_repository = ClienteRepository(database_path)
        self.alert_repository = AlertRepository(database_path)
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
        self.sidebar: QFrame | None = None
        self.sidebar_visible = True
        self.sidebar_toggle_button: QPushButton | None = None
        self.peajes_detail_panel: QFrame | None = None
        self.peajes_detail_title: QLabel | None = None
        self.peajes_detail_table: QTableWidget | None = None
        self.selected_peaje_empresa_id: int | None = None
        self.tabs: QTabWidget | None = None
        self.nav_buttons: dict[str, QPushButton] = {}
        self.page_title_label: QLabel | None = None
        self.page_subtitle_label: QLabel | None = None
        self.new_button: QPushButton | None = None
        self.save_button: QPushButton | None = None
        self.billing_month_combo: QComboBox | None = None
        self.billing_year_combo: QComboBox | None = None
        self.billing_total_card: MetricCard | None = None
        self.billing_month_cards: list[MetricCard] = []
        self.billing_content_widget: QWidget | None = None
        self.billing_toggle_button: QPushButton | None = None
        self.billing_panel_expanded = True
        self.print_mode_combo: QComboBox | None = None
        self.print_month_combo: QComboBox | None = None
        self.print_year_combo: QComboBox | None = None
        self.print_from_date: QDateEdit | None = None
        self.print_to_date: QDateEdit | None = None
        self.print_table: QTableWidget | None = None
        self.print_total_card: MetricCard | None = None
        self.print_count_card: MetricCard | None = None
        self.print_mode_card: QFrame | None = None
        self.print_month_card: QFrame | None = None
        self.print_year_card: QFrame | None = None
        self.print_from_card: QFrame | None = None
        self.print_to_card: QFrame | None = None
        self.print_rows: list[ViajeResumen] = []
        self.company_name_input: QLineEdit | None = None
        self.form_widgets: dict[str, QWidget] = {}
        self.viaje_form_row_labels: dict[str, QWidget] = {}

        self.setWindowTitle("Gestion de viajes")
        self.resize(1180, 760)
        self.setMinimumSize(980, 620)

        self._build_menu()
        self.setCentralWidget(self._build_shell())
        self.setStyleSheet(APP_STYLES)
        QTimer.singleShot(450, self._show_startup_alerts)

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

    def _show_startup_alerts(self) -> None:
        alerts = self.alert_repository.list_startup_alerts()
        if not alerts:
            QTimer.singleShot(350, self._check_updates_on_startup)
            return

        dialog = StartupAlertsDialog(
            self,
            alerts,
            accept_callback=self._accept_startup_alert,
            validate_callback=self._validate_startup_alert,
        )
        dialog.exec()
        QTimer.singleShot(350, self._check_updates_on_startup)

    def _accept_startup_alert(self, alert: AppAlert) -> bool:
        self.alert_repository.accept_alert(alert.key)
        return True

    def _validate_startup_alert(self, alert: AppAlert) -> bool:
        if alert.source == AlertRepository.DRIVER_LICENSE_SOURCE:
            new_date = self._ask_driver_license_due_date(alert)
            if new_date is None:
                return False
            self.chofer_repository.update_fecha_vencimiento_registro(
                alert.entity_id,
                new_date,
            )
            self.alert_repository.clear_alert(alert.key)
            self._refresh_object_table("Chofer")
            return True
        QMessageBox.warning(
            self,
            "Alerta",
            "Esta alerta no tiene una validacion automatica disponible.",
        )
        return False

    def _ask_driver_license_due_date(self, alert: AppAlert) -> str | None:
        dialog = QDialog(self)
        dialog.setWindowTitle("Validar registro")
        layout = QVBoxLayout(dialog)
        layout.setSpacing(12)

        title = QLabel("Nueva fecha de vencimiento")
        title.setObjectName("sectionTitle")
        description = QLabel(alert.message)
        description.setObjectName("muted")
        description.setWordWrap(True)

        date_input = QDateEdit()
        date_input.setCalendarPopup(True)
        date_input.setDisplayFormat("yyyy-MM-dd")
        current_due_date = QDate.fromString(alert.due_date, "yyyy-MM-dd")
        if current_due_date.isValid():
            default_date = current_due_date.addYears(1)
        else:
            default_date = QDate.currentDate()
        date_input.setDate(default_date)

        form = QFormLayout()
        form.addRow("Vencimiento", date_input)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)

        layout.addWidget(title)
        layout.addWidget(description)
        layout.addLayout(form)
        layout.addWidget(buttons)

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return None
        return date_input.date().toString("yyyy-MM-dd")

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
        sidebar.setFixedWidth(188)
        self.sidebar = sidebar

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(14, 18, 14, 14)
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
        self.tabs.addTab(self._build_print_tab(), TAB_LABELS[9])
        self.tabs.addTab(self._build_options_tab(), TAB_LABELS[10])
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

        sidebar_toggle = QPushButton("Ocultar pestañas")
        sidebar_toggle.setObjectName("sidebarToggleButton")
        sidebar_toggle.setCursor(Qt.CursorShape.PointingHandCursor)
        sidebar_toggle.clicked.connect(self._toggle_sidebar)
        self.sidebar_toggle_button = sidebar_toggle

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
        new_button.setCursor(Qt.CursorShape.PointingHandCursor)
        new_button.clicked.connect(self._prepare_new_viaje)
        self.new_button = new_button

        save_button = QPushButton("Guardar viaje")
        save_button.setObjectName("primaryButton")
        save_button.setCursor(Qt.CursorShape.PointingHandCursor)
        save_button.clicked.connect(self._save_viaje)
        self.save_button = save_button

        layout.addWidget(sidebar_toggle)
        layout.addLayout(title_block)
        layout.addStretch()
        layout.addWidget(self.search_input)
        layout.addWidget(new_button)
        layout.addWidget(save_button)
        return topbar

    def _toggle_sidebar(self) -> None:
        self.sidebar_visible = not self.sidebar_visible
        if self.sidebar is not None:
            self.sidebar.setVisible(self.sidebar_visible)
        if self.sidebar_toggle_button is not None:
            self.sidebar_toggle_button.setText(
                "Ocultar pestañas" if self.sidebar_visible else "Mostrar pestañas"
            )

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

        form_grid = QGridLayout()
        form_grid.setHorizontalSpacing(28)
        form_grid.setVerticalSpacing(0)
        form_grid.setColumnStretch(0, 1)
        form_grid.setColumnStretch(1, 1)

        left_form = QFormLayout()
        right_form = QFormLayout()
        for form in (left_form, right_form):
            form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
            form.setFormAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
            form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
            form.setHorizontalSpacing(16)
            form.setVerticalSpacing(10)

        fecha = QDateEdit()
        fecha.setCalendarPopup(True)
        fecha.setDisplayFormat("yyyy-MM-dd")
        fecha.setDate(QDate.currentDate())

        cliente = self._build_combo(
            [("Seleccionar cliente", None)]
            + [(item.etiqueta, item.id) for item in self.cliente_repository.list_all()]
        )
        cliente.currentIndexChanged.connect(self._apply_viaje_field_visibility)
        carta_porte = QLineEdit()
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

        gas_oil_lts = self._decimal_input()

        peaje_empresa = self._build_peaje_empresa_combo()
        peaje_empresa.currentIndexChanged.connect(self._refresh_peaje_checklist)

        peajes = QListWidget()
        peajes.setFixedHeight(92)

        self.form_widgets = {
            "fecha": fecha,
            "cliente": cliente,
            "carta_porte": carta_porte,
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
            "gas_oil_lts": gas_oil_lts,
            "peaje_empresa": peaje_empresa,
            "peajes": peajes,
        }

        self._add_viaje_form_row(left_form, "fecha", fecha)
        self._add_viaje_form_row(left_form, "cliente", cliente)
        self._add_viaje_form_row(left_form, "carta_porte", carta_porte)
        self._add_viaje_form_row(left_form, "carga", carga)
        self._add_viaje_form_row(left_form, "lugar_carga", lugar_carga)
        self._add_viaje_form_row(left_form, "lugar_descarga", lugar_descarga)
        self._add_viaje_form_row(left_form, "observaciones", observaciones)
        self._add_viaje_form_row(left_form, "chofer", chofer)
        self._add_viaje_form_row(left_form, "tipo_carga", tipo_carga)

        self._add_viaje_form_row(right_form, "camion", camion)
        self._add_viaje_form_row(right_form, "semi", semi)
        self._add_viaje_form_row(right_form, "tarifa", tarifa)
        self._add_viaje_form_row(right_form, "fecha_descarga_tarifa", fecha_descarga_tarifa)
        self._add_viaje_form_row(right_form, "demora", demora)
        self._add_viaje_form_row(right_form, "fecha_descarga_demora", fecha_descarga_demora)
        self._add_viaje_form_row(right_form, "vacio", vacio)
        self._add_viaje_form_row(right_form, "fecha_descarga_vacio", fecha_descarga_vacio)
        self._add_viaje_form_row(right_form, "gas_oil_lts", gas_oil_lts)
        self._add_viaje_form_row(right_form, "peaje_empresa", peaje_empresa)
        self._add_viaje_form_row(right_form, "peajes", peajes)

        form_grid.addLayout(left_form, 0, 0)
        form_grid.addLayout(right_form, 0, 1)
        panel_layout.addLayout(form_grid)

        scroll = QScrollArea()
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setWidgetResizable(True)
        scroll.setWidget(panel)

        layout.addWidget(scroll, stretch=1)
        self._refresh_peaje_checklist()
        self._apply_viaje_field_visibility()
        return tab

    def _build_history_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(20)

        layout.addWidget(self._build_monthly_billing_panel())
        layout.addWidget(self._build_table_panel(), stretch=1)
        return tab

    def _add_viaje_form_row(
        self,
        form: QFormLayout,
        field_key: str,
        widget: QWidget,
    ) -> None:
        form.addRow(VIAJE_FORM_LABELS[field_key], widget)
        label = form.labelForField(widget)
        if label is not None:
            self.viaje_form_row_labels[field_key] = label

    def _build_clients_tab(self) -> QWidget:
        return self._build_static_table_tab(
            "Clientes",
            [
                "Nombre",
                "CUIT",
                "Email",
                "Contacto",
                "Es directo",
                "Intermediario",
            ],
            self._cliente_rows(),
            create_callback=self._create_cliente,
            edit_callback=self._edit_cliente,
            delete_callback=self._delete_cliente,
            extra_actions=[
                ("Configurar campos carga", self._configure_cliente_viaje_fields)
            ],
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
        tab = QWidget()
        layout = QHBoxLayout(tab)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        empresas_panel = self._build_readonly_table_panel(
            "Peajes",
            ["Empresa"],
            self._peaje_rows(),
            create_callback=self._create_peaje_empresa,
            edit_callback=self._edit_peaje_empresa,
            delete_callback=self._delete_peaje_empresa,
            extra_actions=[("Ver peajes", self._show_selected_empresa_peajes)],
            create_label="Añadir",
            edit_label="Editar",
            delete_label="Eliminar",
            action_order=("create", "delete", "edit", "extra"),
        )
        empresas_table = self.object_tables.get("Peajes")
        if empresas_table is not None:
            empresas_table.itemDoubleClicked.connect(
                lambda _item: self._show_selected_empresa_peajes()
            )

        layout.addWidget(empresas_panel, stretch=3)
        layout.addWidget(self._build_peajes_detail_panel(), stretch=2)
        return tab

    def _build_peajes_detail_panel(self) -> QFrame:
        panel = QFrame()
        panel.setObjectName("panel")
        panel.setVisible(False)
        panel.setMinimumWidth(380)
        self.peajes_detail_panel = panel

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        header = QFrame()
        header.setObjectName("panelHeader")
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(16, 8, 16, 8)
        header_layout.setSpacing(8)
        title = QLabel("Peajes")
        title.setObjectName("sectionTitle")
        self.peajes_detail_title = title
        header_layout.addWidget(title)

        for row_actions in (
            (
                ("Cerrar lista", self._close_empresa_peajes, ""),
                ("Actualizar varios peajes", self._bulk_update_peajes, ""),
            ),
            (
                ("Editar peaje", self._edit_peaje, ""),
                ("Eliminar peaje", self._delete_peaje, "dangerButton"),
                ("Nuevo peaje", self._create_peaje, "primaryButton"),
            ),
        ):
            button_row = QHBoxLayout()
            button_row.setContentsMargins(0, 0, 0, 0)
            button_row.setSpacing(8)
            for label, callback, object_name in row_actions:
                button = QPushButton(label)
                if object_name:
                    button.setObjectName(object_name)
                button.clicked.connect(callback)
                button_row.addWidget(button)
            button_row.addStretch()
            header_layout.addLayout(button_row)

        table = QTableWidget(0, 4)
        table.setHorizontalHeaderLabels(["ID", "Nombre", "Direccion", "Costo"])
        table.verticalHeader().setVisible(False)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        table.setAlternatingRowColors(True)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.setSelectionMode(QTableWidget.SelectionMode.ExtendedSelection)
        self.peajes_detail_table = table

        layout.addWidget(header)
        layout.addWidget(table, stretch=1)
        return panel

    def _build_statistics_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(20)

        layout.addLayout(self._build_metrics())
        layout.addStretch()
        return tab

    def _build_print_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(20)

        layout.addWidget(self._build_print_controls_panel())
        layout.addWidget(self._build_print_preview_panel(), stretch=1)
        return tab

    def _build_print_controls_panel(self) -> QWidget:
        panel = QFrame()
        panel.setObjectName("panel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(14)

        title = QLabel("Reporte mensual")
        title.setObjectName("sectionTitle")
        description = QLabel(
            "Selecciona un mes y exporta la vista mensual base en Excel o PDF."
        )
        description.setObjectName("muted")
        description.setWordWrap(True)

        controls_layout = QVBoxLayout()
        controls_layout.setSpacing(12)

        top_controls = QHBoxLayout()
        top_controls.setSpacing(12)

        bottom_controls = QHBoxLayout()
        bottom_controls.setSpacing(12)

        current_date = QDate.currentDate()
        mode_combo = self._build_combo(
            [
                ("Mensual", "monthly"),
                ("Anual", "annual"),
                ("Cliente Ricco", "ricco"),
            ]
        )
        mode_combo.currentIndexChanged.connect(self._refresh_print_mode_ui)
        mode_combo.currentIndexChanged.connect(self._refresh_print_report)
        self.print_mode_combo = mode_combo
        mode_card = self._build_billing_filter_card("Modo", mode_combo)
        self.print_mode_card = mode_card
        top_controls.addWidget(mode_card)

        month_combo = self._build_combo(
            [
                (month_name, month_number)
                for month_number, month_name in enumerate(MONTH_NAMES, start=1)
            ]
        )
        month_combo.setCurrentIndex(current_date.month() - 1)
        month_combo.currentIndexChanged.connect(self._refresh_print_report)
        self.print_month_combo = month_combo

        years = {
            year
            for year in self.viaje_repository.billing_years()
            if year <= current_date.year()
        }
        years.update(range(current_date.year() - 1, current_date.year() + 1))
        year_combo = self._build_combo([(str(year), year) for year in sorted(years)])
        year_index = year_combo.findData(current_date.year())
        if year_index >= 0:
            year_combo.setCurrentIndex(year_index)
        year_combo.currentIndexChanged.connect(self._refresh_print_report)
        self.print_year_combo = year_combo

        month_card = self._build_billing_filter_card("Mes", month_combo)
        year_card = self._build_billing_filter_card("Año", year_combo)
        self.print_month_card = month_card
        self.print_year_card = year_card
        top_controls.addWidget(month_card)
        top_controls.addWidget(year_card)

        from_date = QDateEdit()
        from_date.setCalendarPopup(True)
        from_date.setDisplayFormat("yyyy-MM-dd")
        from_date.setDate(QDate(current_date.year(), current_date.month(), 1))
        from_date.dateChanged.connect(self._refresh_print_report)
        self.print_from_date = from_date
        from_card = self._build_billing_filter_card("Desde", from_date)
        self.print_from_card = from_card
        top_controls.addWidget(from_card)

        to_date = QDateEdit()
        to_date.setCalendarPopup(True)
        to_date.setDisplayFormat("yyyy-MM-dd")
        to_date.setDate(
            QDate(current_date.year(), current_date.month(), current_date.daysInMonth())
        )
        to_date.dateChanged.connect(self._refresh_print_report)
        self.print_to_date = to_date
        to_card = self._build_billing_filter_card("Hasta", to_date)
        self.print_to_card = to_card
        top_controls.addWidget(to_card)
        top_controls.addStretch()

        count_card = MetricCard("Viajes del periodo", "0")
        count_card.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        self.print_count_card = count_card
        bottom_controls.addWidget(count_card)

        total_card = MetricCard("Total del periodo", "$ 0")
        total_card.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        self.print_total_card = total_card
        bottom_controls.addWidget(total_card)
        bottom_controls.addStretch()

        export_excel_button = QPushButton("Exportar Excel")
        export_excel_button.setObjectName("primaryButton")
        export_excel_button.setCursor(Qt.CursorShape.PointingHandCursor)
        export_excel_button.clicked.connect(self._export_print_excel)

        export_pdf_button = QPushButton("Exportar PDF")
        export_pdf_button.setCursor(Qt.CursorShape.PointingHandCursor)
        export_pdf_button.clicked.connect(self._export_print_pdf)

        bottom_controls.addWidget(export_excel_button)
        bottom_controls.addWidget(export_pdf_button)

        layout.addWidget(title)
        layout.addWidget(description)
        controls_layout.addLayout(top_controls)
        controls_layout.addLayout(bottom_controls)
        layout.addLayout(controls_layout)
        self._refresh_print_mode_ui()
        return panel

    def _build_print_preview_panel(self) -> QWidget:
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
        header_title = QLabel("Vista previa mensual")
        header_title.setObjectName("sectionTitle")
        header_layout.addWidget(header_title)
        header_layout.addStretch()

        table = QTableWidget(0, 15)
        table.setHorizontalHeaderLabels(
            [
                "Fecha",
                "Cliente",
                "N° Carta de Porte",
                "Carga",
                "Lugar carga",
                "Lugar descarga",
                "Chofer",
                "Camion",
                "Tarifa",
                "Demora",
                "Vacio",
                "Gas oil (lts)",
                "Peajes",
                "Total",
                "Estado",
            ]
        )
        table.verticalHeader().setVisible(False)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        table.setAlternatingRowColors(True)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.print_table = table

        layout.addWidget(header)
        layout.addWidget(table, stretch=1)
        self._refresh_print_report()
        return panel

    def _build_options_tab(self) -> QWidget:
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(20)

        layout.addWidget(
            self._build_readonly_table_panel(
                "Opciones",
                ["Opcion", "Valor"],
                self._options_rows(),
                show_actions=False,
            )
        )
        layout.addWidget(self._build_company_settings_panel())
        layout.addWidget(self._build_updates_panel())
        layout.addWidget(self._build_database_tools_panel())
        layout.addStretch()

        scroll = QScrollArea()
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setWidgetResizable(True)
        scroll.setWidget(content)
        return scroll

    def _options_rows(self) -> list[tuple[int, list[str]]]:
        return [
            (1, ["Base de datos", str(self.database_path)]),
            (2, ["Empresa", self.company_name]),
            (3, ["Actualizaciones", "GitHub Releases"]),
            (4, ["Modo", "Cliente sin servidor"]),
        ]

    def _save_company_name(self) -> None:
        if self.company_name_input is None:
            return
        company_name = normalize_company_name(self.company_name_input.text())
        self.company_name = company_name
        self.app_settings["company_name"] = company_name
        save_app_settings(self.settings_path, self.app_settings)
        self.company_name_input.setText(company_name)
        self._refresh_object_table("Opciones")
        QMessageBox.information(self, "Empresa", "Nombre de empresa guardado.")

    def _build_company_settings_panel(self) -> QWidget:
        panel = QFrame()
        panel.setObjectName("panel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        title = QLabel("Empresa")
        title.setObjectName("sectionTitle")
        description = QLabel(
            "Nombre usado para exportaciones, plantilla Ricco y nombre de archivo."
        )
        description.setObjectName("muted")
        description.setWordWrap(True)

        controls = QHBoxLayout()
        controls.setSpacing(12)

        company_name_input = QLineEdit()
        company_name_input.setText(self.company_name)
        company_name_input.setPlaceholderText("Nombre de la empresa")
        self.company_name_input = company_name_input

        save_button = QPushButton("Guardar nombre")
        save_button.setObjectName("primaryButton")
        save_button.setCursor(Qt.CursorShape.PointingHandCursor)
        save_button.clicked.connect(self._save_company_name)

        controls.addWidget(company_name_input, stretch=1)
        controls.addWidget(save_button)

        layout.addWidget(title)
        layout.addWidget(description)
        layout.addLayout(controls)
        return panel

    def _build_database_tools_panel(self) -> QWidget:
        panel = QFrame()
        panel.setObjectName("panel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        title = QLabel("Base de datos")
        title.setObjectName("sectionTitle")
        description = QLabel(
            "Borra viajes, clientes, lugares, choferes, vehiculos, peajes y tipos de carga."
        )
        description.setObjectName("muted")
        description.setWordWrap(True)

        clear_button = QPushButton("Vaciar base de datos")
        clear_button.setObjectName("dangerButton")
        clear_button.setCursor(Qt.CursorShape.PointingHandCursor)
        clear_button.clicked.connect(self._clear_database_with_confirmation)

        layout.addWidget(title)
        layout.addWidget(description)
        layout.addWidget(clear_button, alignment=Qt.AlignmentFlag.AlignLeft)
        return panel

    def _build_updates_panel(self) -> QWidget:
        panel = QFrame()
        panel.setObjectName("panel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        title = QLabel("Actualizaciones")
        title.setObjectName("sectionTitle")
        description = QLabel(
            "La app descarga el paquete correcto desde GitHub y guarda un backup local "
            "antes de abrir el instalador."
        )
        description.setObjectName("muted")
        description.setWordWrap(True)

        check_button = QPushButton("Buscar actualizaciones ahora")
        check_button.setObjectName("primaryButton")
        check_button.setCursor(Qt.CursorShape.PointingHandCursor)
        check_button.clicked.connect(lambda: self._start_update_check(interactive=True))

        layout.addWidget(title)
        layout.addWidget(description)
        layout.addWidget(check_button, alignment=Qt.AlignmentFlag.AlignLeft)
        return panel


    def _cliente_rows(self) -> list[tuple[int, list[str]]]:
        return [
            (
                item.id,
                [
                    item.etiqueta,
                    item.cuit,
                    item.email,
                    item.numero_contacto,
                    "Si" if item.es_cliente_directo else "No",
                    item.cliente_padre_nombre,
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
            (item.id, [item.nombre])
            for item in self.peaje_repository.list_empresas()
        ]

    def _peajes_detail_rows(self, empresa_id: int) -> list[tuple[int, list[str]]]:
        return [
            (item.id, [item.nombre, item.direccion, _format_money(item.costo)])
            for item in self.peaje_repository.list_all(empresa_id=empresa_id)
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
        extra_actions: list[tuple[str, Callable[[], None]]] | None = None,
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
            extra_actions=extra_actions,
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
        extra_actions: list[tuple[str, Callable[[], None]]] | None = None,
        create_label: str = "Crear",
        edit_label: str = "Editar",
        delete_label: str = "Eliminar",
        action_order: tuple[str, ...] = ("create", "edit", "delete", "extra"),
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
                    extra_actions=extra_actions,
                    create_label=create_label,
                    edit_label=edit_label,
                    delete_label=delete_label,
                    action_order=action_order,
                )
            )

        table = QTableWidget(len(rows), len(headers) + 1)
        table.setHorizontalHeaderLabels(["ID", *headers])
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

    def _populate_table_rows(
        self,
        table: QTableWidget,
        rows: list[tuple[int, list[str]]],
    ) -> None:
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
            "Opciones": self._options_rows,
        }
        loader = loaders.get(title)
        if loader is not None:
            self._populate_object_table(title, loader())
        if title == "Peajes":
            self._refresh_peajes_detail_table()

    def _show_selected_empresa_peajes(self) -> None:
        empresa_id = self._selected_object_id("Peajes")
        if empresa_id is None:
            return

        empresa = self._find_by_id(self.peaje_repository.list_empresas(), empresa_id)
        self.selected_peaje_empresa_id = empresa_id
        if self.peajes_detail_title is not None:
            empresa_nombre = getattr(empresa, "nombre", f"Empresa {empresa_id}")
            self.peajes_detail_title.setText(f"Peajes - {empresa_nombre}")
        if self.peajes_detail_panel is not None:
            self.peajes_detail_panel.setVisible(True)
        self._refresh_peajes_detail_table()

    def _close_empresa_peajes(self) -> None:
        self.selected_peaje_empresa_id = None
        if self.peajes_detail_panel is not None:
            self.peajes_detail_panel.setVisible(False)

    def _refresh_peajes_detail_table(self) -> None:
        if self.peajes_detail_table is None or self.selected_peaje_empresa_id is None:
            return
        self._populate_table_rows(
            self.peajes_detail_table,
            self._peajes_detail_rows(self.selected_peaje_empresa_id),
        )

    def _check_updates_on_startup(self) -> None:
        self._start_update_check(interactive=False)

    def _start_update_check(self, *, interactive: bool) -> None:
        if self.update_check_in_progress:
            if interactive:
                QMessageBox.information(
                    self,
                    "Actualizaciones",
                    "Ya hay una comprobacion de actualizaciones en curso.",
                )
            return

        self.update_check_in_progress = True
        Thread(
            target=self._run_update_check,
            args=(interactive,),
            daemon=True,
        ).start()

    def _run_update_check(self, interactive: bool) -> None:
        try:
            release = check_latest_release(
                GITHUB_OWNER,
                GITHUB_REPO,
                __version__,
            )
        except UpdateCheckError as exc:
            self.update_signals.failed.emit(str(exc), interactive)
            return
        except Exception as exc:
            self.update_signals.failed.emit(str(exc), interactive)
            return

        self.update_signals.finished.emit(release, interactive)

    def _handle_update_check_finished(
        self,
        release: object,
        interactive: bool,
    ) -> None:
        self.update_check_in_progress = False

        if release is None:
            if interactive:
                QMessageBox.information(
                    self,
                    "Actualizaciones",
                    "Esta instalacion ya esta en la ultima version publicada.",
                )
            return

        if not isinstance(release, ReleaseInfo):
            return

        preferred_asset = self._preferred_release_asset(release)
        message = QMessageBox(self)
        message.setIcon(QMessageBox.Icon.Information)
        message.setWindowTitle("Actualizacion disponible")
        message.setText(f"Hay una version nueva disponible: {release.version}")
        if preferred_asset is None:
            message.setInformativeText(
                "No se encontro un paquete automatico para este sistema. "
                "Podes ver la release completa."
            )
        else:
            size_mb = preferred_asset.size / (1024 * 1024) if preferred_asset.size else 0
            size_label = f" ({size_mb:.1f} MB)" if size_mb else ""
            message.setInformativeText(
                f"Paquete recomendado: {preferred_asset.name}{size_label}.\n"
                "Antes de instalar se crea un backup de la base local."
            )
        if release.notes.strip():
            message.setDetailedText(release.notes.strip())

        update_button = None
        if preferred_asset is not None:
            update_button = message.addButton(
                "Descargar e instalar",
                QMessageBox.ButtonRole.AcceptRole,
            )
        release_button = message.addButton("Ver release", QMessageBox.ButtonRole.ActionRole)
        later_button = message.addButton("Mas tarde", QMessageBox.ButtonRole.RejectRole)
        if update_button is not None:
            message.setDefaultButton(update_button)
        message.exec()

        clicked = message.clickedButton()
        if clicked == update_button and preferred_asset is not None:
            self._start_update_download(release, preferred_asset)
        elif clicked == release_button:
            QDesktopServices.openUrl(QUrl(release.html_url))
        elif clicked == later_button:
            return

    def _handle_update_check_failed(self, error_message: str, interactive: bool) -> None:
        self.update_check_in_progress = False
        if interactive:
            QMessageBox.warning(
                self,
                "Actualizaciones",
                f"No se pudo comprobar si hay una version nueva.\n{error_message}",
            )

    def _start_update_download(self, release: ReleaseInfo, asset: ReleaseAsset) -> None:
        if self.update_download_in_progress:
            QMessageBox.information(
                self,
                "Actualizaciones",
                "Ya hay una descarga de actualizacion en curso.",
            )
            return

        self.update_download_in_progress = True
        self.update_progress_dialog = QProgressDialog(
            "Preparando actualizacion...",
            "",
            0,
            100,
            self,
        )
        self.update_progress_dialog.setCancelButton(None)
        self.update_progress_dialog.setWindowTitle("Actualizando")
        self.update_progress_dialog.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.update_progress_dialog.setMinimumDuration(0)
        self.update_progress_dialog.setValue(0)

        Thread(
            target=self._run_update_download,
            args=(release, asset),
            daemon=True,
        ).start()

    def _run_update_download(self, release: ReleaseInfo, asset: ReleaseAsset) -> None:
        try:
            app_data_dir = get_app_data_dir()
            backup_path = create_database_backup(
                self.database_path,
                backups_dir(app_data_dir),
            )
            checksum_asset = select_checksum_asset(release, asset)
            if checksum_asset is None:
                raise UpdateDownloadError(
                    "La release no incluye el archivo de checksum requerido para este paquete."
                )
            package_path = download_release_asset(
                asset,
                updates_dir(app_data_dir) / release.version,
                checksum_asset=checksum_asset,
                progress_callback=self.update_signals.download_progress.emit,
            )
        except (UpdateDownloadError, OSError) as exc:
            self.update_signals.download_failed.emit(str(exc))
            return
        except Exception as exc:
            self.update_signals.download_failed.emit(str(exc))
            return

        self.update_signals.download_finished.emit(package_path, backup_path, asset)

    def _handle_update_download_progress(self, downloaded: int, total_size: int) -> None:
        if self.update_progress_dialog is None:
            return

        if total_size > 0:
            self.update_progress_dialog.setRange(0, total_size)
            self.update_progress_dialog.setValue(min(downloaded, total_size))
            downloaded_mb = downloaded / (1024 * 1024)
            total_mb = total_size / (1024 * 1024)
            self.update_progress_dialog.setLabelText(
                f"Descargando actualizacion... {downloaded_mb:.1f} de {total_mb:.1f} MB"
            )
        else:
            self.update_progress_dialog.setRange(0, 0)
            self.update_progress_dialog.setLabelText("Descargando actualizacion...")

    def _handle_update_download_finished(
        self,
        package_path: object,
        backup_path: object,
        asset: object,
    ) -> None:
        self.update_download_in_progress = False
        if self.update_progress_dialog is not None:
            self.update_progress_dialog.close()
            self.update_progress_dialog = None

        if not isinstance(package_path, Path) or not isinstance(backup_path, Path):
            QMessageBox.warning(
                self,
                "Actualizaciones",
                "La actualizacion se descargo, pero no se pudo abrir el paquete.",
            )
            return

        asset_name = asset.name if isinstance(asset, ReleaseAsset) else package_path.name
        message = QMessageBox(self)
        message.setIcon(QMessageBox.Icon.Information)
        message.setWindowTitle("Actualizacion descargada")
        message.setText("La actualizacion se descargo correctamente.")
        message.setInformativeText(
            f"Paquete: {asset_name}\n"
            f"Backup de base local: {backup_path}\n\n"
            "La app se cerrara para reemplazar los archivos. La base de datos queda "
            "en la carpeta de datos del usuario y no se reemplaza por el instalador."
        )
        install_button = message.addButton("Instalar ahora", QMessageBox.ButtonRole.AcceptRole)
        open_button = message.addButton("Abrir paquete", QMessageBox.ButtonRole.ActionRole)
        folder_button = message.addButton("Ver carpeta", QMessageBox.ButtonRole.ActionRole)
        message.addButton("Cerrar", QMessageBox.ButtonRole.RejectRole)
        message.setDefaultButton(install_button)
        message.exec()

        clicked = message.clickedButton()
        if clicked == install_button:
            self._install_downloaded_update(package_path)
        elif clicked == open_button:
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(package_path)))
        elif clicked == folder_button:
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(package_path.parent)))

    def _install_downloaded_update(self, package_path: Path) -> None:
        try:
            script_path = launch_update_installer(package_path, get_app_data_dir())
        except UpdateInstallError as exc:
            QMessageBox.warning(
                self,
                "Instalacion automatica",
                f"No se pudo preparar la instalacion automatica.\n{exc}",
            )
            return
        except OSError as exc:
            QMessageBox.warning(
                self,
                "Instalacion automatica",
                f"No se pudo iniciar el instalador automatico.\n{exc}",
            )
            return

        QMessageBox.information(
            self,
            "Instalacion automatica",
            "La app se cerrara para instalar la actualizacion y volver a abrirse.\n"
            f"Registro tecnico: {script_path}",
        )
        app = QApplication.instance()
        if app is not None:
            app.quit()

    def _handle_update_download_failed(self, error_message: str) -> None:
        self.update_download_in_progress = False
        if self.update_progress_dialog is not None:
            self.update_progress_dialog.close()
            self.update_progress_dialog = None
        QMessageBox.critical(
            self,
            "Actualizaciones",
            f"No se pudo descargar la actualizacion.\n{error_message}",
        )

    def _preferred_release_asset(self, release: ReleaseInfo) -> ReleaseAsset | None:
        return select_release_asset(
            release,
            system=platform.system(),
            machine=platform.machine(),
        )

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

    def _selected_peaje_id(self) -> int | None:
        table = self.peajes_detail_table
        if table is None:
            return None

        row = table.currentRow()
        if row < 0:
            QMessageBox.warning(
                self,
                "Seleccion requerida",
                "Selecciona un peaje primero.",
            )
            return None

        item = table.item(row, 0)
        return None if item is None else int(item.text())

    def _selected_peaje_ids(self) -> tuple[int, ...]:
        table = self.peajes_detail_table
        if table is None:
            return ()

        rows = sorted({index.row() for index in table.selectedIndexes()})
        peaje_ids: list[int] = []
        for row in rows:
            item = table.item(row, 0)
            if item is not None:
                peaje_ids.append(int(item.text()))
        return tuple(peaje_ids)

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

    def _build_monthly_billing_panel(self) -> QWidget:
        panel = QFrame()
        panel.setObjectName("panel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(16, 14, 16, 16)
        layout.setSpacing(12)

        header = QHBoxLayout()
        title = QLabel("Facturacion meses")
        title.setObjectName("sectionTitle")
        header.addWidget(title)
        total_card = MetricCard("Facturacion anual", "$ 0")
        total_card.setSizePolicy(
            QSizePolicy.Policy.Minimum,
            QSizePolicy.Policy.Fixed,
        )
        self.billing_total_card = total_card
        header.addWidget(total_card)
        toggle_button = QPushButton("Contraer")
        toggle_button.clicked.connect(self._toggle_billing_panel)
        self.billing_toggle_button = toggle_button
        header.addWidget(toggle_button)
        header.addStretch()
        layout.addLayout(header)

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(12)
        self.billing_content_widget = content

        current_date = QDate.currentDate()
        month_combo = QComboBox()
        self.billing_month_combo = month_combo

        years = {
            year
            for year in self.viaje_repository.billing_years()
            if year <= current_date.year()
        }
        years.update(range(current_date.year() - 1, current_date.year() + 1))
        year_combo = self._build_combo([(str(year), year) for year in sorted(years)])
        year_index = year_combo.findData(current_date.year())
        if year_index >= 0:
            year_combo.setCurrentIndex(year_index)
        self.billing_year_combo = year_combo

        self._set_billing_month_options(current_date.month())
        month_combo.currentIndexChanged.connect(self._refresh_billing_months)
        year_combo.currentIndexChanged.connect(self._billing_year_changed)

        header.addWidget(self._build_billing_filter_card("Mes final", month_combo))
        header.addWidget(self._build_billing_filter_card("Año", year_combo))

        month_grid = QGridLayout()
        month_grid.setSpacing(10)
        self.billing_month_cards = []
        for index in range(12):
            card = MetricCard("", "$ 0")
            self.billing_month_cards.append(card)
            month_grid.addWidget(card, index // 6, index % 6)
        content_layout.addLayout(month_grid)
        layout.addWidget(content)

        self._refresh_billing_months()
        return panel

    def _build_billing_filter_card(self, label: str, control: QWidget) -> QFrame:
        card = QFrame()
        card.setObjectName("metric")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(8)

        label_widget = QLabel(label)
        label_widget.setObjectName("muted")
        layout.addWidget(label_widget)
        layout.addWidget(control)
        return card

    def _toggle_billing_panel(self) -> None:
        self.billing_panel_expanded = not self.billing_panel_expanded
        if self.billing_content_widget is not None:
            self.billing_content_widget.setVisible(self.billing_panel_expanded)
        if self.billing_toggle_button is not None:
            self.billing_toggle_button.setText(
                "Contraer" if self.billing_panel_expanded else "Expandir"
            )

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

        self.table = QTableWidget(0, 23)
        self.table.setHorizontalHeaderLabels(
            [
                "ID",
                "Fecha",
                "Cliente",
                "Es directo",
                "N° Carta de Porte",
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
                "Gas oil (lts)",
                "Peajes $",
                "Costo total $",
                "Estado",
            ]
        )
        self.table.setColumnHidden(22, True)
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
        self._refresh_billing_months()
        self._refresh_print_report()

    def _viaje_to_row(self, viaje: ViajeResumen) -> list[str]:
        return [
            str(viaje.id),
            viaje.fecha,
            viaje.cliente,
            "Si" if bool(viaje.cliente_es_directo) else "No",
            viaje.carta_porte,
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
            _format_decimal(viaje.gas_oil_lts),
            _format_money(viaje.peajes),
            _format_money(viaje.costo_total),
            viaje.estado,
        ]

    def _build_crud_actions(
        self,
        section_label: str,
        *,
        create_callback: Callable[[], None] | None = None,
        edit_callback: Callable[[], None] | None = None,
        delete_callback: Callable[[], None] | None = None,
        extra_actions: list[tuple[str, Callable[[], None]]] | None = None,
        create_label: str = "Crear",
        edit_label: str = "Editar",
        delete_label: str = "Eliminar",
        action_order: tuple[str, ...] = ("create", "edit", "delete", "extra"),
    ) -> QWidget:
        actions = QWidget()
        actions.setObjectName("actionButtons")
        layout = QHBoxLayout(actions)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        create_button = QPushButton(create_label)
        create_button.setObjectName("primaryButton")
        create_button.clicked.connect(
            create_callback
            if create_callback is not None
            else lambda: self._show_pending_action(section_label, "Crear")
        )

        edit_button = QPushButton(edit_label)
        edit_button.clicked.connect(
            edit_callback
            if edit_callback is not None
            else lambda: self._show_pending_action(section_label, "Editar")
        )

        delete_button = QPushButton(delete_label)
        delete_button.setObjectName("dangerButton")
        delete_button.clicked.connect(
            delete_callback
            if delete_callback is not None
            else lambda: self._show_pending_action(section_label, "Eliminar")
        )

        buttons_by_name = {
            "create": [create_button],
            "edit": [edit_button],
            "delete": [delete_button],
            "extra": [],
        }
        for label, callback in extra_actions or []:
            button = QPushButton(label)
            button.clicked.connect(callback)
            buttons_by_name["extra"].append(button)
        for group_name in action_order:
            for button in buttons_by_name.get(group_name, []):
                layout.addWidget(button)
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
            and dialog.is_field_visible(str(field["key"]))
            and self._is_empty_record_value(values.get(str(field["key"])))
        ]
        if missing:
            QMessageBox.warning(
                self,
                "Datos incompletos",
                "Completa los campos obligatorios: " + ", ".join(missing),
            )
            return None
        return values

    def _is_empty_record_value(self, value: object) -> bool:
        if value is None:
            return True
        if isinstance(value, str):
            return not value.strip()
        if isinstance(value, tuple | list | set):
            return len(value) == 0
        return False

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

    def _run_silent_data_action(self, callback: Callable[[], None]) -> None:
        try:
            callback()
        except Exception as exc:
            QMessageBox.critical(self, "Error", f"No se pudo completar la accion.\n{exc}")

    def _create_cliente(self) -> None:
        values = self._record_values("Crear cliente", self._cliente_fields())
        if values is None:
            return

        def save() -> None:
            self.cliente_repository.create(
                nombre=str(values["nombre"]).strip(),
                cuit=str(values["cuit"]).strip(),
                email=str(values["email"]).strip(),
                numero_contacto=str(values["numero_contacto"]).strip(),
                es_cliente_directo=bool(int(values["es_cliente_directo"])),
                cliente_padre_id=self._optional_int(values["cliente_padre_id"]),
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
                    "cuit": cliente.cuit,
                    "email": cliente.email,
                    "numero_contacto": cliente.numero_contacto,
                    "es_cliente_directo": 1 if cliente.es_cliente_directo else 0,
                    "cliente_padre_id": cliente.cliente_padre_id or "",
                    "current_cliente_id": cliente.id,
                }
            ),
        )
        if values is None:
            return

        def save() -> None:
            self.cliente_repository.update(
                cliente_id,
                nombre=str(values["nombre"]).strip(),
                cuit=str(values["cuit"]).strip(),
                email=str(values["email"]).strip(),
                numero_contacto=str(values["numero_contacto"]).strip(),
                es_cliente_directo=bool(int(values["es_cliente_directo"])),
                cliente_padre_id=self._optional_int(values["cliente_padre_id"]),
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

    def _configure_cliente_viaje_fields(self) -> None:
        cliente_id = self._selected_object_id("Clientes")
        if cliente_id is None:
            return

        cliente = self._find_by_id(self.cliente_repository.list_all(), cliente_id)
        cliente_label = getattr(cliente, "etiqueta", f"Cliente {cliente_id}")
        enabled_fields = self._enabled_viaje_field_keys(cliente_id)

        dialog = QDialog(self)
        dialog.setWindowTitle("Configurar campos carga")
        layout = QVBoxLayout(dialog)
        layout.setSpacing(12)

        title = QLabel(f"Campos visibles para {cliente_label}")
        title.setObjectName("sectionTitle")
        layout.addWidget(title)

        checkbox_widgets: dict[str, QCheckBox] = {}
        for field_key in VIAJE_CONFIGURABLE_FIELD_KEYS:
            checkbox = QCheckBox(VIAJE_FORM_LABELS[field_key])
            checkbox.setChecked(field_key in enabled_fields)
            checkbox_widgets[field_key] = checkbox
            layout.addWidget(checkbox)

        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        selected_fields = [
            field_key
            for field_key, checkbox in checkbox_widgets.items()
            if checkbox.isChecked()
        ]
        self._set_cliente_viaje_fields(cliente_id, selected_fields)
        self._apply_viaje_field_visibility()
        QMessageBox.information(
            self,
            "Campos carga",
            "Configuracion guardada para el cliente seleccionado.",
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

    def _create_peaje_empresa(self) -> None:
        values = self._record_values(
            "Crear empresa de peajes",
            self._peaje_empresa_fields(),
        )
        if values is None:
            return

        def save() -> None:
            self.peaje_repository.create_empresa(
                nombre=str(values["nombre"]).strip(),
            )
            self._refresh_object_table("Peajes")

        self._run_data_action("Empresa de peajes creada.", save)

    def _edit_peaje_empresa(self) -> None:
        empresa_id = self._selected_object_id("Peajes")
        if empresa_id is None:
            return
        empresa = self._find_by_id(self.peaje_repository.list_empresas(), empresa_id)
        if empresa is None:
            return
        values = self._record_values(
            "Editar empresa de peajes",
            self._peaje_empresa_fields({"nombre": empresa.nombre}),
        )
        if values is None:
            return

        def save() -> None:
            self.peaje_repository.update_empresa(
                empresa_id,
                nombre=str(values["nombre"]).strip(),
            )
            self._refresh_object_table("Peajes")
            self._refresh_viaje_form_options()

        self._run_data_action("Empresa de peajes actualizada.", save)

    def _delete_peaje_empresa(self) -> None:
        empresa_id = self._selected_object_id("Peajes")
        if empresa_id is None or not self._confirm_delete("empresa de peajes"):
            return

        def delete_and_refresh() -> None:
            self.peaje_repository.delete_empresa(empresa_id)
            if self.selected_peaje_empresa_id == empresa_id:
                self._close_empresa_peajes()
            self._refresh_object_table("Peajes")
            self._refresh_table()
            self._refresh_viaje_form_options()

        self._run_silent_data_action(delete_and_refresh)

    def _create_peaje(self) -> None:
        if self.selected_peaje_empresa_id is None:
            QMessageBox.warning(
                self,
                "Seleccion requerida",
                "Selecciona una empresa y abre su lista de peajes primero.",
            )
            return
        values = self._record_values("Crear peaje", self._peaje_fields())
        if values is None:
            return

        def save() -> None:
            self.peaje_repository.create(
                empresa_id=self.selected_peaje_empresa_id or 0,
                nombre=str(values["nombre"]).strip(),
                direccion=str(values["direccion"]).strip(),
                costo=float(values["costo"]),
            )
            self._refresh_peajes_detail_table()
            self._refresh_viaje_form_options()

        self._run_data_action("Peaje creado.", save)

    def _edit_peaje(self) -> None:
        peaje_id = self._selected_peaje_id()
        if peaje_id is None or self.selected_peaje_empresa_id is None:
            return
        peaje = self._find_by_id(
            self.peaje_repository.list_all(empresa_id=self.selected_peaje_empresa_id),
            peaje_id,
        )
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
                empresa_id=self.selected_peaje_empresa_id or 0,
                nombre=str(values["nombre"]).strip(),
                direccion=str(values["direccion"]).strip(),
                costo=float(values["costo"]),
            )
            self._refresh_peajes_detail_table()
            self._refresh_table()
            self._refresh_viaje_form_options()

        self._run_data_action("Peaje actualizado.", save)

    def _delete_peaje(self) -> None:
        peaje_id = self._selected_peaje_id()
        if peaje_id is not None:
            self._soft_delete_object(
                "peaje",
                lambda: self.peaje_repository.delete(peaje_id),
                self._refresh_peajes_detail_table,
            )

    def _bulk_update_peajes(self) -> None:
        peaje_ids = self._selected_peaje_ids()
        if not peaje_ids:
            QMessageBox.warning(
                self,
                "Seleccion requerida",
                "Selecciona uno o mas peajes primero.",
            )
            return

        values = self._record_values(
            "Actualizar varios peajes",
            [
                {
                    "key": "costo",
                    "label": "Nuevo costo",
                    "type": "money",
                    "value": 0,
                }
            ],
        )
        if values is None:
            return

        def save() -> None:
            self.peaje_repository.update_cost_many(
                peaje_ids,
                costo=float(values["costo"]),
            )
            self._refresh_peajes_detail_table()
            self._refresh_table()
            self._refresh_viaje_form_options()

        self._run_data_action("Peajes actualizados.", save)

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
                carta_porte=str(values["carta_porte"]).strip(),
                observaciones=str(values["observaciones"]).strip(),
                tarifa=float(values["tarifa"]),
                fecha_descarga_tarifa=str(values["fecha_descarga_tarifa"]),
                demora=float(values["demora"]),
                fecha_descarga_demora=str(values["fecha_descarga_demora"]),
                vacio=float(values["vacio"]),
                fecha_descarga_vacio=str(values["fecha_descarga_vacio"]),
                gas_oil_lts=float(values["gas_oil_lts"]),
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
            self._run_silent_data_action(lambda: self._delete_viaje_and_refresh(viaje_id))

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

        self._run_silent_data_action(delete_and_refresh)

    def _confirm_delete(self, label: str) -> bool:
        response = QMessageBox.question(
            self,
            "Confirmar eliminacion",
            f"Eliminar {label} seleccionado?",
        )
        return response == QMessageBox.StandardButton.Yes

    def _clear_database_with_confirmation(self) -> None:
        response = QMessageBox.question(
            self,
            "Vaciar base de datos",
            (
                "Se van a borrar todos los datos cargados en la aplicacion.\n"
                "Esta accion no se puede deshacer.\n\n"
                "Continuar?"
            ),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if response != QMessageBox.StandardButton.Yes:
            return

        self._run_data_action(
            "Base de datos vaciada.",
            self._clear_database_and_refresh,
        )

    def _clear_database_and_refresh(self) -> None:
        clear_database(self.database_path)
        self._close_empresa_peajes()
        for title in ("Clientes", "Lugares", "Chofer", "T.Carga", "Vehiculos", "Peajes"):
            self._refresh_object_table(title)
        self._refresh_viaje_form_options()
        self._refresh_table()
        self._refresh_metrics()
        self._clear_viaje_form()

    def _cliente_fields(
        self,
        values: dict[str, object] | None = None,
    ) -> list[dict[str, object]]:
        values = values or {}
        return [
            {"key": "nombre", "label": "Nombre", "value": values.get("nombre", "")},
            {
                "key": "cuit",
                "label": "CUIT",
                "value": values.get("cuit", ""),
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
            {
                "key": "es_cliente_directo",
                "label": "Es cliente directo",
                "type": "combo",
                "value": values.get("es_cliente_directo", 1),
                "options": [("Si", 1), ("No", 0)],
            },
            {
                "key": "cliente_padre_id",
                "label": "Intermediario",
                "type": "combo",
                "value": values.get("cliente_padre_id", ""),
                "options": self._cliente_intermediario_options(
                    values.get("current_cliente_id")
                ),
                "required": False,
                "visible_when": {
                    "field": "es_cliente_directo",
                    "equals": 0,
                },
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

    def _peaje_empresa_fields(
        self,
        values: dict[str, object] | None = None,
    ) -> list[dict[str, object]]:
        values = values or {}
        return [
            {"key": "nombre", "label": "Nombre", "value": values.get("nombre", "")},
        ]

    def _viaje_fields_from_row(self, row: int) -> list[dict[str, object]]:
        return [
            {"key": "fecha", "label": "Fecha", "type": "date", "value": self._cell(row, 1)},
            {
                "key": "carta_porte",
                "label": "N° Carta de Porte",
                "value": self._cell(row, 4),
                "required": False,
            },
            {
                "key": "observaciones",
                "label": "Observaciones",
                "type": "multiline",
                "value": self._cell(row, 8),
                "required": False,
            },
            {
                "key": "tarifa",
                "label": "Tarifa",
                "type": "money",
                "value": self._money_from_display(self._cell(row, 13)),
            },
            {
                "key": "fecha_descarga_tarifa",
                "label": "F.Desc tarifa",
                "type": "date",
                "value": self._cell(row, 14),
                "required": False,
            },
            {
                "key": "demora",
                "label": "Demora",
                "type": "money",
                "value": self._money_from_display(self._cell(row, 15)),
            },
            {
                "key": "fecha_descarga_demora",
                "label": "F.Desc demora",
                "type": "date",
                "value": self._cell(row, 16),
                "required": False,
            },
            {
                "key": "vacio",
                "label": "Vacio",
                "type": "money",
                "value": self._money_from_display(self._cell(row, 17)),
            },
            {
                "key": "fecha_descarga_vacio",
                "label": "F.Desc vacio",
                "type": "date",
                "value": self._cell(row, 18),
                "required": False,
            },
            {
                "key": "gas_oil_lts",
                "label": "Gas oil (lts)",
                "type": "decimal",
                "value": self._decimal_from_display(self._cell(row, 19)),
            },
            {"key": "estado", "label": "Estado", "value": self._cell(row, 22)},
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

    def _decimal_from_display(self, value: str) -> float:
        clean = value.replace(".", "").replace(",", ".").strip()
        return float(clean or 0)

    def _optional_int_from_text(self, value: object) -> int | None:
        text = str(value).strip()
        if not text:
            return None
        return int(text)

    def _optional_int(self, value: object) -> int | None:
        if isinstance(value, int):
            return value
        if value is None:
            return None
        return self._optional_int_from_text(value)

    def _cliente_intermediario_options(
        self,
        current_cliente_id: object | None = None,
    ) -> list[tuple[str, int | None]]:
        excluded_id = current_cliente_id if isinstance(current_cliente_id, int) else None
        options: list[tuple[str, int | None]] = [("Seleccionar intermediario", None)]
        options.extend(
            (item.etiqueta, item.id)
            for item in self.cliente_repository.list_all()
            if item.id != excluded_id
        )
        return options

    def _current_viaje_cliente_id(self) -> int | None:
        cliente = self.form_widgets.get("cliente")
        if not isinstance(cliente, QComboBox):
            return None
        value = cliente.currentData()
        return value if isinstance(value, int) else None

    def _enabled_viaje_field_keys(self, cliente_id: int | None) -> set[str]:
        if cliente_id is None:
            return set()

        settings = self.app_settings.get("cliente_viaje_fields", {})
        configured_fields = None
        if isinstance(settings, dict):
            configured_fields = settings.get(str(cliente_id))

        if not isinstance(configured_fields, list):
            return set(VIAJE_CONFIGURABLE_FIELD_KEYS)

        allowed_fields = set(VIAJE_CONFIGURABLE_FIELD_KEYS)
        return {
            str(field_key)
            for field_key in configured_fields
            if str(field_key) in allowed_fields
        }

    def _set_cliente_viaje_fields(
        self,
        cliente_id: int,
        selected_fields: list[str],
    ) -> None:
        settings = self.app_settings.get("cliente_viaje_fields", {})
        if not isinstance(settings, dict):
            settings = {}

        settings[str(cliente_id)] = [
            field_key
            for field_key in VIAJE_CONFIGURABLE_FIELD_KEYS
            if field_key in selected_fields
        ]
        self.app_settings["cliente_viaje_fields"] = settings
        save_app_settings(self.settings_path, self.app_settings)

    def _apply_viaje_field_visibility(self) -> None:
        cliente_id = self._current_viaje_cliente_id()
        enabled_fields = self._enabled_viaje_field_keys(cliente_id)

        for field_key, widget in self.form_widgets.items():
            visible = field_key == "cliente" or field_key in enabled_fields
            widget.setVisible(visible)
            label = self.viaje_form_row_labels.get(field_key)
            if label is not None:
                label.setVisible(visible)

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
        if not self._confirm_clear_viaje_form():
            return
        self._clear_viaje_form()
        self._go_to_create_tab()

    def _confirm_clear_viaje_form(self) -> bool:
        response = QMessageBox.question(
            self,
            "Nuevo viaje",
            "Se van a borrar los datos cargados en el formulario. Continuar?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        return response == QMessageBox.StandardButton.Yes

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
            carta_porte=self._line_value("carta_porte"),
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
            gas_oil_lts=self._decimal_value("gas_oil_lts"),
            peaje_ids=peaje_ids,
        )

    def _clear_viaje_form(self) -> None:
        for key in ("tarifa", "demora", "vacio", "gas_oil_lts"):
            widget = self.form_widgets[key]
            if isinstance(widget, QDoubleSpinBox):
                widget.setValue(0)

        observaciones = self.form_widgets["observaciones"]
        if isinstance(observaciones, QTextEdit):
            observaciones.clear()

        carta_porte = self.form_widgets["carta_porte"]
        if isinstance(carta_porte, QLineEdit):
            carta_porte.clear()

        for widget in self.form_widgets.values():
            if isinstance(widget, QComboBox):
                if widget.isEditable():
                    widget.setCurrentText("")
                elif widget.count() > 0:
                    widget.setCurrentIndex(0)

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

    def _billing_year_changed(self) -> None:
        selected_month = QDate.currentDate().month()
        if self.billing_month_combo is not None and self.billing_month_combo.count() > 0:
            selected_month = int(self.billing_month_combo.currentData() or selected_month)
        self._set_billing_month_options(selected_month)
        self._refresh_billing_months()

    def _set_billing_month_options(self, selected_month: int) -> None:
        if self.billing_month_combo is None or self.billing_year_combo is None:
            return

        current_date = QDate.currentDate()
        selected_year = int(self.billing_year_combo.currentData() or current_date.year())
        max_month = current_date.month() if selected_year >= current_date.year() else 12
        selected_month = min(max(selected_month, 1), max_month)

        previous_state = self.billing_month_combo.blockSignals(True)
        self.billing_month_combo.clear()
        for month_number, month_name in enumerate(MONTH_NAMES, start=1):
            if month_number <= max_month:
                self.billing_month_combo.addItem(month_name, month_number)

        month_index = self.billing_month_combo.findData(selected_month)
        if month_index >= 0:
            self.billing_month_combo.setCurrentIndex(month_index)
        self.billing_month_combo.blockSignals(previous_state)

    def _refresh_billing_months(self) -> None:
        if (
            self.billing_month_combo is None
            or self.billing_year_combo is None
            or not self.billing_month_cards
        ):
            return

        month = int(self.billing_month_combo.currentData() or QDate.currentDate().month())
        year = int(self.billing_year_combo.currentData() or QDate.currentDate().year())
        end_date = QDate(year, month, 1)
        start_date = end_date.addMonths(-11)

        totals = self.viaje_repository.monthly_billing(
            _month_key(start_date),
            _month_key(end_date),
        )
        annual_total = 0.0

        for index, card in enumerate(self.billing_month_cards):
            month_date = start_date.addMonths(index)
            month_total = totals.get(_month_key(month_date), 0)
            annual_total += month_total
            card.set_label(_month_label(month_date))
            card.set_value(_format_money(month_total))

        if self.billing_total_card is not None:
            self.billing_total_card.set_value(_format_money(annual_total))

    def _refresh_print_report(self) -> None:
        if (
            self.print_mode_combo is None
            or self.print_month_combo is None
            or self.print_year_combo is None
            or self.print_from_date is None
            or self.print_to_date is None
            or self.print_table is None
        ):
            return

        mode = self._selected_print_mode()
        year = int(self.print_year_combo.currentData() or QDate.currentDate().year())
        if mode == "annual":
            rows = self.viaje_repository.annual_report_rows(year)
        elif mode == "ricco":
            start_date = self.print_from_date.date().toString("yyyy-MM-dd")
            end_date = self.print_to_date.date().toString("yyyy-MM-dd")
            if start_date > end_date:
                rows = []
            else:
                rows = self.viaje_repository.period_report_rows(
                    start_date,
                    end_date,
                    client_search="ricco",
                )
        else:
            month = int(self.print_month_combo.currentData() or QDate.currentDate().month())
            rows = self.viaje_repository.monthly_report_rows(year, month)

        summary = build_monthly_report_summary(rows)
        self.print_rows = rows

        if self.print_count_card is not None:
            self.print_count_card.set_value(str(summary.trip_count))
        if self.print_total_card is not None:
            self.print_total_card.set_value(_format_money(summary.total_amount))

        self.print_table.setRowCount(len(rows))
        for row_index, viaje in enumerate(rows):
            for column_index, value in enumerate(self._print_row_values(viaje)):
                item = QTableWidgetItem(value)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.print_table.setItem(row_index, column_index, item)
        self.print_table.resizeColumnsToContents()

    def _refresh_print_mode_ui(self) -> None:
        mode = self._selected_print_mode()
        is_monthly = mode == "monthly"
        is_annual = mode == "annual"
        is_ricco = mode == "ricco"

        if self.print_month_card is not None:
            self.print_month_card.setVisible(is_monthly)
        if self.print_year_card is not None:
            self.print_year_card.setVisible(is_monthly or is_annual)
        if self.print_from_card is not None:
            self.print_from_card.setVisible(is_ricco)
        if self.print_to_card is not None:
            self.print_to_card.setVisible(is_ricco)

    def _export_print_excel(self) -> None:
        if not self.print_rows:
            QMessageBox.information(
                self,
                "Imprimir",
                "No hay viajes cargados para el filtro seleccionado.",
            )
            return

        mode = self._selected_print_mode()
        template_path = None
        if mode == "ricco":
            template_path = find_ricco_template_path()
            if template_path is None:
                selected_template, _ = QFileDialog.getOpenFileName(
                    self,
                    "Seleccionar plantilla RICCO",
                    str(Path.home()),
                    "Archivos Excel (*.xlsx)",
                )
                if not selected_template:
                    return
                template_path = Path(selected_template)
            default_name = build_ricco_export_filename(
                self.print_from_date.date().toString("yyyy-MM-dd"),
                self.print_to_date.date().toString("yyyy-MM-dd"),
                self.company_name,
            )
            default_dir = template_path.parent
        else:
            default_name = f"{self._selected_print_file_stem()}.xlsx"
            default_dir = self.database_path.parent

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar reporte Excel",
            str(default_dir / default_name),
            "Archivos Excel (*.xlsx)",
        )
        if not file_path:
            return

        if mode == "ricco" and template_path is not None:
            export_ricco_report_excel(
                template_path,
                Path(file_path),
                self.print_from_date.date().toString("yyyy-MM-dd"),
                self.print_to_date.date().toString("yyyy-MM-dd"),
                self.print_rows,
                company_name=self.company_name,
            )
        else:
            export_monthly_report_excel(
                Path(file_path),
                self._selected_print_period_label(),
                self.print_rows,
                report_title=self._selected_print_title(),
            )
        QMessageBox.information(
            self,
            "Imprimir",
            f"Reporte Excel generado en:\n{file_path}",
        )

    def _export_print_pdf(self) -> None:
        if not self.print_rows:
            QMessageBox.information(
                self,
                "Imprimir",
                "No hay viajes cargados para el filtro seleccionado.",
            )
            return

        default_name = f"{self._selected_print_file_stem()}.pdf"
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar reporte PDF",
            str(self.database_path.parent / default_name),
            "Archivos PDF (*.pdf)",
        )
        if not file_path:
            return

        export_monthly_report_pdf(
            Path(file_path),
            self._selected_print_period_label(),
            self.print_rows,
            report_title=self._selected_print_title(),
        )
        QMessageBox.information(
            self,
            "Imprimir",
            f"Reporte PDF generado en:\n{file_path}",
        )

    def _selected_print_file_stem(self) -> str:
        mode = self._selected_print_mode()
        if mode == "annual":
            return f"reporte-anual-{self._selected_print_period_key()}"
        if mode == "ricco":
            return f"cliente-ricco-{self._selected_print_period_key()}"
        return f"reporte-mensual-{self._selected_print_period_key()}"

    def _selected_print_mode(self) -> str:
        if self.print_mode_combo is None:
            return "monthly"
        return str(self.print_mode_combo.currentData() or "monthly")

    def _selected_print_title(self) -> str:
        mode = self._selected_print_mode()
        if mode == "annual":
            return "Reporte anual"
        if mode == "ricco":
            return "Reporte Cliente Ricco"
        return "Reporte mensual"

    def _selected_print_period_key(self) -> str:
        mode = self._selected_print_mode()
        if mode == "annual":
            year = int(self.print_year_combo.currentData() or QDate.currentDate().year())
            return str(year)
        if mode == "ricco":
            start_date = self.print_from_date.date().toString("yyyy-MM-dd")
            end_date = self.print_to_date.date().toString("yyyy-MM-dd")
            return f"{start_date}_a_{end_date}"
        month = int(self.print_month_combo.currentData() or QDate.currentDate().month())
        year = int(self.print_year_combo.currentData() or QDate.currentDate().year())
        return f"{year:04d}-{month:02d}"

    def _selected_print_period_label(self) -> str:
        mode = self._selected_print_mode()
        if mode == "annual":
            year = int(self.print_year_combo.currentData() or QDate.currentDate().year())
            return str(year)
        if mode == "ricco":
            start_date = self.print_from_date.date().toString("yyyy-MM-dd")
            end_date = self.print_to_date.date().toString("yyyy-MM-dd")
            return f"Desde {start_date} hasta {end_date}"
        month = int(self.print_month_combo.currentData() or QDate.currentDate().month())
        year = int(self.print_year_combo.currentData() or QDate.currentDate().year())
        return f"{MONTH_NAMES[month - 1]} {year}"

    def _print_row_values(self, viaje: ViajeResumen) -> list[str]:
        return [
            viaje.fecha,
            viaje.cliente,
            viaje.carta_porte,
            viaje.carga,
            viaje.lugar_carga,
            viaje.lugar_descarga,
            viaje.chofer,
            viaje.camion,
            _format_money(viaje.tarifa),
            _format_money(viaje.demora),
            _format_money(viaje.vacio),
            _format_decimal(viaje.gas_oil_lts),
            _format_money(viaje.peajes),
            _format_money(viaje.costo_total),
            viaje.estado,
        ]

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
        if self.save_button is not None:
            self.save_button.setVisible(active_label == "Cargar viaje")

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

    def _build_peaje_empresa_combo(self) -> QComboBox:
        return self._build_combo(
            [("Todas", None)]
            + [(item.nombre, item.id) for item in self.peaje_repository.list_empresas()]
        )

    def _refresh_viaje_form_options(self) -> None:
        combo_sources = {
            "cliente": [("Seleccionar cliente", None)]
            + [
                (item.etiqueta, item.id) for item in self.cliente_repository.list_all()
            ],
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
            "peaje_empresa": [("Todas", None)]
            + [(item.nombre, item.id) for item in self.peaje_repository.list_empresas()],
        }
        if not combo_sources["tipo_carga"]:
            combo_sources["tipo_carga"] = [
                ("General", "GENERAL"),
                ("Carga peligrosa", "PELIGROSA"),
            ]

        for key, items in combo_sources.items():
            widget = self.form_widgets.get(key)
            if isinstance(widget, QComboBox):
                selected_value = widget.currentData()
                was_editable = widget.isEditable()
                widget.clear()
                for label, value in items:
                    widget.addItem(label, value)
                selected_index = widget.findData(selected_value)
                if selected_index >= 0:
                    widget.setCurrentIndex(selected_index)
                if was_editable:
                    widget.setCurrentText("")

        self._refresh_peaje_checklist()
        self._apply_viaje_field_visibility()

    def _selected_peaje_empresa_filter(self) -> int | None:
        widget = self.form_widgets.get("peaje_empresa")
        if not isinstance(widget, QComboBox):
            return None
        value = widget.currentData()
        return value if isinstance(value, int) else None

    def _refresh_peaje_checklist(self) -> None:
        peajes = self.form_widgets.get("peajes")
        if not isinstance(peajes, QListWidget):
            return

        checked_ids = set(self._checked_peaje_ids())
        empresa_id = self._selected_peaje_empresa_filter()
        visible_peajes = self.peaje_repository.list_all(empresa_id=empresa_id)
        visible_ids = {item.id for item in visible_peajes}
        selected_missing_peajes = [
            item
            for item in self.peaje_repository.list_all()
            if item.id in checked_ids and item.id not in visible_ids
        ]

        peajes.clear()
        for item in [*visible_peajes, *selected_missing_peajes]:
            peaje_item = QListWidgetItem(
                f"{item.empresa_nombre} - {item.nombre} - {_format_money(item.costo)}"
            )
            peaje_item.setFlags(peaje_item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            peaje_item.setCheckState(
                Qt.CheckState.Checked if item.id in checked_ids else Qt.CheckState.Unchecked
            )
            peaje_item.setData(Qt.ItemDataRole.UserRole, item.id)
            peajes.addItem(peaje_item)

    def _lugar_options(self, rol: str) -> list[tuple[str, object]]:
        lugares = self.lugar_repository.list_by_viaje_usage(rol)
        return [(item.nombre, item.id) for item in lugares]

    def _build_lugar_combo(self, rol: str) -> QComboBox:
        return self._build_combo(self._lugar_options(rol))

    def _money_input(self) -> QDoubleSpinBox:
        spin = QDoubleSpinBox()
        spin.setRange(0, 999_999_999)
        spin.setDecimals(2)
        spin.setSingleStep(1000)
        spin.setPrefix("$ ")
        return spin

    def _decimal_input(self) -> QDoubleSpinBox:
        spin = QDoubleSpinBox()
        spin.setRange(0, 999_999_999)
        spin.setDecimals(2)
        spin.setSingleStep(10)
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

    def _line_value(self, key: str) -> str:
        widget = self.form_widgets[key]
        if not isinstance(widget, QLineEdit):
            raise ValueError("Campo de linea invalido.")
        return widget.text().strip()

    def _money_value(self, key: str) -> float:
        widget = self.form_widgets[key]
        if not isinstance(widget, QDoubleSpinBox):
            raise ValueError("Campo de importe invalido.")
        return float(widget.value())

    def _decimal_value(self, key: str) -> float:
        widget = self.form_widgets[key]
        if not isinstance(widget, QDoubleSpinBox):
            raise ValueError("Campo decimal invalido.")
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


class StartupAlertsDialog(QDialog):
    def __init__(
        self,
        parent: QWidget,
        alerts: list[AppAlert],
        *,
        accept_callback: Callable[[AppAlert], bool],
        validate_callback: Callable[[AppAlert], bool],
    ) -> None:
        super().__init__(parent)
        self.alerts = list(alerts)
        self.accept_callback = accept_callback
        self.validate_callback = validate_callback
        self.current_alert: AppAlert | None = None

        self.setWindowTitle("Alertas")
        self.setMinimumWidth(520)

        layout = QVBoxLayout(self)
        layout.setSpacing(14)

        self.counter_label = QLabel()
        self.counter_label.setObjectName("muted")
        self.title_label = QLabel()
        self.title_label.setObjectName("sectionTitle")
        self.message_label = QLabel()
        self.message_label.setWordWrap(True)

        button_row = QHBoxLayout()
        button_row.addStretch()
        self.accept_button = QPushButton("Aceptar")
        self.validate_button = QPushButton("Validar")
        self.accept_button.clicked.connect(self._accept_current_alert)
        self.validate_button.clicked.connect(self._validate_current_alert)
        button_row.addWidget(self.accept_button)
        button_row.addWidget(self.validate_button)

        layout.addWidget(self.counter_label)
        layout.addWidget(self.title_label)
        layout.addWidget(self.message_label)
        layout.addLayout(button_row)

        self._show_next_alert()

    def _show_next_alert(self) -> None:
        if not self.alerts:
            self.accept()
            return

        self.current_alert = self.alerts[0]
        self.counter_label.setText(f"Alertas pendientes: {len(self.alerts)}")
        self.title_label.setText(self.current_alert.title)
        self.message_label.setText(self.current_alert.message)

    def _accept_current_alert(self) -> None:
        if self.current_alert is None:
            return
        if self.accept_callback(self.current_alert):
            self._close_current_alert()

    def _validate_current_alert(self) -> None:
        if self.current_alert is None:
            return
        if self.validate_callback(self.current_alert):
            self._close_current_alert()

    def _close_current_alert(self) -> None:
        if self.alerts:
            self.alerts.pop(0)
        self._show_next_alert()


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
        self.row_labels: dict[str, QWidget] = {}
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
            elif field_type == "decimal":
                widget = QDoubleSpinBox()
                widget.setRange(0, 999_999_999)
                widget.setDecimals(2)
                widget.setSingleStep(10)
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
            row_label = form.labelForField(widget)
            if row_label is not None:
                self.row_labels[key] = row_label

        self._connect_visibility_rules()
        self._apply_visibility_rules()

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout.addLayout(form)
        layout.addWidget(buttons)

    def is_field_visible(self, key: str) -> bool:
        widget = self.widgets.get(key)
        return widget is not None and widget.isVisible()

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

    def _connect_visibility_rules(self) -> None:
        dependent_keys = {
            str(field.get("visible_when", {}).get("field"))
            for field in self.fields
            if isinstance(field.get("visible_when"), dict)
        }
        for key in dependent_keys:
            widget = self.widgets.get(key)
            if isinstance(widget, QComboBox):
                widget.currentIndexChanged.connect(
                    lambda *_args: self._apply_visibility_rules()
                )

    def _apply_visibility_rules(self) -> None:
        for field in self.fields:
            key = str(field["key"])
            visible_when = field.get("visible_when")
            visible = True
            if isinstance(visible_when, dict):
                parent_key = str(visible_when.get("field"))
                expected = visible_when.get("equals")
                parent_widget = self.widgets.get(parent_key)
                if isinstance(parent_widget, QComboBox):
                    visible = parent_widget.currentData() == expected
            widget = self.widgets.get(key)
            if widget is not None:
                widget.setVisible(visible)
            label = self.row_labels.get(key)
            if label is not None:
                label.setVisible(visible)


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
        self.label_widget = label_widget
        self.value_widget = value_widget

    def set_label(self, value: str) -> None:
        self.label_widget.setText(value)

    def set_value(self, value: str) -> None:
        self.value_widget.setText(value)


def _format_money(value: float) -> str:
    return f"$ {value:,.0f}".replace(",", ".")


def _format_decimal(value: float) -> str:
    return f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _month_key(date: QDate) -> str:
    return date.toString("yyyy-MM")


def _month_label(date: QDate) -> str:
    return f"{MONTH_NAMES[date.month() - 1]} {date.year()}"


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

QPushButton#sidebarToggleButton {
    min-height: 34px;
    border-radius: 8px;
    padding: 0 10px;
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
