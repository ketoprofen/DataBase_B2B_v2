# stato_targa_tab.py
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QLabel, QTableView, QHeaderView, QMessageBox
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QColor, QStandardItemModel, QStandardItem, QPalette
import pandas as pd
import os
from datetime import datetime, timedelta

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

        self.export_button = QPushButton("Esporta Excel")
        self.export_button.setFixedSize(100, 22)
        self.export_button.clicked.connect(self.export_to_excel)
        
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.search_flotta)
        button_layout.addWidget(self.export_button)
        button_layout.addStretch()

        layout.addLayout(button_layout)

        # Layouts for row 1 and row 2 sums
        self.sum_layout = QHBoxLayout()
        self.total_layout = QHBoxLayout()

       

        # Table view for Stato and Targa
        self.table_view = QTableView()
        layout.addWidget(self.table_view)

         # Add these layouts to the main layout
        layout.addLayout(self.sum_layout)
        layout.addLayout(self.total_layout)
        
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

        # Extract the search filter from a single input field
        search_filter = self.search_flotta.text().upper().strip()
        today_str = QDate.currentDate().toString('dd/MM/yyyy')

        # Construct the query to filter by flotta, targa, or ditta using a single input field
        if search_filter:
            query = '''
                SELECT targa, stato, ditta, data_incarico, data_consegnata
                FROM records
                WHERE (flotta LIKE ? OR targa LIKE ? OR ditta LIKE ?)
                AND (stato != "Consegnata" OR (stato = "Consegnata" AND data_consegnata = ?))
            '''
            # Use the same search term for all three fields
            search_param = f'%{search_filter}%'
            self.cursor.execute(query, (search_param, search_param, search_param, today_str))
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

        # Calculate sum for each column (ignore empty cells)
        column_sums = [len([targa for targa in stato_columns[stato] if targa[0]]) for stato in stati]

        # Clear previous sum labels
        self.clear_layout(self.sum_layout)
        self.clear_layout(self.total_layout)

        # Add sum labels to sum_layout
        for sum_value in column_sums:
            # i want to concatenate the string " " with the str(sum_value) to make it look like "  5"
            
            sum_label = QLabel("      " + str(sum_value))
            self.sum_layout.addWidget(sum_label)

        # Add "Total" label and total sum to total_layout
        total_sum = sum(column_sums)
        total_label = QLabel("Total: {}".format(total_sum))
        self.total_layout.addWidget(total_label)

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

    def clear_layout(self, layout):
        """Utility function to clear all widgets in a layout."""
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

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

        # Define the filename based on the Flotta and save it in the current directory
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

        # Initialize a dictionary to collect 'targa' values by their status
        status_dict = {stato: [] for stato in stati}
        
        # Query for records with the required conditions
        self.cursor.execute('SELECT targa, stato, data_consegnata FROM records')
        for row in self.cursor.fetchall():
            targa = row['targa']
            stato = row['stato']
            data_consegnata = row['data_consegnata']
            
            # Include "Consegnata" only if "data_consegnata" is not None and matches today's date
            if stato == 'Consegnata':
                if data_consegnata is not None:
                    consegnata_date = datetime.strptime(data_consegnata, '%d/%m/%Y')
                    if consegnata_date.date() == datetime.today().date():
                        status_dict[stato].append(targa)
                    
            else:
                if stato in status_dict:
                    status_dict[stato].append(targa)

        # Find the maximum number of entries for any status to create a balanced DataFrame
        max_entries = max(len(entries) for entries in status_dict.values())

        # Create a DataFrame by padding each status list to match max_entries
        for stato in stati:
            status_dict[stato].extend([None] * (max_entries - len(status_dict[stato])))

        df = pd.DataFrame(status_dict)

        # Add custom header row with Flotta name and timestamp
        export_data = pd.DataFrame([[
            f"Flotta: {flotta_filter}",
            f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        ]], columns=["Info", "Timestamp"])
        
        # Append the data under the custom header
        with pd.ExcelWriter(file_path, engine='xlsxwriter') as writer:
            export_data.to_excel(writer, sheet_name='Sheet1', index=False, header=False, startrow=0)
            # Write the DataFrame with column headers starting from row 2
            df.to_excel(writer, sheet_name='Sheet1', startrow=2, index=False, header=True)
            
            # Get the XlsxWriter workbook and worksheet objects
            workbook  = writer.book
            worksheet = writer.sheets['Sheet1']
            
            # Calculate the row for placing the formulas (one row below the last data row)
            formula_row = max_entries + 4  # Add 3 to account for header rows and 0-index
            
                    
            worksheet.write_formula(f'A{formula_row}', f'COUNTIF(A4:A{formula_row-1},"<>")')
            worksheet.write_formula(f'B{formula_row}', f'COUNTIF(B4:B{formula_row-1},"<>")')
            worksheet.write_formula(f'C{formula_row}', f'COUNTIF(C4:C{formula_row-1},"<>")')
            worksheet.write_formula(f'D{formula_row}', f'COUNTIF(D4:D{formula_row-1},"<>")')
            worksheet.write_formula(f'E{formula_row}', f'COUNTIF(E4:E{formula_row-1},"<>")')
            worksheet.write_formula(f'F{formula_row}', f'COUNTIF(F4:F{formula_row-1},"<>")')
            worksheet.write_formula(f'G{formula_row}', f'COUNTIF(G4:G{formula_row-1},"<>")')
            worksheet.write_formula(f'H{formula_row}', f'COUNTIF(H4:H{formula_row-1},"<>")')
            worksheet.write_formula(f'I{formula_row}', f'COUNTIF(I4:I{formula_row-1},"<>")')
            worksheet.write(formula_row, 0, 'Total', workbook.add_format({'bold': True}))
            worksheet.write_formula(f'B{formula_row+1}', f'SUM(A{formula_row}:I{formula_row})')

            # Add any additional formulas as needed for other columns
        QMessageBox.information(self, "Export Complete", f"Data successfully exported to {file_path}")

    def showEvent(self, event):
        """Re-load data every time the tab is shown."""
        self.load_data()
        super().showEvent(event)
