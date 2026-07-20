"""
export_to_sqlite.py
Exporta todas las tablas de DB_Finanzasdb (PostgreSQL) a un archivo SQLite.
Ejecutar UNA sola vez localmente antes de hacer git push.
"""
import pg8000
import sqlite3
import pandas as pd
import os

# ── Config PostgreSQL ──────────────────────────────────────────────────────────
PG = dict(user="postgres", host="localhost", port=5432,
          database="DB_Finanzasdb", password="sorel")

TABLES = ["clientes", "productos", "carteras", "transacciones"]

os.makedirs("data", exist_ok=True)
sqlite_path = os.path.join("data", "finanzas.db")

pg_conn = pg8000.connect(**PG)
sq_conn = sqlite3.connect(sqlite_path)

print(f"Exportando a: {sqlite_path}")

for table in TABLES:
    cur = pg_conn.cursor()
    cur.execute(f'SELECT * FROM "{table}"')
    cols = [d[0] for d in cur.description]
    rows = cur.fetchall()
    df   = pd.DataFrame(rows, columns=cols)

    # Convertir fechas a string ISO para SQLite
    for col in df.columns:
        if hasattr(df[col].dtype, 'name') and 'date' in str(df[col].dtype).lower():
            df[col] = df[col].astype(str)
        try:
            df[col] = pd.to_numeric(df[col])
        except (ValueError, TypeError):
            pass

    df.to_sql(table, sq_conn, if_exists="replace", index=False)
    print(f"  OK {table}: {len(df)} filas")

pg_conn.close()
sq_conn.close()
print("\nSQLite listo. Archivo: data/finanzas.db")
