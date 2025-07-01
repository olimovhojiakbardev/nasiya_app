from PyQt6.QtWidgets import QLineEdit, QLabel, QVBoxLayout, QWidget, QDialog, QTableWidget, QHBoxLayout, QPushButton, QGraphicsDropShadowEffect, QComboBox, QTableWidgetItem, QHeaderView, QMessageBox, QFormLayout, QSizePolicy
from PyQt6.QtCore import Qt, QSize, QDate
from PyQt6.QtGui import QColor, QIcon, QPixmap, QImage
from datetime import datetime, timedelta
from database import *
import matplotlib.pyplot as plt
import io
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import numpy as np
import sys
import mysql.connector

class CustomDialog(QDialog):
    def __init__(self, name, amount, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Message")
        self.setMinimumSize(300, 150) # Set a minimum size for the dialog
        
        # Main layout
        layout = QVBoxLayout(self)
        
        # Message label
        message_label = QLabel(f"{name} ga {amount} so'm qo'shilsinmi?")
        layout.addWidget(message_label)
        
        # Date label and line edit with input mask
        date_label = QLabel("Date:")
        self.date_edit = QLineEdit()
        self.date_edit.setInputMask("00/00/0000")  # Set input mask for date format
        self.date_edit.setText(QDate.currentDate().toString("dd/MM/yyyy"))  # Set current date
        layout.addWidget(date_label)
        layout.addWidget(self.date_edit)
        
        # Buttons
        button_layout = QHBoxLayout()
        yes_button = QPushButton("Yes")
        no_button = QPushButton("No")
        button_layout.addWidget(yes_button)
        button_layout.addWidget(no_button)
        layout.addLayout(button_layout)
        
        # Connections
        yes_button.clicked.connect(self.accept)
        no_button.clicked.connect(self.reject)
    
    def get_date(self):
        return self.date_edit.text()

class FocusShadowLineEdit(QLineEdit):
    def __init__(self, is_last=False, button=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        shadow_effect = QGraphicsDropShadowEffect()
        shadow_effect.setBlurRadius(10)
        shadow_effect.setOffset(0, 0)
        shadow_effect.setColor(QColor(128, 128, 128))
        self.setGraphicsEffect(shadow_effect)
        self.setStyleSheet("""
            QLineEdit {
                border: 2px solid #C0C0C0;
                border-radius: 10px;
                padding: 5px;
                font-size: 18px;
                font-family: Verdana, sans-serif;
                background-color: #FFFFFF;
            }
            QLineEdit:focus {
                border: 2px solid #007BFF;
                background-color: #F0F8FF;
            }
        """)
        self.is_last = is_last
        self.button = button
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed) # Allow horizontal expansion

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            if self.is_last and self.button:
                self.button.click()
            else:
                self.focusNextChild()
        else:
            super().keyPressEvent(event)
    

class create_label(QLabel):
    def __init__(self, text):
        super().__init__(text)
        self.setStyleSheet("font-size: 14px; color: #151515; font-family: Verdana, sans-serif; padding-left: 3px")
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed) # Preferred width, fixed height


class FormattedLineEdit(QLineEdit):
    def __init__(self):
        super().__init__()
        shadow_effect = QGraphicsDropShadowEffect()
        shadow_effect.setBlurRadius(10)
        shadow_effect.setOffset(0, 0)
        shadow_effect.setColor(QColor(128, 128, 128))
        self.setGraphicsEffect(shadow_effect)
        self.setStyleSheet("""
            QLineEdit {
                border: 2px solid #C0C0C0;
                border-radius: 10px;
                padding: 5px;
                font-size: 18px;
                font-family: Verdana, sans-serif;
                background-color: #FFFFFF;
            }
            QLineEdit:focus {
                border: 2px solid #007BFF;
                background-color: #F0F8FF;
            }
        """)
        self.textChanged.connect(self.format_text)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed) # Allow horizontal expansion

    def format_text(self):
        text = self.text().replace(" ", "")
        text = text.lstrip('0')

        if not text.isdigit():
            text = ''.join(filter(str.isdigit, text))

        formatted_text = ''
        for i in range(len(text)):
            if i > 0 and (len(text) - i) % 3 == 0:
                formatted_text += ' '
            formatted_text += text[i]

        self.blockSignals(True)
        self.setText(formatted_text)
        self.blockSignals(False)  

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.focusNextChild()
        else:
            super().keyPressEvent(event)    

