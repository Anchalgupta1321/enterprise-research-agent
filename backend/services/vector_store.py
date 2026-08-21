import os
import faiss
import numpy as np
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from backend.core.config import settings
import json

class VectorStore:
    def __init__(self, index_path="research_index.faiss", meta_path="research_meta.json"):
        self.index_path = index_path
        self.meta_path = meta_path
        
        # We switched to Google Embeddings because HuggingFace/Torch uses too much RAM (2GB+)
        # and crashes the 512MB free tier on Render. Google Embeddings run entirely in the cloud!
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model="models/embedding-001", 
            google_api_key=settings.GEMINI_API_KEY
        )
        self.embedding_dim = 768 # Google embeddings are 768 dimensions
        
        # Load or create FAISS index
        if os.path.exists(self.index_path):
            self.index = faiss.read_index(self.index_path)
            with open(self.meta_path, "r") as f:
                self.metadata = json.load(f)
        else:
            self.index = faiss.IndexFlatL2(self.embedding_dim)
            self.metadata = []

    def add_texts(self, texts: list[str], metadatas: list[dict]):
        if not texts:
            return
        
        # LangChain embeddings interface
        embeddings_list = self.embeddings.embed_documents(texts)
        # Convert to float32 for FAISS
        embeddings_array = np.array(embeddings_list).astype("float32")
        
        self.index.add(embeddings_array)
        self.metadata.extend(metadatas)
        
        # Save to disk
        faiss.write_index(self.index, self.index_path)
        with open(self.meta_path, "w") as f:
            json.dump(self.metadata, f)

    def similarity_search(self, query: str, k: int = 5):
        if self.index.ntotal == 0:
            return []
            
        query_embedding = self.embeddings.embed_query(query)
        query_embedding_array = np.array([query_embedding]).astype("float32")
        
        distances, indices = self.index.search(query_embedding_array, k)
        
        results = []
        for i, idx in enumerate(indices[0]):
            if idx != -1 and idx < len(self.metadata):
                results.append({
                    "metadata": self.metadata[idx],
                    "distance": float(distances[0][i])
                })
        return results

# Singleton instance
vector_store = VectorStore()
