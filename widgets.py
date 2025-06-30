from PyQt6.QtWidgets import QLineEdit, QLabel, QVBoxLayout, QWidget, QDialog, QTableWidget, QHBoxLayout, QPushButton, QGraphicsDropShadowEffect, QComboBox, QTableWidgetItem, QHeaderView, QMessageBox, QFormLayout
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
        self.main_layout = QVBoxLayout()

        self.search_line = FocusShadowLineEdit()
        self.name_line = FocusShadowLineEdit()
        self.contact_line = FocusShadowLineEdit()
        self.description_line = FocusShadowLineEdit()
        self.amount_line = FormattedLineEdit()
        self.save_btn = QPushButton("Saqlash")
        self.date_line = FocusShadowLineEdit(True, self.save_btn)
        self.save_btn.clicked.connect(self.save_to_database)
        self.save_btn.clicked.connect(self.update_table)
        
        self.name_lbl = create_label("Ism kiriting:")
        self.contact_lbl = create_label("Telefon raqam kiriting (99-123-4567):")
        self.description_lbl = create_label("Izoh qoldiring:")
        self.amount_lbl = create_label("Summa kiriting:")
        self.date_lbl = create_label("payback(dd/mm/yyyy):")

        self.table = QTableWidget()
        self.table.horizontalHeader().setDefaultSectionSize(50)

        self.shadow_effect = QGraphicsDropShadowEffect()
        self.shadow_effect.setBlurRadius(30)
        self.shadow_effect.setOffset(5, 5)
        self.shadow_effect.setColor(QColor(128, 128, 128))
        
        self.search_line.setPlaceholderText("Qidiruvga ism yoki telefon raqam kiriting...")
        self.search_line.setFixedSize(405, 40)
        self.search_line.textChanged.connect(self.update_table)
        self.search_layout = QHBoxLayout()
        self.search_layout.addWidget(self.search_line)
        self.search_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.name_line.setPlaceholderText("Ism yarating...")
        self.name_line.setFixedSize(350, 40)
        name_layout = QVBoxLayout()
        name_layout.addWidget(self.name_lbl)
        name_layout.addWidget(self.name_line)
        name_layout.setSpacing(3)

        self.contact_line.setFixedSize(350, 40)
        self.contact_line.setInputMask("00-000-0000;_")

        contact_layout = QVBoxLayout()
        contact_layout.addWidget(self.contact_lbl)
        contact_layout.addWidget(self.contact_line)
        contact_layout.setSpacing(3)

        first_row = QHBoxLayout()
        first_row.addLayout(name_layout)
        first_row.addLayout(contact_layout)
        first_row.setSpacing(50)

        self.description_line.setPlaceholderText("Izoh qoldiring...")
        self.description_line.setFixedSize(750, 50)
        self.description_layout = QVBoxLayout()
        self.description_layout.addWidget(self.description_lbl)
        self.description_layout.addWidget(self.description_line)
        self.description_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.description_layout.setSpacing(5)

        self.amount_line.setPlaceholderText("Summani kiriting: ")
        self.amount_line.setFixedSize(250, 40)
        self.amount_layout = QVBoxLayout()
        self.amount_layout.addWidget(self.amount_lbl)
        self.amount_layout.addWidget(self.amount_line)
        self.amount_layout.setSpacing(3)

        self.date_line.setFixedSize(200, 40)
        self.date_line.setInputMask("00/00/0000;_")
        self.date_layout = QVBoxLayout()
        self.date_layout.addWidget(self.date_lbl)
        self.date_layout.addWidget(self.date_line)
        self.date_layout.setSpacing(3)

        self.save_btn.setFixedSize(200, 40)
        self.save_btn.setStyleSheet("font-size: 18px; border: 0px; border-radius: 12px; background: #525CEB; color: #F8EDFF")
        self.save_btn.setGraphicsEffect(self.shadow_effect)
        self.save_btn.pressed.connect(self.save_btn_press)
        self.save_btn.released.connect(self.save_btn_release)

        self.last_row = QHBoxLayout()
        self.last_row.addLayout(self.amount_layout)
        self.last_row.addLayout(self.date_layout)
        self.last_row.addWidget(self.save_btn)

        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(['Ism', 'Telefon', 'Summa', 'Copy'])
        self.table.setFixedSize(800, 360)
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

        self.table.setColumnWidth(0, 280)
        self.table.setColumnWidth(1, 170)
        self.table.setColumnWidth(2, 200)
        self.table.setColumnWidth(3, 90)
        self.update_table()

        self.main_layout.addLayout(self.search_layout)
        self.main_layout.addLayout(first_row)
        self.main_layout.addLayout(self.description_layout)
        self.main_layout.addLayout(self.last_row)
        self.main_layout.addWidget(self.table)
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.main_layout.setSpacing(10)
        self.setLayout(self.main_layout)

    def show_message(self, name, amount):
        dialog = CustomDialog(name, amount)
        result = dialog.exec()

        if result == QDialog.DialogCode.Accepted:
            selected_date = dialog.get_date()
            QMessageBox.information(None, "Date", f"Confirmed Date: {selected_date}")
            # Save the data with the confirmed or changed date
            return selected_date
        else:
            QMessageBox.information(None, "Cancelled", "The operation was cancelled.")
            return None

    def update_table(self):
        core = Database()
        if not "'" in self.search_line.text():
            self.search_line.setText(self.search_line.text())
        else:
            error = QMessageBox.information(self, 'Error', "Qidiruvga ' belgisi kiritmang❗")
            self.search_line.clear()
            return
        temp = self.search_line.text()
        data = core.find_customers(temp)
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
        core = Database()
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
        except:
            error_message = QMessageBox.information(self, "Error", "Sana noto'g'ri kiritildi ❌")
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
            # reply = QMessageBox.question(self, 'Message',
            #                  f"{name} ga {amount} so'm qo'shilsinmi?",
            #                  QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            #                  QMessageBox.StandardButton.No)

            # if reply == QMessageBox.StandardButton.Yes:
            #     core = Database()
            #     check = core.process_customer_debt(data)
            #     if check:
            #         QMessageBox.information(self, 'Message', f"{amount} so'm {name} ga qo'shildi ✅")
            #         self.amount_line.clear()
            #         self.date_line.clear()
            #     else:
            #         QMessageBox.information(self, "Message", "Xatolik yuz berdi❌")
            # else:
            #     QMessageBox.information(self, "Message", "Xatolik yuz berdi❌")
           

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
                    else:
                        QMessageBox.information(self, "Message", "Xatolik yuz berdi❌")
                except ValueError:
                    QMessageBox.information(self, "Error", "Sana noto'g'ri kiritildi ❌")
            else:
                QMessageBox.information(self, "Message", "Amal bekor qilindi")

            
