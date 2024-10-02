# statistics_tab.py
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTextEdit
import sqlite3

class StatisticsTab(QWidget):
    def __init__(self, conn: sqlite3.Connection):
        super().__init__()
        self.conn = conn
        self.cursor = self.conn.cursor()
        self.init_ui()

    def init_ui(self):
        # Create a vertical layout for the tab
        self.layout = QVBoxLayout()

        # Create a QTextEdit to display statistics
        self.statistics_text = QTextEdit()
        self.statistics_text.setReadOnly(True)
        self.layout.addWidget(self.statistics_text)

        # Load initial statistics
        self.load_statistics()

        # Set the layout for the tab
        self.setLayout(self.layout)

    def load_statistics(self):
        # Example: Get the count of records grouped by 'stato'
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
