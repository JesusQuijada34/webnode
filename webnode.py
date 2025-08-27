
import sys
import os
import re
import requests
from urllib.parse import urlparse
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl
from bs4 import BeautifulSoup

# ---------------------------
# Custom Widgets (QSS GitHub-like)
# ---------------------------

class StyledLineEdit(QtWidgets.QLineEdit):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setFixedHeight(32)
        self.setFont(QtGui.QFont("Roboto", 10))
        self.setContentsMargins(0, 0, 0, 0)
        self.setAttribute(QtCore.Qt.WA_MacShowFocusRect, False)
        self.setStyleSheet(self._style("normal"))
        self.setVisible(True)  # Ensure input is visible

    def enterEvent(self, event):
        self.setStyleSheet(self._style("hover"))
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.setStyleSheet(self._style("normal"))
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        self.setStyleSheet(self._style("pressed"))
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        self.setStyleSheet(self._style("hover"))
        super().mouseReleaseEvent(event)

    def focusInEvent(self, event):
        self.setStyleSheet(self._style("hover"))
        super().focusInEvent(event)

    def focusOutEvent(self, event):
        self.setStyleSheet(self._style("normal"))
        super().focusOutEvent(event)

    def _style(self, state):
        # GitHub-like QSS for input fields
        if state == "normal":
            border = "#444c56"
            bg = "#22272e"
        elif state == "hover":
            border = "#539bf5"
            bg = "#2d333b"
        elif state == "pressed":
            border = "#316dca"
            bg = "#1b1f23"
        else:
            border = "#444c56"
            bg = "#22272e"
        return f"""
        QLineEdit {{
            border: 1px solid {border};
            border-radius: 3px;
            background-color: {bg};
            color: #adbac7;
            padding-left: 8px;
            padding-right: 8px;
            font-family: 'Roboto', Arial, sans-serif;
        }}
        """

class StyledButton(QtWidgets.QPushButton):
    def __init__(self, text, width=128, *args, **kwargs):
        super().__init__(text, *args, **kwargs)
        self.setFixedHeight(32)
        self.setFixedWidth(width)
        self.setFont(QtGui.QFont("Roboto", 10, QtGui.QFont.Bold))
        self.setCursor(QtCore.Qt.PointingHandCursor)
        self.setStyleSheet(self._style("normal"))
        self._state = "normal"

    def enterEvent(self, event):
        self.setStyleSheet(self._style("hover"))
        self._state = "hover"
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.setStyleSheet(self._style("normal"))
        self._state = "normal"
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        self.setStyleSheet(self._style("pressed"))
        self._state = "pressed"
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        self.setStyleSheet(self._style("hover"))
        self._state = "hover"
        super().mouseReleaseEvent(event)

    def _style(self, state):
        # GitHub-like QSS for buttons
        if state == "normal":
            border = "#444c56"
            bg = "#2d333b"
            color = "#adbac7"
        elif state == "hover":
            border = "#539bf5"
            bg = "#444c56"
            color = "#adbac7"
        elif state == "pressed":
            border = "#316dca"
            bg = "#22272e"
            color = "#adbac7"
        else:
            border = "#444c56"
            bg = "#2d333b"
            color = "#adbac7"
        return f"""
        QPushButton {{
            border: 1px solid {border};
            border-radius: 3px;
            background-color: {bg};
            color: {color};
            font-family: 'Roboto', Arial, sans-serif;
        }}
        QPushButton:disabled {{
            color: #768390;
            background-color: #22272e;
        }}
        """

# ---------------------------
# Folder Handling
# ---------------------------

def get_documents_folder():
    # Try standard locations
    if sys.platform.startswith("win"):
        doc = os.path.expandvars(r"%USERPROFILE%\Documents")
    else:
        doc = os.path.expanduser("~/Documents")
    if os.path.isdir(doc):
        return doc

    # Try to find similar folders
    home = os.path.expanduser("~")
    candidates = []
    for name in os.listdir(home):
        path = os.path.join(home, name)
        if os.path.isdir(path) and re.search(r'doc', name, re.IGNORECASE):
            candidates.append(path)
    if candidates:
        # Pick the one with the shortest name (most likely)
        return sorted(candidates, key=lambda x: len(x))[0]
    return None

def get_webnode_apps_folder():
    doc_folder = get_documents_folder()
    if not doc_folder:
        return None
    wn_folder = os.path.join(doc_folder, "WebNode Apps")
    if not os.path.exists(wn_folder):
        os.makedirs(wn_folder, exist_ok=True)
    return wn_folder

def get_app_folder(base_folder, company, name):
    safe_company = sanitize_filename(company)
    safe_name = sanitize_filename(name)
    app_folder = os.path.join(base_folder, "app", f"{safe_company}.{safe_name}")
    os.makedirs(app_folder, exist_ok=True)
    return app_folder

# ---------------------------
# Favicon Extraction
# ---------------------------