class List_people(QWidget):
    def __init__(self, stacked_widget) -> None:
        super().__init__()
        self.stacked_widget = stacked_widget
        self.main_layout = QVBoxLayout()

        self.search_line = FocusShadowLineEdit()
        self.table = QTableWidget()
        self.table.horizontalHeader().setDefaultSectionSize(50)

        self.search_line.setPlaceholderText("Qidiruvga ism yoki telefon raqam kiriting...")

        self.shadow_effect = QGraphicsDropShadowEffect()
        self.shadow_effect.setBlurRadius(30)
        self.shadow_effect.setOffset(5, 5)
        self.shadow_effect.setColor(QColor(128, 128, 128))

        self.search_line.setPlaceholderText("Qidiruvga ism yoki telefon raqam kiriting...")
        self.search_line.setFixedSize(405, 40)
        self.search_line.textChanged.connect(self.update_table)
        self.search_layout = QHBoxLayout()
        self.search_layout.addWidget(self.search_line)
        self.search_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(['Ism', 'Telefon', 'Summa', "Tarix", "To'lov"])
        self.table.setFixedSize(800, 600)
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

        self.table.setColumnWidth(0, 190)
        self.table.setColumnWidth(1, 170)
        self.table.setColumnWidth(2, 200)
        self.table.setColumnWidth(3, 90)
        self.table.setColumnWidth(4, 90)
        self.update_table()

        self.main_layout.addLayout(self.search_layout)
        self.main_layout.addWidget(self.table)
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.main_layout.setSpacing(10)
        self.setLayout(self.main_layout)

    def update_table(self):
        core = Database()
        if not "'" in self.search_line.text():
            self.search_line.setText(self.search_line.text())
        else:
            QMessageBox.information(self, 'Error', "Qidiruvga ' belgisi kiritmang❗")
            self.search_line.clear()
            return
        temp = self.search_line.text()
        data = core.find_customers(temp)
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
        self.setFixedSize(400, 300)
        self.setWindowTitle("To'lov oynasi")
        self.setStyleSheet("font-size: 18px")
        self.main_layout = QVBoxLayout()
        
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
        self.comment_line.setFixedSize(380, 40)

        self.amount_lbl = QLabel("Summani kiriting: ")
        self.amount_lbl.setStyleSheet("font-size: 20px")
        self.amount_line = FormattedLineEdit()
        self.amount_line.setPlaceholderText("Summani kiriting: ")
        self.amount_line.setFixedSize(200, 40)
        self.amount_layout = QHBoxLayout()
        self.amount_layout.addWidget(self.amount_lbl)
        self.amount_layout.addWidget(self.amount_line)
        self.amount_layout.setSpacing(3)

        self.shadow_effect = QGraphicsDropShadowEffect()
        self.shadow_effect.setBlurRadius(30)
        self.shadow_effect.setOffset(5, 5)
        self.shadow_effect.setColor(QColor(128, 128, 128))

        self.save_btn = QPushButton("To'lash")
        self.save_btn.setFixedSize(200, 40)
        self.save_btn.setStyleSheet("font-size: 18px; border: 0px; border-radius: 12px; background: #525CEB; color: #F8EDFF")
        self.save_btn.setGraphicsEffect(self.shadow_effect)
        self.save_btn.pressed.connect(self.save_btn_press)
        self.save_btn.released.connect(self.save_btn_release)
        self.save_btn.clicked.connect(self.save_to_database)

        self.main_layout.addLayout(form_layout)
        self.main_layout.addStretch()
        self.main_layout.addWidget(self.comment_line)
        self.main_layout.addStretch()
        self.main_layout.addLayout(self.amount_layout)
        self.main_layout.addStretch()
        self.main_layout.addWidget(self.save_btn, 0, Qt.AlignmentFlag.AlignCenter)

        self.setLayout(self.main_layout)

    def save_to_database(self):
        amount = self.amount_line.text()
        amount = amount.replace(" ", "")
        amount = int(amount)
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

    def UI(self):
        self.back_btn = QPushButton()
        self.back_btn.clicked.connect(self.back_to_list)
        self.back_btn.setIcon(QIcon('back_btn.png'))
        self.back_btn.setIconSize(QSize(25, 25))
        self.back_btn.setFixedSize(50, 50)
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
        self.debt_table.setFixedSize(375, 450)
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
        self.debt_table.setColumnWidth(0,165)
        self.debt_table.setColumnWidth(1,210)
        self.debt_table.cellClicked.connect(self.show_overflow_text1)

        self.payed_table = QTableWidget()
        self.payed_table = QTableWidget()
        self.payed_table.horizontalHeader().setDefaultSectionSize(50)
        self.payed_table.setColumnCount(2)
        self.payed_table.setHorizontalHeaderLabels(['Summa', 'Olingan vaqt'])
        self.payed_table.setFixedSize(375, 450)
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
        self.payed_table.setColumnWidth(0,165)
        self.payed_table.setColumnWidth(1,210)
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
        self.name_lbl.setFixedHeight(70)

        self.description_lbl.setStyleSheet("font-size: 18px;; color: #333333; font-weight: bold; font-family: 'Roboto';")
        self.description_lbl.setFixedHeight(40)

        self.contact_lbl.setStyleSheet("font-size: 18px;color: #333333; font-weight: bold; font-family: 'Roboto';")
        self.contact_lbl.setFixedHeight(40)

        self.setLayout(self.main_layout)

        self.debt_lbl.setStyleSheet("font-size: 18px; color: #C7253E; font-weight: bold; font-family: 'Roboto'; background: #FEFAE0; padding-left: 3px")
        self.overall_lbl.setStyleSheet("font-size: 18px; color: #333333; font-weight: bold; font-family: 'Roboto'; background: #FEFAE0; padding-left: 3px")        
        self.payed_lbl.setStyleSheet("font-size: 18px; color: #00712D; font-weight: bold; font-family: 'Roboto'; background: #FEFAE0; padding-left: 3px")

        self.debt_lbl.setFixedSize(250, 50)
        self.overall_lbl.setFixedSize(250, 50)
        self.payed_lbl.setFixedSize(250, 50)

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
        
        self.description_layout.addWidget(self.name_lbl)
        self.description_layout.addWidget(self.description_lbl)
        self.description_layout.addWidget(self.contact_lbl)

        self.info_layout.addLayout(self.description_layout)

        self.money_layout.addWidget(self.debt_lbl)
        self.money_layout.addWidget(self.overall_lbl)
        self.money_layout.addWidget(self.payed_lbl)
        self.money_layout.setSpacing(0)

        self.table_layout.addWidget(self.debt_table)
        self.table_layout.addWidget(self.payed_table)
        self.table_layout.setSpacing(10)

        self.description_layout.setSpacing(0)
        self.main_layout.addLayout(self.info_layout)
        self.main_layout.addLayout(self.money_layout)
        self.main_layout.addLayout(self.table_layout)

    def back_to_list(self):
        history_page = List_people(self.stacked_widget)
        history_page.update_table()
        self.stacked_widget.setCurrentIndex(1)

