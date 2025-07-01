from PyQt6.QtWidgets import *
from PyQt6.QtGui import QColor, QIcon
from PyQt6.QtCore import Qt, QSize
from widgets import *
from PIL import Image


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Qarz daftar")
        self.setMinimumSize(1000, 700)  # Set minimum size for the main window

        self.main_layout = QHBoxLayout()

        self.side_menu = QVBoxLayout()
        self.side_menu.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.menu_widget = QWidget()
        self.menu_widget.setLayout(self.side_menu)
        self.menu_widget.setStyleSheet("background-color: #F0EBE3; border: 0px; border-radius: 20px;")
        self.menu_widget.setMinimumWidth(200) # Minimum width, flexible height
        self.menu_widget.setMaximumWidth(250) # Optional: Set a maximum width for the side menu
        self.menu_widget.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)


        shadow_effect = QGraphicsDropShadowEffect()
        shadow_effect.setBlurRadius(30)
        shadow_effect.setOffset(0, 0)
        shadow_effect.setColor(QColor(128, 128, 128))

        self.menu_widget.setGraphicsEffect(shadow_effect)

        self.menu_buttonss = []
        self.menu_buttons = ['Qarz Qo\'shish', 'Qarzlarni ko\'rish', 'statistika', 'Bildirishlar']
        self.images = ['add.png', 'view.png', 'stat.png', 'report.png']
        self.image = ['addwhite.png', 'viewhite.png', 'statwhite.png', 'reportwhite.png']
        
        for inx, button_name in enumerate(self.menu_buttons):
            btn = QPushButton(button_name)
            btn.setIcon(QIcon(self.images[inx]))
            btn.setIconSize(QSize(25, 25))
            btn.clicked.connect(lambda checked, index=inx: self.switch_page(index))
            self.side_menu.addWidget(btn)
            btn.setStyleSheet("""QPushButton {
    background-color: #F0EBE3;
    border: 0px;
    border-radius: 20px;
    padding: 10px;
    color: #112D4E;
    font-size: 16px;
    font-weight: bold;
}
QPushButton:hover {
    background-color: #CCD3CA;
    border: 0;
    color: #151515;
}
""")
            self.menu_buttonss.append(btn) 
        
        self.side_menu.addStretch()

        self.content_area = QStackedWidget()
        self.content_area.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)


        self.page1 = Add_page()
        self.page2 = List_people(self.content_area)
        self.page3 = QLabel("разрабатывается")
        self.page4 = QLabel("разрабатывается")
        self.page5 = History(self.content_area)

        self.content_area.addWidget(self.page1)
        self.content_area.addWidget(self.page2)
        self.content_area.addWidget(self.page3)
        self.content_area.addWidget(self.page4)
        self.content_area.addWidget(self.page5)


        self.main_layout.addWidget(self.menu_widget)
        self.main_layout.addWidget(self.content_area, 1)
        container = QWidget()
        container.setLayout(self.main_layout)
        self.setCentralWidget(container)

    def switch_page(self, index):
        # Only update the table if switching to a different page
        if self.content_area.currentIndex() != index:
            self.content_area.setCurrentIndex(index)
            # Only update List_people table if switching to that specific page
            if index == 1:
                self.page2.update_table()
            # The History page's update_data is called when switching from List_people,
            # so no explicit call is needed here unless you want to force a refresh
            # when directly navigating to History from other non-List pages.

            for inx, btn in enumerate(self.menu_buttonss):
                btn.setStyleSheet("""QPushButton {
                    background-color: #F0EBE3;
                    border: 0px;
                    border-radius: 20px;
                    padding: 10px;
                    color: #112D4E;
                    font-size: 16px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #CCD3CA;
                    border: 0;
                    color: #151515;
                }
                """)
                btn.setIcon(QIcon(self.images[inx]))
                btn.setIconSize(QSize(25, 25))
            
            self.menu_buttonss[index].setStyleSheet("""QPushButton {
                background-color: #45474B;
                border: 0px;
                border-radius: 20px;
                padding: 10px;
                color: #F0EBE3;
                font-size: 16px;
                font-weight: bold;
            }""")
            self.menu_buttonss[index].setIcon(QIcon(self.image[index]))
            self.menu_buttonss[index].setIconSize(QSize(25, 25))

if __name__ == '__main__':
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec()