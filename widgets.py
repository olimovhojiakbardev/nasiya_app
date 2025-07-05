from PyQt6.QtWidgets import (QLineEdit, QLabel, QVBoxLayout, QWidget, QDialog,
                             QTableWidget, QHBoxLayout, QPushButton, QGraphicsDropShadowEffect,
                             QTableWidgetItem, QHeaderView, QMessageBox,
                             QFormLayout, QSizePolicy, QMenu, QDateEdit, QStyle)
from PyQt6.QtCore import Qt, QSize, QDate, QTimer
from PyQt6.QtGui import QColor, QIcon
from datetime import datetime
import os
import subprocess
import sys
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.styles import ParagraphStyle

# Helper function for formatting numbers with spaces
def format_number(num):
    """Formats a number into a string with spaces as thousands separators."""
    try:
        return f"{int(num):,}".replace(",", " ")
    except (ValueError, TypeError):
        return "0"

class EditContactDialog(QDialog):
    """A dialog for editing a customer's contact number."""
    def __init__(self, current_contact, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Raqamni o'zgartirish")
        self.setMinimumSize(350, 150)

        layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        self.contact_line = QLineEdit()
        self.contact_line.setInputMask("00-000-0000;_")
        self.contact_line.setText(current_contact)
        form_layout.addRow("Yangi raqam:", self.contact_line)

        layout.addLayout(form_layout)

        button_layout = QHBoxLayout()
        self.ok_button = QPushButton("Saqlash")
        self.cancel_button = QPushButton("Bekor qilish")
        button_layout.addStretch()
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)

        self.ok_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)

    def get_contact(self):
        """Returns the new contact number without formatting."""
        return self.contact_line.text().replace("-", "")

