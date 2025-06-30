import mysql.connector
from mysql.connector import Error

class Database:
    def __init__(self) -> None:
        self.connection = None
        self.init()
    def init(self) -> None:
        try:
            self.connection = mysql.connector.connect(
                host='localhost',
                user='root',
                password='SecureRoot#2025',
                database='qarz_db'
            )
        except Error as e:
            print(f"Error while connecting to MySQL: {e}")

    def close_connection(self):
        if self.connection.is_connected() and self.connection:
            self.connection.close()

    def process_customer_debt(self, data):
        try:
            self.init()
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
            return True

        except Exception as e:
            print(f"Error processing customer debt: {e}")
            self.connection.rollback()  # Rollback in case of error
            return False

        finally:
            self.close_connection()



    def find_customers(self, text):
        try:
            self.init()
            cursor = self.connection.cursor()
            if text == "":
                query = 'SELECT name, contact, remained, id FROM customers ORDER BY name'
                cursor.execute(query)
                data = cursor.fetchall()
                return data
            else:
                query = f"SELECT name, contact, remained, id FROM customers WHERE name like '%{text}%' or contact like '%{text}%' order by name"
                cursor.execute(query)
                data = cursor.fetchall()
                return data
        except Error as e:
            print(f"Error while processing customer debt: {e}")

        finally:
            self.close_connection()

    def find_customer(self, text):
        try:
            self.init()
            cursor = self.connection.cursor()
            cursor.execute('SELECT name, contact FROM customers WHERE id = %s', (text,))
            data = cursor.fetchone()
            return data
        except Error as e:
            print(f"Error while processing customer debt: {e}")

        finally:
            self.close_connection()


    def payback(self, customer_id, amount, comment):
        try:
            self.init()
            cursor = self.connection.cursor()

            cursor.execute("SELECT payed, remained FROM customers WHERE id = %s", (customer_id,))
            data = cursor.fetchone()

            if data is None:
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
            return True
        except Error as e:
            print(f"Error: {e}")
            return False
        finally:
            self.close_connection()

    def get_comment1(self, amount, date):
        try:
            self.init()
            cursor = self.connection.cursor()
            cursor.execute('SELECT comment FROM debts WHERE amount = %s and date_issued = %s', (amount, date))
            data = cursor.fetchone()
            return data
        except Error as e:
            print(f"Error while processing customer debt: {e}") 
        finally:
            self.close_connection()    

    def get_comment2(self, amount, date):
        try:
            self.init()
            cursor = self.connection.cursor()
            cursor.execute('SELECT comment FROM payments WHERE amount = %s and date_issued = %s', (amount, date))
            data = cursor.fetchone()
            return data
        except Error as e:
            print(f"Error while processing customer debt: {e}") 
        finally:
            self.close_connection() 

    def history(self, customer_id):
        try:
            self.init()
            cursor = self.connection.cursor()
            cursor.execute('SELECT name, contact, remained, payed, total FROM customers WHERE id = %s', (customer_id,))
            temp1 = cursor.fetchone()
            data = {
                "person" : {
                    'name' : temp1[0], 
                    'contact' : temp1[1], 
                    'remained' : temp1[2], 
                    'total' : temp1[4], 
                    'payed' : temp1[3]
                    }
            }
            cursor.execute("SELECT amount, date_issued FROM debts WHERE customer_id = %s ORDER BY date_issued desc", (customer_id,))

            temp2 = cursor.fetchall()

            data['debts'] = temp2

            cursor.execute("SELECT amount, date_issued FROM payments WHERE customer_id = %s ORDER BY date_issued desc", (customer_id,))

            temp3 = cursor.fetchall()

            data['payments'] = temp3
            return data
        except Error as e:
            print(f"Error while processing customer debt: {e}") 
        finally:
            self.close_connection()
    
    def get_finance_data(self):
        try:
            self.init()
            cursor = self.connection.cursor()
            cursor.execute('SELECT amount, date_issued FROM debts')
            temp = cursor.fetchall()
            data = {
                'debts' : temp
            }
            cursor.execute('SELECT amount, date_issued FROM payments')
            temp = cursor.fetchall()
            data['payed'] = temp
            return data
        except Error as e:
            print(f"Error while processing customer debt: {e}") 
        finally:
            self.close_connection()

    def fetch_data(self, date_type, date_value):
        cursor = None
        try:
            cursor = self.connection.cursor(dictionary=True)
            print(f"Fetching data for date_type: {date_type} and date_value: {date_value}")
            if date_type == 'по годам':
                query = """
                SELECT
                    SUM(d.amount) AS total_debts,
                    COALESCE(SUM(p.amount), 0) AS total_payments
                FROM debts d
                LEFT JOIN payments p ON d.customer_id = p.customer_id AND YEAR(d.date_issued) = YEAR(p.date_issued)
                WHERE YEAR(d.date_issued) = %s
                """
                cursor.execute(query, (date_value,))
            elif date_type == 'по месяцам':
                query = """
                SELECT
                    SUM(d.amount) AS total_debts,
                    COALESCE(SUM(p.amount), 0) AS total_payments
                FROM debts d
                LEFT JOIN payments p ON d.customer_id = p.customer_id AND YEAR(d.date_issued) = YEAR(p.date_issued) AND MONTH(d.date_issued) = MONTH(p.date_issued)
                WHERE YEAR(d.date_issued) = %s AND MONTH(d.date_issued) = %s
                """
                year, month = date_value.split('/')
                cursor.execute(query, (year, month))
            elif date_type == 'по неделям':
                start_date, end_date = date_value.split(' - ')
                query = """
                SELECT
                    DATE(d.date_issued) AS date,
                    SUM(d.amount) AS total_debts,
                    COALESCE(SUM(p.amount), 0) AS total_payments
                FROM debts d
                LEFT JOIN payments p ON d.customer_id = p.customer_id AND DATE(d.date_issued) = DATE(p.date_issued)
                WHERE DATE(d.date_issued) BETWEEN %s AND %s
                GROUP BY DATE(d.date_issued)
                """
                cursor.execute(query, (start_date, end_date))
            elif date_type == 'за все время':
                query = """
                SELECT
                    SUM(d.amount) AS total_debts,
                    COALESCE(SUM(p.amount), 0) AS total_payments
                FROM debts d
                LEFT JOIN payments p ON d.customer_id = p.customer_id
                """
                cursor.execute(query)

            data = cursor.fetchall()
            print(f"Data fetched: {data}")
            return data
        except Error as e:
            print(f"Error while fetching data: {e}")
            return []
        finally:
            if cursor:
                cursor.close()
            self.close_connection()

