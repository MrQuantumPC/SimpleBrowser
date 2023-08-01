import sys
import re
from PyQt5.QtWidgets import QApplication, QMainWindow, QAction, QToolBar, QLineEdit, QPushButton, QFileDialog, QMessageBox, QTabWidget, QLabel, QComboBox, QVBoxLayout, QHBoxLayout, QDialog, QToolButton, QColorDialog
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineDownloadItem
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QUrl, QTranslator, QLocale, QSettings

class SimpleBrowser(QMainWindow):
    def __init__(self):
        super().__init__()
        self.new_tab_url = 'https://www.google.com'  # Domyślny adres dla nowej karty
        self.initUI()

    def initUI(self):
        # Pozostała część kodu pozostaje bez zmian...
        self.setWindowTitle("SimpleBrowser")  # Ustawienie tytułu okna

        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.tabs.setDocumentMode(True)
        self.tabs.tabBarDoubleClicked.connect(self.add_new_tab)

        self.add_new_tab()

        self.search_bar = QLineEdit()
        self.search_bar.returnPressed.connect(self.load_url)

        self.go_button = QPushButton(QIcon("search.png"), '')
        self.go_button.clicked.connect(self.load_url)
        self.go_button.setFixedSize(24, 24)

        self.refresh_button = QPushButton(QIcon("refresh.png"), '')
        self.refresh_button.clicked.connect(self.refresh_page)
        self.refresh_button.setFixedSize(24, 24)

        self.add_tab_button = QPushButton(QIcon("add_tab.png"), '')
        self.add_tab_button.clicked.connect(self.add_new_tab)
        self.add_tab_button.setFixedSize(24, 24)

        self.toolbar = QToolBar()
        self.toolbar.setStyleSheet(open("style.css", "r").read())  # Stylizacja paska narzędzi
        self.toolbar.addWidget(self.go_button)
        self.toolbar.addWidget(self.search_bar)
        self.toolbar.addWidget(self.refresh_button)
        self.toolbar.addWidget(self.add_tab_button)

        # Dodanie akcji dla trybu prywatnego
        self.private_mode_action = QAction(QIcon('private_mode.png'), 'Private Mode', self)
        self.private_mode_action.setCheckable(True)
        self.private_mode_action.triggered.connect(self.toggle_private_mode)

        # Dodanie akcji dla ustawień
        self.settings_action = QAction(QIcon('settings.png'), 'Ustawienia', self)
        self.settings_action.triggered.connect(self.show_settings)

        self.toolbar.addAction(self.private_mode_action)
        self.toolbar.addAction(self.settings_action)

        self.addToolBar(self.toolbar)
        self.setCentralWidget(self.tabs)

        self.statusBar().showMessage('Ready')

        # Przypisanie sygnału on_download_requested do metody handle_download
        self.browser.page().profile().downloadRequested.connect(self.handle_download)

        # Włączanie paska postępu
        self.browser.loadProgress.connect(self.update_progress)

        # Zmienna do przechowywania informacji o prywatnym trybie
        self.private_mode = False

        # Wczytanie ustawień
        self.load_settings()

    def load_url(self):
        input_text = self.search_bar.text()
        if self.is_valid_url(input_text):
            if not input_text.startswith('http://') and not input_text.startswith('https://'):
                input_text = 'http://' + input_text
            self.browser.setUrl(QUrl(input_text))
        else:
            search_query = self.get_search_engine_url() + input_text
            self.browser.setUrl(QUrl(search_query))

    def handle_download(self, download: QWebEngineDownloadItem):
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getSaveFileName(self, "Pobierz plik", download.path(), "Wszystkie pliki (*);;Pliki tekstowe (*.txt);;Pliki HTML (*.html);;Pliki PDF (*.pdf)", options=options)

        if file_path:
            download.setPath(file_path)
            download.accept()

    def download_file(self):
        self.browser.page().triggerAction(QWebEnginePage.DownloadLink)

    def is_valid_url(self, url):
        # Sprawdzenie, czy wprowadzone dane są adresem URL
        # Wykorzystujemy prosty regex dla uproszczenia, ale w rzeczywistych przypadkach warto użyć bardziej zaawansowanych metod
        pattern = re.compile(r'^https?://(?:\w+\.)?\w+\.\w+(?:/.*)?$')
        return bool(pattern.match(url))

    def closeEvent(self, event):
        reply = QMessageBox.question(self, 'Potwierdzenie zamknięcia',
                                     "Czy na pewno chcesz wyjść?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()

    def add_new_tab(self):
        browser = CustomWebEngineView(self)
        browser.setUrl(QUrl(self.new_tab_url))
        index = self.tabs.addTab(browser, 'New Tab')
        self.tabs.setCurrentIndex(index)
        self.browser = browser
        self.browser.urlChanged.connect(self.update_url)

    def close_tab(self, index):
        if self.tabs.count() > 1:
            self.tabs.widget(index).deleteLater()
            self.tabs.removeTab(index)
            # Aktualizacja referencji do aktualnej karty
            self.browser = self.tabs.currentWidget()
        if self.tabs.count() == 0:
            self.close()

    def update_url(self, q):
        self.search_bar.setText(q.toString())

    def toggle_private_mode(self):
        self.private_mode = not self.private_mode
        self.statusBar().showMessage('Private Mode Enabled' if self.private_mode else 'Ready')

    def update_progress(self, progress):
        if progress < 100:
            self.statusBar().showMessage(f'Loading... {progress}%')
        else:
            self.statusBar().showMessage('Ready')

    def refresh_page(self):
        self.browser.reload()

    def show_settings(self):
        dialog = SettingsDialog(self)
        dialog.exec_()

    def load_settings(self):
        settings = QSettings('SimpleBrowser', 'Settings')
        self.homepage_url = settings.value('homepage_url', 'https://www.google.com')
        self.new_tab_url = settings.value('new_tab_url', 'https://www.google.com')
        self.search_engine = settings.value('search_engine', 'Google')

    def save_settings(self):
        settings = QSettings('SimpleBrowser', 'Settings')
        settings.setValue('homepage_url', self.homepage_url)
        settings.setValue('new_tab_url', self.new_tab_url)
        settings.setValue('search_engine', self.search_engine)

    def get_search_engine_url(self):
        if self.search_engine == 'Google':
            return 'https://www.google.com/search?q='
        elif self.search_engine == 'Bing':
            return 'https://www.bing.com/search?q='
        elif self.search_engine == 'DuckDuckGo':
            return 'https://duckduckgo.com/?q='

class CustomWebEngineView(QWebEngineView):
    def __init__(self, parent):
        super().__init__(parent)

    def createWindow(self, windowType):
        # Otwieranie nowej karty dla nowych okien
        if windowType == QWebEnginePage.WebBrowserTab:
            view = CustomWebEngineView(self.parent())
            view.urlChanged.connect(self.parent().update_url)
            index = self.parent().tabs.addTab(view, 'New Tab')
            self.parent().tabs.setCurrentIndex(index)
            return view
        return super().createWindow(windowType)

class SettingsDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("Ustawienia")
        self.setFixedSize(400, 200)

        layout = QVBoxLayout()

        # Ustawienie strony startowej
        homepage_label = QLabel("Strona startowa:")
        self.homepage_edit = QLineEdit()
        self.homepage_edit.setText(self.parent().homepage_url)
        layout.addWidget(homepage_label)
        layout.addWidget(self.homepage_edit)

        # Wybór wyszukiwarki
        search_engine_label = QLabel("Wyszukiwarka:")
        self.search_engine_combobox = QComboBox()
        self.search_engine_combobox.addItems(['Google', 'Bing', 'DuckDuckGo'])
        self.search_engine_combobox.setCurrentText(self.parent().search_engine)
        layout.addWidget(search_engine_label)
        layout.addWidget(self.search_engine_combobox)

        # Przyciski Zapisz i Anuluj
        button_layout = QHBoxLayout()
        self.save_button = QPushButton("Zapisz")
        self.save_button.clicked.connect(self.save_settings)
        self.cancel_button = QPushButton("Anuluj")
        self.cancel_button.clicked.connect(self.close)
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)

        layout.addLayout(button_layout)
        self.setLayout(layout)

    def save_settings(self):
        self.parent().homepage_url = self.homepage_edit.text()
        self.parent().new_tab_url = self.homepage_edit.text()
        self.parent().search_engine = self.search_engine_combobox.currentText()
        self.parent().save_settings()
        self.close()

if __name__ == '__main__':
    app = QApplication(sys.argv)

    # Ustawienie tłumaczenia na język systemowy
    translator = QTranslator()
    system_locale = QLocale.system().name()
    translator.load(f":/translations/qtwebengine_{system_locale}")
    app.installTranslator(translator)

    browser = SimpleBrowser()
    browser.showMaximized()  # Uruchomienie przeglądarki w oknie maksymalizowanym
    sys.exit(app.exec_())

