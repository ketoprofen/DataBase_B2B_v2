from PyQt5.QtWidgets import QFileDialog, QMessageBox
import pandas as pd
from datetime import datetime

def execute_extrapolate(main_window):
    # Select the folder to save the file
    folder_path = QFileDialog.getExistingDirectory(main_window, 'Seleziona la cartella di destinazione')
    if not folder_path:
        QMessageBox.warning(main_window, 'Errore', 'Nessuna cartella selezionata.')
        return

    if main_window.radio_all_data.isChecked():
        query = 'SELECT * FROM records'
        params = []
        filename = 'DataBaseB2B.xlsx'
    elif main_window.radio_exclude_consegnata.isChecked():
        query = 'SELECT * FROM records WHERE stato != ?'
        params = ['Consegnata']
        filename = 'DataBaseB2B_lavorazione.xlsx'
    elif main_window.radio_by_flotta.isChecked():
        flotta = main_window.text_flotta_extrapolate.text().upper()
        if not flotta:
            QMessageBox.warning(main_window, 'Errore di input', 'Per favore, inserisci la Flotta.')
            return
        only_consegnata = main_window.checkbox_exclude_consegnata.isChecked()
        query = 'SELECT * FROM records WHERE flotta = ?'
        params = [flotta]
        if only_consegnata:
            query += ' AND stato = ?'
            params.append('Consegnata')
            filename = f'DataBaseB2B_{flotta}_consegnata.xlsx'
        else:
            filename = f'DataBaseB2B_{flotta}.xlsx'
    else:
        QMessageBox.warning(main_window, 'Errore di selezione', 'Per favore, seleziona un\'opzione.')
        return

    try:
        df = pd.read_sql_query(query, main_window.conn, params=params)
        if df.empty:
            QMessageBox.information(main_window, 'Nessun dato', 'Nessun dato trovato per i criteri selezionati.')
            return
        
        # Remove the 'id' column if it exists
        if 'id' in df.columns:
            df = df.drop(columns=['id'])

        # Reorder columns to place 'data_consegnata' between 'stato' and 'note'
        columns_order = df.columns.tolist()
        if 'data_consegnata' in columns_order:
            # Ensure the desired order of columns if they exist
            columns_order.remove('data_consegnata')
            if 'note' in columns_order:
                note_index = columns_order.index('note')
                columns_order.insert(note_index, 'data_consegnata')
            else:
                columns_order.append('data_consegnata')
            df = df[columns_order]

        # Define the full path for the output file
        full_filename = f'{folder_path}/{filename}'

        df.to_excel(full_filename, index=False)
        QMessageBox.information(main_window, 'Successo', f'Dati esportati nel file {full_filename}')
        main_window.extrapolate_group.hide()
    except Exception as e:
        QMessageBox.warning(main_window, 'Errore', str(e))