class Add_page(QWidget):
    def __init__(self):
        super().__init__()
        self.main_layout = QVBoxLayout(self) # Set layout directly on the widget

        self.search_line = FocusShadowLineEdit()
        self.name_line = FocusShadowLineEdit()
        self.contact_line = FocusShadowLineEdit()
        self.description_line = FocusShadowLineEdit()
        self.amount_line = FormattedLineEdit()
        self.save_btn = QPushButton("Saqlash")
        self.date_line = FocusShadowLineEdit(True, self.save_btn)
        self.save_btn.clicked.connect(self.save_to_database)
        # self.save_btn.clicked.connect(self.update_table) # Update table after saving is handled by the dialog
        
        self.name_lbl = create_label("Ism kiriting:")
        self.contact_lbl = create_label("Telefon raqam kiriting (99-123-4567):")
        self.description_lbl = create_label("Izoh qoldiring:")
        self.amount_lbl = create_label("Summa kiriting:")
        self.date_lbl = create_label("payback(dd/mm/yyyy):")

        self.table = QTableWidget()
        self.table.horizontalHeader().setDefaultSectionSize(50)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch) # Make columns stretch
        self.table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch) # Make rows stretch
        self.table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding) # Allow table to expand

        self.shadow_effect = QGraphicsDropShadowEffect()
        self.shadow_effect.setBlurRadius(30)
        self.shadow_effect.setOffset(5, 5)
        self.shadow_effect.setColor(QColor(128, 128, 128))
        
        self.search_line.setPlaceholderText("Qidiruvga ism yoki telefon raqam kiriting...")
        # self.search_line.setFixedSize(405, 40) # Removed fixed size
        self.search_line.setFixedHeight(40) # Keep fixed height for line edits
        self.search_line.textChanged.connect(self.update_table)
        self.search_layout = QHBoxLayout()
        self.search_layout.addStretch() # Center the search line
        self.search_layout.addWidget(self.search_line)
        self.search_layout.addStretch() # Center the search line

        self.name_line.setPlaceholderText("Ism yarating...")
        # self.name_line.setFixedSize(350, 40) # Removed fixed size
        self.name_line.setFixedHeight(40)
        name_layout = QVBoxLayout()
        name_layout.addWidget(self.name_lbl)
        name_layout.addWidget(self.name_line)
        name_layout.setSpacing(3)

        # self.contact_line.setFixedSize(350, 40) # Removed fixed size
        self.contact_line.setFixedHeight(40)
        self.contact_line.setInputMask("00-000-0000;_")

        contact_layout = QVBoxLayout()
        contact_layout.addWidget(self.contact_lbl)
        contact_layout.addWidget(self.contact_line)
        contact_layout.setSpacing(3)

        first_row = QHBoxLayout()
        first_row.addLayout(name_layout, 1) # Add stretch factor
        first_row.addLayout(contact_layout, 1) # Add stretch factor
        first_row.setSpacing(50)

        self.description_line.setPlaceholderText("Izoh qoldiring...")
        # self.description_line.setFixedSize(750, 50) # Removed fixed size
        self.description_line.setFixedHeight(50)
        self.description_layout = QVBoxLayout()
        self.description_layout.addWidget(self.description_lbl)
        self.description_layout.addWidget(self.description_line)
        self.description_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.description_layout.setSpacing(5)

        self.amount_line.setPlaceholderText("Summani kiriting: ")
        # self.amount_line.setFixedSize(250, 40) # Removed fixed size
        self.amount_line.setFixedHeight(40)
        self.amount_layout = QVBoxLayout()
        self.amount_layout.addWidget(self.amount_lbl)
        self.amount_layout.addWidget(self.amount_line)
        self.amount_layout.setSpacing(3)

        # self.date_line.setFixedSize(200, 40) # Removed fixed size
        self.date_line.setFixedHeight(40)
        self.date_line.setInputMask("00/00/0000;_")
        self.date_layout = QVBoxLayout()
        self.date_layout.addWidget(self.date_lbl)
        self.date_layout.addWidget(self.date_line)
        self.date_layout.setSpacing(3)

        # self.save_btn.setFixedSize(200, 40) # Removed fixed size
        self.save_btn.setMinimumSize(150, 40) # Set minimum size for button
        self.save_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.save_btn.setStyleSheet("font-size: 18px; border: 0px; border-radius: 12px; background: #525CEB; color: #F8EDFF")
        self.save_btn.setGraphicsEffect(self.shadow_effect)
        self.save_btn.pressed.connect(self.save_btn_press)
        self.save_btn.released.connect(self.save_btn_release)

        self.last_row = QHBoxLayout()
        self.last_row.addLayout(self.amount_layout, 1) # Add stretch factor
        self.last_row.addLayout(self.date_layout, 1) # Add stretch factor
        self.last_row.addWidget(self.save_btn)
        self.last_row.addStretch() # Push button to left if needed

        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(['Ism', 'Telefon', 'Summa', 'Copy'])
        # self.table.setFixedSize(800, 360) # Removed fixed size
        self.table.setStyleSheet("""
        QTableWidget {
            font-size: 16px;
            font-family: Verdana, sans-serif;
            background-color: #FFFFFF;                
        }
        QTableWidget QHeaderView::section {
                font-family: Arial, sans-serif;
                font-size: 18px;
                font-weight: bold;
                background-color: #E0E0E0;
            }
        """)

        # self.table.setColumnWidth(0, 280) # Removed fixed column widths, let stretch handle it
        # self.table.setColumnWidth(1, 170)
        # self.table.setColumnWidth(2, 200)
        # self.table.setColumnWidth(3, 90)
        self.update_table()

        self.main_layout.addLayout(self.search_layout)
        self.main_layout.addLayout(first_row)
        self.main_layout.addLayout(self.description_layout)
        self.main_layout.addLayout(self.last_row)
        self.main_layout.addWidget(self.table, 1) # Add stretch factor to table
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter) # Align content to center horizontally
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignTop) # Align content to top vertically
        self.main_layout.setSpacing(10)
        # self.setLayout(self.main_layout) # Already set in constructor

    def show_message(self, name, amount):
        dialog = CustomDialog(name, amount)
        result = dialog.exec()

        if result == QDialog.DialogCode.Accepted:
            selected_date = dialog.get_date()
            # QMessageBox.information(None, "Date", f"Confirmed Date: {selected_date}") # Removed redundant message box
            return selected_date
        else:
            # QMessageBox.information(None, "Cancelled", "The operation was cancelled.") # Removed redundant message box
            return None

    def update_table(self):
        core = Database()
        # Sanitize input to prevent SQL injection or unexpected behavior
        search_text = self.search_line.text().replace("'", "") 
        if self.search_line.text() != search_text: # If text was modified, update the line edit
            self.search_line.blockSignals(True) # Block signals to prevent re-triggering textChanged
            self.search_line.setText(search_text)
            self.search_line.blockSignals(False)

        data = core.find_customers(search_text)
        self.table.setRowCount(len(data))
        for i,val in enumerate(data):
            self.table.setRowHeight(i, 40)
            self.table.setItem(i, 0, QTableWidgetItem(val[0]))
            self.table.setItem(i, 1, QTableWidgetItem(val[1][:2] + "-" + val[1][2:5] + "-" + val[1][5:]))
            reversed_string = str(val[2])[::-1]
            spaced_string = ' '.join(reversed_string[i:i+3] for i in range(0, len(reversed_string), 3))
            formatted_string = spaced_string[::-1]
            self.table.setItem(i, 2, QTableWidgetItem(formatted_string))
            
            copy_button = QPushButton("Copy")
            copy_button.setStyleSheet("font-size: 14px; background-color: #525CEB; color: #F8EDFF; border-radius: 5px;")
            copy_button.clicked.connect(lambda checked, row=i: self.copy_row_data(row))
            self.table.setCellWidget(i, 3, copy_button)

    def save_btn_press(self):
        self.shadow_effect.setOffset(2, 2)
    
    def save_btn_release(self):
        self.shadow_effect.setOffset(5, 5)

    def copy_row_data(self, row):
        data = []
        # core = Database() # Not needed here
        self.amount_line.clear()
        self.date_line.clear()
        for col in range(3):
            item = self.table.item(row, col)
            if item:
                data.append(item.text())
            
        self.name_line.setText(data[0])            
        self.contact_line.setText(data[1])            
                
    def save_to_database(self):
        name = self.name_line.text()
        contact = self.contact_line.text()
        contact = contact.replace("-", "")
        description = self.description_line.text()
        temp1 = self.amount_line.text()
        temp1 = temp1.replace(" ", "")
        amount = temp1
        try:
            temp = self.date_line.text()
            date_obj = datetime.strptime(temp, "%d/%m/%Y")
            promised_date = date_obj.strftime("%Y-%m-%d")
        except ValueError: # Catch specific ValueError for datetime parsing
            QMessageBox.information(self, "Error", "Sana noto'g'ri kiritildi ❌")
            self.date_line.clear()
            return
        current_datetime = datetime.now()
        issued_date = current_datetime.strftime("%Y-%m-%d %H:%M:%S")
        if name and contact and amount and temp and promised_date and issued_date:
            data = {
                'name' : name,
                'contact' : contact,
                'description' : description,
                'amount' : amount,
                'promised_date' : promised_date,
                'issued_date' : issued_date
            }
            selected_date = self.show_message(name, amount)
           
            if selected_date:
                try:
                    # Convert the selected date into a datetime object
                    date_part = datetime.strptime(selected_date, "%d/%m/%Y")

                    # Get the current time
                    current_time = datetime.now()

                    # Combine the selected date with the current time
                    final_datetime = datetime.combine(date_part.date(), current_time.time())

                    # Convert to MySQL datetime format (e.g., 'YYYY-MM-DD HH:MM:SS')
                    formatted_date = final_datetime.strftime("%Y-%m-%d %H:%M:%S")
                    # Add the formatted date to the data dictionary
                    data["issued_date"] = formatted_date

                    core = Database()
                    check = core.process_customer_debt(data)
                    if check:
                        QMessageBox.information(self, 'Message', f"{amount} so'm {name} ga qo'shildi ✅")
                        self.amount_line.clear()
                        self.date_line.clear()
                        self.update_table() # Update table after successful save
                    else:
                        QMessageBox.information(self, "Message", "Xatolik yuz berdi❌")
                except ValueError:
                    QMessageBox.information(self, "Error", "Sana noto'g'ri kiritildi ❌")
            else:
                QMessageBox.information(self, "Message", "Amal bekor qilindi")
        else:
            QMessageBox.information(self, "Error", "Iltimos, barcha maydonlarni to'ldiring. ❌") # Added a message for incomplete fields

            