# class Statistics(QWidget):
#     def __init__(self, stacked_widget) -> None:
#         super().__init__()
#         self.stacked_widget = stacked_widget
#         self.create_widgets()
#         self.set_parameters()
#         self.update_charts('month')
#         self.layouts()
#     def create_widgets(self):
#         self.combo_box = QComboBox()
#         self.date_line = FocusShadowLineEdit()
#         self.debts_lbl = QLabel()
#         self.total_lbl = QLabel()
#         self.payment_lbl = QLabel()
#         self.sp_piechart_lbl = QLabel()
#         self.wh_info_lbl = QLabel()
#         self.barchar_lbl = QLabel()

#     def update_charts(self, type):
#         # Example data for the pie chart
#         pie_labels = ['оплачено', 'остался']
#         pie_sizes = [60, 40]  # Replace with your actual data
#         buf_pie = create_pie_chart_image(pie_labels, pie_sizes)
#         image_pie = QImage.fromData(buf_pie.getvalue())
#         pixmap_pie = QPixmap.fromImage(image_pie)
#         self.sp_piechart_lbl.setPixmap(pixmap_pie)

#         # Example data for the bar chart
#         months = ['янв', 'фев', 'март', 'апр', 'май', 'июнь', 'июль', 'авг', 'сент', 'окт', 'ноя', 'дек']
#         data1 = np.random.randint(1, 10, size=12)
#         data2 = np.random.randint(1, 10, size=12)
#         print(data1)
#         print(data2)
#         buf_bar = create_bar_chart_image(months, data1, data2)
#         image_bar = QImage.fromData(buf_bar.getvalue())
#         pixmap_bar = QPixmap.fromImage(image_bar)
#         self.barchar_lbl.setPixmap(pixmap_bar)

