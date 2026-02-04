import sqlite3

def dump_schema():
    conn = sqlite3.connect('nvs_portal.db')
    cursor = conn.cursor()
    cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='invoices';")
    schema = cursor.fetchone()
    with open('schema.txt', 'w') as f:
        if schema:
            f.write(schema[0])
        else:
            f.write("Table 'invoices' not found.")
    conn.close()

if __name__ == "__main__":
    dump_schema()
