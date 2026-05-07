import pyodbc
from app_config import get_sql_connection_string

conn_str = get_sql_connection_string()
conn = pyodbc.connect(conn_str)
cursor = conn.cursor()

sql_find_constraint = """
SELECT tc.CONSTRAINT_NAME
FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS tc
JOIN INFORMATION_SCHEMA.CONSTRAINT_COLUMN_USAGE ccu 
  ON tc.CONSTRAINT_NAME = ccu.CONSTRAINT_NAME
WHERE tc.TABLE_NAME = 'Client' 
  AND ccu.COLUMN_NAME = 'phone' 
  AND tc.CONSTRAINT_TYPE = 'UNIQUE'
"""

cursor.execute(sql_find_constraint)
row = cursor.fetchone()

if row:
    constraint_name = row[0]
    print(f'Found constraint: {constraint_name}')
    sql_drop = f'ALTER TABLE Client DROP CONSTRAINT {constraint_name}'
    cursor.execute(sql_drop)
    conn.commit()
    print('Constraint dropped successfully.')
else:
    print('No UNIQUE constraint found on Client.phone.')
