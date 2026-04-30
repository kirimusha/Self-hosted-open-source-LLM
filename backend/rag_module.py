import os
import hashlib
from typing import List, Tuple
from sentence_transformers import SentenceTransformer
import chromadb
import PyPDF2
from docx import Document as DocxDocument
from pathlib import Path

class RAGModule:
    def __init__(self, chroma_path: str = "/chroma_db", knowledge_base_path: str = "/knowledge_base"):
        self.chroma_path = chroma_path
        self.knowledge_base_path = knowledge_base_path
        
        print("Loading embedding model")
        self.embedding_model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
        
        print("Connecting to Chroma")
        self.chroma_client = chromadb.PersistentClient(path=chroma_path)
        
        self.collection_name = "knowledge_base"
        self.collection = self._get_or_create_collection()
        
    def _get_or_create_collection(self):
        try:
            return self.chroma_client.get_collection(self.collection_name)
        except:
            return self.chroma_client.create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )
    
    def _get_embedding(self, text: str) -> List[float]:
        return self.embedding_model.encode(text).tolist()
    
    def split_text_into_chunks(self, text: str, chunk_size: int = 800, overlap: int = 150) -> List[str]:
        words = text.split()
        chunks = []
        for i in range(0, len(words), chunk_size - overlap):
            chunk = ' '.join(words[i:i + chunk_size])
            if chunk.strip():
                chunks.append(chunk)
        return chunks
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        text = ""
        try:
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                for page in reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        except Exception as e:
            print(f"Error reading PDF {pdf_path}: {e}")
        return text
    
    def extract_text_from_docx(self, docx_path: str) -> str:
        try:
            doc = DocxDocument(docx_path)
            return "\n".join([p.text for p in doc.paragraphs if p.text])
        except Exception as e:
            print(f"Error reading DOCX {docx_path}: {e}")
            return ""
    
    def index_document(self, file_path: str, source_name: str = None) -> int:
        file_path = Path(file_path)
        source_name = source_name or file_path.name
        
        print(f"Indexing: {source_name}")
        
        if file_path.suffix.lower() == '.pdf':
            text = self.extract_text_from_pdf(str(file_path))
        elif file_path.suffix.lower() in ['.docx', '.doc']:
            text = self.extract_text_from_docx(str(file_path))
        elif file_path.suffix.lower() in ['.txt', '.md']:
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
        else:
            return 0
        
        if not text.strip():
            return 0
        
        chunks = self.split_text_into_chunks(text)
        
        for i, chunk in enumerate(chunks):
            chunk_id = hashlib.md5(f"{source_name}_{i}".encode()).hexdigest()
            
            existing = self.collection.get(ids=[chunk_id])
            if not existing['ids']:
                embedding = self._get_embedding(chunk)
                self.collection.add(
                    ids=[chunk_id],
                    embeddings=[embedding],
                    documents=[chunk],
                    metadatas=[{
                        "source": source_name,
                        "chunk_index": i,
                        "total_chunks": len(chunks)
                    }]
                )
        
        return len(chunks)
    
    def search(self, query: str, n_results: int = 5) -> Tuple[List[str], List[dict]]:
        query_embedding = self._get_embedding(query)
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results
        )
        return results['documents'][0], results['metadatas'][0]
    
    def build_prompt(self, query: str, documents: List[str]) -> str:
        context = "\n\n---\n\n".join(documents[:3])
        
        if len(context) > 3000:
            context = context[:3000] + "..."
        
        return f"""Ты — эксперт по управлению проектами. Составь иерархическую структуру работ (ИСР).

                    Цель проекта: {query}

                    Нормативные требования:
                    {context}

                    Формат ответа:
                    1. Название этапа
                    - Комментарий: ...
                    1.1. Подэтап
                            - Комментарий: ...

                    ИСР:"""

rag_instance = None

def get_rag():
    global rag_instance
    if rag_instance is None:
        rag_instance = RAGModule()
    return rag_instance

async def generate_wbs(goal: str) -> Tuple[str, List[str]]:
    rag = get_rag()
    documents, metadatas = rag.search(goal, n_results=5)
    prompt = rag.build_prompt(goal, documents)
    sources = list(set([m.get('source', 'unknown') for m in metadatas]))
    return prompt, sources