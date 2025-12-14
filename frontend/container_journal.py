# frontend/container_journal.py
from PySide6.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView
from PySide6.QtCore import Qt

class JournalWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)

        # Tabella con 8 colonne
        self.table = QTableWidget(0, 8)
        self.table.setHorizontalHeaderLabels([
            "Data", 
            "N. protocollo", 
            "N. documento", 
            "Data documento",
            "Cliente/Fornitore", 
            "Descrizione", 
            "Conto Dare/Avere", 
            "Importo"
        ])

        # Configura l'header per ridimensionamento automatico
        header = self.table.horizontalHeader()
        # Colonne corte: dimensione automatica
        for i in [0, 1, 2, 3, 7]:
            header.setSectionResizeMode(i, QHeaderView.ResizeToContents)
        # Colonne lunghe: si espandono
        for i in [4, 5, 6]:
            header.setSectionResizeMode(i, QHeaderView.Stretch)

        header.setStretchLastSection(True)

        # Abilita word wrap nelle celle (non sugli header)
        self.table.setWordWrap(True)

        # Impedisci che la tabella superi la larghezza del contenitore
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        layout.addWidget(self.table)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

    def add_entry(self, entry):
        """
        entry deve essere una lista/tupla con 8 valori:
        [data, n_protocollo, n_documento, data_documento,
         cliente/fornitore, descrizione, conto dare/avere, importo]
        """
        row = self.table.rowCount()
        self.table.insertRow(row)
        for col, value in enumerate(entry):
            item = QTableWidgetItem(str(value))
            item.setTextAlignment(Qt.AlignCenter)
            item.setToolTip(str(value))  # mostra contenuto completo se troppo lungo
            item.setFlags(Qt.ItemIsEnabled)  # non editabile
            self.table.setItem(row, col, item)

    def load_from_db(self, entries):
        """Carica più righe dal DB (lista di tuple)."""
        self.table.setRowCount(0)  # reset tabella
        for entry in entries:
            self.add_entry(entry)
