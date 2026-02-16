import psycopg2

conn = psycopg2.connect(
    host="localhost",
    port="5432",
    database="it_resource_manager",
    user="postgres",
    password="your_password"
)
print("✓ Connected!")
conn.close()
