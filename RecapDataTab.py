from PyQt5 import QtWidgets, QtGui, QtCore
import datetime

class RecapDataTab(QtWidgets.QWidget):
    def __init__(self, conn):
        super().__init__()
        self.conn = conn
        self.setWindowTitle("Recap Data")
        self.init_ui()

    def init_ui(self):
        layout = QtWidgets.QVBoxLayout()

        # Table widget to display data
        self.table_widget = QtWidgets.QTableWidget()
        layout.addWidget(self.table_widget)

        # Set table headers
        headers = [
            "DITTA",
            "NR. OPERATORI",
            "GG.LAV",
            "VETTURE FINITE NEL MESE",
            "MEDIA VETTURE AL GG.",
            "MEDIA PZ. PER VETTURA",
            "MEDIA PEZZI AL GG.",
            "MEDIA PZ. PER OP. AL GG",
            "TOTALE PZ."
        ]
        self.table_widget.setColumnCount(len(headers))
        self.table_widget.setHorizontalHeaderLabels(headers)

        # Load data from database
        self.load_data()

        self.setLayout(layout)

    def load_data(self):
        try:
            cursor = self.conn.cursor()

            # Get working days in the current month
            today = datetime.date.today()
            first_day = today.replace(day=1)
            last_day = (first_day + datetime.timedelta(days=32)).replace(day=1) - datetime.timedelta(days=1)
            working_days = len([1 for i in range((last_day - first_day).days + 1)
                               if (first_day + datetime.timedelta(days=i)).weekday() < 5])

            # Fetch data for VETTURE FINITE NEL MESE
            cursor.execute("SELECT COUNT(*) FROM records WHERE stato IN ('PRONTA', 'CONSEGNATA')")
            vetture_finite_nel_mese = cursor.fetchone()[0]

            # Set data in table widget
            self.table_widget.setRowCount(1)  # Assuming one row for summary data
            self.table_widget.setItem(0, 0, QtWidgets.QTableWidgetItem("DITTA_NAME"))  # Placeholder for DITTA
            self.table_widget.setItem(0, 1, QtWidgets.QTableWidgetItem("0"))  # Placeholder for NR. OPERATORI (editable)
            self.table_widget.setItem(0, 2, QtWidgets.QTableWidgetItem(str(working_days)))
            self.table_widget.setItem(0, 3, QtWidgets.QTableWidgetItem(str(vetture_finite_nel_mese)))
            self.table_widget.setItem(0, 4, QtWidgets.QTableWidgetItem("0"))  # Placeholder for MEDIA VETTURE AL GG.
            self.table_widget.setItem(0, 5, QtWidgets.QTableWidgetItem("0"))  # Placeholder for MEDIA PZ. PER VETTURA
            self.table_widget.setItem(0, 6, QtWidgets.QTableWidgetItem("0"))  # Placeholder for MEDIA PEZZI AL GG.
            self.table_widget.setItem(0, 7, QtWidgets.QTableWidgetItem("0"))  # Placeholder for MEDIA PZ. PER OP. AL GG
            self.table_widget.setItem(0, 8, QtWidgets.QTableWidgetItem("0"))  # Placeholder for TOTALE PZ.

            # Allow editing NR. OPERATORI
            self.table_widget.item(0, 1).setFlags(QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)

        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", f"Failed to load data: {e}")
