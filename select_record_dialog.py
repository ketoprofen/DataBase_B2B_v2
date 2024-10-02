# select_record_dialog.py
from PyQt5.QtWidgets import QDialog , QVBoxLayout , QListWidget , QHBoxLayout , QPushButton , QMessageBox
    
class SelectRecordDialog(QDialog):
    def __init__(self, records):
        super().__init__()
        self.setWindowTitle('Seleziona Record')
        self.records = records
        self.selected_record = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        self.list_widget = QListWidget()
        for record in self.records:
            item_text = f"Targa: {record['targa']}, Entrata: {record['entrata']}, Data Incarico: {record['data_incarico']}"
            self.list_widget.addItem(item_text)

        layout.addWidget(self.list_widget)

        button_layout = QHBoxLayout()
        self.button_select = QPushButton('Seleziona')
        self.button_select.clicked.connect(self.select_record)
        self.button_cancel = QPushButton('Annulla')
        self.button_cancel.clicked.connect(self.reject)

        button_layout.addWidget(self.button_select)
        button_layout.addWidget(self.button_cancel)

        layout.addLayout(button_layout)

        self.setLayout(layout)

    def select_record(self):
        selected_index = self.list_widget.currentRow()
        if selected_index >= 0:
            self.selected_record = self.records[selected_index]
            self.accept()
        else:
            QMessageBox.warning(self, 'Errore', 'Per favore, seleziona un record.')
