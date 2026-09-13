from dotenv import load_dotenv

load_dotenv()

from sentence_transformers import SentenceTransformer
import numpy as np

class EmbeddingModel:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)

    def embed_text(self, text: str) -> np.ndarray:
        return self.model.encode(text)
    
    def embed_texts(self, texts: list[str]) -> np.ndarray:
        return self.model.encode(texts)
    
    
if __name__ == "__main__":
    # Testing multiple embeddings
    model = EmbeddingModel()
    texts = ["Hello world", "How are you?", "This is a test."]
    embeddings = model.embed_texts(texts)
    for text, emb in zip(texts, embeddings):
        print(f"Text: {text}, Embedding shape: {emb.shape}")
        print(f"Embedding: {emb}\n")
        
    print(embeddings.shape)  # (number of texts, embedding dimensions)