class EditDeleteDialog(QDialog):
    """A dialog for editing or deleting a debt or payment entry."""
    def __init__(self, db, entry_id, entry_type, current_amount, current_comment, current_date_str=None, parent=None):
        super().__init__(parent)
        self.db = db
        self.entry_id = entry_id
        self.entry_type = entry_type
        self.setWindowTitle(f"Tahrirlash: {entry_type.capitalize()}")
        self.setMinimumSize(400, 250)
        self.is_deleted = False

        self.main_layout = QVBoxLayout(self)
        self.form_layout = QFormLayout()

        self.amount_line = FormattedLineEdit()
        self.amount_line.setText(str(current_amount))
        self.form_layout.addRow("Summa:", self.amount_line)

        self.comment_line = FocusShadowLineEdit()
        self.comment_line.setText(current_comment)
        self.form_layout.addRow("Izoh:", self.comment_line)

        self.date_edit = None
        if self.entry_type == 'debt':
            self.date_edit = QDateEdit()
            self.date_edit.setCalendarPopup(True)
            self.date_edit.setDisplayFormat("dd/MM/yyyy")
            if current_date_str:
                try:
                    date_obj = datetime.strptime(current_date_str, '%Y-%m-%d').date()
                    self.date_edit.setDate(QDate(date_obj))
                except (ValueError, TypeError):
                    self.date_edit.setDate(QDate.currentDate())
            else:
                self.date_edit.setDate(QDate.currentDate())
            self.form_layout.addRow("Vada qilingan sana:", self.date_edit)

        self.main_layout.addLayout(self.form_layout)
        button_layout = QHBoxLayout()
        self.save_btn = QPushButton("Saqlash")
        self.delete_btn = QPushButton("O'chirish")
        self.cancel_btn = QPushButton("Bekor qilish")
        self.save_btn.setStyleSheet("font-size: 16px; background-color: #4CAF50; color: white; border-radius: 5px; padding: 8px;")
        self.delete_btn.setStyleSheet("font-size: 16px; background-color: #F44336; color: white; border-radius: 5px; padding: 8px;")
        self.cancel_btn.setStyleSheet("font-size: 16px; background-color: #607D8B; color: white; border-radius: 5px; padding: 8px;")
        button_layout.addWidget(self.save_btn)
        button_layout.addWidget(self.delete_btn)
        button_layout.addWidget(self.cancel_btn)
        self.main_layout.addLayout(button_layout)

        self.save_btn.clicked.connect(self.accept_edit)
        self.delete_btn.clicked.connect(self.perform_delete)
        self.cancel_btn.clicked.connect(self.reject)

    def accept_edit(self):
        """Validates input and calls the database to update the entry."""
        new_amount_str = self.amount_line.text().replace(" ", "")
        try:
            new_amount = int(new_amount_str)
        except ValueError:
            QMessageBox.warning(self, "Xato", "Iltimos, to'g'ri summa kiriting.")
            return

        new_comment = self.comment_line.text().strip() or "Izoh qoldirilmagan"
        
        success = False
        if self.entry_type == 'debt':
            new_promised_date = self.date_edit.date().toString("yyyy-MM-dd")
            success = self.db.update_debt_entry(self.entry_id, new_amount, new_comment, new_promised_date)
        elif self.entry_type == 'payment':
            success = self.db.update_payment_entry(self.entry_id, new_amount, new_comment)

        if success:
            QMessageBox.information(self, "Muvaffaqiyatli", f"{self.entry_type.capitalize()} muvaffaqiyatli yangilandi.")
            self.accept()
        else:
            QMessageBox.critical(self, "Xato", f"{self.entry_type.capitalize()} yangilashda xato yuz berdi.")
    
    def perform_delete(self):
        """Confirms with the user and calls the database to delete the entry."""
        reply = QMessageBox.question(self, 'O\'chirishni tasdiqlash',
                                     f"Haqiqatan ham ushbu {self.entry_type} yozuvini o'chirmoqchimisiz?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            success = False
            if self.entry_type == 'debt':
                success = self.db.delete_debt_entry(self.entry_id)
            elif self.entry_type == 'payment':
                success = self.db.delete_payment_entry(self.entry_id)

            if success:
                QMessageBox.information(self, "Muvaffaqiyatli", f"{self.entry_type.capitalize()} muvaffaqiyatli o'chirildi.")
                self.is_deleted = True
                self.accept()
            else:
                QMessageBox.critical(self, "Xato", f"{self.entry_type.capitalize()} o'chirishda xato yuz berdi.")
        else:
            QMessageBox.information(self, "Bekor qilindi", "O'chirish amali bekor qilindi.")

class CustomDialog(QDialog):
    """A custom dialog to confirm an action and get a date."""
    def __init__(self, name, amount, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Tasdiqlash")
        self.setMinimumSize(300, 150)
        
        layout = QVBoxLayout(self)
        message_label = QLabel(f"{name} ga {amount} so'm qo'shilsinmi?")
        layout.addWidget(message_label)
        
        date_label = QLabel("Sana:")
        self.date_edit = QLineEdit()
        self.date_edit.setInputMask("00/00/0000")
        self.date_edit.setText(QDate.currentDate().toString("dd/MM/yyyy"))
        layout.addWidget(date_label)
        layout.addWidget(self.date_edit)
        
        button_layout = QHBoxLayout()
        yes_button = QPushButton("Ha")
        no_button = QPushButton("Yo'q")
        button_layout.addWidget(yes_button)
        button_layout.addWidget(no_button)
        layout.addLayout(button_layout)
        
        yes_button.clicked.connect(self.accept)
        no_button.clicked.connect(self.reject)
    
    def get_date(self):
        return self.date_edit.text()

class FocusShadowLineEdit(QLineEdit):
    """A custom QLineEdit with a shadow effect that changes on focus."""
    def __init__(self, is_last=False, button=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        shadow_effect = QGraphicsDropShadowEffect(self)
        shadow_effect.setBlurRadius(10)
        shadow_effect.setOffset(0, 0)
        shadow_effect.setColor(QColor(128, 128, 128))
        self.setGraphicsEffect(shadow_effect)
        self.setStyleSheet("""
            QLineEdit {
                border: 2px solid #C0C0C0; border-radius: 10px; padding: 5px;
                font-size: 18px; font-family: Verdana, sans-serif; background-color: #FFFFFF;
            }
            QLineEdit:focus { border: 2px solid #007BFF; background-color: #F0F8FF; }
        """)
        self.is_last = is_last
        self.button = button
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def keyPressEvent(self, event):
        """Focuses next child on Enter/Return key press."""
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            if self.is_last and self.button: self.button.click()
            else: self.focusNextChild()
        else: super().keyPressEvent(event)
    
class create_label(QLabel):
    """A helper class for creating styled labels."""
    def __init__(self, text):
        super().__init__(text)
        self.setStyleSheet("font-size: 14px; color: #151515; font-family: Verdana, sans-serif; padding-left: 3px")
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)

class FormattedLineEdit(QLineEdit):
    """A QLineEdit that automatically formats numbers with thousands separators."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        shadow_effect = QGraphicsDropShadowEffect(self)
        shadow_effect.setBlurRadius(10)
        shadow_effect.setOffset(0, 0)
        shadow_effect.setColor(QColor(128, 128, 128))
        self.setGraphicsEffect(shadow_effect)
        self.setStyleSheet("""
            QLineEdit {
                border: 2px solid #C0C0C0; border-radius: 10px; padding: 5px;
                font-size: 18px; font-family: Verdana, sans-serif; background-color: #FFFFFF;
            }
            QLineEdit:focus { border: 2px solid #007BFF; background-color: #F0F8FF; }
        """)
        self.textChanged.connect(self._format_text)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def _format_text(self, text):
        """Slot connected to textChanged signal for formatting."""
        text_no_spaces = text.replace(" ", "")
        if not text_no_spaces.isdigit():
            text_no_spaces = ''.join(filter(str.isdigit, text_no_spaces))
        
        formatted_text = format_number(text_no_spaces) if text_no_spaces else ""
        
        self.blockSignals(True)
        self.setText(formatted_text)
        self.blockSignals(False)
        self.setCursorPosition(len(self.text()))

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.focusNextChild()
        else:
            super().keyPressEvent(event)

class Add_page(QWidget):
    """The main page for adding new debts."""
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.main_layout = QVBoxLayout(self)
        self.setup_ui()
        self.update_table()

    def setup_ui(self):
        """Initializes and arranges all UI elements for this page."""
        # Create Widgets
        self.search_line = FocusShadowLineEdit(placeholderText="Qidiruvga ism yoki telefon raqam kiriting...")
        self.name_line = FocusShadowLineEdit(placeholderText="Ism yarating...")
        self.contact_line = FocusShadowLineEdit()
        self.description_line = FocusShadowLineEdit(placeholderText="Izoh qoldiring...")
        self.amount_line = FormattedLineEdit(placeholderText="Summani kiriting...")
        self.save_btn = QPushButton("Saqlash")
        self.date_line = FocusShadowLineEdit(True, self.save_btn)
        
        # Configure Widgets
        self.contact_line.setInputMask("00-000-0000;_")
        self.date_line.setInputMask("00/00/0000;_")
        self.save_btn.setStyleSheet("font-size: 18px; border: 0px; border-radius: 12px; background: #525CEB; color: #F8EDFF")
        self.save_btn.setMinimumSize(150, 40)
        
        # Table Widget
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(['Ism', 'Telefon', 'Qoldiq qarz', 'Nusxalash'])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
        self.table.verticalHeader().setDefaultSectionSize(40)
        self.table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
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

        # Layouts
        search_layout = QHBoxLayout()
        search_layout.addStretch()
        search_layout.addWidget(self.search_line)
        search_layout.addStretch()

        name_layout = QVBoxLayout()
        name_layout.addWidget(create_label("Ism kiriting:"))
        name_layout.addWidget(self.name_line)
        
        contact_layout = QVBoxLayout()
        contact_layout.addWidget(create_label("Telefon raqam kiriting (99-123-4567):"))
        contact_layout.addWidget(self.contact_line)

        first_row = QHBoxLayout()
        first_row.addLayout(name_layout, 1)
        first_row.addLayout(contact_layout, 1)
        
        description_layout = QVBoxLayout()
        description_layout.addWidget(create_label("Izoh qoldiring:"))
        description_layout.addWidget(self.description_line)

        amount_layout = QVBoxLayout()
        amount_layout.addWidget(create_label("Summa kiriting:"))
        amount_layout.addWidget(self.amount_line)

        date_layout = QVBoxLayout()
        date_layout.addWidget(create_label("Qaytarish sanasi (dd/mm/yyyy):"))
        date_layout.addWidget(self.date_line)
        
        last_row = QHBoxLayout()
        last_row.addLayout(amount_layout, 1)
        last_row.addLayout(date_layout, 1)
        last_row.addWidget(self.save_btn)

        # Add to Main Layout
        self.main_layout.addLayout(search_layout)
        self.main_layout.addLayout(first_row)
        self.main_layout.addLayout(description_layout)
        self.main_layout.addLayout(last_row)
        self.main_layout.addWidget(self.table, 1)
        
        # Connections
        self.search_timer = QTimer(self)
        self.search_timer.setSingleShot(True)
        self.search_timer.setInterval(300)
        self.search_line.textChanged.connect(self.search_timer.start)
        self.search_timer.timeout.connect(self.update_table)
        self.save_btn.clicked.connect(self.save_to_database)

    def update_table(self):
        """Fetches customer data from the DB and populates the table."""
        search_text = self.search_line.text().strip()
        data = self.db.find_customers(search_text)
        self.table.setUpdatesEnabled(False)
        self.table.setRowCount(len(data))
        for i, val in enumerate(data):
            self.table.setRowHeight(i, 40)
            self.table.setItem(i, 0, QTableWidgetItem(val[0]))
            self.table.setItem(i, 1, QTableWidgetItem(f"{val[1][:2]}-{val[1][2:5]}-{val[1][5:]}"))
            self.table.setItem(i, 2, QTableWidgetItem(format_number(val[2])))
            
            copy_button = QPushButton("Nusxalash")
            copy_button.clicked.connect(lambda checked, row=i: self.copy_row_data(row))
            copy_button.setStyleSheet("font-size: 14px; background-color: #525CEB; color: #F8EDFF; border-radius: 5px;")
            self.table.setCellWidget(i, 3, copy_button)
        self.table.setUpdatesEnabled(True)

    def copy_row_data(self, row):
        """Copies data from a table row to the input fields."""
        self.name_line.setText(self.table.item(row, 0).text())
        self.contact_line.setText(self.table.item(row, 1).text())
        self.amount_line.clear()
        self.date_line.clear()
        self.description_line.clear()
        self.name_line.setFocus()

    def save_to_database(self):
        """Validates input and saves a new debt record to the database."""
        name = self.name_line.text().strip()
        contact = self.contact_line.text().replace("-", "")
        description = self.description_line.text().strip() or "Izoh qoldirilmagan"
        amount_str = self.amount_line.text().replace(" ", "")
        promised_date_str = self.date_line.text()

        if not all([name, contact, amount_str, promised_date_str]):
            QMessageBox.warning(self, "Xato", "Iltimos, barcha maydonlarni to'ldiring. ❌")
            return
        
        try:
            amount = int(amount_str)
            promised_date_obj = datetime.strptime(promised_date_str, "%d/%m/%Y")
            promised_date = promised_date_obj.strftime("%Y-%m-%d")
        except ValueError:
            QMessageBox.warning(self, "Xato", "Summa yoki sana noto'g'ri kiritildi ❌")
            return

        dialog = CustomDialog(name, format_number(amount))
        if dialog.exec() == QDialog.DialogCode.Accepted:
            try:
                issued_date_obj = datetime.strptime(dialog.get_date(), "%d/%m/%Y")
                issued_date = issued_date_obj.strftime("%Y-%m-%d %H:%M:%S")
                
                data = {
                    'name': name, 'contact': contact, 'description': description,
                    'amount': amount, 'promised_date': promised_date,
                    'issued_date': issued_date
                }
                if self.db.process_customer_debt(data):
                    QMessageBox.information(self, 'Muvaffaqiyatli', f"{format_number(amount)} so'm {name} ga qo'shildi ✅")
                    self.amount_line.clear()
                    self.date_line.clear()
                    self.description_line.clear()
                    self.name_line.clear()
                    self.contact_line.clear()
                    self.update_table()
                else:
                    QMessageBox.critical(self, "Xatolik", "Ma'lumotlarni saqlashda xatolik yuz berdi❌")
            except ValueError:
                QMessageBox.warning(self, "Xatolik", "Tasdiqlash oynasida sana noto'g'ri kiritildi ❌")
        else:
            QMessageBox.information(self, "Bekor qilindi", "Amal bekor qilindi")

class List_people(QWidget):
    """A page for listing all customers and navigating to their history or payment pages."""
    def __init__(self, stacked_widget, db) -> None:
        super().__init__()
        self.db = db
        self.stacked_widget = stacked_widget
        self.main_layout = QVBoxLayout(self)
        self.setup_ui()
        self.update_table()

    def setup_ui(self):
        """Initializes and arranges all UI elements for this page."""
        self.search_line = FocusShadowLineEdit(placeholderText="Qidiruvga ism yoki telefon raqam kiriting...")
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(['Ism', 'Telefon', 'Qoldiq qarz', "Tarix", "To'lov"])
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
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
        self.table.verticalHeader().setDefaultSectionSize(40)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        search_layout = QHBoxLayout()
        search_layout.addStretch()
        search_layout.addWidget(self.search_line)
        search_layout.addStretch()

        self.main_layout.addLayout(search_layout)
        self.main_layout.addWidget(self.table, 1)

        self.search_timer = QTimer(self)
        self.search_timer.setSingleShot(True)
        self.search_timer.setInterval(300)
        self.search_line.textChanged.connect(self.search_timer.start)
        self.search_timer.timeout.connect(self.update_table)

    def update_table(self):
        """Fetches customer data from the DB and populates the table."""
        search_text = self.search_line.text().strip()
        data = self.db.find_customers(search_text)
        self.table.setUpdatesEnabled(False)
        self.table.setRowCount(len(data))
        for i, val in enumerate(data):
            self.table.setRowHeight(i, 40)
            self.table.setItem(i, 0, QTableWidgetItem(val[0]))
            self.table.setItem(i, 1, QTableWidgetItem(f"{val[1][:2]}-{val[1][2:5]}-{val[1][5:]}"))
            self.table.setItem(i, 2, QTableWidgetItem(format_number(val[2])))
            
            history_button = QPushButton("Tarix")
            pay_button = QPushButton("To'lov")
            history_button.clicked.connect(lambda checked, cid=val[3]: self.switch_to_history(cid))
            pay_button.clicked.connect(lambda checked, cid=val[3]: self.open_payment_page(cid))
            history_button.setStyleSheet("font-size: 14px; background-color: #525CEB; color: #F8EDFF; border-radius: 5px;")
            pay_button.setStyleSheet("font-size: 14px; background-color: #525CEB; color: #F8EDFF; border-radius: 5px;")
            self.table.setCellWidget(i, 3, history_button)
            self.table.setCellWidget(i, 4, pay_button)
        self.table.setUpdatesEnabled(True)

    def switch_to_history(self, customer_id):
        """Switches the view to the History page for the selected customer."""
        # Corrected line:
        history_widget = self.stacked_widget.widget(5) 
        history_widget.update_data(customer_id)
        self.stacked_widget.setCurrentIndex(5)

    def open_payment_page(self, customer_id):
        """Opens the payment window for the selected customer."""
        self.payment_window = payment(main_window=self, db=self.db, customer_id=customer_id)
        self.payment_window.show()
    
    def on_second_window_closed(self):
        """Callback method to refresh the table when the payment window is closed."""
        self.update_table()

class payment(QWidget):
    """A separate window for making a payment for a customer."""
    def __init__(self, main_window, db, customer_id) -> None:
        super().__init__()
        self.main_window = main_window
        self.db = db
        self.customer_id = customer_id
        self.setup_ui()

    def setup_ui(self):
        """Initializes and arranges all UI elements for this window."""
        self.setMinimumSize(400, 300)
        self.setWindowTitle("To'lov oynasi")
        self.setStyleSheet("font-size: 18px")
        self.main_layout = QVBoxLayout(self)
        
        data = self.db.find_customer(self.customer_id)
        if not data:
            QMessageBox.critical(self, "Xato", "Mijoz topilmadi.")
            QTimer.singleShot(0, self.close) # Close window if customer not found
            return
            
        self.name_lbl = QLabel(f"{data[0]}")
        self.number_lbl = QLabel(f"{data[1][:2]}-{data[1][2:5]}-{data[1][5:]}")

        form_layout = QFormLayout()
        form_layout.addRow(QLabel("Ism:"), self.name_lbl)
        form_layout.addRow(QLabel("Telefon:"), self.number_lbl)

        self.comment_line = FocusShadowLineEdit(placeholderText="Izoh qoldiring...")
        self.amount_line = FormattedLineEdit(placeholderText="Summani kiriting...")
        self.save_btn = QPushButton("To'lash")
        self.save_btn.setStyleSheet("font-size: 18px; border: 0px; border-radius: 12px; background: #525CEB; color: #F8EDFF")
        self.save_btn.setMinimumSize(150, 40)

        self.main_layout.addLayout(form_layout)
        self.main_layout.addStretch()
        self.main_layout.addWidget(create_label("Izoh:"))
        self.main_layout.addWidget(self.comment_line)
        self.main_layout.addStretch()
        self.main_layout.addWidget(create_label("Summa:"))
        self.main_layout.addWidget(self.amount_line)
        self.main_layout.addStretch()
        self.main_layout.addWidget(self.save_btn, 0, Qt.AlignmentFlag.AlignCenter)

        self.save_btn.clicked.connect(self.save_to_database)
        
    def save_to_database(self):
        """Validates input and saves a new payment record to the database."""
        amount_str = self.amount_line.text().replace(" ", "")
        try:
            amount = int(amount_str)
            if amount <= 0: raise ValueError
        except ValueError:
            QMessageBox.warning(self, "Xato", "Summa noto'g'ri kiritildi ❌")
            return

        comment = self.comment_line.text().strip() or "Izoh qoldirilmagan"
        reply = QMessageBox.question(self, 'Tasdiqlash',
                             f"{format_number(amount)} so'm to'lov qilinsinmi?",
                             QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                             QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            if self.db.payback(self.customer_id, amount, comment):
                QMessageBox.information(self, "Muvaffaqiyatli", f"{format_number(amount)} so'm to'lov qilindi ✅")
                self.close()
            else:
                QMessageBox.critical(self, "Xatolik", "To'lovni saqlashda xatolik yuz berdi❌")
        
    def closeEvent(self, event):
        """Ensures the main list is updated when this window is closed."""
        self.main_window.on_second_window_closed()
        event.accept()

class History(QWidget):
    """A page for viewing the detailed debt and payment history of a customer."""
    def __init__(self, stacked_widget, db) -> None:
        super().__init__()
        self.db = db
        self.stacked_widget = stacked_widget
        self.customer_id = None
        self.information = None # Cache for fetched data
        self.setup_ui()

    def setup_ui(self):
        """Initializes and arranges all UI elements for this page."""
        # Use a standard icon for the back button for better compatibility
        self.back_btn = QPushButton(icon=self.style().standardIcon(QStyle.StandardPixmap.SP_ArrowLeft))
        self.back_btn.setStyleSheet("""
            QPushButton {
                border: 0px; 
                background: transparent; 
                border-radius: 25px;
                padding: 7px;
            }
            QPushButton:hover {
                background: #FFE3CA;
            }
        """)

        self.print_btn = QPushButton(" Chop etish (PDF)")
        # Use a standard icon for a more professional look
        self.print_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogSaveButton))
        self.print_btn.setStyleSheet("""
            QPushButton {
                font-size: 16px; border: 0px; border-radius: 12px; 
                background: #00712D; color: #F8EDFF; padding: 10px;
            }
            QPushButton:hover { background: #005724; }
        """)

        self.edit_contact_btn = QPushButton("Tahrir")
        self.edit_contact_btn.setStyleSheet("font-size: 12px; background-color: #DDDDDD; border-radius: 5px;")
        self.name_lbl = QLabel()
        self.name_lbl.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.MinimumExpanding)
        self.name_lbl.setStyleSheet("font-size: 25px; color: #333333; font-weight: bold; font-family: 'Roboto';")
        self.description_lbl = QLabel("Izoh ko'rish uchun jadvaldagi yozuvga bosing")
        self.description_lbl.setStyleSheet("font-size: 18px;; color: #333333; font-weight: bold; font-family: 'Roboto';")
        self.description_lbl.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.MinimumExpanding)
        self.contact_lbl = QLabel()
        self.debt_lbl = QLabel()
        self.overall_lbl = QLabel()
        self.payed_lbl = QLabel()

        self.contact_lbl.setStyleSheet("font-size: 18px;color: #333333; font-weight: bold; font-family: 'Roboto';")
        self.contact_lbl.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.MinimumExpanding)
        self.edit_contact_btn.setStyleSheet("padding:10px; font-size: 18px; border: 0px; border-radius: 12px; background: #525CEB; color: #F8EDFF")

        self.debt_lbl.setStyleSheet("font-size: 18px; color: #C7253E; font-weight: bold; font-family: 'Roboto'; background: #FEFAE0; padding-left: 3px")
        self.overall_lbl.setStyleSheet("font-size: 18px; color: #333333; font-weight: bold; font-family: 'Roboto'; background: #FEFAE0; padding-left: 3px")        
        self.payed_lbl.setStyleSheet("font-size: 18px; color: #00712D; font-weight: bold; font-family: 'Roboto'; background: #FEFAE0; padding-left: 3px")

        # Removed fixed sizes and fixed heights for these labels.
        # Set size policy to expanding in both directions so they can fill space.
        self.debt_lbl.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.overall_lbl.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.payed_lbl.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # Debt Table
        self.debt_table = QTableWidget()
        self.debt_table.setColumnCount(3)
        self.debt_table.setHorizontalHeaderLabels(['ID', 'Summa', 'Olingan vaqt'])
        self.debt_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.debt_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.debt_table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
        self.debt_table.verticalHeader().setDefaultSectionSize(40)
        self.debt_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
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

        # Payment Table
        self.payed_table = QTableWidget()
        self.payed_table.setColumnCount(3)
        self.payed_table.setHorizontalHeaderLabels(['ID', 'Summa', 'To\'langan vaqt'])
        self.payed_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.payed_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.payed_table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
        self.payed_table.verticalHeader().setDefaultSectionSize(40)
        self.payed_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
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

        # Layouts
        self.main_layout = QVBoxLayout(self)
        info_layout = QHBoxLayout()
        description_layout = QVBoxLayout()
        money_layout = QHBoxLayout()
        table_layout = QHBoxLayout()
        contact_layout = QHBoxLayout()

        contact_layout.addWidget(self.contact_lbl)
        contact_layout.addWidget(self.edit_contact_btn)
        contact_layout.addWidget(self.print_btn) # MOVED a few lines down
        contact_layout.addStretch()

        description_layout.addWidget(self.name_lbl)
        description_layout.addWidget(self.description_lbl)
        description_layout.addLayout(contact_layout)
        description_layout.addStretch(1)

        info_layout.addWidget(self.back_btn)
        info_layout.addLayout(description_layout, 1)

        money_layout.addWidget(self.debt_lbl, 1)
        money_layout.addWidget(self.overall_lbl, 1)
        money_layout.addWidget(self.payed_lbl, 1)

        table_layout.addWidget(self.debt_table, 1)
        table_layout.addWidget(self.payed_table, 1)

        self.main_layout.addLayout(info_layout)
        self.main_layout.addLayout(money_layout)
        self.main_layout.addLayout(table_layout, 1)

        # Connections
        self.back_btn.clicked.connect(self.back_to_list)
        self.edit_contact_btn.clicked.connect(self.edit_customer_contact)
        self.debt_table.cellClicked.connect(self.show_debt_comment)
        self.debt_table.customContextMenuRequested.connect(self.open_debt_context_menu)
        self.payed_table.cellClicked.connect(self.show_payment_comment)
        self.payed_table.customContextMenuRequested.connect(self.open_payment_context_menu)
        self.print_btn.clicked.connect(self.generate_a4_report)

    def show_debt_comment(self, row, column):
        """Displays the comment for the clicked debt entry using cached data."""
        if not self.information: return
        item_id = self.debt_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        comment = next((d[3] for d in self.information['debts'] if d[0] == item_id), "Izoh topilmadi.")
        self.description_lbl.setText(f"Izoh: {comment}")

    def show_payment_comment(self, row, column):
        """Displays the comment for the clicked payment entry using cached data."""
        if not self.information: return
        item_id = self.payed_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        comment = next((p[3] for p in self.information['payments'] if p[0] == item_id), "Izoh topilmadi.")
        self.description_lbl.setText(f"Izoh: {comment}")

    def update_data(self, customer_id):
        """Fetches and caches all data for a customer and updates the UI."""
        self.customer_id = customer_id
        self.information = self.db.history(self.customer_id)
        if not self.information: 
            QMessageBox.warning(self, "Xato", "Mijoz ma'lumotlarini yuklab bo'lmadi.")
            return
        
        person = self.information['person']
        self.name_lbl.setText(person['name'])
        contact = person['contact']
        self.contact_lbl.setText(f"{contact[:2]}-{contact[2:5]}-{contact[5:]}")
        self.debt_lbl.setText(f"Qarz: {format_number(person['remained'])}")
        self.overall_lbl.setText(f"Umumiy: {format_number(person['total'])}")
        self.payed_lbl.setText(f"To'langan: {format_number(person['payed'])}")
        self.description_lbl.setText("Izoh ko'rish uchun jadvaldagi yozuvga bosing")
        
        # Populate Debts Table
        self.debt_table.setRowCount(len(self.information['debts']))
        for i, val in enumerate(self.information['debts']):
            # val: (id, amount, date_issued, comment, date_promised)
            item_id = QTableWidgetItem(str(val[0]))
            item_id.setData(Qt.ItemDataRole.UserRole, val[0])
            self.debt_table.setItem(i, 0, item_id)
            self.debt_table.setItem(i, 1, QTableWidgetItem(format_number(val[1])))
            self.debt_table.setItem(i, 2, QTableWidgetItem(val[2].strftime('%d/%m/%Y %H:%M')))
        
        # Populate Payments Table
        self.payed_table.setRowCount(len(self.information['payments']))
        for i, val in enumerate(self.information['payments']):
            # val: (id, amount, date_issued, comment)
            item_id = QTableWidgetItem(str(val[0]))
            item_id.setData(Qt.ItemDataRole.UserRole, val[0])
            self.payed_table.setItem(i, 0, item_id)
            self.payed_table.setItem(i, 1, QTableWidgetItem(format_number(val[1])))
            self.payed_table.setItem(i, 2, QTableWidgetItem(val[2].strftime('%d/%m/%Y %H:%M')))
            
    def edit_customer_contact(self):
        """Opens a dialog to edit the customer's contact number."""
        if not self.information: return
        current_contact = self.information['person']['contact']
        dialog = EditContactDialog(current_contact, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_contact = dialog.get_contact()
            if self.db.update_customer_contact(self.customer_id, new_contact):
                QMessageBox.information(self, "Muvaffaqiyatli", "Mijoz raqami yangilandi.")
                self.update_data(self.customer_id) # Refresh data
            else:
                QMessageBox.critical(self, "Xato", "Raqamni yangilashda xatolik yuz berdi.")

    def open_debt_context_menu(self, position):
        """Opens a context menu to edit or delete a debt entry."""
        if not self.information: return
        row = self.debt_table.indexAt(position).row()
        if row < 0: return
        
        debt_id = self.debt_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        debt_entry = next((d for d in self.information['debts'] if d[0] == debt_id), None)
        if not debt_entry: return
        
        menu = QMenu()
        edit_action = menu.addAction("Tahrirlash / O'chirish")
        action = menu.exec(self.debt_table.viewport().mapToGlobal(position))

        if action == edit_action:
            date_str = debt_entry[4].strftime('%Y-%m-%d') if debt_entry[4] else None
            dialog = EditDeleteDialog(self.db, debt_id, 'debt', debt_entry[1], debt_entry[3], date_str)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                self.update_data(self.customer_id)

    def open_payment_context_menu(self, position):
        """Opens a context menu to edit or delete a payment entry."""
        if not self.information: return
        row = self.payed_table.indexAt(position).row()
        if row < 0: return

        payment_id = self.payed_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        payment_entry = next((p for p in self.information['payments'] if p[0] == payment_id), None)
        if not payment_entry: return

        menu = QMenu()
        edit_action = menu.addAction("Tahrirlash / O'chirish")
        action = menu.exec(self.payed_table.viewport().mapToGlobal(position))

        if action == edit_action:
            dialog = EditDeleteDialog(self.db, payment_id, 'payment', payment_entry[1], payment_entry[3])
            if dialog.exec() == QDialog.DialogCode.Accepted:
                self.update_data(self.customer_id)
    


    def generate_a4_report(self):
        """Generates and saves a customer history report as an A4 PDF with Cyrillic support."""
        if not self.information:
            QMessageBox.warning(self, "Xato", "Mijoz ma'lumotlari mavjud emas.")
            return

        # --- FONT REGISTRATION ---
        # 1. Check for the font file and register it.
        font_path = "DejaVuSans.ttf" 
        if not os.path.exists(font_path):
            QMessageBox.critical(self, "Xatolik", f"Font fayli topilmadi: {font_path}. Iltimos, shrift faylini dastur papkasiga joylashtiring.")
            return
        pdfmetrics.registerFont(TTFont('DejaVuSans', font_path))
        # --- END FONT REGISTRATION ---

        person_data = self.information['person']
        customer_name = person_data['name']

        safe_customer_name = "".join(c for c in customer_name if c.isalnum())
        filename = f"Mijoz_Tarixi_{safe_customer_name}.pdf"

        doc = SimpleDocTemplate(filename, pagesize=A4)
        styles = getSampleStyleSheet()

        # --- CUSTOM STYLES WITH NEW FONT ---
        # 2. Create styles that use the new font.
        style_h1 = ParagraphStyle(name='h1_cyrillic', parent=styles['h1'], fontName='DejaVuSans')
        style_h2 = ParagraphStyle(name='h2_cyrillic', parent=styles['h2'], fontName='DejaVuSans')
        style_body = ParagraphStyle(name='body_cyrillic', parent=styles['BodyText'], fontName='DejaVuSans', alignment=1) # Centered
        # --- END CUSTOM STYLES ---

        story = []

        # 1. Title
        title = Paragraph(f"{customer_name} - Qarz Tarixi", style_h1)
        story.append(title)
        story.append(Spacer(1, 0.2*inch))

        # 2. Summary Table
        summary_data = [
            [Paragraph("Umumiy qarz:", style_body), Paragraph(f"{format_number(person_data['total'])} so'm", style_body)],
            [Paragraph("To'langan:", style_body), Paragraph(f"{format_number(person_data['payed'])} so'm", style_body)],
            [Paragraph("Qoldiq qarz:", style_body), Paragraph(f"{format_number(person_data['remained'])} so'm", style_body)],
            [Paragraph("Telefon raqami:", style_body), Paragraph(person_data['contact'], style_body)],
        ]
        summary_table = Table(summary_data, colWidths=[2*inch, 3*inch])
        # 3. Apply the font to the table style.
        summary_table.setStyle(TableStyle([
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('FONTNAME', (0,0), (-1,-1), 'DejaVuSans'), # USE THE FONT
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
            ('BACKGROUND', (0,0), (-1,-1), colors.lightgrey),
            ('GRID', (0,0), (-1,-1), 1, colors.black),
        ]))
        story.append(summary_table)
        story.append(Spacer(1, 0.4*inch))

        # 4. Debts Table
        if self.information['debts']:
            story.append(Paragraph("Olingan qarzlar ro'yxati", style_h2))
            story.append(Spacer(1, 0.1*inch))

            debt_header = [[Paragraph("Summa", style_body), Paragraph("Olingan sana", style_body), Paragraph("Vada qilingan sana", style_body), Paragraph("Izoh", style_body)]]
            debt_rows = [
                [
                    Paragraph(format_number(d[1]), style_body),
                    Paragraph(d[2].strftime('%d/%m/%Y'), style_body),
                    Paragraph(d[4].strftime('%d/%m/%Y') if d[4] else "N/A", style_body),
                    Paragraph(d[3], style_body) # Wrap comment in Paragraph
                ] for d in self.information['debts']
            ]

            debt_table = Table(debt_header + debt_rows, colWidths=[1.5*inch, 1.2*inch, 1.5*inch, 2.5*inch])
            debt_table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#C7253E')),
                ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
                ('FONTNAME', (0,0), (-1,-1), 'DejaVuSans'), # USE THE FONT
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ('BOTTOMPADDING', (0,0), (-1,0), 12),
                ('BACKGROUND', (0,1), (-1,-1), colors.white),
                ('GRID', (0,0), (-1,-1), 1, colors.black)
            ]))
            story.append(debt_table)
            story.append(Spacer(1, 0.4*inch))

        # 5. Payments Table
        if self.information['payments']:
            story.append(Paragraph("Qilingan to'lovlar ro'yxati", style_h2))
            story.append(Spacer(1, 0.1*inch))

            payment_header = [[Paragraph("Summa", style_body), Paragraph("To'langan sana", style_body), Paragraph("Izoh", style_body)]]
            payment_rows = [
                [
                    Paragraph(format_number(p[1]), style_body),
                    Paragraph(p[2].strftime('%d/%m/%Y %H:%M'), style_body),
                    Paragraph(p[3], style_body) # Wrap comment in Paragraph
                ] for p in self.information['payments']
            ]

            payment_table = Table(payment_header + payment_rows, colWidths=[1.5*inch, 2*inch, 3.2*inch])
            payment_table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#00712D')),
                ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
                ('FONTNAME', (0,0), (-1,-1), 'DejaVuSans'), # USE THE FONT
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ('BOTTOMPADDING', (0,0), (-1,0), 12),
                ('BACKGROUND', (0,1), (-1,-1), colors.white),
                ('GRID', (0,0), (-1,-1), 1, colors.black)
            ]))
            story.append(payment_table)

        try:
            doc.build(story)
            QMessageBox.information(self, "Muvaffaqiyatli", f"Hisobot '{filename}' fayliga saqlandi.")

            if sys.platform == "win32":
                os.startfile(filename)
            else:
                opener = "open" if sys.platform == "darwin" else "xdg-open"
                subprocess.call([opener, filename])

        except Exception as e:
            QMessageBox.critical(self, "Xato", f"PDF faylni yaratishda xato yuz berdi:\n{e}")
    def back_to_list(self):
        """Switches the view back to the main customer list."""
        list_people_widget = self.stacked_widget.widget(1)
        list_people_widget.update_table()
        self.stacked_widget.setCurrentIndex(1)