class List_people(QWidget):
    def __init__(self, stacked_widget) -> None:
        super().__init__()
        self.stacked_widget = stacked_widget
        self.main_layout = QVBoxLayout(self) # Set layout directly on the widget

        self.search_line = FocusShadowLineEdit()
        self.table = QTableWidget()
        self.table.horizontalHeader().setDefaultSectionSize(50)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch) # Make columns stretch
        self.table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch) # Make rows stretch
        self.table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding) # Allow table to expand


        self.shadow_effect = QGraphicsDropShadowEffect()
        self.shadow_effect.setBlurRadius(30)
        self.shadow_effect.setOffset(5, 5)
        self.shadow_effect.setColor(QColor(128, 128, 128))

        self.search_line.setPlaceholderText("Qidiruvga ism yoki telefon raqam kiriting...")
        # self.search_line.setFixedSize(405, 40) # Removed fixed size
        self.search_line.setFixedHeight(40)
        self.search_line.textChanged.connect(self.update_table)
        self.search_layout = QHBoxLayout()
        self.search_layout.addStretch()
        self.search_layout.addWidget(self.search_line)
        self.search_layout.addStretch()

        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(['Ism', 'Telefon', 'Summa', "Tarix", "To'lov"])
        # self.table.setFixedSize(800, 600) # Removed fixed size
        self.table.setStyleSheet("""
        QTableWidget {
            font-size: 16px;
            font-family: Verdana, sans-serif;
            background-color: #FFFFFF;                
        }
        QTableWidget QHeaderView::section {
                font-family: Arial, sans-serif;
                font-size: 18px;
                font-weight: bold;
                background-color: #E0E0E0;
            }
        """)

        # self.table.setColumnWidth(0, 190) # Removed fixed column widths
        # self.table.setColumnWidth(1, 170)
        # self.table.setColumnWidth(2, 200)
        # self.table.setColumnWidth(3, 90)
        # self.table.setColumnWidth(4, 90)
        self.update_table()

        self.main_layout.addLayout(self.search_layout)
        self.main_layout.addWidget(self.table, 1) # Add stretch factor to table
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.main_layout.setSpacing(10)
        # self.setLayout(self.main_layout) # Already set in constructor

    def update_table(self):
        core = Database()
        # Sanitize input to prevent SQL injection or unexpected behavior
        search_text = self.search_line.text().replace("'", "")
        if self.search_line.text() != search_text:
            self.search_line.blockSignals(True)
            self.search_line.setText(search_text)
            self.search_line.blockSignals(False)

        data = core.find_customers(search_text)
        self.table.setRowCount(len(data))
        for i,val in enumerate(data):
            self.table.setRowHeight(i, 40)
            self.table.setItem(i, 0, QTableWidgetItem(val[0]))
            self.table.setItem(i, 1, QTableWidgetItem(val[1][:2] + "-" + val[1][2:5] + "-" + val[1][5:]))
            reversed_string = str(val[2])[::-1]
            spaced_string = ' '.join(reversed_string[i:i+3] for i in range(0, len(reversed_string), 3))
            formatted_string = spaced_string[::-1]
            self.table.setItem(i, 2, QTableWidgetItem(formatted_string))
            
            history_button = QPushButton("Tarix")
            pay_button = QPushButton("To'lov")
            history_button.setStyleSheet("font-size: 14px; background-color: #525CEB; color: #F8EDFF; border-radius: 5px;")
            pay_button.setStyleSheet("font-size: 14px; background-color: #525CEB; color: #F8EDFF; border-radius: 5px;")
            history_button.clicked.connect(lambda checked, x=val[3]: self.switch_page(x))
            pay_button.clicked.connect(lambda checked, x=val[3]: self.open_payment_page(x))
            self.table.setCellWidget(i, 3, history_button)
            self.table.setCellWidget(i, 4, pay_button)

    def switch_page(self, customer_id):
        history_widget = self.stacked_widget.widget(4)
        history_widget.update_data(customer_id)
        self.stacked_widget.setCurrentIndex(4)

    def open_payment_page(self, customer_id):
        self.payment_window = payment(self, customer_id)
        self.payment_window.show()
    
    def on_second_window_closed(self):
        self.update_table()


