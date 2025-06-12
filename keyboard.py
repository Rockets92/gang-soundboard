import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QFrame, QVBoxLayout, QGridLayout, QSizePolicy,
    QPushButton, QGraphicsBlurEffect, QHBoxLayout, QGraphicsDropShadowEffect, QComboBox, QToolButton, QStackedLayout
)
from PyQt6.QtGui import QColor
from PyQt6.QtCore import Qt, QTimer, QLocale
from qt_material import apply_stylesheet
import math

class KeyboardWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # Set initial window size and center before creating backing store
        self.resize(900, 400)
        screen = QApplication.primaryScreen().availableGeometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)
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
        
        # Layer 2: keyboard widget container (no blur)
        self.keyboard_frame = QWidget(self.glass_container)
        
        # Stack layers
        stack = QStackedLayout(self.glass_container)
        stack.setStackingMode(QStackedLayout.StackingMode.StackAll)
        stack.addWidget(self.background_frame)
        stack.addWidget(self.keyboard_frame)
        self.glass_container.setLayout(stack)
        # Prepare keyboard_frame layout (only once)
        self.keyboard_layout = QVBoxLayout(self.keyboard_frame)
        self.keyboard_layout.setContentsMargins(20,20,20,20)
        self.keyboard_layout.setSpacing(12)
        self.grid_layout = QGridLayout()
        self.grid_layout.setSpacing(12)
        self.keyboard_layout.addLayout(self.grid_layout)


        # Fixed keyboard settings
        self.layout_type = "60%"
        self.key_format = "ISO"
        self.lang = QLocale.system().name()


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


        QTimer.singleShot(0, self.build_keyboard)

        # Center glass container horizontally

        # Center glass container horizontally
        hbox = QHBoxLayout()
        hbox.addStretch()
        hbox.addWidget(self.glass_container)
        hbox.addStretch()
        main_layout.addLayout(hbox)
        main_layout.addStretch()


    def toggleMaxRestore(self):
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()

    def build_keyboard(self):
        # Key layout (Windows)
        rows = [
            ['Esc','1','2','3','4','5','6','7','8','9','0','-','=','Backspace'],
            ['Tab','Q','W','E','R','T','Y','U','I','O','P','[',']','\\'],
            ['Caps','A','S','D','F','G','H','J','K','L',';','\'','Enter'],
            ['Shift','Z','X','C','V','B','N','M',',','.','/','Shift'],
            ['Ctrl','Win','Alt','Space','Alt','Fn','Ctrl']
        ]
        key_spans = {
            'Tab': 1.5, 'Caps': 1.75, 'Shift': 2.25,
            'Enter': 2, 'Backspace': 2, 'Space': 6,
            'Esc': 1.25, 'Fn': 1
        }
        # Dynamic sizing: calculate key dimensions to fit the frame
        margins = 20
        spacing = 12
        rows_count = len(rows)
        max_span = max(sum(key_spans.get(k, 1) for k in row_keys) for row_keys in rows)
        # Clamp frame dimensions to the window size to avoid excessively large buffers
        max_w = self.width()
        max_h = self.height()
        frame_w = min(self.keyboard_frame.width(), max_w)
        frame_h = min(self.keyboard_frame.height(), max_h)
        avail_w = frame_w - 2 * margins
        avail_h = frame_h - 2 * margins
        if avail_w <= 0 or avail_h <= 0:
            # Fallback to default key size before layout is applied
            cell_w = 60
            cell_h = 60
        else:
            cell_w = (avail_w - (max_span - 1) * spacing) / max_span
            cell_h = (avail_h - (rows_count - 1) * spacing) / rows_count
        # Clear previous keys
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
        # Ensure uniform column width to prevent key overlap
        num_cols = math.ceil(max_span)
        for col in range(num_cols):
            self.grid_layout.setColumnMinimumWidth(col, math.ceil(cell_w))
        # Evenly distribute any extra space across all columns to prevent key overlap
        for col in range(num_cols):
            self.grid_layout.setColumnStretch(col, 1)
        # Populate grid
        for r, row_keys in enumerate(rows):
            c = 0
            for key in row_keys:
                span = key_spans.get(key,1)
                span_int = math.ceil(span)
                btn = QPushButton(key)
                btn.setFixedHeight(int(cell_h))
                btn.setMinimumWidth(int(cell_w * span_int + (span_int - 1) * spacing))
                btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
                btn.setStyleSheet('''
QPushButton {
    background-color: rgba(255, 255, 255, 0.15);
    border: 1px solid rgba(255, 255, 255, 0.4);
    border-radius: 8px;
    color: #3A76A5;
    font-size: 8px;
    font-weight: bold;
}
QPushButton:hover {
    background-color: rgba(255, 255, 255, 0.25);
}
QPushButton:pressed {
    background-color: rgba(255, 255, 255, 0.35);
}
''')
                shadow = QGraphicsDropShadowEffect(btn)
                shadow.setBlurRadius(15)
                shadow.setOffset(0,4)
                shadow.setColor(QColor(0,0,0,80))
                btn.setGraphicsEffect(shadow)
                self.grid_layout.addWidget(btn, r, c, 1, span_int)
                c += span_int

        # Adjust glass container size to fit new layout
        total_width = num_cols * math.ceil(cell_w) + (num_cols - 1) * spacing + 2 * margins
        total_height = int(cell_h * rows_count + (rows_count - 1) * spacing + 2 * margins)
        self.glass_container.setFixedSize(total_width, total_height)
        # Apply blur after sizing to avoid giant offscreen buffers
        if not hasattr(self, '_blur_initialized'):
            blur = QGraphicsBlurEffect(self.background_frame)
            blur.setBlurRadius(50)
            self.background_frame.setGraphicsEffect(blur)
            self._blur_initialized = True

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.build_keyboard()
      
    def on_tab_changed(self, index):
        # Rebuild keyboard when platform tab changes
        self.build_keyboard()

def main():
    app = QApplication(sys.argv)
    # Apply Material 3 light theme (choose any qt-material theme)
    apply_stylesheet(app, theme='light_cyan_500.xml')
    window = KeyboardWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()