# logs_windows.py

from PyQt5.QtWidgets import QDialog, QLabel, QVBoxLayout

class LogsWindow(QDialog):
    def __init__(self, conn, cursor):
        super().__init__()
        self.setWindowTitle('Logs')
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

