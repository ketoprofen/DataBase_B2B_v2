from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QSizePolicy, QMessageBox, QFileDialog, QPushButton
from PyQt5 import QtGui
import datetime
import pandas as pd

class Statistiche2Tab(QWidget):
    def __init__(self, conn):
        super().__init__()
        self.conn = conn
        self.cursor = self.conn.cursor()
        self.setWindowTitle("Statistiche 2 - Estrapolazioni")
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Add title for Statistiche 2
        title_label = QLabel("Statistiche 2: Entrate e Consegnate per Flotta")
        title_label.setFont(QtGui.QFont("Arial", 16, QtGui.QFont.Bold))
        layout.addWidget(title_label)

        # Table widget for showing the data
        self.statistiche_table = QTableWidget()
        self.statistiche_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(self.statistiche_table)

        # Add button to export data to Excel
        self.export_button = QPushButton("Esporta in Excel")
        self.export_button.clicked.connect(self.export_to_excel)
        layout.addWidget(self.export_button)

        # Set the layout for the tab
        self.setLayout(layout)

        # Load data into the table
        self.load_data()

    def load_data(self):
        try:
            # Get current date and current month/year
            current_date = datetime.date.today()
            current_month = current_date.month
            current_year = current_date.year

            # Fetch records grouped by 'flotta' with normalization
            self.cursor.execute("""
                SELECT TRIM(UPPER(flotta)) AS normalized_flotta,
                       COUNT(CASE WHEN strftime('%Y-%m', data_incarico) = ? AND date(data_incarico) <= ? THEN 1 END) AS entrate,
                       COUNT(CASE WHEN strftime('%Y-%m', data_consegnata) = ? THEN 1 END) AS uscite_consegnate
                FROM records
                WHERE flotta IS NOT NULL
                GROUP BY normalized_flotta
            """, (f"{current_year}-{current_month:02}", current_date.strftime('%Y-%m-%d'), f"{current_year}-{current_month:02}"))
            records = self.cursor.fetchall()

            # Set the number of rows and columns in the table
            self.statistiche_table.setRowCount(len(records))
            self.statistiche_table.setColumnCount(3)
            self.statistiche_table.setHorizontalHeaderLabels(["Flotta", "Entrate (ad oggi nel mese corrente)", "Uscite/Consegnate (mese corrente)"])

            # Populate the table
            for row_index, record in enumerate(records):
                normalized_flotta, entrate, uscite_consegnate = record
                self.statistiche_table.setItem(row_index, 0, QTableWidgetItem(normalized_flotta))
                self.statistiche_table.setItem(row_index, 1, QTableWidgetItem(str(entrate)))
                self.statistiche_table.setItem(row_index, 2, QTableWidgetItem(str(uscite_consegnate)))

            # Resize columns to fit contents
            self.statistiche_table.resizeColumnsToContents()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load data for Statistiche 2: {e}")

    def export_to_excel(self):
        try:
            # Ask user for file location
            options = QFileDialog.Options()
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Salva File",
                f"Statistiche2_{datetime.date.today().strftime('%Y_%m_%d')}.xlsx",
                "Excel Files (*.xlsx);;All Files (*)",
                options=options
            )
            if file_path:
                # Collect data from the table
                data = []
                for row in range(self.statistiche_table.rowCount()):
                    row_data = []
                    for column in range(self.statistiche_table.columnCount()):
                        item = self.statistiche_table.item(row, column)
                        row_data.append(item.text() if item else '')
                    data.append(row_data)

                # Export to Excel
                df = pd.DataFrame(data, columns=["Flotta", "Entrate (ad oggi nel mese corrente)", "Uscite/Consegnate (mese corrente)"])
                df.to_excel(file_path, index=False)

                QMessageBox.information(self, "Successo", f"File salvato con successo in {file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to export data: {e}")
