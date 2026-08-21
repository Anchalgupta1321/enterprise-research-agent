import os
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
import json

class VectorStore:
    def __init__(self, index_path="research_index.faiss", meta_path="research_meta.json"):
        self.index_path = index_path
        self.meta_path = meta_path
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        self.embedding_dim = self.model.get_sentence_embedding_dimension()
        
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
        
        embeddings = self.model.encode(texts)
        # Convert to float32 for FAISS
        embeddings = np.array(embeddings).astype("float32")
        
        self.index.add(embeddings)
        self.metadata.extend(metadatas)
        
        # Save to disk
        faiss.write_index(self.index, self.index_path)
        with open(self.meta_path, "w") as f:
            json.dump(self.metadata, f)

    def similarity_search(self, query: str, k: int = 5):
        if self.index.ntotal == 0:
            return []
            
        query_embedding = self.model.encode([query])
        query_embedding = np.array(query_embedding).astype("float32")
        
        distances, indices = self.index.search(query_embedding, k)
        
        results = []
        for i, idx in enumerate(indices[0]):
            if idx != -1 and idx < len(self.metadata): # -1 means not enough results
                results.append({
                    "metadata": self.metadata[idx],
                    "distance": float(distances[0][i])
                })
        return results

# Singleton instance
vector_store = VectorStore()
