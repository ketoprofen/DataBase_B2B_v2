from PyQt5.QtWidgets import QGroupBox, QFormLayout, QRadioButton, QButtonGroup, QLineEdit, QCheckBox, QPushButton, QHBoxLayout, QVBoxLayout

class DataExporter:
    def __init__(self, parent):
        self.parent = parent
        self.setup_ui()

    def setup_ui(self):
        # Initialize extrapolation group and layout
        self.extrapolate_group = QGroupBox('Estrapola Dati')
        self.extrapolate_layout = QFormLayout()

        # Initialize buttons before adding to layout
        self.button_extrapolate_execute = QPushButton('Estrapola Excel')
        self.button_extrapolate_execute.clicked.connect(self.extrapolate_data)
        self.button_back = QPushButton('Indietro')
        self.button_back.clicked.connect(self.parent.toggle_extrapolate_group)

        # Initialize radio buttons
        self.radio_all_data = QRadioButton('Estrapola tutti i dati in Excel')
        self.radio_exclude_consegnata = QRadioButton('Estrapola tutti i dati escludendo "Consegnata"')
        self.radio_by_flotta = QRadioButton('Estrapola dati per Flotta')
        self.radio_stato_report = QRadioButton('Estrapola Stato')

        # Group radio buttons
        self.radio_group = QButtonGroup()
        self.radio_group.addButton(self.radio_all_data)
        self.radio_group.addButton(self.radio_exclude_consegnata)
        self.radio_group.addButton(self.radio_by_flotta)
        self.radio_group.addButton(self.radio_stato_report)

        # Add radio buttons to layout
        self.extrapolate_layout.addRow(self.radio_all_data)
        self.extrapolate_layout.addRow(self.radio_exclude_consegnata)
        self.extrapolate_layout.addRow(self.radio_by_flotta)
        self.extrapolate_layout.addRow(self.radio_stato_report)

        # Add buttons to layout
        button_layout_extrapolate = QHBoxLayout()
        button_layout_extrapolate.addWidget(self.button_extrapolate_execute)
        button_layout_extrapolate.addWidget(self.button_back)
        self.extrapolate_layout.addRow('', button_layout_extrapolate)

        # Initialize other widgets
        self.text_flotta_extrapolate = QLineEdit()
        self.text_flotta_extrapolate.setMaximumWidth(200)
        self.checkbox_exclude_consegnata = QCheckBox('Solo "Consegnata"')
        self.checkbox_exclude_consegnata.setChecked(False)

        # Add widgets to layout
        self.extrapolate_layout.addRow('Flotta:', self.text_flotta_extrapolate)
        self.extrapolate_layout.addRow('', self.checkbox_exclude_consegnata)

        # Disable inputs initially
        self.text_flotta_extrapolate.setEnabled(False)
        self.checkbox_exclude_consegnata.setEnabled(False)

        # Connect radio buttons to options update
        self.radio_all_data.toggled.connect(self.update_extrapolate_options)
        self.radio_exclude_consegnata.toggled.connect(self.update_extrapolate_options)
        self.radio_by_flotta.toggled.connect(self.update_extrapolate_options)
        self.radio_stato_report.toggled.connect(self.update_extrapolate_options)

        self.extrapolate_group.setLayout(self.extrapolate_layout)

        # Check if parent has a layout, if not, create one
        if not self.parent.layout():
            self.parent.setLayout(QVBoxLayout())

        # Add extrapolation group to the parent's layout
        self.parent.layout().addWidget(self.extrapolate_group)
        self.extrapolate_group.hide()

    def extrapolate_data(self):
        # Assuming the parent class has the `execute_extrapolate` function
        execute_extrapolate(self.parent)

    def update_extrapolate_options(self):
        if self.radio_by_flotta.isChecked():
            self.text_flotta_extrapolate.setEnabled(True)
            self.checkbox_exclude_consegnata.setEnabled(True)
        else:
            self.text_flotta_extrapolate.setEnabled(False)
            self.checkbox_exclude_consegnata.setEnabled(False)
