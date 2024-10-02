# notifications_window.py
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QLabel, QTableView, QHeaderView
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QStandardItemModel, QStandardItem, QPalette
import pandas as pd
from datetime import datetime, timedelta

class NotificationsWindow(QWidget):
    def __init__(self, conn):
        super().__init__()
        self.setWindowTitle('Notifiche - Controlla queste targhe!!!')
        self.resize(1000, 600)
        self.conn = conn
        self.cursor = self.conn.cursor()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        button_layout = QHBoxLayout()

        # Search Box
        self.search_box = QLineEdit(self)
        self.search_box.setPlaceholderText("Search by Targa...")
        self.search_box.setFixedWidth(150)
        self.search_box.textChanged.connect(self.load_notifications)  # Update notifications when text changes
        button_layout.addWidget(self.search_box)

        # Refresh Button
        self.refresh_button = QPushButton('Refresh')
        self.refresh_button.clicked.connect(self.refresh_notifications)
        button_layout.addWidget(self.refresh_button)

        button_layout.addStretch()

        layout.addLayout(button_layout)

        self.table = QTableView()
        layout.addWidget(self.table)

        # Legend
        legend_layout = QHBoxLayout()
        legend_label = QLabel("Legenda:")
        yellow_label = QLabel("10-15 giorni")
        yellow_label.setAutoFillBackground(True)
        yellow_palette = yellow_label.palette()
        yellow_palette.setColor(QPalette.Window, QColor('yellow'))
        yellow_label.setPalette(yellow_palette)
        yellow_label.setFixedSize(100, 20)
        yellow_label.setAlignment(Qt.AlignCenter)

        orange_label = QLabel("16-20 giorni")
        orange_label.setAutoFillBackground(True)
        orange_palette = orange_label.palette()
        orange_palette.setColor(QPalette.Window, QColor('orange'))
        orange_label.setPalette(orange_palette)
        orange_label.setFixedSize(100, 20)
        orange_label.setAlignment(Qt.AlignCenter)

        red_label = QLabel("Oltre 20 giorni")
        red_label.setAutoFillBackground(True)
        red_palette = red_label.palette()
        red_palette.setColor(QPalette.Window, QColor('red'))
        red_label.setPalette(red_palette)
        red_label.setFixedSize(100, 20)
        red_label.setAlignment(Qt.AlignCenter)

        legend_layout.addWidget(legend_label)
        legend_layout.addWidget(yellow_label)
        legend_layout.addWidget(orange_label)
        legend_layout.addWidget(red_label)
        legend_layout.addStretch()

        layout.addLayout(legend_layout)

        self.setLayout(layout)
        self.load_notifications()

    def load_notifications(self):
        # Get search filter from search box
        search_text = self.search_box.text().upper().strip()

        query = '''
            SELECT * FROM records
            WHERE stato != "Consegnata"
        '''

        if search_text:
            query += f" AND targa LIKE '%{search_text}%'"

        self.cursor.execute(query)
        records = self.cursor.fetchall()

        notifications = []
        for record in records:
            data_incarico_str = record['data_incarico']
            try:
                data_incarico = datetime.strptime(data_incarico_str, '%d/%m/%Y')
                working_days = self.calculate_working_days(data_incarico, datetime.now())
                if working_days > 10:
                    record_dict = {}
                    for key in record.keys():
                        record_dict[key] = record[key]
                    record_dict['working_days'] = working_days
                    notifications.append(record_dict)
            except Exception:
                continue  # Skip records with invalid dates

        if notifications:
            df = pd.DataFrame(notifications)

            def get_color(working_days):
                if 10 < working_days <= 15:
                    return 'yellow'
                elif 15 < working_days <= 20:
                    return 'orange'
                elif working_days > 20:
                    return 'red'
                else:
                    return ''

            df['Color'] = df['working_days'].apply(get_color)

            standard_model = QStandardItemModel()
            headers = [col for col in df.columns if col != 'Color']
            standard_model.setHorizontalHeaderLabels(headers)

            for _, row in df.iterrows():
                items = []
                for field in headers:
                    item = QStandardItem(str(row[field]))
                    items.append(item)
                standard_model.appendRow(items)

            self.table.setModel(standard_model)
            self.table.setEditTriggers(QTableView.NoEditTriggers)
            self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            self.table.hideColumn(0)

            # Apply color to rows
            for row in range(standard_model.rowCount()):
                color = df.iloc[row]['Color']
                if color:
                    for col in range(standard_model.columnCount()):
                        item = standard_model.item(row, col)
                        if item:
                            item.setBackground(QColor(color))
        else:
            # Clear table if no records are found
            standard_model = QStandardItemModel()
            self.table.setModel(standard_model)

    def refresh_notifications(self):
        self.search_box.clear()  # Clear the search box to reset the filter
        self.load_notifications()

    def calculate_working_days(self, start_date, end_date):
        if start_date > end_date:
            return 0
        day_generator = (start_date + timedelta(days=x) for x in range((end_date - start_date).days + 1))
        working_days = sum(1 for day in day_generator if day.weekday() < 5)
        return working_days
