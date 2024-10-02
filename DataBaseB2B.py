import sys
import sqlite3
import bcrypt
import os
from datetime import datetime, timedelta
import pandas as pd
from PyQt5.QtWidgets import (
    QApplication, QWidget, QDialog, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QHBoxLayout, QMessageBox, QTableView, QHeaderView,
    QFormLayout, QComboBox, QTextEdit, QSpinBox, QGroupBox, QCheckBox,
    QRadioButton, QButtonGroup, QListWidget, QInputDialog, QFileDialog,
    QTabWidget, QFrame
)
from PyQt5.QtSql import QSqlDatabase, QSqlQueryModel
from PyQt5.QtCore import QDate, Qt, QTimer, QObject, QEvent
from PyQt5.QtGui import QColor, QStandardItemModel, QStandardItem, QPalette

from select_record_dialog import SelectRecordDialog



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

    
class StatoTargaTab(QWidget):
    def __init__(self, conn):
        super().__init__()
        self.setWindowTitle('Stato Lavorazioni')
        self.resize(1000, 600)
        self.conn = conn
        self.cursor = self.conn.cursor()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Search bar and buttons
        self.search_flotta = QLineEdit(self)
        self.search_flotta.setPlaceholderText("Search by Flotta...")
        self.search_flotta.setFixedSize(150, 22)
        self.search_flotta.textChanged.connect(self.load_data)

        
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.setFixedSize(80, 22)
        self.refresh_button.clicked.connect(self.load_data)

        self.export_button = QPushButton("Esporta Excel")
        self.export_button.setFixedSize(100, 22)
        self.export_button.clicked.connect(self.export_to_excel)
        
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.search_flotta)
        button_layout.addWidget(self.refresh_button)
        button_layout.addWidget(self.export_button)
        button_layout.addStretch()

        layout.addLayout(button_layout)

        # Table view for Stato and Targa
        self.table_view = QTableView()
        layout.addWidget(self.table_view)
        
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
        self.load_data()

    def load_data(self):
        stati = [
            'Attesa Perizia', 'Attesa Autorizzazione', 'Attesa Ricambi',
            'Lavorazione Carr.', 'Lavorazione Mecc.', 'Casa Madre',
            'Altri Lavori', 'Pronta', 'Consegnata'
        ]

        flotta_filter = self.search_flotta.text().upper().strip()
        today_str = QDate.currentDate().toString('dd/MM/yyyy')

        if flotta_filter:
            query = '''
                SELECT targa, stato, data_incarico, data_consegnata
                FROM records
                WHERE flotta = ? AND (stato != "Consegnata" OR (stato = "Consegnata" AND data_consegnata = ?))
            '''
            self.cursor.execute(query, (flotta_filter, today_str))
        else:
            query = '''
                SELECT targa, stato, data_incarico, data_consegnata
                FROM records
                WHERE stato != "Consegnata" OR (stato = "Consegnata" AND data_consegnata = ?)
            '''
            self.cursor.execute(query, (today_str,))


        records = self.cursor.fetchall()

        # Initialize the table model
        standard_model = QStandardItemModel()
        standard_model.setHorizontalHeaderLabels(stati)

        # Dictionary to store the targa by stato
        stato_columns = {stato: [] for stato in stati}

        # Populate the dictionary with targa for each stato
        for row in records:
            targa = row['targa']
            stato = row['stato']
            data_incarico = row['data_incarico']

            if stato in stato_columns:
                if stato == 'Consegnata':
                    color = 'green'  # Consegnata status should always be green
                else: 
                    color = self.get_notification_color(data_incarico)
                stato_columns[stato].append((targa, color))

        # Find the maximum number of rows required
        max_rows = max(len(targas) for targas in stato_columns.values())

        # Fill each column (stato) separately with targa and color the cell
        for stato in stati:
            col_index = stati.index(stato)
            targhe_in_stato = stato_columns[stato]
            for row_index in range(max_rows):
                if row_index < len(targhe_in_stato):
                    targa, color = targhe_in_stato[row_index]
                    item = QStandardItem(targa)
                    if color:
                        item.setBackground(QColor(color))
                else:
                    item = QStandardItem('')  # Empty cell if no targa at this row

                standard_model.setItem(row_index, col_index, item)

        self.table_view.setModel(standard_model)
        self.table_view.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

    def get_notification_color(self, data_incarico):
        """Get color based on working days."""
        try:
            data_incarico_date = datetime.strptime(data_incarico, '%d/%m/%Y')
            working_days = self.calculate_working_days(data_incarico_date, datetime.now())
            if 10 < working_days <= 15:
                return 'yellow'
            elif 15 < working_days <= 20:
                return 'orange'
            elif working_days > 20:
                return 'red'
        except ValueError:
            return ''
        return ''

    def calculate_working_days(self, start_date, end_date):
        """Calculate working days between two dates."""
        if start_date > end_date:
            return 0
        day_generator = (start_date + timedelta(days=x) for x in range((end_date - start_date).days + 1))
        working_days = sum(1 for day in day_generator if day.weekday() < 5)
        return working_days

   
    def export_to_excel(self):
        # Get the current Flotta name for the filename
        flotta_filter = self.search_flotta.text().upper().strip() or "Flotta_All"

        # Get the current working directory (location from where the script was run)
        current_dir = os.getcwd()

        # Define the filename based on the Flotta and save in the current directory
        filename = f"{flotta_filter}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        file_path = os.path.join(current_dir, filename)

        # Define the specific states
        stati = [
            'Attesa Perizia', 'Attesa Autorizzazione', 'Attesa Ricambi',
            'Lavorazione Carr.', 'Lavorazione Mecc.', 'Casa Madre',
            'Altri Lavori', 'Pronta', 'Consegnata'
        ]

        # Get all unique 'targa' values, filtering by Flotta if necessary
        if flotta_filter != "Flotta_All":
            query = 'SELECT DISTINCT targa FROM records WHERE flotta LIKE ?'
            self.cursor.execute(query, (f'%{flotta_filter}%',))
        else:
            self.cursor.execute('SELECT DISTINCT targa FROM records')

        targas = [row['targa'] for row in self.cursor.fetchall()]

        # Create a dictionary to map targa to their corresponding stato
        targa_dict = {targa: {stato: '' for stato in stati} for targa in targas}
        self.cursor.execute('SELECT targa, stato FROM records')
        for row in self.cursor.fetchall():
            targa = row['targa']
            stato = row['stato']
            if targa in targa_dict and stato in stati:
                targa_dict[targa][stato] = targa

        # Convert the dictionary to a DataFrame
        df = pd.DataFrame.from_dict(targa_dict, orient='index', columns=stati)

        # Add custom header row with Flotta name and timestamp
        export_data = pd.DataFrame([[
            f"Flotta: {flotta_filter}",
            f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        ]], columns=["Info", "Timestamp"])
        
        # Append the data under the custom header
        with pd.ExcelWriter(file_path, engine='xlsxwriter') as writer:
            export_data.to_excel(writer, sheet_name='Sheet1', index=False, header=False, startrow=0)
            df.to_excel(writer, sheet_name='Sheet1', startrow=2, index=False)  # Export without Targa index

        QMessageBox.information(self, "Export Complete", f"Data successfully exported to {file_path}")

    def showEvent(self, event):
        """Re-load data every time the tab is shown."""
        self.load_data()
        super().showEvent(event)

class LoginDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('DatabaseB2B - Login')
        self.resize(300, 150)
        self.init_ui()
        self.conn = sqlite3.connect('app_database.db')
        self.cursor = self.conn.cursor()
        self.create_users_table()

    def init_ui(self):
        self.label_username = QLabel('Username')
        self.label_password = QLabel('Password')
        self.text_username = QLineEdit()
        self.text_password = QLineEdit()
        self.text_password.setEchoMode(QLineEdit.Password)
        self.button_login = QPushButton('Login')
        self.button_login.clicked.connect(self.handle_login)

        layout = QVBoxLayout()
        layout.addWidget(self.label_username)
        layout.addWidget(self.text_username)
        layout.addWidget(self.label_password)
        layout.addWidget(self.text_password)
        layout.addWidget(self.button_login)

        self.setLayout(layout)

    def create_users_table(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                password BLOB
            )
        ''')
        self.conn.commit()

        self.cursor.execute("SELECT * FROM users WHERE username = ?", ('b2b',))
        if not self.cursor.fetchone():
            hashed_password = bcrypt.hashpw('0000v'.encode('utf-8'), bcrypt.gensalt())
            self.cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", ('b2b', hashed_password))
            self.conn.commit()

    def handle_login(self):
        username = self.text_username.text()
        password = self.text_password.text().encode('utf-8')

        self.cursor.execute("SELECT password FROM users WHERE username=?", (username,))
        result = self.cursor.fetchone()

        if result and bcrypt.checkpw(password, result[0]):
            self.accept()
        else:
            QMessageBox.warning(self, 'Errore', 'Nome utente o password errati')


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('DatabaseB2B')
        self.resize(1400, 800)
        self.conn = sqlite3.connect('app_database.db')
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
        self.create_records_table()

        self.db = QSqlDatabase.addDatabase('QSQLITE')
        self.db.setDatabaseName('app_database.db')
        if not self.db.open():
            QMessageBox.critical(self, 'Errore Database', self.db.lastError().text())
            sys.exit(1)

        self.init_ui()
        self.notifications_checked = False

    def create_records_table(self):
        self.cursor.execute('PRAGMA table_info(records)')
        columns = [info[1] for info in self.cursor.fetchall()]

        required_columns = {
            'id': 'INTEGER PRIMARY KEY AUTOINCREMENT',
            'flotta': 'TEXT',
            'targa': 'TEXT',
            'modello': 'TEXT',
            'entrata': 'TEXT',
            'data_incarico': 'TEXT',
            'ditta': 'TEXT',
            'inizio_mecc': 'TEXT',
            'fine_mecc': 'TEXT',
            'inizio_carr': 'TEXT',
            'fine_carr': 'TEXT',
            'pezzi_carr': 'INTEGER',
            'stato': 'TEXT',
            'note': 'TEXT',
            'gg_entrata_data_incarico': 'INTEGER',
            'prev_uscita': 'TEXT',
            'gg_inizio_meccanica': 'INTEGER',
            'gg_inizio_carr': 'INTEGER',
            'gg_lavorazione_mecc': 'INTEGER',
            'gg_lavorazione_carr': 'INTEGER',
            'downtime': 'INTEGER',
            'data_consegnata': 'TEXT'
        }

        if not columns:
            columns_def = ', '.join([f'{col} {col_type}' for col, col_type in required_columns.items()])
            columns_def += ', UNIQUE(targa, entrata, data_incarico)'
            self.cursor.execute(f'''
                CREATE TABLE records ({columns_def})
            ''')
            self.conn.commit()
        else:
            for col, col_type in required_columns.items():
                if col not in columns:
                    self.cursor.execute(f'ALTER TABLE records ADD COLUMN {col} {col_type}')
            self.conn.commit()

    def init_ui(self):
        self.tab_widget = QTabWidget()
        self.layout = QVBoxLayout()

        # Data Tab
        self.data_tab = QWidget()
        self.data_layout = QHBoxLayout()

        # Left side - Insert Data
        self.insert_group = QGroupBox('Inserisci Dati')
        self.insert_layout = QFormLayout()

        self.text_flotta = QLineEdit()
        self.text_flotta.setMaxLength(16)
        self.text_flotta.setMaximumWidth(200)
        self.text_targa = QLineEdit()
        self.text_targa.setMaxLength(16)
        self.text_targa.setMaximumWidth(200)
        self.text_modello = QLineEdit()
        self.text_modello.setMaxLength(16)
        self.text_modello.setMaximumWidth(200)
        self.date_entrata = QLineEdit()
        self.date_entrata.setMaxLength(10)
        self.date_entrata.setMaximumWidth(200)
        self.date_incarico = QLineEdit()
        self.date_incarico.setMaxLength(10)
        self.date_incarico.setMaximumWidth(200)
        self.date_incarico.returnPressed.connect(self.add_record_wrapper)

        self.insert_layout.addRow('Flotta:', self.text_flotta)
        self.insert_layout.addRow('Targa:', self.text_targa)
        self.insert_layout.addRow('Modello:', self.text_modello)
        self.insert_layout.addRow('Entrata:', self.date_entrata)

        incarico_layout = QHBoxLayout()
        incarico_layout.addWidget(self.date_incarico)
        self.button_add = QPushButton('Aggiungi Record')
        self.button_add.clicked.connect(self.add_record_wrapper)
        self.button_add.setMaximumWidth(120)
        incarico_layout.addWidget(self.button_add)
        incarico_layout.addStretch()

        self.insert_layout.addRow('Data Incarico:', incarico_layout)

        self.insert_group.setLayout(self.insert_layout)

        # Right side - Update Data
        self.update_group = QGroupBox('Aggiorna Dati')
        self.update_layout = QFormLayout()

        self.search_targa = QLineEdit()
        self.search_targa.setMaxLength(16)
        self.search_targa.setMaximumWidth(200)
        self.search_targa.returnPressed.connect(self.search_record_wrapper)
        self.button_search = QPushButton('Cerca')
        self.button_search.clicked.connect(self.search_record_wrapper)
        self.button_search.setMaximumWidth(80)

        search_layout = QHBoxLayout()
        search_layout.addWidget(self.search_targa)
        search_layout.addWidget(self.button_search)
        search_layout.addStretch()
        self.update_layout.addRow('Targa:', search_layout)

        self.update_fields_widget = QWidget()
        self.update_fields_layout = QFormLayout()

        self.text_ditta = QLineEdit()
        self.text_ditta.setMaxLength(16)
        self.text_ditta.setMaximumWidth(200)
        self.date_inizio_mecc = QLineEdit()
        self.date_inizio_mecc.setMaxLength(10)
        self.date_inizio_mecc.setMaximumWidth(200)
        self.date_fine_mecc = QLineEdit()
        self.date_fine_mecc.setMaxLength(10)
        self.date_fine_mecc.setMaximumWidth(200)
        self.date_inizio_carr = QLineEdit()
        self.date_inizio_carr.setMaxLength(10)
        self.date_inizio_carr.setMaximumWidth(200)
        self.date_fine_carr = QLineEdit()
        self.date_fine_carr.setMaxLength(10)
        self.date_fine_carr.setMaximumWidth(200)
        self.spin_pezzi_carr = QSpinBox()
        self.spin_pezzi_carr.setRange(0, 99)
        self.spin_pezzi_carr.setMaximumWidth(200)
        self.combo_stato = QComboBox()
        self.combo_stato.addItems([
            'Attesa Perizia', 'Attesa Autorizzazione', 'Attesa Ricambi',
            'Lavorazione Carr.', 'Lavorazione Mecc.', 'Casa Madre',
            'Altri Lavori', 'Pronta', 'Consegnata'
        ])
        self.combo_stato.setMaximumWidth(200)
        self.text_note = QTextEdit()
        self.text_note.setMaximumHeight(100)
        self.text_note.setMaximumWidth(200)

        self.update_fields_layout.addRow('Ditta:', self.text_ditta)
        self.update_fields_layout.addRow('Inizio Mecc.:', self.date_inizio_mecc)
        self.update_fields_layout.addRow('Fine Mecc.:', self.date_fine_mecc)
        self.update_fields_layout.addRow('Inizio Carr.:', self.date_inizio_carr)
        self.update_fields_layout.addRow('Fine Carr.:', self.date_fine_carr)
        self.update_fields_layout.addRow('Pezzi Carr.:', self.spin_pezzi_carr)
        self.update_fields_layout.addRow('Stato:', self.combo_stato)
        self.update_fields_layout.addRow('Note:', self.text_note)

        self.button_update = QPushButton('Aggiorna Record')
        self.button_update.clicked.connect(self.update_record_wrapper)
        self.button_update.setMaximumWidth(120)
        self.button_delete = QPushButton('Elimina Record')
        self.button_delete.clicked.connect(self.delete_record_wrapper)
        self.button_delete.setMaximumWidth(120)
        self.button_back_update = QPushButton('Indietro')
        self.button_back_update.clicked.connect(self.hide_update_fields)
        self.button_back_update.setMaximumWidth(100)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.button_update)
        button_layout.addWidget(self.button_delete)
        button_layout.addWidget(self.button_back_update)
        button_layout.addStretch()
        self.update_fields_layout.addRow('', button_layout)

        self.update_fields_widget.setLayout(self.update_fields_layout)

        self.update_fields_widget.hide()

        self.update_layout.addRow(self.update_fields_widget)
        self.update_group.setLayout(self.update_layout)

        # Estrapola Data Group
        self.extrapolate_group = QGroupBox('Estrapola Dati')
        self.extrapolate_layout = QFormLayout()

        self.radio_all_data = QRadioButton('Estrapola tutti i dati in Excel')
        self.radio_exclude_consegnata = QRadioButton('Estrapola tutti i dati escludendo "Consegnata"')
        self.radio_by_flotta = QRadioButton('Estrapola dati per Flotta')
        self.radio_stato_report = QRadioButton('Estrapola Stato')

        self.radio_group = QButtonGroup()
        self.radio_group.addButton(self.radio_all_data)
        self.radio_group.addButton(self.radio_exclude_consegnata)
        self.radio_group.addButton(self.radio_by_flotta)
        self.radio_group.addButton(self.radio_stato_report)

        self.extrapolate_layout.addRow(self.radio_all_data)
        self.extrapolate_layout.addRow(self.radio_exclude_consegnata)
        self.extrapolate_layout.addRow(self.radio_by_flotta)
        self.extrapolate_layout.addRow(self.radio_stato_report)

        self.text_flotta_extrapolate = QLineEdit()
        self.text_flotta_extrapolate.setMaximumWidth(200)
        self.checkbox_exclude_consegnata = QCheckBox('Solo "Consegnata"')
        self.checkbox_exclude_consegnata.setChecked(False)

        self.extrapolate_layout.addRow('Flotta:', self.text_flotta_extrapolate)
        self.extrapolate_layout.addRow('', self.checkbox_exclude_consegnata)

        self.text_flotta_extrapolate.setEnabled(False)
        self.checkbox_exclude_consegnata.setEnabled(False)

        self.radio_all_data.toggled.connect(self.update_extrapolate_options)
        self.radio_exclude_consegnata.toggled.connect(self.update_extrapolate_options)
        self.radio_by_flotta.toggled.connect(self.update_extrapolate_options)
        self.radio_stato_report.toggled.connect(self.update_extrapolate_options)

        self.button_extrapolate_execute = QPushButton('Estrapola Excel')
        self.button_extrapolate_execute.clicked.connect(self.execute_extrapolate)
        self.button_back = QPushButton('Indietro')
        self.button_back.clicked.connect(self.toggle_extrapolate_group)
        button_layout_extrapolate = QHBoxLayout()
        button_layout_extrapolate.addWidget(self.button_extrapolate_execute)
        button_layout_extrapolate.addWidget(self.button_back)
        self.extrapolate_layout.addRow('', button_layout_extrapolate)

        self.extrapolate_group.setLayout(self.extrapolate_layout)
        self.extrapolate_group.hide()

        self.button_extrapolate = QPushButton('Estrapola Dati')
        self.button_extrapolate.clicked.connect(self.toggle_extrapolate_group)
        self.button_extrapolate.setMaximumWidth(150)

        # Import Data Button
        self.button_import = QPushButton('Importa Dati')
        self.button_import.clicked.connect(self.import_data_wrapper)
        self.button_import.setMaximumWidth(150)

        # Arrange layouts
        left_layout = QVBoxLayout()
        left_layout.addWidget(self.insert_group)

        # Create a horizontal layout for "Estrapola Dati" and "Importa Dati" buttons
        extrapolate_import_layout = QHBoxLayout()
        extrapolate_import_layout.addWidget(self.button_extrapolate)
        extrapolate_import_layout.addWidget(self.button_import)
        extrapolate_import_layout.addStretch()

        left_layout.addLayout(extrapolate_import_layout)
        left_layout.addWidget(self.extrapolate_group)
        left_layout.addStretch()

        right_layout = QVBoxLayout()
        right_layout.addWidget(self.update_group)
        right_layout.addStretch()

        self.data_layout.addLayout(left_layout)
        self.data_layout.addLayout(right_layout)

        # Table View
        self.table = QTableView()
        self.load_data()

        data_main_layout = QVBoxLayout()
        data_main_layout.addLayout(self.data_layout)
        data_main_layout.addWidget(self.table)

        self.data_tab.setLayout(data_main_layout)

        # Notifications Tab
        self.notifications_tab = NotificationsWindow(self.conn)
        
        # StatoTarga Tab (new tab for Stato and Targa)
        self.stato_targa_tab = StatoTargaTab(self.conn)



        # Add tabs to tab widget
        self.tab_widget.addTab(self.data_tab, "Dati")
        self.tab_widget.addTab(self.notifications_tab, "Notifiche")
        self.tab_widget.addTab(self.stato_targa_tab, "Stato Lavorazioni")

        self.layout.addWidget(self.tab_widget)
        self.setLayout(self.layout)

        # Install event filter to detect first user action
        self.installEventFilter(self)

    def eventFilter(self, source, event):
        if not self.notifications_checked and event.type() in (QEvent.MouseButtonPress, QEvent.KeyPress):
            self.check_notifications()
            self.notifications_checked = True
        return super().eventFilter(source, event)

    def hide_update_fields(self):
        self.update_fields_widget.hide()

    def toggle_extrapolate_group(self):
        if self.extrapolate_group.isVisible():
            self.extrapolate_group.hide()
        else:
            self.extrapolate_group.show()

    def update_extrapolate_options(self):
        if self.radio_by_flotta.isChecked():
            self.text_flotta_extrapolate.setEnabled(True)
            self.checkbox_exclude_consegnata.setEnabled(True)
        else:
            self.text_flotta_extrapolate.setEnabled(False)
            self.checkbox_exclude_consegnata.setEnabled(False)

    def execute_extrapolate(self):
        if self.radio_all_data.isChecked():
            query = 'SELECT * FROM records'
            params = []
            filename = 'DataBaseB2B.xlsx'
        elif self.radio_exclude_consegnata.isChecked():
            query = 'SELECT * FROM records WHERE stato != ?'
            params = ['Consegnata']
            filename = 'DataBaseB2B_lavorazione.xlsx'
        elif self.radio_by_flotta.isChecked():
            flotta = self.text_flotta_extrapolate.text().upper()
            if not flotta:
                QMessageBox.warning(self, 'Errore di input', 'Per favore, inserisci la Flotta.')
                return
            only_consegnata = self.checkbox_exclude_consegnata.isChecked()
            query = 'SELECT * FROM records WHERE flotta = ?'
            params = [flotta]
            if only_consegnata:
                query += ' AND stato = ?'
                params.append('Consegnata')
                filename = f'DataBaseB2B_{flotta}_consegnata.xlsx'
            else:
                filename = f'DataBaseB2B_{flotta}.xlsx'
        elif self.radio_stato_report.isChecked():
            query = '''
                SELECT targa, stato, data_consegnata 
                FROM records 
                WHERE NOT (stato = "Consegnata" AND data_consegnata < ?)
            '''
            params = [datetime.now().strftime('%d/%m/%Y')]
            filename = 'DataBaseB2B_stato.xlsx'
        else:
            QMessageBox.warning(self, 'Errore di selezione', 'Per favore, seleziona un\'opzione.')
            return

        try:
            df = pd.read_sql_query(query, self.conn, params=params)
            if df.empty:
                QMessageBox.information(self, 'Nessun dato', 'Nessun dato trovato per i criteri selezionati.')
                return

            if self.radio_stato_report.isChecked():
                stato_counts = df['stato'].value_counts()
                total_count = len(df)
                df_summary = pd.DataFrame({
                    'Stato': stato_counts.index,
                    'Conteggio': stato_counts.values
                })
                total_row = pd.DataFrame({'Stato': ['Totale'], 'Conteggio': [total_count]})
                df_summary = pd.concat([df_summary, total_row], ignore_index=True)
                with pd.ExcelWriter(filename) as writer:
                    df.to_excel(writer, index=False, sheet_name='Dati')
                    df_summary.to_excel(writer, index=False, sheet_name='Riepilogo')
            else:
                df.to_excel(filename, index=False)
            QMessageBox.information(self, 'Successo', f'Dati esportati nel file {filename}')
            self.extrapolate_group.hide()
        except Exception as e:
            QMessageBox.warning(self, 'Errore', str(e))

    def load_data(self):
        self.model = QSqlQueryModel(self)
        self.model.setQuery('SELECT * FROM records ORDER BY id DESC LIMIT 40', self.db)

        headers = [
            'ID', 'Flotta', 'Targa', 'Modello', 'Entrata', 'Data Incarico',
            'Ditta', 'Inizio Mecc.', 'Fine Mecc.', 'Inizio Carr.', 'Fine Carr.',
            'Pezzi Carr.', 'Stato', 'Note', 'Prev. Uscita', 'Data Consegnata','Downtime',
            'GG Entrata_Incarico', 'GG Inizio Mecc.', 'GG Inizio Carr.',
            'GG Lavorazione Mecc.', 'GG Lavorazione Carr.',  
        ]

        for i, header in enumerate(headers):
            self.model.setHeaderData(i, Qt.Horizontal, header)

        self.table.setModel(self.model)
        self.table.hideColumn(0)  # Hide ID column
        self.table.setEditTriggers(QTableView.NoEditTriggers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

    def add_record_wrapper(self):
        self.add_record()

    def search_record_wrapper(self):
        self.search_record()

    def update_record_wrapper(self):
        self.update_record()

    def delete_record_wrapper(self):
        self.delete_record()

    def add_record(self):
        flotta = self.text_flotta.text().upper()
        targa = self.text_targa.text().upper()
        modello = self.text_modello.text().upper()
        entrata = self.date_entrata.text()
        data_incarico = self.date_incarico.text()

        if not all([flotta, targa, modello, entrata, data_incarico]):
            QMessageBox.warning(self, 'Errore di input', 'Per favore, riempi tutti i campi.')
            return

        entrata_date = QDate.fromString(entrata, 'dd/MM/yyyy')
        data_incarico_date = QDate.fromString(data_incarico, 'dd/MM/yyyy')
        if not entrata_date.isValid() or not data_incarico_date.isValid():
            QMessageBox.warning(self, 'Errore di input', 'Inserisci le date nel formato dd/mm/yyyy')
            return

        self.cursor.execute('''
            SELECT COUNT(*) FROM records WHERE targa = ? AND entrata = ? AND data_incarico = ?
        ''', (targa, entrata, data_incarico))
        if self.cursor.fetchone()[0] > 0:
            QMessageBox.warning(self, 'Errore', 'Targa già presente nel Database!')
            return

        self.cursor.execute('''
            SELECT COUNT(*) FROM records WHERE targa = ? AND entrata = ?
        ''', (targa, entrata))
        if self.cursor.fetchone()[0] > 0:
            QMessageBox.warning(self, 'Errore', 'Targa già presente con la stessa data di entrata!')
            return

        gg_entrata_data_incarico = self.calculate_working_days(entrata, data_incarico)
        prev_uscita = self.add_working_days(data_incarico, 10)

        try:
            self.cursor.execute('''
                INSERT INTO records (flotta, targa, modello, entrata, data_incarico,
                                     gg_entrata_data_incarico, prev_uscita)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (flotta, targa, modello, entrata, data_incarico,
                  gg_entrata_data_incarico, prev_uscita))
            self.conn.commit()
            self.text_flotta.clear()
            self.text_targa.clear()
            self.text_modello.clear()
            self.date_entrata.clear()
            self.date_incarico.clear()
            self.load_data()
            self.notifications_tab.load_notifications()
        except Exception as e:
            QMessageBox.warning(self, 'Errore', str(e))

    def search_record(self):
        targa = self.search_targa.text().upper()
        if not targa:
            QMessageBox.warning(self, 'Errore di input', 'Per favore, inserisci la Targa da cercare.')
            return
        try:
            self.cursor.execute('SELECT * FROM records WHERE targa = ?', (targa,))
            records = self.cursor.fetchall()
            if records:
                if len(records) == 1:
                    self.record = records[0]
                    self.update_fields_widget.show()
                    self.populate_update_fields()
                else:
                    self.select_record_dialog = SelectRecordDialog(records)
                    if self.select_record_dialog.exec_():
                        self.record = self.select_record_dialog.selected_record
                        self.update_fields_widget.show()
                        self.populate_update_fields()
                    else:
                        self.update_fields_widget.hide()
            else:
                QMessageBox.warning(self, 'Non trovato', 'Nessun record trovato per la Targa inserita.')
                self.update_fields_widget.hide()
        except Exception as e:
            QMessageBox.warning(self, 'Errore', str(e))

    def populate_update_fields(self):
        self.text_ditta.setText(self.record['ditta'] or '')
        self.date_inizio_mecc.setText(self.record['inizio_mecc'] or '')
        self.date_fine_mecc.setText(self.record['fine_mecc'] or '')
        self.date_inizio_carr.setText(self.record['inizio_carr'] or '')
        self.date_fine_carr.setText(self.record['fine_carr'] or '')
        self.spin_pezzi_carr.setValue(self.record['pezzi_carr'] if self.record['pezzi_carr'] is not None else 0)
        if self.record['stato']:
            index = self.combo_stato.findText(self.record['stato'])
            if index >= 0:
                self.combo_stato.setCurrentIndex(index)
            else:
                self.combo_stato.setCurrentIndex(0)
        else:
            self.combo_stato.setCurrentIndex(0)
        self.text_note.setText(self.record['note'] or '')

    def update_record(self):
        if not hasattr(self, 'record') or not self.record:
            QMessageBox.warning(self, 'Errore', 'Nessun record selezionato per l\'aggiornamento.')
            return
        targa = self.record['targa']
        entrata = self.record['entrata']
        data_incarico = self.record['data_incarico']
        ditta = self.text_ditta.text().upper()
        inizio_mecc = self.date_inizio_mecc.text()
        fine_mecc = self.date_fine_mecc.text()
        inizio_carr = self.date_inizio_carr.text()
        fine_carr = self.date_fine_carr.text()
        pezzi_carr = self.spin_pezzi_carr.value()
        stato = self.combo_stato.currentText()
        note = self.text_note.toPlainText()

        date_fields = [inizio_mecc, fine_mecc, inizio_carr, fine_carr]
        for date_str in date_fields:
            if date_str:
                date_obj = QDate.fromString(date_str, 'dd/MM/yyyy')
                if not date_obj.isValid():
                    QMessageBox.warning(self, 'Errore di input', 'Inserisci le date nel formato dd/mm/yyyy')
                    return

        gg_inizio_meccanica = self.calculate_working_days(data_incarico, inizio_mecc) if inizio_mecc else None
        gg_inizio_carr = self.calculate_working_days(data_incarico, inizio_carr) if inizio_carr else None
        gg_lavorazione_mecc = self.calculate_working_days(inizio_mecc, fine_mecc) if inizio_mecc and fine_mecc else None
        gg_lavorazione_carr = self.calculate_working_days(inizio_carr, fine_carr) if inizio_carr and fine_carr else None

        date_list = [fine_mecc, fine_carr, inizio_mecc, inizio_carr]
        date_list = [date for date in date_list if date]
        if date_list:
            try:
                last_date = max([datetime.strptime(date, '%d/%m/%Y') for date in date_list]).strftime('%d/%m/%Y')
                downtime = self.calculate_working_days(data_incarico, last_date)
            except ValueError:
                downtime = None
        else:
            downtime = None

        data_consegnata = self.record['data_consegnata']
        if stato == 'Consegnata':
            if not data_consegnata:
                data_consegnata = datetime.now().strftime('%d/%m/%Y')
        else:
            data_consegnata = None

        try:
            self.cursor.execute('''
                UPDATE records
                SET ditta = ?, inizio_mecc = ?, fine_mecc = ?, inizio_carr = ?, fine_carr = ?,
                    pezzi_carr = ?, stato = ?, note = ?,
                    gg_inizio_meccanica = ?, gg_inizio_carr = ?,
                    gg_lavorazione_mecc = ?, gg_lavorazione_carr = ?, downtime = ?,
                    data_consegnata = ?
                WHERE targa = ? AND entrata = ? AND data_incarico = ?
            ''', (ditta, inizio_mecc, fine_mecc, inizio_carr, fine_carr, pezzi_carr, stato, note,
                  gg_inizio_meccanica, gg_inizio_carr, gg_lavorazione_mecc, gg_lavorazione_carr,
                  downtime, data_consegnata, targa, entrata, data_incarico))
            self.conn.commit()
            QMessageBox.information(self, 'Successo', 'Record aggiornato con successo.')
            self.update_fields_widget.hide()
            self.load_data()
            self.notifications_tab.load_notifications()
        except Exception as e:
            QMessageBox.warning(self, 'Errore', str(e))

    def delete_record(self):
        if not hasattr(self, 'record') or not self.record:
            QMessageBox.warning(self, 'Errore', 'Nessun record selezionato per la cancellazione.')
            return
        password, ok = QInputDialog.getText(self, 'Password Master', 'Inserisci la password master:', QLineEdit.Password)
        if ok:
            if password == 'b2b2024!':
                reply = QMessageBox.question(self, 'Conferma Cancellazione', 'Sei sicuro di voler cancellare questo record?',
                                             QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                if reply == QMessageBox.Yes:
                    targa = self.record['targa']
                    entrata = self.record['entrata']
                    data_incarico = self.record['data_incarico']
                    try:
                        self.cursor.execute('''
                            DELETE FROM records WHERE targa = ? AND entrata = ? AND data_incarico = ?
                        ''', (targa, entrata, data_incarico))
                        self.conn.commit()
                        QMessageBox.information(self, 'Successo', 'Record cancellato con successo.')
                        self.update_fields_widget.hide()
                        self.load_data()
                        self.notifications_tab.load_notifications()
                        self.record = None
                    except Exception as e:
                        QMessageBox.warning(self, 'Errore', str(e))
                else:
                    pass
            else:
                QMessageBox.warning(self, 'Errore', 'Password master errata.')

    def calculate_working_days(self, start_date_str, end_date_str):
        if not start_date_str or not end_date_str:
            return 0
        try:
            start_date = datetime.strptime(start_date_str, '%d/%m/%Y')
            end_date = datetime.strptime(end_date_str, '%d/%m/%Y')
            if start_date > end_date:
                return 0
            day_generator = (start_date + timedelta(days=x) for x in range((end_date - start_date).days + 1))
            working_days = sum(1 for day in day_generator if day.weekday() < 5)
            return working_days
        except ValueError:
            return 0

    def add_working_days(self, start_date_str, days_to_add):
        if not start_date_str:
            return None
        try:
            start_date = datetime.strptime(start_date_str, '%d/%m/%Y')
            current_date = start_date
            added_days = 0
            while added_days < days_to_add:
                current_date += timedelta(days=1)
                if current_date.weekday() < 5:
                    added_days += 1
            return current_date.strftime('%d/%m/%Y')
        except ValueError:
            return None

    def import_data_wrapper(self):
        self.import_data()

    def import_data(self):
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getOpenFileName(self, "Importa Dati", "",
                                                "Excel Files (*.xlsx);;CSV Files (*.csv)", options=options)
        if file_path:
            try:
                # Load the data
                if file_path.endswith('.xlsx'):
                    df = pd.read_excel(file_path)
                elif file_path.endswith('.csv'):
                    df = pd.read_csv(file_path)
                else:
                    QMessageBox.warning(self, 'Formato non supportato', 'Seleziona un file .xlsx o .csv')
                    return

                # Required columns expected by the database
                required_columns = [
                    'flotta', 'targa', 'modello', 'entrata', 'data_incarico',
                    'ditta', 'inizio_mecc', 'fine_mecc', 'inizio_carr', 'fine_carr',
                    'pezzi_carr', 'stato', 'note', 'data_consegnata'
                ]
                
                # Function to match similar column names (fuzzy matching)
                def find_closest_column(required_col, available_columns):
                    for col in available_columns:
                        if required_col.lower() in col.lower() or col.lower() in required_col.lower():
                            return col
                    return None

                # Try to map the columns based on fuzzy matching
                column_mapping = {}
                for required_col in required_columns:
                    matched_col = find_closest_column(required_col, df.columns)
                    if matched_col:
                        column_mapping[required_col] = matched_col

                # Only import the matched columns
                matched_columns = [col for col in required_columns if col in column_mapping]
                
                # Log any missing columns that couldn't be matched
                missing_columns = [col for col in required_columns if col not in column_mapping]
                if missing_columns:
                    print(f"Skipping missing columns: {missing_columns}")
                
                if matched_columns:
                    for index, row in df.iterrows():
                        try:
                            # Extract values for matched columns and convert Timestamps to string
                            record_values = []
                            for col in matched_columns:
                                value = row[column_mapping[col]]
                                
                                # Check if the value is a Timestamp and convert it to a string
                                if isinstance(value, pd.Timestamp):
                                    value = value.strftime('%Y-%m-%d')  # Format as 'YYYY-MM-DD'
                                elif pd.isna(value):
                                    value = ''  # Handle missing values
                                
                                record_values.append(value)

                            # Prepare the INSERT SQL statement dynamically based on matched columns
                            placeholders = ', '.join(['?' for _ in matched_columns])
                            sql = f"INSERT INTO records ({', '.join(matched_columns)}) VALUES ({placeholders})"

                            # Execute the SQL statement with the extracted values
                            self.cursor.execute(sql, tuple(record_values))

                        except Exception as e:
                            print(f"Error inserting record at row {index}: {e}")
                            continue  # Skip problematic rows

                    self.conn.commit()
                    print(f"Successfully imported data with available columns: {matched_columns}")

                    QMessageBox.information(self, 'Successo', 'Dati importati con successo.')
                    self.load_data()
                    self.notifications_tab.load_notifications()
                else:
                    QMessageBox.warning(self, 'Errore di formato', 'Nessuna colonna corrisponde ai dati richiesti.')

            except Exception as e:
                QMessageBox.warning(self, 'Errore', str(e))



    def check_notifications(self):
        self.notifications_tab.load_notifications()

    def load_notifications(self):
        self.notifications_tab.load_notifications()

    def load_notifications_tab(self):
        self.notifications_tab.load_notifications()




def main():
    app = QApplication(sys.argv)
    login = LoginDialog()
    if login.exec_() == QDialog.Accepted:
        window = MainWindow()
        window.show()
        sys.exit(app.exec_())


if __name__ == '__main__':
    main()
