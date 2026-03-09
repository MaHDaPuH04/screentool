"""
Диалоговое окно справки
"""
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QTextBrowser, QPushButton, QHBoxLayout
# from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from help_manual import HELP_MANUAL


class HelpDialog(QDialog):
    """Диалог с руководством пользователя"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Справка - Auto Screenshot Tool")
        self.resize(700, 600)
        self.setModal(False)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        # Текст справки
        self.text_browser = QTextBrowser()
        self.text_browser.setHtml(HELP_MANUAL)
        self.text_browser.setOpenExternalLinks(True)
        self.text_browser.setFont(QFont("Arial", 10))
        layout.addWidget(self.text_browser)
        
        # Кнопка закрытия
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.close_btn = QPushButton("Закрыть")
        self.close_btn.setFixedWidth(100)
        self.close_btn.clicked.connect(self.close)
        button_layout.addWidget(self.close_btn)
        
        layout.addLayout(button_layout)