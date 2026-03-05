from app.rag.document_loader import DocumentLoader
from app.config import settings

loader = DocumentLoader(settings.json_directory)
docs = loader.load_all()
print(f"Toplam döküman: {len(docs)}")

# İlk 5 dökümanın boyutuna bak
for doc in docs[:5]:
    print(f"Madde={doc.metadata.get('article_number','')} | {len(doc.page_content)} chars | title={doc.metadata.get('title','')[:40]}")