def get_favicon_url(url):
    try:
        resp = requests.get(url, timeout=5, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(resp.text, "html.parser")
        icon_link = soup.find("link", rel=lambda x: x and "icon" in x.lower())
        if icon_link and icon_link.get("href"):
            href = icon_link["href"]
            if href.startswith("http"):
                return href
            else:
                parsed = urlparse(url)
                base = f"{parsed.scheme}://{parsed.netloc}"
                if href.startswith("/"):
                    return base + href
                else:
                    return base + "/" + href
        # fallback to /favicon.ico
        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}/favicon.ico"
    except Exception:
        # fallback to /favicon.ico
        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}/favicon.ico"

def download_favicon(favicon_url, save_path):
    try:
        resp = requests.get(favicon_url, timeout=5, headers={"User-Agent": "Mozilla/5.0"})
        if resp.status_code == 200 and resp.content:
            with open(save_path, "wb") as f:
                f.write(resp.content)
            return True
    except Exception:
        pass
    return False

# ---------------------------
# Script Generation Logic
# ---------------------------

SCRIPT_TEMPLATE = '''import sys
import os
from PyQt5 import QtWidgets, QtGui
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl

def main():
    app = QtWidgets.QApplication(sys.argv)
    win = QtWidgets.QMainWindow()
    win.setWindowTitle("{title}")
    win.resize(1024, 768)
    icon_path = "{icon_path}"
    if icon_path and os.path.exists(icon_path):
        win.setWindowIcon(QtGui.QIcon(icon_path))
    view = QWebEngineView()
    view.setUrl(QUrl({url}))
    win.setCentralWidget(view)
    win.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
'''

def sanitize_filename(s):
    # Remove problematic characters for filenames
    return re.sub(r'[^a-zA-Z0-9._-]', '', s)

def validate_url(url):
    # Basic validation for http(s) URLs
    return re.match(r'^https?://', url.strip())

def generate_script(company, name, title, url, folder):
    safe_company = sanitize_filename(company)
    safe_name = sanitize_filename(name)
    app_folder = get_app_folder(folder, company, name)
    filename = f"webnode.{safe_company}.{safe_name}.py"
    icon_filename = f"webnode.{safe_company}.{safe_name}.ico"
    script_path = os.path.join(app_folder, filename)
    icon_path = os.path.join(app_folder, icon_filename)

    # Download favicon
    favicon_url = get_favicon_url(url)
    download_favicon(favicon_url, icon_path)

    # url must be a string literal for QUrl
    script = SCRIPT_TEMPLATE.format(
        title=title.replace('"', '\\"'),
        url=repr(url.strip()),
        icon_path=icon_path.replace("\\", "\\\\").replace('"', '\\"')
    )
    with open(script_path, "w", encoding="utf-8") as f:
        f.write(script)
    return script_path

# ---------------------------
# Main Application Window
# ---------------------------

class MainWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("WebNode Script Generator")
        self.setFixedSize(800, 400)
        self.setStyleSheet("""
            QWidget {
                background-color: #22272e;
            }
            QLabel {
                color: #adbac7;
                font-size: 13px;
                font-family: 'Roboto', Arial, sans-serif;
            }
        """)
        self.init_ui()

    def init_ui(self):
        # Main horizontal layout
        main_layout = QtWidgets.QHBoxLayout()
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(24)

        # Left: Form layout
        form_widget = QtWidgets.QWidget()
        form_layout = QtWidgets.QVBoxLayout()
        form_layout.setSpacing(18)
        form_layout.setContentsMargins(0, 0, 0, 0)

        self.inputs = {}
        for label_text, key in [
            ("Company", "company"),
            ("Name", "name"),
            ("Title", "title"),
            ("URL", "url")
        ]:
            field_widget = QtWidgets.QWidget()
            field_layout = QtWidgets.QVBoxLayout()
            field_layout.setSpacing(6)
            field_layout.setContentsMargins(0, 0, 0, 0)
            lbl = QtWidgets.QLabel(label_text)
            lbl.setFont(QtGui.QFont("Roboto", 11))
            inp = StyledLineEdit()
            inp.setPlaceholderText(f"Enter {label_text}...")
            inp.setVisible(True)  # Ensure input is visible
            self.inputs[key] = inp
            field_layout.addWidget(lbl)
            field_layout.addSpacing(2)
            field_layout.addWidget(inp)
            field_layout.addSpacing(8)
            field_widget.setLayout(field_layout)
            form_layout.addWidget(field_widget)

        form_layout.addSpacing(10)

        # Generate button
        self.btn_generate = StyledButton("Generate Script", width=160)
        self.btn_generate.clicked.connect(self.on_generate)
        btn_layout = QtWidgets.QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_generate)
        btn_layout.addStretch()
        form_layout.addLayout(btn_layout)

        # Status label
        self.status = QtWidgets.QLabel("")
        self.status.setAlignment(QtCore.Qt.AlignCenter)
        self.status.setStyleSheet("color: #539bf5; font-size: 11px; font-family: 'Roboto', Arial, sans-serif;")
        form_layout.addSpacing(8)
        form_layout.addWidget(self.status)

        form_widget.setLayout(form_layout)
        main_layout.addWidget(form_widget, 1)

        # Right: Script preview
        preview_widget = QtWidgets.QWidget()
        preview_layout = QtWidgets.QVBoxLayout()
        preview_layout.setContentsMargins(0, 0, 0, 0)
        preview_layout.setSpacing(8)

        preview_label = QtWidgets.QLabel("Script Preview")
        preview_label.setFont(QtGui.QFont("Roboto", 12, QtGui.QFont.Bold))
        preview_label.setStyleSheet("color: #adbac7; margin-bottom: 4px;")
        preview_layout.addWidget(preview_label)

        self.script_preview = QtWidgets.QPlainTextEdit()
        self.script_preview.setReadOnly(True)
        self.script_preview.setFont(QtGui.QFont("Roboto Mono", 10))
        self.script_preview.setStyleSheet("""
            QPlainTextEdit {
                background-color: #2d333b;
                color: #adbac7;
                border: 1px solid #444c56;
                border-radius: 3px;
                font-family: 'Roboto Mono', 'Consolas', monospace;
                padding: 8px;
            }
        """)
        self.script_preview.setMinimumWidth(340)
        self.script_preview.setMaximumWidth(400)
        self.script_preview.setMinimumHeight(320)
        preview_layout.addWidget(self.script_preview, 1)

        preview_widget.setLayout(preview_layout)
        main_layout.addWidget(preview_widget, 1)

        self.setLayout(main_layout)

        # Connect input changes to preview update
        for key in self.inputs:
            self.inputs[key].textChanged.connect(self.update_preview)
        self.update_preview()

    def update_preview(self):
        company = self.inputs["company"].text().strip()
        name = self.inputs["name"].text().strip()
        title = self.inputs["title"].text().strip()
        url = self.inputs["url"].text().strip()
        # Use dummy values if empty for preview
        preview_title = title if title else "App Title"
        preview_url = url if url else "https://example.com"
        safe_company = sanitize_filename(company if company else "company")
        safe_name = sanitize_filename(name if name else "name")
        icon_path = os.path.join("app", f"{safe_company}.{safe_name}", f"webnode.{safe_company}.{safe_name}.ico")
        # url must be a string literal for QUrl
        script = SCRIPT_TEMPLATE.format(
            title=preview_title.replace('"', '\\"'),
            url=repr(preview_url),
            icon_path=icon_path.replace("\\", "\\\\").replace('"', '\\"')
        )
        self.script_preview.setPlainText(script)

    def on_generate(self):
        company = self.inputs["company"].text().strip()
        name = self.inputs["name"].text().strip()
        title = self.inputs["title"].text().strip()
        url = self.inputs["url"].text().strip()

        # Input validation
        if not company or not name or not title or not url:
            self.status.setText("All fields are required.")
            return
        if not validate_url(url):
            self.status.setText("URL must start with http:// or https://")
            return

        folder = get_webnode_apps_folder()
        if not folder:
            self.status.setText("Could not locate a Documents folder.")
            return

        try:
            script_path = generate_script(company, name, title, url, folder)
            self.status.setText(f"Script generated: {os.path.basename(script_path)}")
        except Exception as e:
            self.status.setText(f"Error: {e}")

# ---------------------------
# Main Entry Point
# ---------------------------

def main():
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle("Fusion")
    # Set dark palette
    palette = QtGui.QPalette()
    palette.setColor(QtGui.QPalette.Window, QtGui.QColor("#22272e"))
    palette.setColor(QtGui.QPalette.WindowText, QtGui.QColor("#adbac7"))
    palette.setColor(QtGui.QPalette.Base, QtGui.QColor("#22272e"))
    palette.setColor(QtGui.QPalette.AlternateBase, QtGui.QColor("#2d333b"))
    palette.setColor(QtGui.QPalette.ToolTipBase, QtGui.QColor("#2d333b"))
    palette.setColor(QtGui.QPalette.ToolTipText, QtGui.QColor("#adbac7"))
    palette.setColor(QtGui.QPalette.Text, QtGui.QColor("#adbac7"))
    palette.setColor(QtGui.QPalette.Button, QtGui.QColor("#2d333b"))
    palette.setColor(QtGui.QPalette.ButtonText, QtGui.QColor("#adbac7"))
    palette.setColor(QtGui.QPalette.BrightText, QtCore.Qt.red)
    palette.setColor(QtGui.QPalette.Highlight, QtGui.QColor("#539bf5"))
    palette.setColor(QtGui.QPalette.HighlightedText, QtGui.QColor("#fff"))
    app.setPalette(palette)

    # Set Roboto as default font if available
    font = QtGui.QFont("Roboto", 10)
    app.setFont(font)

    win = MainWindow()
    win.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
