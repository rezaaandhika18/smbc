import psycopg2 # type: ignore
import random
import uuid

conn = psycopg2.connect(host="localhost", database="source_db", user="postgres", password="admin123")
cur = conn.cursor()

names = ["Alice", "Bob", "Charlie", "David"]
emails = ["a@example.com", "b@example.com", "c@example.com", "d@example.com"]

# Insert new customer
def insert_customer():
    name = random.choice(names)
    email = random.choice(emails)
    cur.execute("INSERT INTO customers (id, name, email) VALUES (%s, %s, %s)", 
                (str(uuid.uuid4()), name, email))

# Update a customer's name/email
def update_customer():
    cur.execute("SELECT id FROM customers ORDER BY random() LIMIT 1")
    result = cur.fetchone()
    if result:
        new_name = random.choice(names)
        new_email = random.choice(emails)
        cur.execute("UPDATE customers SET name=%s, email=%s WHERE id=%s", 
                    (new_name, new_email, result[0]))

# Delete a customer
def delete_customer():
    cur.execute("SELECT id FROM customers ORDER BY random() LIMIT 1")
    result = cur.fetchone()
    if result:
        cur.execute("DELETE FROM customers WHERE id=%s", (result[0],))

# Randomly perform one of the actions
action = random.choice([insert_customer, update_customer, delete_customer])
action()
conn.commit()
cur.close()
conn.close()