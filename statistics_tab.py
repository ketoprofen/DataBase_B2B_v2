from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton
import sqlite3
from data_exporter_layout import DataExporter
from data_importer_layout import DataImporter

class StatisticsTab(QWidget):
    def __init__(self, conn: sqlite3.Connection, parent=None):
        super().__init__()
        self.conn = conn
        self.cursor = self.conn.cursor()
        self.parent = parent  # Salvează referința către `MainWindow`
        self.init_ui()

    def init_ui(self):
        # Create a vertical layout for the whole tab
        self.main_layout = QVBoxLayout()

        # Separate container for the buttons
        self.button_layout = QHBoxLayout()
        self.data_exporter_button = QPushButton("Export Data")
        self.data_importer_button = QPushButton("Import Data")

        # Connect the buttons to their respective actions
        self.data_exporter_button.clicked.connect(self.export_data)
        self.data_importer_button.clicked.connect(self.import_data)

        # Add buttons to the button layout
        self.button_layout.addWidget(self.data_exporter_button)
        self.button_layout.addWidget(self.data_importer_button)

        # Add the button layout to the main layout
        self.main_layout.addLayout(self.button_layout)

        # Separate container for statistics display
        self.statistics_layout = QVBoxLayout()
        self.statistics_text = QTextEdit()
        self.statistics_text.setReadOnly(True)
        self.statistics_layout.addWidget(self.statistics_text)

        # Add the statistics layout to the main layout
        self.main_layout.addLayout(self.statistics_layout)

        # Set the main layout for the tab
        self.setLayout(self.main_layout)

        # Load initial statistics
        self.load_statistics()

    def load_statistics(self):
        # Query example: Get the count of records grouped by 'stato'
        self.cursor.execute('''
            SELECT stato, COUNT(*) as count FROM records GROUP BY stato
        ''')
        results = self.cursor.fetchall()

        # Prepare the text to display in the statistics tab
        stats_text = "Statistics:\n\n"
        for row in results:
            stats_text += f"{row['stato']}: {row['count']} records\n"

        # Display the statistics in the text edit widget
        self.statistics_text.setText(stats_text)

    def export_data(self):
        # Logic for exporting data goes here
        self.data_exporter = DataExporter(self.parent)
        self.data_exporter.button_back.clicked.connect(self.parent.toggle_extrapolate_group)


    def import_data(self):
        # Logic for importing data goes here
        self.data_importer = DataImporter(self.parent)
