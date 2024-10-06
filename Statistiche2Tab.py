from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QSizePolicy, QMessageBox, QFileDialog, QPushButton
from PyQt5 import QtGui
from PyQt5.QtCore import QTimer, QSize
import datetime
import pandas as pd

class Statistiche2Tab(QWidget):
    def __init__(self, conn):
        super().__init__()
        self.conn = conn
        self.cursor = self.conn.cursor()
        self.setWindowTitle("Statistiche 2 - Estrapolazioni")
        self.init_ui()
        self.setup_timer()
        self.adjust_window_size()

    def init_ui(self):
        layout = QVBoxLayout()

        # Create a horizontal layout for the title and export button
        header_layout = QHBoxLayout()

        # Add title for Statistiche 2
        title_label = QLabel("Statistiche 2: Entrate e Consegnate per Flotta")
        title_label.setFont(QtGui.QFont("Arial", 16, QtGui.QFont.Bold))
        header_layout.addWidget(title_label)

        # Add button to export data to Excel (smaller and on the right of the title)
        self.export_button = QPushButton("Esporta Excel")
        self.export_button.setMaximumWidth(80)
        self.export_button.clicked.connect(self.export_to_excel)
        header_layout.addStretch()
        header_layout.addWidget(self.export_button)

        # Add header layout to the main layout
        layout.addLayout(header_layout)

        # Table widget for showing the data
        self.statistiche_table = QTableWidget()
        self.statistiche_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(self.statistiche_table)

        # Set the layout for the tab
        self.setLayout(layout)

        # Load data into the table in real-time
        self.load_data()

    def setup_timer(self):
        # Set up a timer to refresh data every 2 seconds
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.load_data)
        self.timer.start(2000)  # Refresh every 2000 ms (2 seconds)

    def adjust_window_size(self):
        # Adjust window size to fit the table
        self.resize(QSize(800, 600))  # You can adjust the width and height as needed

    def load_data(self):
        try:
            # Get current date and current month/year
            current_date = datetime.date.today()
            current_month = current_date.month
            current_year = current_date.year

            # Fetch records grouped by 'flotta' with normalization
            self.cursor.execute("""
                SELECT TRIM(UPPER(flotta)) AS normalized_flotta,
                       SUM(CASE WHEN substr(data_incarico, 4, 2) = ? AND substr(data_incarico, 7, 4) = ? THEN 1 ELSE 0 END) AS entrate,
                       SUM(CASE WHEN substr(data_consegnata, 4, 2) = ? AND substr(data_consegnata, 7, 4) = ? THEN 1 ELSE 0 END) AS uscite_consegnate
                FROM records
                WHERE flotta IS NOT NULL AND flotta != ''
                GROUP BY normalized_flotta
            """, (f"{current_month:02}", f"{current_year}", f"{current_month:02}", f"{current_year}"))
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

    def refresh_data(self):
        # Reload data in the table in real-time
        self.load_data()