#     def set_parameters(self):
#         self.combo_box.setFixedSize(375, 40)
#         shadow_effect = QGraphicsDropShadowEffect()
#         shadow_effect.setBlurRadius(10)
#         shadow_effect.setOffset(0, 0)
#         shadow_effect.setColor(QColor(128, 128, 128))
#         self.combo_box.setGraphicsEffect(shadow_effect)
#         self.combo_box.setStyleSheet("""
#             QComboBox {
#                 border: 2px solid #C0C0C0;
#                 border-radius: 10px;
#                 padding: 5px;
#                 font-size: 18px;
#                 font-family: Verdana, sans-serif;
#                 background-color: #FFFFFF;
                
#             }
#             QComboBox:focus {
#                 border: 2px solid #007BFF;
#                 background-color: #F0F8FF;
#             }
#         """)
#         temp = ['по годам', 'по месяцам', 'по неделям', 'по дням', 'за все время']
#         self.combo_box.addItems(temp)
#         self.set_mask(self.combo_box.currentText())
#         self.combo_box.currentIndexChanged.connect(lambda: self.set_mask(self.combo_box.currentText()))

#     def set_mask(self, text):

#         if text == 'по годам':
#             self.date_line.setInputMask('0000')
#         elif text == 'по месяцам':
#             self.date_line.setInputMask('00/0000;_')
#         elif text == 'по неделям':
#             self.date_line.setInputMask('00/00/0000-00/00/0000;_')
#         elif text == 'по дням':
#             self.date_line.setInputMask('00/00/0000;_')
#         elif text == 'за все время':
#             self.date_line.clear()
#         self.date_line.textChanged.connect(self.update_stat_page)

