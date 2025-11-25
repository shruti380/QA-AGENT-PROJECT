"""
Vector Store for document retrieval - Cloud-friendly version using scikit-learn
"""
import os
import json
import pickle
from typing import List, Dict, Any, Optional
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer


class VectorStore:
    """Scikit-learn based vector store for semantic search (cloud-compatible)"""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2", index_path: str = "vector_db"):
        """
        Initialize vector store
        
        Args:
            model_name: Sentence transformer model name
            index_path: Directory to store index
        """
        self.model_name = model_name
        self.index_path = index_path
        self.embedding_model = SentenceTransformer(model_name)
        self.dimension = self.embedding_model.get_sentence_embedding_dimension()
        
        # Initialize storage
        self.embeddings = None  # numpy array of embeddings
        self.metadata_store = []  # Store metadata for each vector
        self.documents = []  # Store original document content
        
        # Create index directory if it doesn't exist
        os.makedirs(index_path, exist_ok=True)
    
    def _create_index(self):
        """Create new index"""
        self.embeddings = None
        self.metadata_store = []
        self.documents = []
    
    def add_documents(self, documents: List[Dict[str, Any]]) -> None:
        """
        Add documents to vector store
        
        Args:
            documents: List of document dictionaries with 'content' and 'metadata'
        """
        if not documents:
            return
        
        # Extract content from documents
        texts = [doc['content'] for doc in documents]
        
        # Generate embeddings
        print(f"Generating embeddings for {len(texts)} documents...")
        new_embeddings = self.embedding_model.encode(
            texts,
            show_progress_bar=True,
            convert_to_numpy=True
        )
        
        # Add to existing embeddings or create new
        if self.embeddings is None:
            self.embeddings = new_embeddings.astype('float32')
        else:
            self.embeddings = np.vstack([self.embeddings, new_embeddings.astype('float32')])
        
        # Store metadata and documents
        for doc in documents:
            self.metadata_store.append(doc.get('metadata', {}))
            self.documents.append(doc['content'])
        
        print(f"Added {len(documents)} documents to vector store")
        print(f"Total documents in store: {len(self.documents)}")
    
    def similarity_search(
        self, 
        query: str, 
        k: int = 5,
        score_threshold: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar documents using cosine similarity
        
        Args:
            query: Search query
            k: Number of results to return
            score_threshold: Minimum similarity score (0-1, higher is better)
            
        Returns:
            List of documents with metadata and similarity scores
        """
        if self.embeddings is None or len(self.embeddings) == 0:
            return []
        
        # Ensure k doesn't exceed available documents
        k = min(k, len(self.documents))
        
        # Generate query embedding
        query_embedding = self.embedding_model.encode([query], convert_to_numpy=True)
        
        # Calculate cosine similarity
        similarities = cosine_similarity(query_embedding, self.embeddings)[0]
        
        # Get top k indices (sorted by similarity, highest first)
        top_k_indices = np.argsort(similarities)[::-1][:k]
        
        # Prepare results
        results = []
        for rank, idx in enumerate(top_k_indices):
            similarity_score = float(similarities[idx])
            
            # Skip if score threshold is set and not met
            if score_threshold is not None and similarity_score < score_threshold:
                continue
            
            result = {
                'content': self.documents[idx],
                'metadata': self.metadata_store[idx],
                'similarity_score': similarity_score,
                'rank': rank + 1
            }
            results.append(result)
        
        return results
    
    @property
    def ntotal(self):
        """Get total number of documents (for compatibility with FAISS API)"""
        return len(self.documents) if self.documents else 0
    
    def save(self) -> None:
        """Save index and metadata to disk"""
        if self.embeddings is None or len(self.embeddings) == 0:
            print("No index to save")
            return
        
        # Save embeddings
        embeddings_file = os.path.join(self.index_path, "embeddings.npy")
        np.save(embeddings_file, self.embeddings)
        
        # Save metadata and documents (maintaining compatibility with FAISS version)
        metadata_file = os.path.join(self.index_path, "metadata.pkl")
        with open(metadata_file, 'wb') as f:
            pickle.dump({
                'metadata_store': self.metadata_store,
                'documents': self.documents,
                'model_name': self.model_name,
                'dimension': self.dimension
            }, f)
        
        print(f"Saved vector store to {self.index_path}")
    
    def load(self) -> bool:
        """
        Load index and metadata from disk
        
        Returns:
            True if successful, False otherwise
        """
        embeddings_file = os.path.join(self.index_path, "embeddings.npy")
        metadata_file = os.path.join(self.index_path, "metadata.pkl")
        
        # Also check for old FAISS format files
        old_faiss_file = os.path.join(self.index_path, "faiss_index.bin")
        
        if os.path.exists(old_faiss_file) and not os.path.exists(embeddings_file):
            print("Warning: Old FAISS index detected. Please rebuild knowledge base.")
            return False
        
        if not os.path.exists(embeddings_file) or not os.path.exists(metadata_file):
            print("No saved index found")
            return False
        
        try:
            # Load embeddings
            self.embeddings = np.load(embeddings_file)
            
            # Load metadata and documents
            with open(metadata_file, 'rb') as f:
                data = pickle.load(f)
                self.metadata_store = data['metadata_store']
                self.documents = data['documents']
                saved_model = data.get('model_name', self.model_name)
                
                # Warn if model changed
                if saved_model != self.model_name:
                    print(f"Warning: Loaded index uses model {saved_model}, but current model is {self.model_name}")
            
            print(f"Loaded vector store with {len(self.documents)} documents")
            return True
            
        except Exception as e:
            print(f"Error loading index: {str(e)}")
            return False
    
    def clear(self) -> None:
        """Clear the vector store"""
        self._create_index()
        print("Vector store cleared")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the vector store
        
        Returns:
            Dictionary with statistics
        """
        if self.embeddings is None:
            return {
                'total_documents': 0,
                'dimension': self.dimension,
                'model_name': self.model_name,
                'is_empty': True
            }
        
        # Count documents by source
        sources = {}
        for metadata in self.metadata_store:
            source = metadata.get('source', 'unknown')
            sources[source] = sources.get(source, 0) + 1
        
        return {
            'total_documents': len(self.documents),
            'dimension': self.dimension,
            'model_name': self.model_name,
            'is_empty': len(self.documents) == 0,
            'sources': sources
        }


def test_vector_store():
    """Test vector store functionality"""
    print("Testing Vector Store...")
    
    # Create vector store
    vs = VectorStore(index_path="test_vector_db")
    
    # Sample documents
    sample_docs = [
        {
            'content': 'Python is a high-level programming language.',
            'metadata': {'source': 'python_doc.txt', 'topic': 'programming'}
        },
        {
            'content': 'Machine learning is a subset of artificial intelligence.',
            'metadata': {'source': 'ml_doc.txt', 'topic': 'AI'}
        },
        {
            'content': 'Scikit-learn is a library for efficient similarity search.',
            'metadata': {'source': 'sklearn_doc.txt', 'topic': 'search'}
        }
    ]
    
    # Add documents
    vs.add_documents(sample_docs)
    
    # Search
    print("\nSearching for: 'programming language'")
    results = vs.similarity_search('programming language', k=2)
    for result in results:
        print(f"  - {result['content'][:50]}... (score: {result['similarity_score']:.4f})")
    
    # Save
    vs.save()
    
    # Load
    vs2 = VectorStore(index_path="test_vector_db")
    loaded = vs2.load()
    print(f"\nLoaded: {loaded}")
    
    # Get stats
    stats = vs2.get_stats()
    print(f"\nStats: {json.dumps(stats, indent=2)}")


if __name__ == "__main__":
    test_vector_store()