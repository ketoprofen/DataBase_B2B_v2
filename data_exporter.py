import pandas as pd
from PyQt5.QtWidgets import QMessageBox
from datetime import datetime


def execute_extrapolate(main_window):
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
    elif main_window.radio_stato_report.isChecked():
        query = '''
            SELECT targa, stato, data_consegnata 
            FROM records 
            WHERE NOT (stato = "Consegnata" AND data_consegnata < ?)
        '''
        params = [datetime.now().strftime('%d/%m/%Y')]
        filename = 'DataBaseB2B_stato.xlsx'
    else:
        QMessageBox.warning(main_window, 'Errore di selezione', 'Per favore, seleziona un\'opzione.')
        return

    try:
        df = pd.read_sql_query(query, main_window.conn, params=params)
        if df.empty:
            QMessageBox.information(main_window, 'Nessun dato', 'Nessun dato trovato per i criteri selezionati.')
            return

        if main_window.radio_stato_report.isChecked():
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
        QMessageBox.information(main_window, 'Successo', f'Dati esportati nel file {filename}')
        main_window.extrapolate_group.hide()
    except Exception as e:
        QMessageBox.warning(main_window, 'Errore', str(e))
