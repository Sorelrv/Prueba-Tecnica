import pg8000.native as pg

conn = pg.Connection(
    user='postgres',
    host='localhost',
    port=5432,
    database='DB_Finanzasdb',
    password='sorel'
)
print('Conectado a DB_Finanzasdb!')

# Listar tablas
tables = conn.run("""
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema = 'public' 
    ORDER BY table_name
""")
print('=== TABLAS ===')
for t in tables:
    print(t[0])

# Columnas de cada tabla
for t in tables:
    table_name = t[0]
    cols = conn.run("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_schema = 'public' AND table_name = :tname
        ORDER BY ordinal_position
    """, tname=table_name)
    print(f'\n=== {table_name} ===')
    for col in cols:
        print(f'  {col[0]} ({col[1]})')

# Muestra de datos de cada tabla
print('\n\n=== MUESTRA DE DATOS ===')
for t in tables:
    table_name = t[0]
    rows = conn.run(f'SELECT * FROM "{table_name}" LIMIT 3')
    print(f'\n--- {table_name} (primeras 3 filas) ---')
    for row in rows:
        print(row)

conn.close()
