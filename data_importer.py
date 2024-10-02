import pandas as pd
from PyQt5.QtWidgets import QFileDialog, QMessageBox
from datetime import datetime
    
def import_data(main_window):
    options = QFileDialog.Options()
    file_path, _ = QFileDialog.getOpenFileName(main_window, "Importa Dati", "",
                                            "Excel Files (*.xlsx);;CSV Files (*.csv)", options=options)
    if file_path:
        try:
            # Load the data
            if file_path.endswith('.xlsx'):
                df = pd.read_excel(file_path)
            elif file_path.endswith('.csv'):
                df = pd.read_csv(file_path)
            else:
                QMessageBox.warning(main_window, 'Formato non supportato', 'Seleziona un file .xlsx o .csv')
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
                        main_window.cursor.execute(sql, tuple(record_values))

                    except Exception as e:
                        print(f"Error inserting record at row {index}: {e}")
                        continue  # Skip problematic rows

                main_window.conn.commit()
                print(f"Successfully imported data with available columns: {matched_columns}")

                QMessageBox.information(main_window, 'Successo', 'Dati importati con successo.')
                main_window.load_data()
                main_window.notifications_tab.load_notifications()
            else:
                QMessageBox.warning(main_window, 'Errore di formato', 'Nessuna colonna corrisponde ai dati richiesti.')

        except Exception as e:
            QMessageBox.warning(main_window, 'Errore', str(e))
