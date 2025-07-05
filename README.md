# Nasiya Debt Management App

A desktop application built with Python and PyQt6 to help manage personal debts and payments for customers.

## Features

* Add new customers and their debts.
* Track remaining balances, total debt, and total payments.
* View a detailed history of all transactions for each customer.
* Edit or delete debt and payment entries.
* Generate printable A4 PDF reports of a customer's history.
* Create and send database backups to a Telegram chat.

## Setup & Installation

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/olimovhojiakbardev/nasiya_app.git](https://github.com/olimovhojiakbardev/nasiya_app.git)
    cd nasiya_app
    ```

2.  **Create a virtual environment:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure the application:**
    * Copy the example configuration file:
        ```bash
        cp config.py.example config.py
        ```
    * Open `config.py` and add your actual Telegram Bot Token and User IDs.

5.  **Database Setup:**
    * Make sure you have a MySQL server running.
    * Update the database credentials in `database.py` if they are different from the defaults.
    * Create a database named `qarz_db` and the required tables (`customers`, `debts`, `payments`).

## Usage

To run the application, execute the `Nasiya.py` script:
```bash
python Nasiya.py
```