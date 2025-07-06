from PyQt6.QtWidgets import (QMainWindow, QHBoxLayout, QVBoxLayout, QWidget, QGraphicsDropShadowEffect,
                             QPushButton, QStackedWidget, QLabel, QSizePolicy, QApplication, QMessageBox)
from PyQt6.QtGui import QColor
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QObject
# In Nasiya.py
from widgets import Add_page, List_people, History, StatisticsPage, ActivityLogPage
from database import Database
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_USER_IDS
import sys
import requests
import subprocess
import os
import gzip
import shutil
import asyncio
from datetime import datetime
from telegram import Bot
from telegram.error import TelegramError
from telegram.request import HTTPXRequest

class BackupWorker(QObject):
    status_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool, str)

    def __init__(self, db):
        super().__init__()
        self.db = db

    def run(self):
        # Step 1: Check internet connection
        self.status_signal.emit("Checking internet connection...")
        if not self.check_internet():
            self.finished_signal.emit(False, "No internet connection. Please check your network.")
            return

        # Step 2: Create backup
        self.status_signal.emit("Creating backup...")
        backup_file = self.create_backup()
        if backup_file is None:
            self.finished_signal.emit(False, "Failed to create backup. Check database credentials or mysqldump path.")
            return

        # Step 3: Compress backup file
        self.status_signal.emit("Compressing backup file...")
        compressed_file = self.compress_backup(backup_file)
        if compressed_file is None:
            self.finished_signal.emit(False, "Failed to compress backup file.")
            os.remove(backup_file)
            return

        # Step 4: Send backup via Telegram
        self.status_signal.emit("Sending backup via Telegram...")
        success, message = self.send_backup(compressed_file)
        
        # Step 5: Cleanup local files
        os.remove(backup_file)
        if os.path.exists(compressed_file):
            os.remove(compressed_file)
            
        # Step 6: Signal completion
        self.finished_signal.emit(success, message)

    def check_internet(self, url='http://www.google.com', timeout=5):
        try:
            requests.get(url, timeout=timeout)
            return True
        except (requests.ConnectionError, requests.Timeout):
            return False

    def create_backup(self):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = f"backup_{timestamp}.sql"
        
        # Use the correct database credentials from the db object
        command = [
            "mysqldump",
            "-h", self.db.host,
            "-u", self.db.user,
            f"-p{self.db.password}", # Note: No space after -p
            self.db.database
        ]
        try:
            # Using subprocess.run for better error handling
            with open(backup_file, "w", encoding='utf-8') as f:
                result = subprocess.run(command, stdout=f, stderr=subprocess.PIPE, text=True, check=False)
            
            if result.returncode != 0:
                error_message = f"Error creating backup: {result.stderr}"
                self.status_signal.emit(error_message)
                print(error_message) # Also print to console for debugging
                return None
            return backup_file
        except FileNotFoundError:
            error_message = "Error: 'mysqldump' command not found. Is MySQL installed and in your system's PATH?"
            self.status_signal.emit(error_message)
            print(error_message)
            return None
        except Exception as e:
            error_message = f"An exception occurred during backup: {str(e)}"
            self.status_signal.emit(error_message)
            print(error_message)
            return None

    def compress_backup(self, backup_file):
        compressed_file = f"{backup_file}.gz"
        try:
            with open(backup_file, "rb") as f_in:
                with gzip.open(compressed_file, "wb") as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            file_size_mb = os.path.getsize(compressed_file) / (1024 * 1024)
            if file_size_mb > 49: # Keep it under 50MB for safety
                self.status_signal.emit(f"Compressed file size ({file_size_mb:.2f} MB) exceeds Telegram's limit.")
                return None
            return compressed_file
        except Exception as e:
            self.status_signal.emit(f"Error compressing backup: {str(e)}")
            return None

    # --- New: Asynchronous core function for sending ---
    async def _send_telegram_async(self, backup_file):
        """The actual async part of sending the backup."""
        # --- New: Set a longer timeout for requests ---
        httpx_request = HTTPXRequest(connect_timeout=20, read_timeout=20)
        bot = Bot(token=TELEGRAM_BOT_TOKEN, request=httpx_request)
        
        error_messages = []
        success_count = 0

        try:
            # Test bot connectivity
            self.status_signal.emit("Authenticating bot...")
            bot_info = await bot.get_me()
            self.status_signal.emit(f"Bot authenticated as {bot_info.username}.")
        except Exception as e:
            return False, f"Bot authentication failed: {e}. Check bot token and internet."

        for user_id in TELEGRAM_USER_IDS:
            try:
                self.status_signal.emit(f"Sending to user {user_id}...")
                caption_text = f"Database backup created on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                with open(backup_file, "rb") as document:
                    await bot.send_document(chat_id=user_id, document=document, caption=caption_text)
                self.status_signal.emit(f"Successfully sent to user {user_id}.")
                success_count += 1
            except Exception as e:
                error_msg = f"Failed to send to user {user_id}: {e}"
                self.status_signal.emit(error_msg)
                error_messages.append(error_msg)

        if success_count == len(TELEGRAM_USER_IDS):
            return True, f"Backup sent successfully to all {success_count} user(s)."
        else:
            final_message = f"Sent to {success_count}/{len(TELEGRAM_USER_IDS)} user(s). Errors: {'; '.join(error_messages)}"
            return False, final_message

    # --- Rewritten: Synchronous wrapper that calls the async function ---
    def send_backup(self, backup_file):
        """Synchronous wrapper to run the async send operation."""
        try:
            # asyncio.run is the modern way to run an async function from sync code.
            # It creates and manages the event loop automatically.
            return asyncio.run(self._send_telegram_async(backup_file))
        except Exception as e:
            # Catch any unexpected errors during the asyncio.run call
            return False, f"A general error occurred in the sending process: {e}"

