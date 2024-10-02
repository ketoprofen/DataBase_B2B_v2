from PyQt5.QtWidgets import QDialog, QLabel, QLineEdit, QPushButton, QVBoxLayout, QMessageBox
import bcrypt
import sqlite3

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

