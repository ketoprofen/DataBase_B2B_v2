from PyQt5.QtWidgets import QDialog, QLabel, QLineEdit, QPushButton, QVBoxLayout, QMessageBox, QHBoxLayout
import bcrypt
import sqlite3
from PyQt5.QtWidgets import QLabel, QDialog

class LoginDialog(QDialog):
    MASTER_PASSWORD = 'b2b2024!'  # Sostituisci con la tua master password

    def __init__(self):
        super().__init__()
        self.setWindowTitle('DatabaseB2B - Login')
        self.resize(300, 150)
        self.init_ui()
        self.conn = sqlite3.connect('app_database.db')
        self.cursor = self.conn.cursor()
        self.create_users_table()
        self.create_activity_log_table()  # Creazione tabella di log

    def init_ui(self):
        self.label_username = QLabel('Username')
        self.label_password = QLabel('Password')
        self.text_username = QLineEdit()
        self.text_password = QLineEdit()
        self.text_password.setEchoMode(QLineEdit.Password)
        self.button_login = QPushButton('Login')
        self.button_create_account = QPushButton('Crea un account')

        self.button_login.clicked.connect(self.handle_login)
        self.button_create_account.clicked.connect(self.open_create_account_dialog)

        layout = QVBoxLayout()
        layout.addWidget(self.label_username)
        layout.addWidget(self.text_username)
        layout.addWidget(self.label_password)
        layout.addWidget(self.text_password)
        layout.addWidget(self.button_login)

        create_layout = QHBoxLayout()
        create_layout.addStretch()
        create_layout.addWidget(self.button_create_account)
        layout.addLayout(create_layout)

        self.setLayout(layout)

    def create_users_table(self):
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password BLOB
        )''')
        self.conn.commit()

        # Crea un utente di default solo se non esiste
        self.cursor.execute("SELECT * FROM users WHERE username = ?", ('b2b',))
        if not self.cursor.fetchone():
            hashed_password = bcrypt.hashpw('0000v'.encode('utf-8'), bcrypt.gensalt())
            self.cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", ('b2b', hashed_password))
            self.conn.commit()

    def create_activity_log_table(self):
        # Creazione della tabella di log
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS activity_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT,
                action TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        self.conn.commit()

    def log_activity(self, username, action):
        # Inserisce un log per ogni azione effettuata
        self.cursor.execute('''
            INSERT INTO activity_log (username, action) 
            VALUES (?, ?)
        ''', (username, action))
        self.conn.commit()

    def handle_login(self):
        username = self.text_username.text()
        password = self.text_password.text().encode('utf-8')

        self.cursor.execute("SELECT password FROM users WHERE username=?", (username,))
        result = self.cursor.fetchone()

        if result and bcrypt.checkpw(password, result[0]):
            self.log_activity(username, "Login")  # Log dell'accesso
            self.accept()  # Login corretto
        else:
            QMessageBox.warning(self, 'Errore', 'Nome utente o password errati')

    def open_create_account_dialog(self):
        dialog = CreateAccountDialog(self.conn, self.cursor, self.MASTER_PASSWORD)
        if dialog.exec_():
            QMessageBox.information(self, 'Successo', 'Nuovo account creato con successo!')

class CreateAccountDialog(QDialog):
    def __init__(self, conn, cursor, master_password):
        super().__init__()
        self.setWindowTitle('Crea un account')
        self.conn = conn
        self.cursor = cursor
        self.master_password = master_password
        self.init_ui()

    def init_ui(self):
        self.label_new_username = QLabel('Nuovo Username')
        self.label_new_password = QLabel('Nuova Password')
        self.label_master_password = QLabel('Master Password')

        self.text_new_username = QLineEdit()
        self.text_new_password = QLineEdit()
        self.text_new_password.setEchoMode(QLineEdit.Password)
        self.text_master_password = QLineEdit()
        self.text_master_password.setEchoMode(QLineEdit.Password)

        self.button_create = QPushButton('Crea')
        self.button_create.clicked.connect(self.create_account)

        layout = QVBoxLayout()
        layout.addWidget(self.label_new_username)
        layout.addWidget(self.text_new_username)
        layout.addWidget(self.label_new_password)
        layout.addWidget(self.text_new_password)
        layout.addWidget(self.label_master_password)
        layout.addWidget(self.text_master_password)
        layout.addWidget(self.button_create)

        self.setLayout(layout)

    def create_account(self):
        new_username = self.text_new_username.text()
        new_password = self.text_new_password.text().encode('utf-8')
        master_password = self.text_master_password.text()

        if master_password == self.master_password:
            hashed_password = bcrypt.hashpw(new_password, bcrypt.gensalt())
            try:
                self.cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (new_username, hashed_password))
                self.conn.commit()
                self.accept()  # Chiudi la finestra e conferma creazione
            except sqlite3.IntegrityError:
                QMessageBox.warning(self, 'Errore', 'Nome utente già esistente.')
        else:
            QMessageBox.warning(self, 'Errore', 'Master password errata.')

class ActivityLogDialog(QDialog):
    def __init__(self, conn, cursor):
        super().__init__()
        self.setWindowTitle('Activity Log')
        self.conn = conn
        self.cursor = cursor
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        self.log_text = QLabel()
        layout.addWidget(self.log_text)
        self.setLayout(layout)
        self.load_logs()

    def load_logs(self):
        self.cursor.execute("SELECT username, action, timestamp FROM activity_log ORDER BY timestamp DESC")
        logs = self.cursor.fetchall()
        log_text = "\n".join([f"{row[2]} - {row[0]}: {row[1]}" for row in logs])
        self.log_text.setText(log_text)