class BackupPage(QWidget):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.layout = QVBoxLayout()
        self.layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.status_label = QLabel("Click the button to start the backup and sending process.")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.start_button = QPushButton("Start Backup and Send")
        self.start_button.setFixedSize(200, 50)
        self.start_button.clicked.connect(self.start_backup)
        
        self.layout.addWidget(self.status_label)
        self.layout.addWidget(self.start_button, alignment=Qt.AlignmentFlag.AlignCenter)
        
        self.setLayout(self.layout)

    def start_backup(self):
        self.start_button.setEnabled(False)
        self.status_label.setText("Starting backup process...")
        
        self.worker = BackupWorker(self.db)
        self.thread = QThread()
        self.worker.moveToThread(self.thread)
        
        self.thread.started.connect(self.worker.run)
        self.worker.status_signal.connect(self.update_status)
        self.worker.finished_signal.connect(self.backup_finished)
        
        # Clean up the thread when it's finished
        self.thread.finished.connect(self.thread.deleteLater)
        self.worker.finished_signal.connect(self.thread.quit)

        self.thread.start()

    def update_status(self, status):
        self.status_label.setText(status)

    def backup_finished(self, success, message):
        self.start_button.setEnabled(True)
        if success:
            QMessageBox.information(self, "Success", message)
            self.status_label.setText("Backup process completed successfully.")
        else:
            QMessageBox.critical(self, "Error", message)
            self.status_label.setText("Backup process failed. Check console for details.")

