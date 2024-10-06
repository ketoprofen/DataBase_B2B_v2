from PyQt5 import QtWidgets, QtGui, QtCore
import datetime
import calendar
import pandas as pd

class RecapDataTab(QtWidgets.QWidget):
    def __init__(self, conn):
        super().__init__()
        self.conn = conn
        self.setWindowTitle("Statistiche")
        self.init_ui()

    def init_ui(self):
        layout = QtWidgets.QVBoxLayout()  # Define the layout

        # Add controls for month and year selection
        controls_layout = QtWidgets.QHBoxLayout()
        
        month_label = QtWidgets.QLabel("Mese:")
        self.month_combo = QtWidgets.QComboBox()
        self.month_combo.addItems([calendar.month_name[i] for i in range(1, 13)])
        self.month_combo.setCurrentIndex(datetime.date.today().month - 1)
        
        year_label = QtWidgets.QLabel("Anno:")
        self.year_spin = QtWidgets.QSpinBox()
        current_year = datetime.date.today().year
        self.year_spin.setRange(2000, current_year + 5)
        self.year_spin.setValue(current_year)
        
        # Export Button
        self.export_button = QtWidgets.QPushButton("Esporta in Excel")
        self.export_button.clicked.connect(self.export_to_excel)
        
        # Add widgets to the layout
        controls_layout.addWidget(month_label)
        controls_layout.addWidget(self.month_combo)
        controls_layout.addWidget(year_label)
        controls_layout.addWidget(self.year_spin)
        controls_layout.addStretch()
        controls_layout.addWidget(self.export_button)
        
        layout.addLayout(controls_layout)

        # Define headers here
        self.headers = [
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

        # Table widget for Monthly Statistics
        self.monthly_table = QtWidgets.QTableWidget()
        self.monthly_table.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.monthly_table.setColumnCount(len(self.headers))
        self.monthly_table.setHorizontalHeaderLabels(self.headers)
        self.monthly_table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        layout.addWidget(self.monthly_table, stretch=1)

        # Separator
        separator = QtWidgets.QFrame()
        separator.setFrameShape(QtWidgets.QFrame.HLine)
        separator.setFrameShadow(QtWidgets.QFrame.Sunken)
        layout.addWidget(separator)

        # Weekly Statistics Tables
        self.week_tables = []

        # Set the layout
        self.setLayout(layout)  # Ensure the layout is set here

        # Connect signals to reload data when selection changes
        self.month_combo.currentIndexChanged.connect(self.refresh_data)
        self.year_spin.valueChanged.connect(self.refresh_data)

        # Load data
        self.refresh_data()

    def refresh_data(self):
        # Clear existing week tables
        self.clear_week_tables()
        # Reload data in monthly table
        self.load_monthly_data()
        # Reload data in weekly tables
        self.load_weekly_tables()

    def load_weekly_tables(self):
            # Get selected month and year
            month = self.month_combo.currentIndex() + 1
            year = self.year_spin.value()

            # Get all the weeks in the selected month
            weeks_in_month = self.get_weeks_in_month(year, month)

            for week_index, (week_num, week_dates) in enumerate(weeks_in_month):
                week_label = QtWidgets.QLabel(f"Settimana {week_index + 1}")
                week_label.setFont(QtGui.QFont("Arial", 14, QtGui.QFont.Bold))
                self.layout().addWidget(week_label)

                week_table = QtWidgets.QTableWidget()
                week_table.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
                week_table.setColumnCount(len(self.headers))
                week_table.setHorizontalHeaderLabels(self.headers)
                week_table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
                self.layout().addWidget(week_table, stretch=1)
                self.week_tables.append((week_num, week_dates, week_table))

                # Load weekly data
                self.load_weekly_data(week_num, week_dates, week_table)

    def export_to_excel(self):
            try:
                # Ask user for file location
                options = QtWidgets.QFileDialog.Options()
                file_path, _ = QtWidgets.QFileDialog.getSaveFileName(
                    self,
                    "Salva File",
                    f"Statistiche_{self.year_spin.value()}_{self.month_combo.currentIndex() + 1}.xlsx",
                    "Excel Files (*.xlsx);;All Files (*)",
                    options=options
                )
                if file_path:
                    # Collect data from monthly table
                    monthly_data = self.get_table_data(self.monthly_table)

                    # Collect data from weekly tables
                    weekly_data = []
                    for week_index, (week_num, week_dates, week_table) in enumerate(self.week_tables):
                        week_data = self.get_table_data(week_table)
                        weekly_data.append((f"Settimana {week_index + 1}", week_data))

                    # Export to Excel
                    with pd.ExcelWriter(file_path) as writer:
                        # Monthly data
                        df_monthly = pd.DataFrame(monthly_data, columns=self.headers)
                        df_monthly.to_excel(writer, sheet_name="Mese", index=False)

                        # Weekly data
                        for week_name, data in weekly_data:
                            df_week = pd.DataFrame(data, columns=self.headers)
                            df_week.to_excel(writer, sheet_name=week_name, index=False)

                    QtWidgets.QMessageBox.information(self, "Successo", f"File salvato con successo in {file_path}")
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, "Error", f"Failed to export data: {e}")

    def get_table_data(self, table_widget):
        data = []
        for row in range(table_widget.rowCount()):
            row_data = []
            for column in range(table_widget.columnCount()):
                item = table_widget.item(row, column)
                row_data.append(item.text() if item else '')
            data.append(row_data)
        return data
    
    def clear_week_tables(self):
        layout = self.layout()  # Get the existing layout
        if layout is None:
            return  # If layout is not set, skip the clearing process

        for i in reversed(range(layout.count())):
            widget = layout.itemAt(i).widget()
            if isinstance(widget, QtWidgets.QTableWidget) and widget != self.monthly_table:
                layout.removeWidget(widget)
                widget.deleteLater()
            elif isinstance(widget, QtWidgets.QLabel) and widget.text().startswith("Settimana"):
                layout.removeWidget(widget)
                widget.deleteLater()
            elif isinstance(widget, QtWidgets.QFrame):
                # Stop removing widgets when we reach the separator
                break
            else:
                continue
        self.week_tables.clear()

    # Rest of the methods...
        # Reload data in monthly table
        self.load_monthly_data()
        # Reload data in weekly tables
        for week_num, week_dates, week_table in self.week_tables:
            self.load_weekly_data(week_num, week_dates, week_table)

    def get_weeks_in_month(self, year, month):
        c = calendar.Calendar()
        month_weeks = c.monthdatescalendar(year, month)
        weeks = []
        for week in month_weeks:
            week_number = None
            week_dates = []
            for day in week:
                if day.month == month:
                    if week_number is None:
                        week_number = day.isocalendar()[1]
                    week_dates.append(day)
            if week_dates:
                weeks.append((week_number, week_dates))
        return weeks

    def iso_year_start(self, iso_year):
        "The Gregorian calendar date of the first day of the given ISO year"
        fourth_jan = datetime.date(iso_year, 1, 4)
        delta = datetime.timedelta(days=(fourth_jan.isoweekday() - 1))
        return fourth_jan - delta

    def iso_to_gregorian(self, iso_year, iso_week, iso_day):
        "Gregorian calendar date for the given ISO year, week, and day"
        year_start = self.iso_year_start(iso_year)
        return year_start + datetime.timedelta(days=iso_day - 1, weeks=iso_week - 1)

    def load_monthly_data(self):
        try:
            cursor = self.conn.cursor()

            # Get working days up to today in the current month
            today = datetime.date.today()
            first_day = today.replace(day=1)

            # Define holidays in Rome
            holidays_in_rome = self.get_holidays_in_rome(today.year)

            # Calculate working days from first day of the month up to today (excluding future days)
            working_days_so_far = self.get_working_days(first_day, today, holidays_in_rome)

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
            self.monthly_table.setRowCount(len(ditta_list))

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
                self.monthly_table.setItem(row_index, 0, QtWidgets.QTableWidgetItem(ditta))
                self.monthly_table.setItem(row_index, 1, QtWidgets.QTableWidgetItem(str(nr_operatori)))
                self.monthly_table.setItem(row_index, 2, QtWidgets.QTableWidgetItem(str(working_days_so_far)))
                self.monthly_table.setItem(row_index, 3, QtWidgets.QTableWidgetItem(str(vetture_finite_nel_mese)))
                self.monthly_table.setItem(row_index, 4, QtWidgets.QTableWidgetItem(f"{media_vetture_al_gg:.2f}"))
                self.monthly_table.setItem(row_index, 5, QtWidgets.QTableWidgetItem(f"{media_pz_per_vettura:.2f}"))
                self.monthly_table.setItem(row_index, 6, QtWidgets.QTableWidgetItem(f"{media_pezzi_al_gg:.2f}"))
                self.monthly_table.setItem(row_index, 7, QtWidgets.QTableWidgetItem(f"{media_pz_per_op_al_gg:.2f}"))
                self.monthly_table.setItem(row_index, 8, QtWidgets.QTableWidgetItem(str(totale_pz)))

                # Allow editing NR. OPERATORI
                item_nr_operatori = self.monthly_table.item(row_index, 1)
                item_nr_operatori.setFlags(item_nr_operatori.flags() | QtCore.Qt.ItemIsEditable)

            # Resize columns to fit contents
            self.monthly_table.resizeColumnsToContents()

            # Connect itemChanged signal
            self.monthly_table.itemChanged.connect(self.on_monthly_item_changed)

        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", f"Failed to load data: {e}")

    def load_weekly_data(self, week_number, week_dates, table_widget):
        try:
            cursor = self.conn.cursor()
            today = datetime.date.today()
            current_year = today.year

            # Define holidays in Rome
            holidays_in_rome = self.get_holidays_in_rome(current_year)

            # Only consider dates up to today
            week_dates_current = [date for date in week_dates if date <= today]

            # Calculate working days in the week within the current month
            working_days = sum(1 for date in week_dates_current if date.weekday() < 5 and date not in holidays_in_rome)

            # Check if the week is over
            week_is_over = today > week_dates[-1]

            # Fetch unique Ditta names
            cursor.execute("""
                SELECT DISTINCT CASE WHEN UPPER(ditta) = 'HPSV' THEN 'HPS' ELSE ditta END as ditta_name
                FROM records 
                WHERE ditta IS NOT NULL AND ditta != '' AND LOWER(ditta) != 'approntamento'
            """)
            ditta_list = [row[0] for row in cursor.fetchall()]
            ditta_list = list(set(ditta_list))  # Ensure uniqueness
            ditta_list.sort()

            # Fetch NR. OPERATORI values
            cursor.execute("SELECT ditta, nr_operatori FROM ditta_operatori")
            nr_operatori_data = dict(cursor.fetchall())

            # Set the row count
            table_widget.setRowCount(len(ditta_list))

            for row_index, ditta in enumerate(ditta_list):
                nr_operatori = nr_operatori_data.get(ditta, 0)

                if week_is_over:
                    # Retrieve stored data
                    cursor.execute("""
                        SELECT vetture_finite_nel_settimana, totale_pz, media_vetture_al_gg, media_pz_per_vettura,
                               media_pezzi_al_gg, media_pz_per_op_al_gg, working_days
                        FROM weekly_statistics
                        WHERE ditta = ? AND week_number = ? AND year = ?
                    """, (ditta, week_number, current_year))
                    result = cursor.fetchone()
                    if result:
                        (vetture_finite_nel_settimana, totale_pz, media_vetture_al_gg, media_pz_per_vettura,
                         media_pezzi_al_gg, media_pz_per_op_al_gg, working_days) = result
                    else:
                        vetture_finite_nel_settimana = totale_pz = media_vetture_al_gg = media_pz_per_vettura = media_pezzi_al_gg = media_pz_per_op_al_gg = 0
                        working_days = 0
                else:
                    # Fetch data
                    start_date_str = min(week_dates_current).strftime('%Y-%m-%d') if week_dates_current else None
                    end_date_str = max(week_dates_current).strftime('%Y-%m-%d') if week_dates_current else None

                    if start_date_str and end_date_str:
                        cursor.execute("""
                            SELECT COUNT(DISTINCT targa) FROM records
                            WHERE (CASE WHEN UPPER(ditta) = 'HPSV' THEN 'HPS' ELSE ditta END) = ?
                            AND stato IN ('Pronta', 'Consegnata')
                            AND date(substr(data_consegnata, 7, 4) || '-' ||
                                     substr(data_consegnata, 4, 2) || '-' ||
                                     substr(data_consegnata, 1, 2)) BETWEEN ? AND ?
                        """, (ditta, start_date_str, end_date_str))
                        vetture_finite_nel_settimana = cursor.fetchone()[0]

                        cursor.execute("""
                            SELECT SUM(pezzi_carr) FROM records
                            WHERE (CASE WHEN UPPER(ditta) = 'HPSV' THEN 'HPS' ELSE ditta END) = ?
                            AND pezzi_carr IS NOT NULL
                            AND date(substr(data_consegnata, 7, 4) || '-' ||
                                     substr(data_consegnata, 4, 2) || '-' ||
                                     substr(data_consegnata, 1, 2)) BETWEEN ? AND ?
                        """, (ditta, start_date_str, end_date_str))
                        totale_pz = cursor.fetchone()[0] or 0
                    else:
                        vetture_finite_nel_settimana = 0
                        totale_pz = 0

                    # Calculations
                    media_vetture_al_gg = vetture_finite_nel_settimana / working_days if working_days else 0
                    media_pz_per_vettura = totale_pz / vetture_finite_nel_settimana if vetture_finite_nel_settimana else 0
                    media_pezzi_al_gg = totale_pz / working_days if working_days else 0
                    media_pz_per_op_al_gg = totale_pz / (nr_operatori * working_days) if nr_operatori and working_days else 0

                    # If the week is ending today, store the data
                    if today == week_dates[-1]:
                        cursor.execute("""
                            INSERT OR REPLACE INTO weekly_statistics (
                                ditta, week_number, year, vetture_finite_nel_settimana, totale_pz,
                                media_vetture_al_gg, media_pz_per_vettura, media_pezzi_al_gg,
                                media_pz_per_op_al_gg, nr_operatori, working_days
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (ditta, week_number, current_year, vetture_finite_nel_settimana, totale_pz,
                              media_vetture_al_gg, media_pz_per_vettura, media_pezzi_al_gg,
                              media_pz_per_op_al_gg, nr_operatori, working_days))
                        self.conn.commit()

                # Populate the table
                table_widget.setItem(row_index, 0, QtWidgets.QTableWidgetItem(ditta))
                table_widget.setItem(row_index, 1, QtWidgets.QTableWidgetItem(str(nr_operatori)))
                table_widget.setItem(row_index, 2, QtWidgets.QTableWidgetItem(str(working_days)))
                table_widget.setItem(row_index, 3, QtWidgets.QTableWidgetItem(str(vetture_finite_nel_settimana)))
                table_widget.setItem(row_index, 4, QtWidgets.QTableWidgetItem(f"{media_vetture_al_gg:.2f}"))
                table_widget.setItem(row_index, 5, QtWidgets.QTableWidgetItem(f"{media_pz_per_vettura:.2f}"))
                table_widget.setItem(row_index, 6, QtWidgets.QTableWidgetItem(f"{media_pezzi_al_gg:.2f}"))
                table_widget.setItem(row_index, 7, QtWidgets.QTableWidgetItem(f"{media_pz_per_op_al_gg:.2f}"))
                table_widget.setItem(row_index, 8, QtWidgets.QTableWidgetItem(str(totale_pz)))

                # Allow editing NR. OPERATORI if the week is current
                item_nr_operatori = table_widget.item(row_index, 1)
                if not week_is_over:
                    item_nr_operatori.setFlags(item_nr_operatori.flags() | QtCore.Qt.ItemIsEditable)
                    # Connect the itemChanged signal
                    table_widget.itemChanged.connect(self.on_week_item_changed)
                else:
                    item_nr_operatori.setFlags(item_nr_operatori.flags() & ~QtCore.Qt.ItemIsEditable)

                # Resize columns to fit contents
                table_widget.resizeColumnsToContents()

        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", f"Failed to load weekly data: {e}")

    def get_holidays_in_rome(self, year):
        holidays = [
            datetime.date(year, 1, 1),   # New Year's Day
            datetime.date(year, 1, 6),   # Epiphany
            datetime.date(year, 4, 25),  # Liberation Day
            datetime.date(year, 5, 1),   # Labor Day
            datetime.date(year, 6, 2),   # Republic Day
            datetime.date(year, 6, 29),  # St. Peter and Paul (Patron Saints of Rome)
            datetime.date(year, 8, 15),  # Assumption Day
            datetime.date(year, 11, 1),  # All Saints' Day
            datetime.date(year, 12, 8),  # Immaculate Conception
            datetime.date(year, 12, 25), # Christmas Day
            datetime.date(year, 12, 26), # St. Stephen's Day
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
        easter_sunday = datetime.date(year, month, day)
        easter_monday = easter_sunday + datetime.timedelta(days=1)
        return easter_monday

    def get_working_days(self, start_date, end_date, holidays):
        working_days = 0
        delta = end_date - start_date
        for i in range(delta.days + 1):
            current_day = start_date + datetime.timedelta(days=i)
            if current_day.weekday() < 5 and current_day not in holidays:
                working_days += 1
        return working_days

    def on_monthly_item_changed(self, item):
        if item.column() == 1:  # NR. OPERATORI column
            try:
                nr_operatori = int(item.text())
                if nr_operatori < 0:
                    raise ValueError
                ditta = self.monthly_table.item(item.row(), 0).text()
                # Update nr_operatori in the database
                cursor = self.conn.cursor()
                cursor.execute("""
                    INSERT INTO ditta_operatori (ditta, nr_operatori)
                    VALUES (?, ?)
                    ON CONFLICT(ditta) DO UPDATE SET nr_operatori=excluded.nr_operatori
                """, (ditta, nr_operatori))
                self.conn.commit()
                self.recalculate_monthly_row(item.row())
            except ValueError:
                QtWidgets.QMessageBox.warning(self, "Invalid Input", "Per favore, inserisci un numero intero non negativo per NR. OPERATORI.")
                item.setText('0')
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, "Error", f"Failed to update NR. OPERATORI: {e}")

    def recalculate_monthly_row(self, row_index):
        try:
            nr_operatori = int(self.monthly_table.item(row_index, 1).text())
            totale_pz = float(self.monthly_table.item(row_index, 8).text())
            working_days_so_far = int(self.monthly_table.item(row_index, 2).text())

            media_pz_per_op_al_gg = totale_pz / (nr_operatori * working_days_so_far) if nr_operatori and working_days_so_far else 0

            self.monthly_table.itemChanged.disconnect()
            self.monthly_table.setItem(row_index, 7, QtWidgets.QTableWidgetItem(f"{media_pz_per_op_al_gg:.2f}"))
            self.monthly_table.itemChanged.connect(self.on_monthly_item_changed)
        except Exception as e:
            print(f"Error recalculating monthly row {row_index}: {e}")

    def on_week_item_changed(self, item):
        if item.column() == 1:  # NR. OPERATORI column
            try:
                nr_operatori = int(item.text())
                if nr_operatori < 0:
                    raise ValueError
                table_widget = item.tableWidget()
                row_index = item.row()
                ditta = table_widget.item(row_index, 0).text()
                # Update nr_operatori in the database
                cursor = self.conn.cursor()
                cursor.execute("""
                    INSERT INTO ditta_operatori (ditta, nr_operatori)
                    VALUES (?, ?)
                    ON CONFLICT(ditta) DO UPDATE SET nr_operatori=excluded.nr_operatori
                """, (ditta, nr_operatori))
                self.conn.commit()
                self.recalculate_week_row(table_widget, row_index)
            except ValueError:
                QtWidgets.QMessageBox.warning(self, "Invalid Input", "Per favore, inserisci un numero intero non negativo per NR. OPERATORI.")
                item.setText('0')
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, "Error", f"Failed to update NR. OPERATORI: {e}")

    def recalculate_week_row(self, table_widget, row_index):
        try:
            nr_operatori = int(table_widget.item(row_index, 1).text())
            totale_pz = float(table_widget.item(row_index, 8).text())
            working_days_so_far = int(table_widget.item(row_index, 2).text())

            media_pz_per_op_al_gg = totale_pz / (nr_operatori * working_days_so_far) if nr_operatori and working_days_so_far else 0

            table_widget.itemChanged.disconnect()
            table_widget.setItem(row_index, 7, QtWidgets.QTableWidgetItem(f"{media_pz_per_op_al_gg:.2f}"))
            table_widget.itemChanged.connect(self.on_week_item_changed)
        except Exception as e:
            print(f"Error recalculating week row {row_index}: {e}")