#     def update_stat_page(self):
#         core = Database()
#         data = core.get_finance_data()
#         text = self.combo_box.currentText()
#         if text == 'по годам':
#             if int(self.date_line.text().strip()) > 2023:
#                 year = int(self.date_line.text().strip())
#                 debts = [debt for debt in data['debts'] if debt[1].year == year]
#                 payments = [payment for payment in data['payments'] if payment[1].year == year]
#                 print(debts, payments)
#             else:
#                 return
#         elif text == 'по месяцам':
#             self.date_line.setInputMask('00/0000;_')
#         elif text == 'по неделям':
#             self.date_line.setInputMask('00/00/0000-00/00/0000;_')
#         elif text == 'по дням':
#             self.date_line.setInputMask('00/00/0000;_')
#         elif text == 'за все время':
#             pass

#     def layouts(self):
#         self.main_layout = QVBoxLayout()
#         self.main_layout.setSpacing(20)

#         self.setting_spec = QHBoxLayout()
#         self.number_layout = QHBoxLayout()
#         self.pie_charts = QHBoxLayout()

#         self.setting_spec.addWidget(self.combo_box)
#         self.setting_spec.addWidget(self.date_line)

#         self.number_layout.addWidget(self.debts_lbl)
#         self.number_layout.addWidget(self.total_lbl)
#         self.number_layout.addWidget(self.payment_lbl)

#         self.pie_charts.addWidget(self.sp_piechart_lbl)
#         self.pie_charts.addWidget(self.wh_info_lbl)

#         self.main_layout.addLayout(self.setting_spec)
#         self.main_layout.addLayout(self.number_layout)
#         self.main_layout.addLayout(self.pie_charts)
#         self.main_layout.addWidget(self.barchar_lbl)
#         self.setLayout(self.main_layout)



# class StatisticsPage(QWidget):
#     def __init__(self):
#         super().__init__()
#         self.initUI()

#     def initUI(self):
#         # Initialize and set up the combo box
#         self.combo_box = QComboBox()
#         self.combo_box.addItems(['по годам', 'по месяцам', 'по неделям', 'за все время'])
#         self.combo_box.currentIndexChanged.connect(self.update_charts)
        
#         # Initialize and set up the line edit with default date
#         self.line_edit = QLineEdit()
#         default_date = self.get_default_date()
#         self.line_edit.setText(default_date.strftime('%Y-%m-%d'))
#         self.line_edit.textChanged.connect(self.update_charts)
        
#         # Initialize and set up the labels
#         self.total_debts_label = QLabel("Total Debts: 0 UZS")
#         self.paid_amount_label = QLabel("Paid Amount: 0 UZS")
#         self.remaining_debts_label = QLabel("Remaining Debts: 0 UZS")
        