class payment(QWidget):
    def __init__(self, main_window, customer_id) -> None:
        super().__init__()
        self.main_window = main_window
        self.customer_id = customer_id
        # self.setFixedSize(400, 300) # Removed fixed size
        self.setMinimumSize(400, 300) # Set minimum size for payment window
        self.setWindowTitle("To'lov oynasi")
        self.setStyleSheet("font-size: 18px")
        self.main_layout = QVBoxLayout(self) # Set layout directly on the widget
        
        core = Database()
        data = core.find_customer(self.customer_id)
        self.name_lbl = QLabel(f"{data[0]}")
        temp = data[1][:2] + "-" + data[1][2:5] + "-" + data[1][5:]
        self.number_lbl = QLabel(temp)

        form_layout = QFormLayout()
        form_layout.addRow(QLabel("Ism: "), self.name_lbl)
        form_layout.addRow(QLabel("Telefon: "), self.number_lbl)

        self.comment_line = FocusShadowLineEdit()
        self.comment_line.setPlaceholderText("Izoh qoldiring...")
        # self.comment_line.setFixedSize(380, 40) # Removed fixed size
        self.comment_line.setFixedHeight(40)

        self.amount_lbl = QLabel("Summani kiriting: ")
        self.amount_lbl.setStyleSheet("font-size: 20px")
        self.amount_line = FormattedLineEdit()
        self.amount_line.setPlaceholderText("Summani kiriting: ")
        # self.amount_line.setFixedSize(200, 40) # Removed fixed size
        self.amount_line.setFixedHeight(40)
        self.amount_layout = QHBoxLayout()
        self.amount_layout.addWidget(self.amount_lbl)
        self.amount_layout.addWidget(self.amount_line, 1) # Add stretch factor
        self.amount_layout.setSpacing(3)

        self.shadow_effect = QGraphicsDropShadowEffect()
        self.shadow_effect.setBlurRadius(30)
        self.shadow_effect.setOffset(5, 5)
        self.shadow_effect.setColor(QColor(128, 128, 128))

        self.save_btn = QPushButton("To'lash")
        # self.save_btn.setFixedSize(200, 40) # Removed fixed size
        self.save_btn.setMinimumSize(150, 40)
        self.save_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.save_btn.setStyleSheet("font-size: 18px; border: 0px; border-radius: 12px; background: #525CEB; color: #F8EDFF")
        self.save_btn.setGraphicsEffect(self.shadow_effect)
        self.save_btn.pressed.connect(self.save_btn_press)
        self.save_btn.released.connect(self.save_btn_release)
        self.save_btn.clicked.connect(self.save_to_database)

        self.main_layout.addLayout(form_layout)
        self.main_layout.addStretch(1) # Add stretch
        self.main_layout.addWidget(self.comment_line)
        self.main_layout.addStretch(1) # Add stretch
        self.main_layout.addLayout(self.amount_layout)
        self.main_layout.addStretch(1) # Add stretch
        self.main_layout.addWidget(self.save_btn, 0, Qt.AlignmentFlag.AlignCenter)

        # self.setLayout(self.main_layout) # Already set in constructor

    def save_to_database(self):
        amount = self.amount_line.text()
        amount = amount.replace(" ", "")
        try:
            amount = int(amount)
        except ValueError:
            QMessageBox.information(self, "Error", "Summa noto'g'ri kiritildi ❌")
            return

        comment = self.comment_line.text()
        if not comment:
            comment = "Izoh qoldirilmagan"
        core = Database()
        reply = QMessageBox.question(self, 'Message',
                             f"{amount} so'm to'lov qilinsinmi?",
                             QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                             QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            check = core.payback(self.customer_id, amount, comment)
            if check:
                QMessageBox.information(self, "Message", f"{amount} so'm to'lov qilindi ✅")
                self.close()
            else:
                QMessageBox.information(self, "Message", "Xatolik yuz berdi❌")
        else:
            QMessageBox.information(self, "Message", "Xatolik yuz berdi❌")
        
    def closeEvent(self, event):
        self.main_window.on_second_window_closed()
        event.accept()

    def save_btn_press(self):
        self.shadow_effect.setOffset(2, 2)
    
    def save_btn_release(self):
        self.shadow_effect.setOffset(5, 5)

class History(QWidget):
    def __init__(self, stacked_widget) -> None:
        super().__init__()
        self.stacked_widget = stacked_widget
        self.customer_id = None

        self.UI()
        self.layouts()

        self.setLayout(self.main_layout) # Set layout here

    def UI(self):
        self.back_btn = QPushButton()
        self.back_btn.clicked.connect(self.back_to_list)
        self.back_btn.setIcon(QIcon('back_btn.png'))
        self.back_btn.setIconSize(QSize(25, 25))
        # self.back_btn.setFixedSize(50, 50) # Removed fixed size
        self.back_btn.setMinimumSize(50, 50)
        self.back_btn.setMaximumSize(50, 50) # Keep button square
        self.back_btn.setStyleSheet("""
            QPushButton {
                border: 0px; 
                background: transparent; 
                border-radius: 25px;
            }
            QPushButton:hover {
                background: #FFE3CA;
            }
        """)

        self.name_lbl = QLabel()
        self.description_lbl = QLabel()
        self.contact_lbl = QLabel()
        self.debt_lbl = QLabel()
        self.overall_lbl = QLabel()
        self.payed_lbl = QLabel()
        self.tooltip_label = QLabel(self)
        self.tooltip_label.setStyleSheet("background-color: yellow; border: 1px solid black; padding: 5px;")
        self.tooltip_label.setVisible(False)

        self.debt_table = QTableWidget()
        self.debt_table.horizontalHeader().setDefaultSectionSize(50)
        self.debt_table.setColumnCount(2)
        self.debt_table.setHorizontalHeaderLabels(['Summa', 'Olingan vaqt'])
        # self.debt_table.setFixedSize(375, 450) # Removed fixed size
        self.debt_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.debt_table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.debt_table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.debt_table.setStyleSheet("""
        QTableWidget {
            font-size: 16px;
            font-family: Verdana, sans-serif;
            background-color: #FFFFFF;                
        }
        QTableWidget QHeaderView::section {
                font-family: Arial, sans-serif;
                font-size: 18px;
                font-weight: bold;
                background-color: #E0E0E0;
                color: #C7253E
            }
        """)
        # self.debt_table.setColumnWidth(0,165) # Removed fixed column widths
        # self.debt_table.setColumnWidth(1,210)
        self.debt_table.cellClicked.connect(self.show_overflow_text1)

        self.payed_table = QTableWidget()
        self.payed_table.horizontalHeader().setDefaultSectionSize(50)
        self.payed_table.setColumnCount(2)
        self.payed_table.setHorizontalHeaderLabels(['Summa', 'Olingan vaqt'])
        # self.payed_table.setFixedSize(375, 450) # Removed fixed size
        self.payed_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.payed_table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.payed_table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.payed_table.setStyleSheet("""
        QTableWidget {
            font-size: 16px;
            font-family: Verdana, sans-serif;
            background-color: #FFFFFF;                
        }
        QTableWidget QHeaderView::section {
                font-family: Arial, sans-serif;
                font-size: 18px;
                font-weight: bold;
                background-color: #E0E0E0;
                color: #00712D
            }
        """)
        # self.payed_table.setColumnWidth(0,165) # Removed fixed column widths
        # self.payed_table.setColumnWidth(1,210)
        self.payed_table.cellClicked.connect(self.show_overflow_text2)

        self.main_layout = QVBoxLayout()
        self.info_layout = QHBoxLayout()
        self.description_layout = QVBoxLayout()
        self.money_layout = QHBoxLayout()
        self.table_layout = QHBoxLayout()

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(8)
        shadow.setXOffset(1)
        shadow.setYOffset(1)
        shadow.setColor(QColor(128, 128, 128))

        self.name_lbl.setStyleSheet("font-size: 25px; color: #333333; font-weight: bold; font-family: 'Roboto';")
        # self.name_lbl.setFixedHeight(70) # Removed fixed height
        self.name_lbl.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.MinimumExpanding)


        self.description_lbl.setStyleSheet("font-size: 18px;; color: #333333; font-weight: bold; font-family: 'Roboto';")
        # self.description_lbl.setFixedHeight(40) # Removed fixed height
        self.description_lbl.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.MinimumExpanding)


        self.contact_lbl.setStyleSheet("font-size: 18px;color: #333333; font-weight: bold; font-family: 'Roboto';")
        # self.contact_lbl.setFixedHeight(40) # Removed fixed height
        self.contact_lbl.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.MinimumExpanding)


        self.debt_lbl.setStyleSheet("font-size: 18px; color: #C7253E; font-weight: bold; font-family: 'Roboto'; background: #FEFAE0; padding-left: 3px")
        self.overall_lbl.setStyleSheet("font-size: 18px; color: #333333; font-weight: bold; font-family: 'Roboto'; background: #FEFAE0; padding-left: 3px")        
        self.payed_lbl.setStyleSheet("font-size: 18px; color: #00712D; font-weight: bold; font-family: 'Roboto'; background: #FEFAE0; padding-left: 3px")

        # self.debt_lbl.setFixedSize(250, 50) # Removed fixed size
        # self.overall_lbl.setFixedSize(250, 50) # Removed fixed size
        # self.payed_lbl.setFixedSize(250, 50) # Removed fixed size
        self.debt_lbl.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.overall_lbl.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.payed_lbl.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.debt_lbl.setFixedHeight(50)
        self.overall_lbl.setFixedHeight(50)
        self.payed_lbl.setFixedHeight(50)


    def show_overflow_text1(self, row, column):
        core = Database()
        item1 = self.debt_table.item(row, 0)
        item1 = item1.text().replace(" ", "")
        item2 = self.debt_table.item(row, 1)
        date_object = datetime.strptime(item2.text(), '%d/%m/%Y %H:%M:%S')
        comment = core.get_comment1(item1, date_object)

        if not comment:
            return
        
        self.description_lbl.setText(comment[0])

    def show_overflow_text2(self, row, column):
        core = Database()
        item1 = self.payed_table.item(row, 0)
        item1 = item1.text().replace(" ", "")
        item2 = self.payed_table.item(row, 1)
        date_object = datetime.strptime(item2.text(), '%d/%m/%Y %H:%M:%S')
        comment = core.get_comment2(item1, date_object)

        if not comment:
            return
        
        self.description_lbl.setText(comment[0])
        

    def update_data(self, customer_id):
        self.customer_id = customer_id
        core = Database()
        information = core.history(self.customer_id)
        
        self.name_lbl.setText(information['person']['name'])
        contact = information['person']['contact'][:2] + "-" + information['person']['contact'][2:5] + "-" + information['person']['contact'][5:]
        self.contact_lbl.setText(contact)

        reversed_string = str(information['person']['remained'])[::-1]
        spaced_string = ' '.join(reversed_string[i:i+3] for i in range(0, len(reversed_string), 3))
        formatted_debt = spaced_string[::-1]

        reversed_string = str(information['person']['total'])[::-1]
        spaced_string = ' '.join(reversed_string[i:i+3] for i in range(0, len(reversed_string), 3))
        formatted_total = spaced_string[::-1]

        reversed_string = str(information['person']['payed'])[::-1]
        spaced_string = ' '.join(reversed_string[i:i+3] for i in range(0, len(reversed_string), 3))
        formatted_payed = spaced_string[::-1]

        self.debt_lbl.setText(formatted_debt)
        self.overall_lbl.setText(formatted_total)
        self.payed_lbl.setText(formatted_payed)

        self.debt_table.setRowCount(len(information['debts']))
        self.payed_table.setRowCount(len(information['payments']))

        for i, val in enumerate(information['debts']):
            self.debt_table.setRowHeight(i, 40)
            reversed_string = str(val[0])[::-1]
            spaced_string = ' '.join(reversed_string[i:i+3] for i in range(0, len(reversed_string), 3))
            formatted_string = spaced_string[::-1]
            self.debt_table.setItem(i, 0, QTableWidgetItem(formatted_string))
            datetime_obj = val[1]
            formatted_date = datetime_obj.strftime('%d/%m/%Y %H:%M:%S')
            self.debt_table.setItem(i, 1, QTableWidgetItem(formatted_date))

        for i, val in enumerate(information['payments']):
            self.payed_table.setRowHeight(i, 40)
            reversed_string = str(val[0])[::-1]
            spaced_string = ' '.join(reversed_string[i:i+3] for i in range(0, len(reversed_string), 3))
            formatted_string = spaced_string[::-1]
            self.payed_table.setItem(i, 0, QTableWidgetItem(formatted_string))
            datetime_obj = val[1]
            formatted_date = datetime_obj.strftime('%d/%m/%Y %H:%M:%S')
            self.payed_table.setItem(i, 1, QTableWidgetItem(formatted_date))

    def layouts(self):
        self.info_layout.addWidget(self.back_btn)
        self.info_layout.addStretch(1) # Add stretch to push back button to left
        
        self.description_layout.addWidget(self.name_lbl)
        self.description_layout.addWidget(self.description_lbl)
        self.description_layout.addWidget(self.contact_lbl)
        self.description_layout.addStretch(1) # Add stretch to push labels to top


        self.info_layout.addLayout(self.description_layout, 1) # Add stretch factor

        self.money_layout.addWidget(self.debt_lbl)
        self.money_layout.addWidget(self.overall_lbl)
        self.money_layout.addWidget(self.payed_lbl)
        self.money_layout.setSpacing(0)
        self.money_layout.addStretch(1) # Add stretch to fill remaining space


        self.table_layout.addWidget(self.debt_table, 1) # Add stretch factor
        self.table_layout.addWidget(self.payed_table, 1) # Add stretch factor
        self.table_layout.setSpacing(10)

        self.description_layout.setSpacing(0)
        self.main_layout.addLayout(self.info_layout)
        self.main_layout.addLayout(self.money_layout)
        self.main_layout.addLayout(self.table_layout, 1) # Add stretch factor to table layout
        self.main_layout.addStretch(1) # Add stretch to push content to top


    def back_to_list(self):
        # No need to create a new List_people instance, just update the existing one
        list_people_widget = self.stacked_widget.widget(1)
        list_people_widget.update_table()
        self.stacked_widget.setCurrentIndex(1)