import platform
from PySide6.QtCore import QFile, QTextStream, Qt
from PySide6.QtWidgets import QMainWindow, QSplitter, QTabWidget, QWidget, QVBoxLayout, QMenuBar, QStackedLayout, QPlainTextEdit, QHeaderView
from PySide6.QtGui import QShortcut, QKeySequence
from frontend.widgets import SearchBar, HelpBrowser, TerminalWidget
from backend.dsl_parser import execute_command
from backend.modules.help_logic import get_help_text, TIPS
from frontend.container_journal import JournalWidget
from backend import db


class ContaIDE(QMainWindow):
    def __init__(self):
        super().__init__()
        # Shortcut globali UX
        # Journal
        QShortcut(QKeySequence("Ctrl+1"), self, activated=lambda: self.main_panel.setCurrentIndex(0))
        # Mastrini
        QShortcut(QKeySequence("Ctrl+2"), self, activated=lambda: self.main_panel.setCurrentIndex(1))
        # Bilancio
        QShortcut(QKeySequence("Ctrl+3"), self, activated=lambda: self.main_panel.setCurrentIndex(2))
        # Terminale focus
        QShortcut(QKeySequence("Ctrl+T"), self, activated=lambda: self.terminal.input_line.setFocus())
        # Help focus
        QShortcut(QKeySequence("Ctrl+R"), self, activated=lambda: self.searchbar.setFocus())
        # Toggle help
        QShortcut(QKeySequence("Ctrl+Y"), self, activated=self.toggle_help) 

        self.setWindowTitle("Accounting IDE")
        self.resize(1400, 800)
        
        # Applica il tema di sistema
        self.apply_system_theme()

        # Menu bar
        menu_bar = QMenuBar()
        self.setMenuBar(menu_bar)
        menu_bar.addMenu("File")
        menu_bar.addMenu("Edit")
        menu_bar.addMenu("View")
        menu_bar.addMenu("Help")

        # Split verticale
        main_splitter = QSplitter(Qt.Vertical)

        # Split orizzontale
        self.top_splitter = QSplitter(Qt.Horizontal)

        # Pannello principale
        self.main_panel = QTabWidget()
        self.main_panel.setMinimumWidth(300)  # larghezza minima in px

        # Journal tab
        self.journal_tab = JournalWidget()
        header = self.journal_tab.table.horizontalHeader()
        # Colonne corte: ResizeToContents
        for i in [0, 1, 2, 3, 7]:
            header.setSectionResizeMode(i, QHeaderView.ResizeToContents)
        # Colonne lunghe: Stretch
        for i in [4, 5, 6]:
            header.setSectionResizeMode(i, QHeaderView.Stretch)
        header.setStretchLastSection(True)
        self.journal_tab.table.setAlternatingRowColors(True)
        self.journal_tab.table.setStyleSheet("""
            QTableWidget {
                background-color: #1c1c1e;
                alternate-background-color: #2c2c2e;
                gridline-color: #3a3a3c;
                selection-background-color: #0a84ff;
                selection-color: #ffffff;
                font-family: "SF Pro Text", "Helvetica Neue", "Arial", sans-serif;
                font-size: 14px;
            }
            QHeaderView::section {
                background-color: #2c2c2e;
                color: #f5f5f7;
                font-weight: 600;
                border: none;
                padding: 6px;
            }
        """)
        self.main_panel.addTab(self.journal_tab, "Prima nota")
        entries = db.get_journal_entries()
        self.journal_tab.load_from_db(entries)

        # Mastrini tab
        mastrini_tab = QWidget()
        mastrini_layout = QVBoxLayout(mastrini_tab)
        mastrini_view = QPlainTextEdit()
        mastrini_view.setObjectName("mastriniView")
        mastrini_view.setReadOnly(True)
        mastrini_view.setPlainText(
            "📊 Mastrini (Conti)\n\n"
            "Cassa:\n  Dare 1000 | Avere 0 | Saldo 1000\n\n"
            "Banca:\n  Dare 0 | Avere 500 | Saldo -500\n\n"
            "Clienti:\n  Dare 2000 | Avere 0 | Saldo 2000\n"
        )
        mastrini_layout.addWidget(mastrini_view)
        self.main_panel.addTab(mastrini_tab, "Mastrini")
        mastrini_layout.setContentsMargins(0, 0, 0, 0)
        mastrini_layout.setSpacing(0)

        # Bilancio tab
        bilancio_tab = QWidget()
        bilancio_layout = QVBoxLayout(bilancio_tab)
        bilancio_view = QPlainTextEdit()
        bilancio_view.setObjectName("bilancioView")
        bilancio_view.setReadOnly(True)
        bilancio_view.setPlainText(
            "📈 Bilancio\n\n"
            "Attività:\n  Cassa 1000\n  Clienti 2000\n\n"
            "Passività:\n  Banca 500\n\n"
            "Patrimonio Netto: 2500\n"
        )
        bilancio_layout.addWidget(bilancio_view)
        self.main_panel.addTab(bilancio_tab, "Bilancio")
        bilancio_layout.setContentsMargins(0, 0, 0, 0)
        bilancio_layout.setSpacing(0)

        # Salva i tab di default per reset
        self.default_tabs = [
            ("Prima nota", self.journal_tab),
            ("Mastrini", mastrini_tab),
            ("Bilancio", bilancio_tab),
        ]
        # Help contestuale con searchbar + browser
        help_widget = QWidget()
        help_layout = QVBoxLayout(help_widget)

        self.searchbar = SearchBar(list(TIPS.keys()))
        self.searchbar.textChanged.connect(self.update_help)

        self.help_browser = HelpBrowser()

        help_layout.addWidget(self.searchbar)
        help_layout.addWidget(self.help_browser)

        # Contenitore sinistro
        self.left_container = QWidget()
        self.left_stack = QStackedLayout(self.left_container)
        self.left_stack.setContentsMargins(0, 0, 0, 0)
        self.left_stack.setSpacing(0)

        self.left_stack.addWidget(self.main_panel)

        # Inserisci contenitore sinistro + help nello splitter orizzontale
        self.top_splitter.addWidget(self.left_container)   # usa il contenitore
        self.top_splitter.addWidget(help_widget)
        self.top_splitter.setSizes([1000, 400])

        # Configura la collassabilità degli splitter
        self.top_splitter.setCollapsible(0, False)  # colonna sinistra non collassabile
        self.top_splitter.setCollapsible(1, True)   # help collassabile
    
        # Terminale 
        self.terminal = TerminalWidget()
        self.terminal.setMinimumHeight(150)
        main_splitter.addWidget(self.top_splitter)
        main_splitter.addWidget(self.terminal)
        main_splitter.setSizes([640, 240])

        # Impedisci che i pannelli vengano collassati
        main_splitter.setCollapsible(0, False)  # la parte superiore (tabs+help) non collassabile
        main_splitter.setCollapsible(1, False)  # il terminale non collassabile

        self.setCentralWidget(main_splitter)
        # Force focus to the terminal input line on startup
        self.terminal.input_line.setFocus()



    def update_help(self, text):
        self.help_browser.setText(get_help_text(text))
     

    def apply_system_theme(self):
        is_dark = self.is_dark_mode()
        qss_path = "frontend/styles_dark.qss" if is_dark else "frontend/styles_light.qss"
        f = QFile(qss_path)
        if f.open(QFile.ReadOnly | QFile.Text):
            s = QTextStream(f)
            self.setStyleSheet(s.readAll())



    def is_dark_mode(self) -> bool:
        # macOS/Windows/Linux: usa il valore della palette (robusto con Qt 6)
        bg_value = self.palette().color(self.backgroundRole()).value()
        return bg_value < 128
    


    def wrap_keypress(self, original_event): 
        def handler(event): 
            if event.key() in (Qt.Key_Return, Qt.Key_Enter): 
                text = self.terminal.toPlainText().splitlines()[-1] 
                output = execute_command(text) 
                self.terminal.appendPlainText(output) 
            else: original_event(event) 
        return handler



    def show_split(self, left_index: int, right_index: int):
        self.reset_split()
        count = self.main_panel.count()
        if not (1 <= left_index <= count and 1 <= right_index <= count):
            return
        if left_index == right_index:
            return
        li, ri = left_index - 1, right_index - 1
        left_title = self.main_panel.tabText(li)
        left_widget = self.main_panel.widget(li)
        right_title = self.main_panel.tabText(ri)
        right_widget = self.main_panel.widget(ri)

        # Rimuovi i tab dal main_panel (partendo dal maggiore per evitare shift)
        for idx in sorted([li, ri], reverse=True):
            self.main_panel.removeTab(idx)

        # Crea per-lato QTabWidget rispettando l’ordine del comando
        left_side = QTabWidget()
        left_side.addTab(left_widget, left_title)

        right_side = QTabWidget()
        right_side.addTab(right_widget, right_title)

        self.split_view = QSplitter(Qt.Horizontal)
        self.split_view.addWidget(left_side)
        self.split_view.addWidget(right_side)
        self.split_view.setSizes([700, 700])

        self.left_stack.addWidget(self.split_view)
        self.left_stack.setCurrentWidget(self.split_view)

        # Salva i tab splittati per reinserirli in reset
        self.split_tabs = [(left_title, left_widget), (right_title, right_widget)]



    def reset_split(self):
        if hasattr(self, "split_view"):
            idx = self.left_stack.indexOf(self.split_view)
            if idx != -1:
                w = self.left_stack.widget(idx)
                self.left_stack.removeWidget(w)
                w.deleteLater()
            del self.split_view

        self.left_stack.setCurrentWidget(self.main_panel)

        # Se hai salvato i tab splittati, reinseriscili
        if hasattr(self, "split_tabs"):
            for title, widget in self.split_tabs:
                self.main_panel.addTab(widget, title)
            del self.split_tabs
        else:
            # Altrimenti ricrea dai default
            self.main_panel.clear()
            for title, widget in self.default_tabs:
                self.main_panel.addTab(widget, title)



    def toggle_help(self):
        if self.help_browser.isVisible():
            # Nascondi help
            self.searchbar.hide()
            self.help_browser.hide()
            self.top_splitter.setSizes([1400, 0])
            self.terminal.input_line.setFocus()
        else:
            # Mostra help
            self.searchbar.show()
            self.help_browser.show()
            self.top_splitter.setSizes([1000, 400])
