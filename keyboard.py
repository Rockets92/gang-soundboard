import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QFrame, QVBoxLayout, QGridLayout,
    QPushButton, QGraphicsBlurEffect, QHBoxLayout, QGraphicsDropShadowEffect, QComboBox, QToolButton, QSlider, QLabel, QTabBar, QStackedLayout
)
from PyQt6.QtGui import QColor
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtCore import QSettings
from qt_material import apply_stylesheet

class KeyboardWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # Frameless and transparent window
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # Central widget without blur effect
        self.central_widget = QFrame()
        self.central_widget.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 rgba(255, 218, 185, 255), stop:1 rgba(176, 224, 230, 255));
            border: none;
            border-radius: 20px;
        """)
        self.setCentralWidget(self.central_widget)

        # Glass container for keyboard
        self.glass_container = QFrame(self.central_widget)
        self.glass_container.setStyleSheet("background: transparent;")
        
        # Layer 1: blurred background
        self.background_frame = QFrame(self.glass_container)
        self.background_frame.setStyleSheet("""
            background-color: rgba(255, 255, 255, 0.1);
            border: 1px solid rgba(255, 255, 255, 0.4);
            border-radius: 20px;
        """)
        bg_blur = QGraphicsBlurEffect(self.background_frame)
        bg_blur.setBlurRadius(50)
        self.background_frame.setGraphicsEffect(bg_blur)
        
        # Layer 2: keyboard widget container (no blur)
        self.keyboard_frame = QWidget(self.glass_container)
        
        # Stack layers
        stack = QStackedLayout(self.glass_container)
        stack.addWidget(self.background_frame)
        stack.addWidget(self.keyboard_frame)
        stack.setCurrentWidget(self.keyboard_frame)
        self.glass_container.setLayout(stack)


        # Costruzione dinamica della tastiera in base alle preferenze salvate
        layout_type = self.settings.value("size_combo", "65%") if hasattr(self, 'settings') else "65%"
        key_format = self.settings.value("format_combo", "ANSI") if hasattr(self, 'settings') else "ANSI"
        lang = self.settings.value("lang_combo", "US English") if hasattr(self, 'settings') else "US English"

        if layout_type in ["60%", "65%", "TKL"]:
            rows = [
                ['Q', 'W', 'E', 'R', 'T', 'Y', 'U', 'I', 'O', 'P'],
                ['A', 'S', 'D', 'F', 'G', 'H', 'J', 'K', 'L'],
                ['Z', 'X', 'C', 'V', 'B', 'N', 'M']
            ]
        elif layout_type == "75%":
            rows = [
                ['Esc', 'Q', 'W', 'E', 'R', 'T', 'Y', 'U', 'I', 'O', 'P', 'Del'],
                ['Tab', 'A', 'S', 'D', 'F', 'G', 'H', 'J', 'K', 'L', ';'],
                ['Shift', 'Z', 'X', 'C', 'V', 'B', 'N', 'M', ',', '.']
            ]
        else:
            rows = [
                ['Esc', '1', '2', '3', '4', '5', '6', '7', '8', '9', '0', 'Del'],
                ['Tab', 'Q', 'W', 'E', 'R', 'T', 'Y', 'U', 'I', 'O', 'P', '[', ']'],
                ['Caps', 'A', 'S', 'D', 'F', 'G', 'H', 'J', 'K', 'L', ';', '\''],
                ['Shift', 'Z', 'X', 'C', 'V', 'B', 'N', 'M', ',', '.', '/', 'Shift']
            ]

        self.glass_container.adjustSize()
        key_width = 60
        key_height = 60
        spacing = 12
        num_rows = len(rows)
        num_cols = max(len(r) for r in rows)

        total_width = (key_width + spacing) * num_cols - spacing + 40
        total_height = (key_height + spacing) * num_rows - spacing + 40

        self.glass_container.setFixedSize(total_width, total_height)

        # Add drop shadow to keyboard container for 3D effect
        container_shadow = QGraphicsDropShadowEffect(self.glass_container)
        container_shadow.setBlurRadius(30)
        container_shadow.setOffset(0, 10)
        container_shadow.setColor(QColor(0, 0, 0, 100))
        self.glass_container.setGraphicsEffect(container_shadow)

        # Layout for keys centered
        main_layout = QVBoxLayout(self.central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(12)
        # Window control buttons (minimize, maximize/restore, close)
        title_layout = QHBoxLayout()
        title_layout.addStretch()
        min_btn = QToolButton()
        min_btn.setText("–")
        min_btn.clicked.connect(self.showMinimized)
        max_btn = QToolButton()
        max_btn.setText("□")
        max_btn.clicked.connect(self.toggleMaxRestore)
        close_btn = QToolButton()
        close_btn.setText("✕")
        close_btn.clicked.connect(self.close)
        for btn in (min_btn, max_btn, close_btn):
            btn.setFixedSize(30, 30)
            btn.setStyleSheet("""
                QToolButton {
                    background: transparent;
                    color: #ffffff;
                    font-size: 16px;
                    border: none;
                }
                QToolButton:hover {
                    background: rgba(255,255,255,30);
                }
            """)
            title_layout.addWidget(btn)
        main_layout.addLayout(title_layout)
        # Tab bar for Mac/Windows selection
        tab_bar = QTabBar()
        tab_bar.addTab("Windows")
        tab_bar.addTab("Mac")
        tab_bar.setDrawBase(False)
        tab_bar.setExpanding(False)
        tab_bar.setStyleSheet("""
            QTabBar {
                background: transparent;
                border: none;
            }
            QTabBar::tab {
                background-color: rgba(255,255,255,0.15);
                border: none;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                padding: 8px 16px;
                margin-right: 4px;
                color: #3A76A5;
                font-weight: bold;
            }
            QTabBar::tab:last {
                margin-right: 0;
            }
            QTabBar::tab:selected {
                background-color: rgba(255,255,255,0.35);
                border-bottom: 3px solid #3A76A5;
            }
        """)
        shadow = QGraphicsDropShadowEffect(tab_bar)
        shadow.setBlurRadius(15)
        shadow.setOffset(0, 2)
        shadow.setColor(QColor(0, 0, 0, 80))
        tab_bar.setGraphicsEffect(shadow)
        # Tab bar and volume slider
        self.tab_bar = tab_bar
        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setRange(0, 100)
        slider.setValue(50)
        slider.setFixedHeight(20)
        slider.setStyleSheet("""
            QSlider::groove:horizontal {
                background: transparent;
                height: 8px;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: rgba(255,255,255,0.9);
                border: none;
                width: 16px;
                margin: -4px 0;
                border-radius: 8px;
            }
        """)
        # Label for volume slider
        volume_label = QLabel("Volume")
        volume_label.setStyleSheet("""
            background: transparent;
            color: #ffffff;
            font-size: 16px;
            padding-right: 8px;
        """)
        self.slider = slider
        slider.valueChanged.connect(lambda val: self.settings.setValue("volume_slider", val))

        # Place tabs, label, and slider in a transparent container with fixed width and space-between alignment
        tab_slider_container = QWidget()
        tab_slider_container.setStyleSheet("background: transparent;")
        tab_slider_container.setFixedWidth(750)

        tab_slider_layout = QHBoxLayout(tab_slider_container)
        tab_slider_layout.setContentsMargins(0, 0, 0, 0)
        tab_slider_layout.setSpacing(8)
        tab_slider_layout.addWidget(tab_bar)
        tab_slider_layout.addStretch()
        tab_slider_layout.addWidget(volume_label)
        tab_slider_layout.addWidget(slider)

        top_hbox = QHBoxLayout()
        top_hbox.addStretch()
        top_hbox.addWidget(tab_slider_container)
        top_hbox.addStretch()
        main_layout.addLayout(top_hbox)
        # Dropdown controls at top of window
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(10)
        size_combo = QComboBox()
        size_combo.addItems(['60%', '65%', '75%', '80%', '100%', 'TKL', '1800'])
        format_combo = QComboBox()
        format_combo.addItems(['ANSI', 'ISO', 'JIS'])
        lang_combo = QComboBox()
        lang_combo.addItems(['US English', 'UK English', 'DE', 'FR', 'IT', 'ES'])
        for combo in (size_combo, format_combo, lang_combo):
            combo.setStyleSheet("""
                QComboBox {
                    background-color: rgba(255, 255, 255, 0.15);
                    border: 1px solid rgba(255, 255, 255, 0.4);
                    border-radius: 8px;
                    color: #3A76A5;
                    padding: 5px;
                }
                QComboBox::drop-down {
                    border: none;
                }
                QComboBox QAbstractItemView {
                    background-color: rgba(255, 255, 255, 0.9);
                    border: 1px solid rgba(255, 255, 255, 0.4);
                    border-radius: 8px;
                    selection-background-color: rgba(92, 167, 219, 0.2);
                    selection-color: #3A76A5;
                    outline: none;
                }
                QComboBox QAbstractItemView::item {
                    padding: 8px;
                }
            """)
            shadow = QGraphicsDropShadowEffect(combo)
            shadow.setBlurRadius(15)
            shadow.setOffset(0, 2)
            shadow.setColor(QColor(0, 0, 0, 80))
            combo.setGraphicsEffect(shadow)
            controls_layout.addWidget(combo)
        # Connetti segnali per salvare le modifiche
        size_combo.currentTextChanged.connect(lambda val: self.settings.setValue("size_combo", val))
        format_combo.currentTextChanged.connect(lambda val: self.settings.setValue("format_combo", val))
        lang_combo.currentTextChanged.connect(lambda val: self.settings.setValue("lang_combo", val))
        # Salva l'indice del tab selezionato
        tab_bar.currentChanged.connect(lambda index: self.settings.setValue("tab_index", index))
        # QSettings per persistenza
        self.settings = QSettings("GangSoundboard", "KeyboardApp")

        # Ripristina i valori salvati
        size_combo.setCurrentText(self.settings.value("size_combo", "65%"))
        format_combo.setCurrentText(self.settings.value("format_combo", "ANSI"))
        lang_combo.setCurrentText(self.settings.value("lang_combo", "US English"))
        slider.setValue(int(self.settings.value("volume_slider", 50)))
        tab_bar.setCurrentIndex(int(self.settings.value("tab_index", 0)))
        # Center dropdown controls above keyboard
        ctrl_hbox = QHBoxLayout()
        ctrl_hbox.addStretch()
        ctrl_hbox.addLayout(controls_layout)
        ctrl_hbox.addStretch()
        main_layout.addLayout(ctrl_hbox)
        main_layout.addStretch()


        # Keep track of combos and spacing
        self.combos = [size_combo, format_combo, lang_combo]
        self.controls_spacing = controls_layout.spacing()
        QTimer.singleShot(0, self.adjust_combo_widths)

        # Layout inside keyboard_frame: controls + keyboard grid
        keyboard_layout = QVBoxLayout(self.keyboard_frame)
        keyboard_layout.setContentsMargins(20, 20, 20, 20)
        keyboard_layout.setSpacing(12)

        # Keyboard grid
        grid_layout = QGridLayout()
        grid_layout.setSpacing(12)

        # Key width multipliers for special keys
        key_spans = {
            'Tab': 1.5, 'Caps': 1.75, 'Shift': 2.25, 'Enter': 2,
            'Backspace': 2, 'Del': 1.5, 'Space': 6, 'Esc': 1.25,
        }

        # Aggiunta dei tasti al layout
        for row_idx, row_keys in enumerate(rows):
            col_idx = 0
            for key in row_keys:
                span = key_spans.get(key, 1)
                btn = QPushButton(key)
                btn.setMinimumSize(int(60 * span + (span - 1) * 12), 60)
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: rgba(255, 255, 255, 0.15);
                        border: 1px solid rgba(255, 255, 255, 0.4);
                        border-radius: 8px;
                        color: #3A76A5;
                        font-size: 20px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background-color: rgba(255, 255, 255, 0.25);
                    }
                    QPushButton:pressed {
                        background-color: rgba(255, 255, 255, 0.35);
                    }
                """)
                shadow = QGraphicsDropShadowEffect(btn)
                shadow.setBlurRadius(15)
                shadow.setOffset(0, 4)
                shadow.setColor(QColor(0, 0, 0, 80))
                btn.setGraphicsEffect(shadow)
                grid_layout.addWidget(btn, row_idx, col_idx, 1, int(span))
                col_idx += int(span)

        # Attach grid layout below controls
        keyboard_layout.addLayout(grid_layout)

        # Center glass container horizontally
        hbox = QHBoxLayout()
        hbox.addStretch()
        hbox.addWidget(self.glass_container)
        hbox.addStretch()
        main_layout.addLayout(hbox)
        main_layout.addStretch()

        # Window size and centering
        self.resize(900, 900)
        screen = QApplication.primaryScreen().availableGeometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)

    def toggleMaxRestore(self):
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()

    def adjust_combo_widths(self):
        # Make combo widths equal so that total equals keyboard width
        width = self.glass_container.width()
        total_spacing = self.controls_spacing * (len(self.combos) - 1)
        if width > total_spacing:
            cw = int((width - total_spacing) / len(self.combos))
            for combo in self.combos:
                combo.setFixedWidth(cw)
        # Keep slider width matching tab_bar width
        slider_width = self.tab_bar.width()
        self.slider.setFixedWidth(slider_width)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.adjust_combo_widths()

def main():
    app = QApplication(sys.argv)
    # Apply Material 3 light theme (choose any qt-material theme)
    apply_stylesheet(app, theme='light_cyan_500.xml')
    window = KeyboardWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()