from PySide6.QtWidgets import QLineEdit, QCompleter, QPlainTextEdit, QTextBrowser, QLabel, QWidget, QVBoxLayout, QApplication, QSplitter
from PySide6.QtCore import Qt, QStringListModel
from backend.dsl_parser import COMMANDS, execute_command

class SearchBar(QLineEdit):
    def __init__(self, suggestions: list[str]):
        super().__init__()
        self.setPlaceholderText("🔍 Cerca causale o comando DSL...")
        completer = QCompleter(suggestions)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.setCompleter(completer)


class HelpBrowser(QTextBrowser):
    def __init__(self):
        super().__init__()
        self.setText("💡 Digita un termine per vedere suggerimenti.")



class TerminalInput(QLineEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_widget = parent  # riferimento al TerminalWidget


    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Tab and self.completer():
            c = self.completer()
            c.setCompletionPrefix(self.text())
            c.complete()
            m = c.popup().model()
            if m and m.rowCount() > 0:
                c.setCurrentRow(0)
                completion = c.currentCompletion()
                if completion:
                    self.setText(completion)
                    self.setCursorPosition(len(completion))
                c.popup().hide()
                event.accept()
                return
            event.accept()
            return
        
        # Gestione storico ↑/↓
        if event.key() == Qt.Key_Up:
            if self.parent_widget:
                cmd = self.parent_widget.get_prev_history()
                if cmd is not None:
                    self.setText(cmd)
                    self.setCursorPosition(len(cmd))
            event.accept()
            return

        if event.key() == Qt.Key_Down:
            if self.parent_widget:
                cmd = self.parent_widget.get_next_history()
                if cmd is not None:
                    self.setText(cmd)
                    self.setCursorPosition(len(cmd))
                else:
                    self.clear()
            event.accept()
            return

        super().keyPressEvent(event)


class TerminalWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)   # niente margini
        layout.setSpacing(0)                    # niente spaziatura
        default_font = QApplication.font()


        # Output area
        self.output_area = QPlainTextEdit()
        self.output_area.setReadOnly(True)
        self.output_area.setStyleSheet("""
            QPlainTextEdit {
                border: none;
                background: black;
                color: #d4d4d4;
                padding: 8px;
                font-size: 14px;
            }
        """)
        self.output_area.setFont(default_font)

        self.history = []
        self.history_index = -1

        # Input line
        self.input_line = TerminalInput(parent=self)
        self.input_line.setObjectName("terminalInput")
        self.input_line.setPlaceholderText("Scrivi comandi DSL...")
        self.input_line.setStyleSheet("""
            QLineEdit {
                border: none;
                border-radius: 0px;                  
                background: black;
                color: #d4d4d4;
                padding: 8px;
                font-family: "SF Pro Text", "Helvetica Neue", "Segoe UI", "Arial", sans-serif;
                font-size: 14px;
            }
        """)
        self.input_line.returnPressed.connect(self.run_command)

       

        # Autocomplete
        completer = QCompleter(COMMANDS, self)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        completer.setFilterMode(Qt.MatchStartsWith)
        completer.setCompletionMode(QCompleter.PopupCompletion)
        self.input_line.setCompleter(completer)

        layout.addWidget(self.output_area)
        layout.addWidget(self.input_line)

    def run_command(self):
        cmd = self.input_line.text().strip()
        if cmd:
            result = execute_command(cmd)

            # stampa sempre il comando digitato
            self.output_area.appendPlainText(f"> {cmd}")

            if isinstance(result, dict):
                action = result.get("action")
                if action == "split":
                    self.window().show_split(result["left"], result["right"])
                    self.output_area.appendPlainText(f"🔀 Split {result['left']} and {result['right']}")
                elif action == "unsplit":
                    self.window().reset_split()
                    self.output_area.appendPlainText("↩️ Vista tab ripristinata")
            else:
                self.output_area.appendPlainText(str(result))


            self.output_area.appendPlainText("")  # riga vuota per separare
            # aggiorna lo storico
            self.history.append(cmd)
            self.history_index = len(self.history)

        self.input_line.clear()


    def get_prev_history(self):
        if self.history and self.history_index > 0:
            self.history_index -= 1
            return self.history[self.history_index]
        elif self.history and self.history_index == 0:
            return self.history[0]
        return None

    def get_next_history(self):
        if self.history and self.history_index < len(self.history) - 1:
            self.history_index += 1
            return self.history[self.history_index]
        elif self.history_index == len(self.history) - 1:
            self.history_index += 1
            return None
        return None
    


























