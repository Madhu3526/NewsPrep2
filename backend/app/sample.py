from backend.app.db.session import SessionLocal
from backend.app.db.models.article import Article

db = SessionLocal()

sample = Article(
    title="Test Article 1",
    text="This is a test news article",
    topic_id=0  # Assign to existing topic or use -1 for unclassified
)

db.add(sample)
db.commit()
db.close()

print("Sample article inserted with topic assignment!")
