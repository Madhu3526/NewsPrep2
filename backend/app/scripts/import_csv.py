import csv
from datetime import datetime
from backend.app.db.session import SessionLocal
from backend.app.db.models.article import Article

CSV_PATH = r"backend\app\ml\data\topic_corpus\ag_bbc_india_with_topics.csv"

def parse_date(date_str):
    """Converts date string -> datetime or None"""
    if not date_str or date_str.strip() == "":
        return None
    try:
        return datetime.fromisoformat(date_str)
    except:
        # try YYYY-MM-DD or other formats
        try:
            return datetime.strptime(date_str, "%Y-%m-%d")
        except:
            return None

def import_csv_to_db(path=CSV_PATH):
    db = SessionLocal()

    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        count = 0
        for row in reader:
            art = Article(
                title=row.get("title"),
                text=row.get("text"),
                published_date=parse_date(row.get("published")),
                topic_id=int(row.get("bertopic_topic")) if row.get("bertopic_topic") else None
            )
            db.add(art)
            count += 1

        db.commit()
        db.close()

    print(f"Imported {count} rows from CSV into DB")

if __name__ == "__main__":
    import_csv_to_db()
