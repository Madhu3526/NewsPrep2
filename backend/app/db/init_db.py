from backend.app.db.session import engine, Base


def _ensure_column(conn, table: str, column: str, ddl: str):
    """Ensure a column exists on a sqlite table, otherwise add it using the given DDL."""
    # SQLAlchemy 2.x: use exec_driver_sql for driver-specific statements like PRAGMA/ALTER
    try:
        res = conn.exec_driver_sql(f"PRAGMA table_info('{table}')")
        cols = [r[1] for r in res.fetchall()]
    except Exception:
        # If we cannot introspect, assume column missing to be safe
        cols = []

    if column not in cols:
        print(f"Adding missing column '{column}' to '{table}'")
        try:
            conn.exec_driver_sql(ddl)
        except Exception as e:
            # bubble up so caller can log
            raise


def init_db():
    print("Creating tables...")
    Base.metadata.create_all(bind=engine)

    # SQLite: add missing columns if the models evolved
    with engine.connect() as conn:
        try:
            _ensure_column(conn, 'articles', 'summary', "ALTER TABLE articles ADD COLUMN summary TEXT")
            # store key_points as JSON text
            _ensure_column(conn, 'articles', 'key_points', "ALTER TABLE articles ADD COLUMN key_points TEXT")
        except Exception as e:
            # Non-fatal: log and continue
            print("Warning: could not ensure schema columns:", e)

    print("DB initialized.")