class MainWindow(QMainWindow):
    def __init__(self, db) -> None:
        super().__init__()
        self.db = db
        self.setWindowTitle("Qarz Daftar")
        self.setMinimumSize(1000, 700)

        self.main_layout = QHBoxLayout()

        self.side_menu = QVBoxLayout()
        self.side_menu.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.menu_widget = QWidget()
        self.menu_widget.setLayout(self.side_menu)
        self.menu_widget.setStyleSheet("background-color: #F0EBE3; border: 0px; border-radius: 20px;")
        self.menu_widget.setMinimumWidth(200)
        self.menu_widget.setMaximumWidth(250)
        self.menu_widget.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)

        shadow_effect = QGraphicsDropShadowEffect()
        shadow_effect.setBlurRadius(30)
        shadow_effect.setOffset(0, 0)
        shadow_effect.setColor(QColor(128, 128, 128))
        self.menu_widget.setGraphicsEffect(shadow_effect)

        self.menu_buttons_list = []
        # In MainWindow.__init__
        self.menu_map = {
            'Qarz Qo\'shish': 0,
            'Qarzlarni ko\'rish': 1,
            'Statistika': 2,
            'Amallar Tarixi': 3, # Renamed from "Bildirishlar"
            'Backup and Send': 4
        }
        
        for button_name, page_index in self.menu_map.items():
            btn = QPushButton(button_name)
            btn.clicked.connect(lambda checked, i=page_index: self.switch_page(i))
            self.side_menu.addWidget(btn)
            self.menu_buttons_list.append(btn)
        
        self.side_menu.addStretch()

        self.content_area = QStackedWidget()
        self.content_area.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # Page indices must match the menu_map
        self.page_add = Add_page(self.db)
        self.page_list = List_people(self.content_area, self.db)
        self.page_stats = StatisticsPage(self.db)
        self.page_activity_log = ActivityLogPage(self.db)
        self.page_backup = BackupPage(self.db)
        self.page_history = History(self.content_area, self.db) # This page is not in the menu

        self.content_area.addWidget(self.page_add)           # index 0
        self.content_area.addWidget(self.page_list)          # index 1
        self.content_area.addWidget(self.page_stats)         # index 2
        self.content_area.addWidget(self.page_activity_log)  # index 3
        self.content_area.addWidget(self.page_backup)        # index 4
        self.content_area.addWidget(self.page_history)       # index 5 (for navigation from page_list)

        self.main_layout.addWidget(self.menu_widget)
        self.main_layout.addWidget(self.content_area, 1)
        container = QWidget()
        container.setLayout(self.main_layout)
        self.setCentralWidget(container)
        
        self.switch_page(0)

    def switch_page(self, index):
        # Special handling for history page which is not in the main menu
        if index == 5: # History page
            self.content_area.setCurrentIndex(5)
            # Deselect all menu buttons
            active_button_index = -1
        else:
            self.content_area.setCurrentIndex(index)
            active_button_index = index

        if index == 1: # If switching to the list page, refresh it
            self.page_list.update_table()

        for i, btn in enumerate(self.menu_buttons_list):
            if i == active_button_index:
                btn.setStyleSheet("""QPushButton {
                    background-color: #45474B; border: 0px; border-radius: 20px;
                    padding: 10px; color: #F0EBE3; font-size: 16px; font-weight: bold;
                }""")
            else:
                btn.setStyleSheet("""QPushButton {
                    background-color: #F0EBE3; border: 0px; border-radius: 20px;
                    padding: 10px; color: #112D4E; font-size: 16px; font-weight: bold;
                }
                QPushButton:hover { background-color: #CCD3CA; border: 0; color: #151515; }
                """)

def cleanup_old_files():
    """Deletes leftover .pdf, .sql, and .sql.gz files from the current directory."""
    print("Running startup cleanup...")
    current_dir = os.getcwd() # Gets the application's folder
    files_to_delete = []
    for filename in os.listdir(current_dir):
        if filename.endswith((".pdf", ".sql", ".sql.gz")):
            files_to_delete.append(filename)

    if not files_to_delete:
        print("No old files to clean up.")
        return

    for f in files_to_delete:
        try:
            os.remove(os.path.join(current_dir, f))
            print(f"Deleted old file: {f}")
        except OSError as e:
            print(f"Error deleting file {f}: {e}")


if __name__ == '__main__':
    app = QApplication(sys.argv)

    cleanup_old_files()
    
    db_connection = Database()

    if not db_connection.connection:
        QMessageBox.critical(None, "Database Error", 
                             "Could not connect to the database. The application will now exit.")
        sys.exit(1)

    window = MainWindow(db_connection)
    window.show()

    exit_code = 0
    try:
        exit_code = app.exec()
    finally:
        print("Application closing, shutting down database connection...")
        db_connection.close_connection()
        sys.exit(exit_code)
