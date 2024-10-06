import sys
import sqlite3
import pandas as pd
from PyQt5.QtWidgets import (
    QApplication, QWidget, QDialog, QLineEdit, QPushButton,
    QVBoxLayout, QHBoxLayout, QMessageBox, QTableView, QHeaderView,
    QFormLayout, QComboBox, QTextEdit, QSpinBox, QGroupBox, QCheckBox,
    QRadioButton, QButtonGroup, QInputDialog, QFileDialog,
    QTabWidget
)
from PyQt5.QtSql import QSqlDatabase, QSqlQueryModel
from PyQt5.QtCore import QDate, Qt, QEvent, pyqtSignal

from select_record_dialog import SelectRecordDialog
from datetime import datetime, timedelta
from notifications_window import NotificationsWindow
from stato_targa_tab import StatoTargaTab
from login_dialog import LoginDialog
from data_importer import import_data
from data_exporter import execute_extrapolate
from RecapDataTab import RecapDataTab  
from Statistiche2Tab import Statistiche2Tab

class MainWindow(QWidget):
    data_changed = pyqtSignal()  #Signal to indicate data change

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

        # Create the ditta_operatori table if it doesn't exist
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS ditta_operatori (
                ditta TEXT PRIMARY KEY,
                nr_operatori INTEGER
            )
        ''')
        self.conn.commit()

        # Create the weekly_statistics table if it doesn't exist
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS weekly_statistics (
                ditta TEXT,
                week_number INTEGER,
                year INTEGER,
                vetture_finite_nel_settimana INTEGER,
                totale_pz INTEGER,
                media_vetture_al_gg REAL,
                media_pz_per_vettura REAL,
                media_pezzi_al_gg REAL,
                media_pz_per_op_al_gg REAL,
                nr_operatori INTEGER,
                working_days INTEGER,
                PRIMARY KEY (ditta, week_number, year)
            )
        ''')
        self.conn.commit()

        # Check and add the 'working_days' column if it doesn't exist
        self.cursor.execute("PRAGMA table_info(weekly_statistics)")
        weekly_columns = [info[1] for info in self.cursor.fetchall()]
        if 'working_days' not in weekly_columns:
            self.cursor.execute("ALTER TABLE weekly_statistics ADD COLUMN working_days INTEGER")
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
        self.date_incarico.returnPressed.connect(self.add_record)

        self.combo_stato_insert = QComboBox()
        self.combo_stato_insert.addItems([
            'Attesa Perizia', 'Attesa Autorizzazione', 'Attesa Ricambi',
            'Lavorazione Carr.', 'Lavorazione Mecc.', 'Casa Madre',
            'Altri Lavori', 'Pronta', 'Consegnata'
        ])
        self.combo_stato_insert.setMaximumWidth(200)

        self.insert_layout.addRow('Flotta:', self.text_flotta)
        self.insert_layout.addRow('Targa:', self.text_targa)
        self.insert_layout.addRow('Modello:', self.text_modello)
        self.insert_layout.addRow('Entrata:', self.date_entrata)

        incarico_layout = QHBoxLayout()
        incarico_layout.addWidget(self.date_incarico)
        self.button_add = QPushButton('Aggiungi Record')
        self.button_add.clicked.connect(self.add_record)
        self.button_add.setMaximumWidth(120)
        incarico_layout.addWidget(self.button_add)
        incarico_layout.addStretch()

        self.insert_layout.addRow('Data Incarico:', incarico_layout)
        self.insert_layout.addRow('Stato:', self.combo_stato_insert)

        self.insert_group.setLayout(self.insert_layout)

        # Right side - Update Data
        self.update_group = QGroupBox('Aggiorna Dati')
        self.update_layout = QFormLayout()

        self.search_targa = QLineEdit()
        self.search_targa.setMaxLength(16)
        self.search_targa.setMaximumWidth(200)
        self.search_targa.returnPressed.connect(self.search_record)
        self.button_search = QPushButton('Cerca')
        self.button_search.clicked.connect(self.search_record)
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
        self.button_update.clicked.connect(self.update_record)
        self.button_update.setMaximumWidth(120)
        self.button_delete = QPushButton('Elimina Record')
        self.button_delete.clicked.connect(self.delete_record)
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

        self.radio_group = QButtonGroup()
        self.radio_group.addButton(self.radio_all_data)
        self.radio_group.addButton(self.radio_exclude_consegnata)

        self.extrapolate_layout.addRow(self.radio_all_data)
        self.extrapolate_layout.addRow(self.radio_exclude_consegnata)

        self.checkbox_exclude_consegnata = QCheckBox('Solo "Consegnata"')
        self.checkbox_exclude_consegnata.setChecked(False)

        self.extrapolate_layout.addRow('', self.checkbox_exclude_consegnata)

        self.checkbox_exclude_consegnata.setEnabled(False)

        self.radio_all_data.toggled.connect(self.update_extrapolate_options)
        self.radio_exclude_consegnata.toggled.connect(self.update_extrapolate_options)

        self.button_extrapolate_execute = QPushButton('Estrapola Excel')
        self.button_extrapolate_execute.clicked.connect(lambda: execute_extrapolate(self))
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
        self.button_import.clicked.connect(lambda: import_data(self))
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

        # StatoTarga Tab
        self.stato_targa_tab = StatoTargaTab(self.conn)
        
        # RecapDataTab
        self.recap_data_tab = RecapDataTab(self.conn)
        self.data_changed.connect(self.recap_data_tab.refresh_data)  # Connect the signal

        # Statistiche2
        self.statistiche2_tab = Statistiche2Tab(self.conn) 
        # Add tabs to tab widget
        self.tab_widget.addTab(self.data_tab, "Dati")
        self.tab_widget.addTab(self.notifications_tab, "Notifiche")
        self.tab_widget.addTab(self.stato_targa_tab, "Stato Lavorazioni")
        self.tab_widget.addTab(self.recap_data_tab, "Statistiche")
        self.tab_widget.addTab(self.statistiche2_tab, "Statistiche 2")

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
        self.checkbox_exclude_consegnata.setEnabled(self.radio_exclude_consegnata.isChecked())

    def load_data(self):
        self.model = QSqlQueryModel(self)
        self.model.setQuery('SELECT * FROM records ORDER BY id DESC LIMIT 40', self.db)

        headers = [
            'ID', 'Flotta', 'Targa', 'Modello', 'Entrata', 'Data Incarico',
            'Ditta', 'Inizio Mecc.', 'Fine Mecc.', 'Inizio Carr.', 'Fine Carr.',
            'Pezzi Carr.', 'Stato', 'Note', 'Prev. Uscita', 'Data Consegnata', 'Downtime',
            'GG Entrata_Incarico', 'GG Inizio Mecc.', 'GG Inizio Carr.',
            'GG Lavorazione Mecc.', 'GG Lavorazione Carr.',
        ]

        for i, header in enumerate(headers):
            self.model.setHeaderData(i, Qt.Horizontal, header)

        self.table.setModel(self.model)
        self.table.hideColumn(0)  # Hide ID column
        self.table.setEditTriggers(QTableView.NoEditTriggers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

    def add_record(self):
        flotta = self.text_flotta.text().upper()
        targa = self.text_targa.text().upper()
        modello = self.text_modello.text().upper()
        entrata = self.date_entrata.text()
        data_incarico = self.date_incarico.text()
        stato = self.combo_stato_insert.currentText()

        if not all([flotta, targa, modello, entrata, data_incarico, stato]):
            QMessageBox.warning(self, 'Errore di input', 'Per favore, riempi tutti i campi.')
            return

        entrata_date = QDate.fromString(entrata, 'dd/MM/yyyy')
        data_incarico_date = QDate.fromString(data_incarico, 'dd/MM/yyyy')
        if not entrata_date.isValid() or not data_incarico_date.isValid():
            QMessageBox.warning(self, 'Errore di input', 'Inserisci le date nel formato dd/mm/yyyy')
            return

        # Adjust dates to last working day
        entrata = self.adjust_date_to_last_working_day(entrata)
        data_incarico = self.adjust_date_to_last_working_day(data_incarico)

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
                                     stato, gg_entrata_data_incarico, prev_uscita)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (flotta, targa, modello, entrata, data_incarico, stato,
                  gg_entrata_data_incarico, prev_uscita))
            self.conn.commit()
            self.data_changed.emit()  # Emit signal to update statistics
            self.text_flotta.clear()
            self.text_targa.clear()
            self.text_modello.clear()
            self.date_entrata.clear()
            self.date_incarico.clear()
            self.combo_stato_insert.setCurrentIndex(0)
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
            QMessageBox.warning(self, 'Errore', "Nessun record selezionato per l'aggiornamento.")
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

        # Adjust dates to last working day
        date_fields_dict = {
            'inizio_mecc': inizio_mecc,
            'fine_mecc': fine_mecc,
            'inizio_carr': inizio_carr,
            'fine_carr': fine_carr
        }
        for key, date_str in date_fields_dict.items():
            if date_str:
                adjusted_date = self.adjust_date_to_last_working_day(date_str)
                date_fields_dict[key] = adjusted_date

        # Update variables with adjusted dates
        inizio_mecc = date_fields_dict['inizio_mecc']
        fine_mecc = date_fields_dict['fine_mecc']
        inizio_carr = date_fields_dict['inizio_carr']
        fine_carr = date_fields_dict['fine_carr']

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
            self.data_changed.emit()  # Emit signal to update statistics
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
                        self.data_changed.emit()  # Emit signal to update statistics
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
            start_date = datetime.strptime(start_date_str, '%d/%m/%Y').date()
            end_date = datetime.strptime(end_date_str, '%d/%m/%Y').date()
            if start_date > end_date:
                return 0
            holidays = self.get_holidays_in_rome(start_date.year)
            day_generator = (start_date + timedelta(days=x) for x in range((end_date - start_date).days + 1))
            working_days = sum(1 for day in day_generator if day.weekday() < 5 and day not in holidays)
            return working_days
        except ValueError:
            return 0

    def add_working_days(self, start_date_str, days_to_add):
        if not start_date_str:
            return None
        try:
            start_date = datetime.strptime(start_date_str, '%d/%m/%Y').date()
            current_date = start_date
            added_days = 0
            holidays = self.get_holidays_in_rome(start_date.year)
            while added_days < days_to_add:
                current_date += timedelta(days=1)
                if current_date.weekday() < 5 and current_date not in holidays:
                    added_days += 1
            return current_date.strftime('%d/%m/%Y')
        except ValueError:
            return None

    def get_holidays_in_rome(self, year):
        holidays = [
            datetime(year, 1, 1).date(),   # New Year's Day
            datetime(year, 1, 6).date(),   # Epiphany
            datetime(year, 4, 25).date(),  # Liberation Day
            datetime(year, 5, 1).date(),   # Labor Day
            datetime(year, 6, 2).date(),   # Republic Day
            datetime(year, 6, 29).date(),  # St. Peter and Paul
            datetime(year, 8, 15).date(),  # Assumption Day
            datetime(year, 11, 1).date(),  # All Saints' Day
            datetime(year, 12, 8).date(),  # Immaculate Conception
            datetime(year, 12, 25).date(), # Christmas Day
            datetime(year, 12, 26).date(), # St. Stephen's Day
        ]
        # Include Easter Monday
        easter_monday = self.calculate_easter_monday(year)
        holidays.append(easter_monday)
        return holidays

    def calculate_easter_monday(self, year):
        a = year % 19
        b = year // 100
        c = year % 100
        d = b // 4
        e = b % 4
        f = (b + 8) // 25
        g = (b - f + 1) // 3
        h = (19 * a + b - d - g + 15) % 30
        i = c // 4
        k = c % 4
        l = (32 + 2 * e + 2 * i - h - k) % 7
        m = (a + 11 * h + 22 * l) // 451
        month = (h + l - 7 * m + 114) // 31
        day = ((h + l - 7 * m + 114) % 31) + 1
        easter_sunday = datetime(year, month, day).date()
        easter_monday = easter_sunday + timedelta(days=1)
        return easter_monday

    def adjust_date_to_last_working_day(self, date_str):
        date_obj = datetime.strptime(date_str, '%d/%m/%Y').date()
        holidays = self.get_holidays_in_rome(date_obj.year)
        while date_obj.weekday() >= 5 or date_obj in holidays:
            date_obj -= timedelta(days=1)
        return date_obj.strftime('%d/%m/%Y')

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
