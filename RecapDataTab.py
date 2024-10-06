from PyQt5 import QtWidgets, QtGui, QtCore
import datetime

class RecapDataTab(QtWidgets.QWidget):
    def __init__(self, conn):
        super().__init__()
        self.conn = conn
        self.setWindowTitle("Statistiche")
        self.init_ui()

    def init_ui(self):
        layout = QtWidgets.QVBoxLayout()

        # Table widget to display data
        self.table_widget = QtWidgets.QTableWidget()
        self.table_widget.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        layout.addWidget(self.table_widget, stretch=1)

        # Set table headers
        headers = [
            "DITTA",
            "NR. OPERATORI",
            "GG.LAV",
            "VETTURE FINITE NEL MESE",
            "MEDIA VETTURE AL GG.",
            "MEDIA PZ. PER VETTURA",
            "MEDIA PEZZI AL GG.",
            "MEDIA PZ. PER OP. AL GG",
            "TOTALE PZ."
        ]
        self.table_widget.setColumnCount(len(headers))
        self.table_widget.setHorizontalHeaderLabels(headers)

        # Make the table fill the space
        self.table_widget.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)

        # Load data from database
        self.load_data()

        # Connect itemChanged signal
        self.table_widget.itemChanged.connect(self.on_item_changed)

        self.setLayout(layout)

    def load_data(self):
        try:
            cursor = self.conn.cursor()

            # Get working days up to today in the current month
            today = datetime.date.today()
            first_day = today.replace(day=1)

            # Calculate working days from first day of the month up to today (excluding future days)
            working_days_so_far = len([
                1 for i in range((today - first_day).days + 1)
                if (first_day + datetime.timedelta(days=i)).weekday() < 5
            ])

            # Fetch unique Ditta names, mapping 'HPSV' to 'HPS'
            cursor.execute("""
                SELECT DISTINCT CASE WHEN UPPER(ditta) = 'HPSV' THEN 'HPS' ELSE ditta END as ditta_name
                FROM records 
                WHERE ditta IS NOT NULL AND ditta != '' AND LOWER(ditta) != 'approntamento'
            """)
            ditta_list = [row[0] for row in cursor.fetchall()]
            ditta_list = list(set(ditta_list))  # Ensure uniqueness
            ditta_list.sort()  # Optional: sort the list

            # Fetch NR. OPERATORI values from ditta_operatori table
            cursor.execute("SELECT ditta, nr_operatori FROM ditta_operatori")
            nr_operatori_data = dict(cursor.fetchall())

            # Set the row count of the table
            self.table_widget.setRowCount(len(ditta_list))

            # Iterate over each Ditta and calculate statistics
            for row_index, ditta in enumerate(ditta_list):
                # Fetch NR. OPERATORI for this Ditta
                nr_operatori = nr_operatori_data.get(ditta, 0)  # Default to 0

                # VETTURE FINITE NEL MESE (Counting distinct targa with adjusted date parsing)
                cursor.execute("""
                    SELECT COUNT(DISTINCT targa) FROM records
                    WHERE (CASE WHEN UPPER(ditta) = 'HPSV' THEN 'HPS' ELSE ditta END) = ?
                    AND stato IN ('Pronta', 'Consegnata')
                    AND date(substr(data_consegnata, 7, 4) || '-' ||
                             substr(data_consegnata, 4, 2) || '-' ||
                             substr(data_consegnata, 1, 2)) <= date('now')
                    AND strftime('%Y-%m', substr(data_consegnata, 7, 4) || '-' ||
                                              substr(data_consegnata, 4, 2) || '-' ||
                                              substr(data_consegnata, 1, 2)) = strftime('%Y-%m', 'now')
                """, (ditta,))
                vetture_finite_nel_mese = cursor.fetchone()[0]

                # TOTALE PZ.
                cursor.execute("""
                    SELECT SUM(pezzi_carr) FROM records
                    WHERE (CASE WHEN UPPER(ditta) = 'HPSV' THEN 'HPS' ELSE ditta END) = ?
                    AND pezzi_carr IS NOT NULL
                    AND date(substr(data_consegnata, 7, 4) || '-' ||
                             substr(data_consegnata, 4, 2) || '-' ||
                             substr(data_consegnata, 1, 2)) <= date('now')
                    AND strftime('%Y-%m', substr(data_consegnata, 7, 4) || '-' ||
                                              substr(data_consegnata, 4, 2) || '-' ||
                                              substr(data_consegnata, 1, 2)) = strftime('%Y-%m', 'now')
                """, (ditta,))
                totale_pz = cursor.fetchone()[0] or 0

                # Calculations using working_days_so_far
                media_vetture_al_gg = vetture_finite_nel_mese / working_days_so_far if working_days_so_far else 0
                media_pz_per_vettura = totale_pz / vetture_finite_nel_mese if vetture_finite_nel_mese else 0
                media_pezzi_al_gg = totale_pz / working_days_so_far if working_days_so_far else 0
                media_pz_per_op_al_gg = totale_pz / (nr_operatori * working_days_so_far) if nr_operatori and working_days_so_far else 0

                # Populate the table row
                self.table_widget.setItem(row_index, 0, QtWidgets.QTableWidgetItem(ditta))
                self.table_widget.setItem(row_index, 1, QtWidgets.QTableWidgetItem(str(nr_operatori)))
                self.table_widget.setItem(row_index, 2, QtWidgets.QTableWidgetItem(str(working_days_so_far)))
                self.table_widget.setItem(row_index, 3, QtWidgets.QTableWidgetItem(str(vetture_finite_nel_mese)))
                self.table_widget.setItem(row_index, 4, QtWidgets.QTableWidgetItem(f"{media_vetture_al_gg:.2f}"))
                self.table_widget.setItem(row_index, 5, QtWidgets.QTableWidgetItem(f"{media_pz_per_vettura:.2f}"))
                self.table_widget.setItem(row_index, 6, QtWidgets.QTableWidgetItem(f"{media_pezzi_al_gg:.2f}"))
                self.table_widget.setItem(row_index, 7, QtWidgets.QTableWidgetItem(f"{media_pz_per_op_al_gg:.2f}"))
                self.table_widget.setItem(row_index, 8, QtWidgets.QTableWidgetItem(str(totale_pz)))

                # Allow editing NR. OPERATORI
                item_nr_operatori = self.table_widget.item(row_index, 1)
                item_nr_operatori.setFlags(item_nr_operatori.flags() | QtCore.Qt.ItemIsEditable)

            # Resize columns to fit contents
            self.table_widget.resizeColumnsToContents()

        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", f"Failed to load data: {e}")

    def on_item_changed(self, item):
        if item.column() == 1:  # NR. OPERATORI column
            try:
                nr_operatori = int(item.text())
                if nr_operatori < 0:
                    raise ValueError
                ditta = self.table_widget.item(item.row(), 0).text()
                # Update nr_operatori in the database
                cursor = self.conn.cursor()
                cursor.execute("""
                    INSERT INTO ditta_operatori (ditta, nr_operatori)
                    VALUES (?, ?)
                    ON CONFLICT(ditta) DO UPDATE SET nr_operatori=excluded.nr_operatori
                """, (ditta, nr_operatori))
                self.conn.commit()
                self.recalculate_row(item.row())
            except ValueError:
                QtWidgets.QMessageBox.warning(self, "Invalid Input", "Per favore, inserisci un numero intero non negativo per NR. OPERATORI.")
                item.setText('0')
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, "Error", f"Failed to update NR. OPERATORI: {e}")

    def recalculate_row(self, row_index):
        try:
            nr_operatori = int(self.table_widget.item(row_index, 1).text())
            totale_pz = float(self.table_widget.item(row_index, 8).text())
            working_days_so_far = int(self.table_widget.item(row_index, 2).text())

            media_pz_per_op_al_gg = totale_pz / (nr_operatori * working_days_so_far) if nr_operatori and working_days_so_far else 0

            self.table_widget.itemChanged.disconnect()
            self.table_widget.setItem(row_index, 7, QtWidgets.QTableWidgetItem(f"{media_pz_per_op_al_gg:.2f}"))
            self.table_widget.itemChanged.connect(self.on_item_changed)
        except Exception as e:
            print(f"Error recalculating row {row_index}: {e}")