#         # Initialize pie chart info label
#         self.pie_info_label = QLabel("Total Debts: 0 UZS")
        
#         # Initialize Matplotlib figure and canvas
#         self.figure = plt.figure(figsize=(8, 6))
#         self.bar_chart_canvas = FigureCanvas(self.figure)
        
#         # Layout setup
#         layout = QVBoxLayout()
#         layout.addWidget(self.combo_box)
#         layout.addWidget(self.line_edit)
#         layout.addWidget(self.total_debts_label)
#         layout.addWidget(self.paid_amount_label)
#         layout.addWidget(self.remaining_debts_label)
#         layout.addWidget(self.pie_info_label)  # Add the pie info label to the layout
#         layout.addWidget(self.bar_chart_canvas)  # Add the bar chart canvas to the layout
        
#         self.setLayout(layout)
        
#         # Update charts initially
#         self.update_charts()

#     def get_default_date(self):
#         # Get the first day of the last month
#         today = datetime.now()
#         first_day_of_current_month = today.replace(day=1)
#         last_month = first_day_of_current_month - timedelta(days=1)
#         return last_month.replace(day=1)

#     def update_charts(self):
#         date_type = self.combo_box.currentText()
#         date_value = self.line_edit.text()
        
#         # Fetch and update data
#         core = Database()
#         data = core.fetch_data(date_type, date_value)
#         self.update_labels(data)
#         self.update_pie_chart(data)
#         self.update_bar_chart(data)

#     def update_labels(self, data):
#         try:
#             # Replace None with 0 to avoid TypeError
#             total_debts = sum((item.get('total_debts', 0) or 0) for item in data)
#             total_payments = sum((item.get('total_payments', 0) or 0) for item in data)

#             remaining_debts = total_debts - total_payments

#             # Update your QLabel widgets with the calculated values
#             self.total_debts_label.setText(f"Total Debts: {total_debts} UZS")
#             self.paid_amount_label.setText(f"Paid Amount: {total_payments} UZS")
#             self.remaining_debts_label.setText(f"Remaining Debts: {remaining_debts} UZS")
#         except Exception as e:
#             print(f"Error updating labels: {e}")

#     def update_pie_chart(self, data):
#         # Filter out items where 'total_debts' is None and convert to zero
#         filtered_data = [item for item in data if item.get('total_debts') is not None]

#         if not filtered_data:
#             # Handle case where no valid data is available
#             print("No valid data to display in pie chart.")
#             return

#         total_debts = sum(item.get('total_debts', 0) for item in filtered_data)

#         if total_debts == 0:
#             # Handle case where total debts are zero
#             print("Total debts are zero, cannot display pie chart.")
#             return

#         # Proceed with pie chart plotting
#         pie_labels = []
#         pie_values = []

#         for item in filtered_data:
#             # Use a default label if 'label' is not present
#             label = item.get('label', 'Unknown')
#             pie_labels.append(label)
#             pie_values.append(item.get('total_debts', 0))

#         # Create and update the pie chart
#         self.figure.clear()
#         ax = self.figure.add_subplot(121)
#         ax.clear()
#         ax.pie(pie_values, labels=pie_labels, autopct='%1.1f%%')

#         # Update the pie chart info label
#         self.pie_info_label.setText(f"Total Debts: {total_debts} UZS")

#     def update_bar_chart(self, data):
#         self.figure.clear()
#         dates = [item.get('date') for item in data if 'date' in item]
#         debts = [item.get('total_debts', 0) for item in data if 'total_debts' in item]
#         payments = [item.get('total_payments', 0) for item in data if 'total_payments' in item]

#         ax = self.figure.add_subplot(122)
#         ax.bar(dates, debts, label='Debts')
#         ax.bar(dates, payments, label='Payments', bottom=debts)
        
#         ax.set_ylabel('Amount (UZS)')
#         ax.set_title('Daily/Monthly Statistics')
#         ax.legend()

#         self.bar_chart_canvas.draw()