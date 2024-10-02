from PyQt5.QtWidgets import QPushButton
class DataImporter:
    def __init__(self, parent):
        self.parent = parent
        self.setup_ui()

    def setup_ui(self):
        self.button_import = QPushButton('Importa Dati')
        self.button_import.clicked.connect(self.import_data)
        self.button_import.setMaximumWidth(150)

        self.parent.layout.addWidget(self.button_import)

    def import_data(self):
        # Assuming the parent class has the `import_data` function
        import_data(self.parent)
