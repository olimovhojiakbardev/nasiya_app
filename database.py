import mysql.connector
from mysql.connector import Error
import time

class Database:
    def __init__(self):
        """
        The constructor now immediately tries to establish a
        persistent connection.
        """
        self.connection = None
        # --- Corrected: Removed trailing commas ---
        self.host = 'localhost'
        self.user = 'root'
        self.password = 'SecureRoot#2025'
        self.database = 'qarz_db'
        try:
            self.connection = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database
            )
            print("Database connection established successfully.")
        except Error as e:
            print(f"FATAL: Could not connect to MySQL: {e}")
            self.connection = None

    def _reconnect(self, attempts=3, delay=2):
        """
        A private method to handle automatic reconnection if the connection is lost.
        """
        if self.connection and self.connection.is_connected():
            return True # Already connected
            
        print("Connection lost. Attempting to reconnect...")
        for i in range(attempts):
            try:
                self.connection = mysql.connector.connect(
                    host=self.host,
                    user=self.user,
                    password=self.password,
                    database=self.database
                )
                if self.connection.is_connected():
                    print("Reconnection successful.")
                    return True
            except Error as e:
                print(f"Reconnect attempt {i+1}/{attempts} failed: {e}")
                time.sleep(delay)
        print("FATAL: Could not reconnect to the database.")
        return False

    def close_connection(self):
        """
        This method should now only be called ONCE when the application is exiting.
        """
        if self.connection and self.connection.is_connected():
            self.connection.close()
            print("Database connection closed.")

    def process_customer_debt(self, data):
        if not self._reconnect(): return False
        try:
            cursor = self.connection.cursor()
            name = data['name']
            contact = data['contact']
            description = data['description']
            amount = int(data['amount'])
            promised_date = data['promised_date']
            issued_date = data['issued_date']
            cursor.execute("SELECT id, total, remained, contact FROM customers WHERE name = %s", (name,))
            customer = cursor.fetchone()

            if customer:
                customer_id = customer[0]
                new_total = customer[1] + amount
                new_remained = customer[2] + amount
                old_contact = customer[3]

                if old_contact == contact:
                    cursor.execute(
                        "UPDATE customers SET total = %s, remained = %s WHERE id = %s",
                        (new_total, new_remained, customer_id)
                    )
                else:
                    cursor.execute(
                        "UPDATE customers SET total = %s, remained = %s, contact = %s WHERE id = %s",
                        (new_total, new_remained, contact, customer_id)
                    )
            else:
                cursor.execute(
                    "INSERT INTO customers (name, contact, total, payed, remained) VALUES (%s, %s, %s, %s, %s)",
                    (name, contact, amount, 0, amount)
                )
                customer_id = cursor.lastrowid

            cursor.execute(
                "INSERT INTO debts (customer_id, amount, date_issued, date_promised, comment) VALUES (%s, %s, %s, %s, %s)",
                (customer_id, amount, issued_date, promised_date, description)
            )

            self.connection.commit()
            cursor.close()
            return True
        except Exception as e:
            print(f"Error processing customer debt: {e}")
            if self.connection: self.connection.rollback()
            return False

    def find_customers(self, text):
        if not self._reconnect(): return []
        try:
            cursor = self.connection.cursor()
            if text == "":
                query = 'SELECT name, contact, remained, id FROM customers ORDER BY name'
                cursor.execute(query)
            else:
                query = "SELECT name, contact, remained, id FROM customers WHERE name LIKE %s OR contact LIKE %s ORDER BY name"
                search_text = f"%{text}%"
                cursor.execute(query, (search_text, search_text))

            data = cursor.fetchall()
            cursor.close()
            return data
        except Error as e:
            print(f"Error finding customers: {e}")
            return []

    def find_customer(self, customer_id):
        if not self._reconnect(): return None
        try:
            cursor = self.connection.cursor()
            cursor.execute('SELECT name, contact FROM customers WHERE id = %s', (customer_id,))
            data = cursor.fetchone()
            cursor.close()
            return data
        except Error as e:
            print(f"Error finding customer by ID: {e}")
            return None

    def history(self, customer_id):
        if not self._reconnect(): return None
        try:
            cursor = self.connection.cursor()
            cursor.execute('SELECT name, contact, remained, payed, total FROM customers WHERE id = %s', (customer_id,))
            person_data = cursor.fetchone()
            
            if not person_data:
                cursor.close()
                return None

            data = {
                "person": {
                    'name': person_data[0],
                    'contact': person_data[1],
                    'remained': person_data[2],
                    'payed': person_data[3],
                    'total': person_data[4]
                }
            }
            cursor.execute("SELECT id, amount, date_issued, comment, date_promised FROM debts WHERE customer_id = %s ORDER BY date_issued DESC", (customer_id,))
            data['debts'] = cursor.fetchall()

            cursor.execute("SELECT id, amount, date_issued, comment FROM payments WHERE customer_id = %s ORDER BY date_issued DESC", (customer_id,))
            data['payments'] = cursor.fetchall()
            
            cursor.close()
            return data
        except Error as e:
            print(f"Error fetching history: {e}")
            return None

    def payback(self, customer_id, amount, comment):
        if not self._reconnect(): return False
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT payed, remained FROM customers WHERE id = %s", (customer_id,))
            data = cursor.fetchone()

            if data is None:
                cursor.close()
                return False

            payed, remained = data
            remained -= amount
            payed += amount

            cursor.execute(
                "UPDATE customers SET payed = %s, remained = %s WHERE id = %s",
                (payed, remained, customer_id)
            )
            cursor.execute(
                "INSERT INTO payments (customer_id, amount, comment, date_issued) VALUES (%s, %s, %s, NOW())",
                (customer_id, amount, comment)
            )

            self.connection.commit()
            cursor.close()
            return True
        except Error as e:
            print(f"Error during payback: {e}")
            if self.connection: self.connection.rollback()
            return False

    def update_customer_contact(self, customer_id, new_contact):
        if not self._reconnect(): return False
        try:
            cursor = self.connection.cursor()
            cursor.execute("UPDATE customers SET contact = %s WHERE id = %s", (new_contact, customer_id))
            self.connection.commit()
            cursor.close()
            return True
        except Error as e:
            print(f"Error updating customer contact: {e}")
            if self.connection: self.connection.rollback()
            return False

    def update_debt_entry(self, debt_id, new_amount, new_comment, new_promised_date):
        if not self._reconnect(): return False
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT amount, customer_id FROM debts WHERE id = %s", (debt_id,))
            debt_info = cursor.fetchone()
            if debt_info:
                old_amount, customer_id = debt_info
                amount_diff = new_amount - old_amount
                cursor.execute("UPDATE debts SET amount = %s, comment = %s, date_promised = %s WHERE id = %s",
                               (new_amount, new_comment, new_promised_date, debt_id))
                cursor.execute("UPDATE customers SET total = total + %s, remained = remained + %s WHERE id = %s",
                               (amount_diff, amount_diff, customer_id))
                self.connection.commit()
                cursor.close()
                return True
            cursor.close()
            return False
        except Error as e:
            print(f"Error updating debt entry: {e}")
            if self.connection: self.connection.rollback()
            return False

    def update_payment_entry(self, payment_id, new_amount, new_comment):
        if not self._reconnect(): return False
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT amount, customer_id FROM payments WHERE id = %s", (payment_id,))
            payment_info = cursor.fetchone()
            if payment_info:
                old_amount, customer_id = payment_info
                amount_diff = new_amount - old_amount
                cursor.execute("UPDATE payments SET amount = %s, comment = %s WHERE id = %s",
                               (new_amount, new_comment, payment_id))
                cursor.execute("UPDATE customers SET payed = payed + %s, remained = remained - %s WHERE id = %s",
                               (amount_diff, amount_diff, customer_id))
                self.connection.commit()
                cursor.close()
                return True
            cursor.close()
            return False
        except Error as e:
            print(f"Error updating payment entry: {e}")
            if self.connection: self.connection.rollback()
            return False

    def delete_debt_entry(self, debt_id):
        if not self._reconnect(): return False
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT amount, customer_id FROM debts WHERE id = %s", (debt_id,))
            debt_info = cursor.fetchone()
            if debt_info:
                debt_amount, customer_id = debt_info
                cursor.execute("DELETE FROM debts WHERE id = %s", (debt_id,))
                cursor.execute("UPDATE customers SET total = total - %s, remained = remained - %s WHERE id = %s",
                               (debt_amount, debt_amount, customer_id))
                self.connection.commit()
                cursor.close()
                return True
            cursor.close()
            return False
        except Error as e:
            print(f"Error deleting debt entry: {e}")
            if self.connection: self.connection.rollback()
            return False

    def delete_payment_entry(self, payment_id):
        if not self._reconnect(): return False
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT amount, customer_id FROM payments WHERE id = %s", (payment_id,))
            payment_info = cursor.fetchone()
            if payment_info:
                payment_amount, customer_id = payment_info
                cursor.execute("DELETE FROM payments WHERE id = %s", (payment_id,))
                cursor.execute("UPDATE customers SET payed = payed - %s, remained = remained + %s WHERE id = %s",
                               (payment_amount, payment_amount, customer_id))
                self.connection.commit()
                cursor.close()
                return True
            cursor.close()
            return False
        except Error as e:
            print(f"Error deleting payment entry: {e}")
            if self.connection: self.connection.rollback()
            return False
        

    def get_statistics(self, start_date, end_date):
        """
        Fetches all necessary statistics for the dashboard.
        start_date and end_date should be in 'YYYY-MM-DD' format.
        """
        if not self._reconnect(): return None
        
        stats = {}
        try:
            cursor = self.connection.cursor()

            # Global KPIs (not dependent on date)
            cursor.execute("SELECT SUM(remained), COUNT(*) FROM customers WHERE remained > 0")
            total_remained, active_debtors = cursor.fetchone()
            stats['total_outstanding_debt'] = total_remained or 0
            stats['active_debtors'] = active_debtors or 0

            # Date-filtered KPIs
            cursor.execute("SELECT SUM(amount) FROM debts WHERE DATE(date_issued) BETWEEN %s AND %s", (start_date, end_date))
            stats['total_loaned_period'] = cursor.fetchone()[0] or 0
            
            cursor.execute("SELECT SUM(amount) FROM payments WHERE DATE(date_issued) BETWEEN %s AND %s", (start_date, end_date))
            stats['total_recovered_period'] = cursor.fetchone()[0] or 0

            # Monthly activity for the line chart
            query_loans = """
                SELECT YEAR(date_issued), MONTH(date_issued), SUM(amount)
                FROM debts
                WHERE DATE(date_issued) BETWEEN %s AND %s
                GROUP BY YEAR(date_issued), MONTH(date_issued)
                ORDER BY YEAR(date_issued), MONTH(date_issued)
            """
            cursor.execute(query_loans, (start_date, end_date))
            # This is the critical fix: (amount or 0) converts any NULL/None from the DB to 0
            stats['monthly_loans'] = {f"{year:04d}-{month:02d}": (amount or 0) for year, month, amount in cursor.fetchall()}

            query_payments = """
                SELECT YEAR(date_issued), MONTH(date_issued), SUM(amount)
                FROM payments
                WHERE DATE(date_issued) BETWEEN %s AND %s
                GROUP BY YEAR(date_issued), MONTH(date_issued)
                ORDER BY YEAR(date_issued), MONTH(date_issued)
            """
            cursor.execute(query_payments, (start_date, end_date))
            # This is the critical fix: (amount or 0) converts any NULL/None from the DB to 0
            stats['monthly_payments'] = {f"{year:04d}-{month:02d}": (amount or 0) for year, month, amount in cursor.fetchall()}

            # Top 5 Debtors
            # 4. Top 20 Debtors (global)
            cursor.execute("SELECT name, remained FROM customers WHERE remained > 0 ORDER BY remained DESC LIMIT 20")
            stats['top_debtors'] = cursor.fetchall()
            
            # Overdue Debts
            cursor.execute("""
                SELECT COUNT(*) FROM debts d
                JOIN customers c ON d.customer_id = c.id
                WHERE d.date_promised < CURDATE() AND c.remained > 0
            """)
            stats['overdue_debts_count'] = cursor.fetchone()[0] or 0

            cursor.execute("""
                SELECT COUNT(*) FROM debts d
                JOIN customers c ON d.customer_id = c.id
                WHERE c.remained > 0
            """)
            stats['active_debts_count'] = cursor.fetchone()[0] or 0

            cursor.close()
            return stats
        except Exception as e:
            print(f"Error getting statistics: {e}")
            return None
        
    def get_activity_log(self, start_date, end_date, action_type, customer_name):
        """
        Fetches a combined log of debts and payments for the activity page.
        - action_type can be 'all', 'debts', or 'payments'.
        - customer_name is a string for searching.
        """
        if not self._reconnect(): return None
        
        try:
            cursor = self.connection.cursor()
            
            base_query = """
                SELECT date_issued, customer_id, amount, 'qarz' as type, comment FROM debts
                UNION ALL
                SELECT date_issued, customer_id, amount, 'tolov' as type, comment FROM payments
            """
            
            query = f"""
                SELECT a.date_issued, c.name, a.amount, a.type, a.comment
                FROM ({base_query}) AS a
                JOIN customers c ON a.customer_id = c.id
                WHERE DATE(a.date_issued) BETWEEN %s AND %s
            """
            
            params = [start_date, end_date]
            
            if action_type != 'all':
                query += " AND a.type = %s"
                params.append(action_type.rstrip('s')) # 'debts' -> 'debt', 'payments' -> 'payment'
            
            if customer_name:
                query += " AND c.name LIKE %s"
                params.append(f"%{customer_name}%")
                
            query += " ORDER BY a.date_issued DESC"
            
            cursor.execute(query, tuple(params))
            
            results = cursor.fetchall()
            cursor.close()
            return results

        except Exception as e:
            print(f"Error getting activity log: {e}")
            return None