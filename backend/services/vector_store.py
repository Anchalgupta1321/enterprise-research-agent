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
        
        # Cloud-native Gemini embeddings
        try:
            self.embeddings = GoogleGenerativeAIEmbeddings(
                model="models/gemini-embedding-001", 
                google_api_key=settings.GEMINI_API_KEY
            )
        except Exception as e:
            print(f"Warning: Could not initialize GoogleGenerativeAIEmbeddings ({e})")
            self.embeddings = None
            
        self.embedding_dim = 3072 # gemini-embedding-001 dimension
        
        # Load or create FAISS index
        if os.path.exists(self.index_path):
            try:
                self.index = faiss.read_index(self.index_path)
                with open(self.meta_path, "r") as f:
                    self.metadata = json.load(f)
                if self.index.d != self.embedding_dim:
                    print(f"Index dimension mismatch ({self.index.d} vs {self.embedding_dim}). Resetting index.")
                    self.index = faiss.IndexFlatL2(self.embedding_dim)
                    self.metadata = []
            except Exception as e:
                print(f"Failed to load FAISS index ({e}). Creating new index.")
                self.index = faiss.IndexFlatL2(self.embedding_dim)
                self.metadata = []
        else:
            self.index = faiss.IndexFlatL2(self.embedding_dim)
            self.metadata = []

    def add_texts(self, texts: list[str], metadatas: list[dict]):
        if not texts or self.embeddings is None:
            return
        
        try:
            # LangChain embeddings interface
            embeddings_list = self.embeddings.embed_documents(texts)
            embeddings_array = np.array(embeddings_list).astype("float32")
            
            # Dimension guard
            dim = embeddings_array.shape[1]
            if self.index.d != dim:
                self.index = faiss.IndexFlatL2(dim)
                self.metadata = []
            
            self.index.add(embeddings_array)
            self.metadata.extend(metadatas)
            
            # Save to disk
            faiss.write_index(self.index, self.index_path)
            with open(self.meta_path, "w") as f:
                json.dump(self.metadata, f)
        except Exception as e:
            print(f"Warning: Vector embedding failed ({e}). Proceeding without vector index update.")

    def similarity_search(self, query: str, k: int = 5):
        if self.index.ntotal == 0 or self.embeddings is None:
            return []
            
        try:
            query_embedding = self.embeddings.embed_query(query)
            query_embedding_array = np.array([query_embedding]).astype("float32")
            
            if self.index.d != query_embedding_array.shape[1]:
                return []

            distances, indices = self.index.search(query_embedding_array, k)
            
            results = []
            for i, idx in enumerate(indices[0]):
                if idx != -1 and idx < len(self.metadata):
                    results.append({
                        "metadata": self.metadata[idx],
                        "distance": float(distances[0][i])
                    })
            return results
        except Exception as e:
            print(f"Warning: Similarity search failed ({e})")
            return []

# Singleton instance
vector_store = VectorStore()
