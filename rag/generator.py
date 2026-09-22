import os
from urllib import response

from groq import Groq

from .vector_store import VectorStore
from chromadb import Collection
from settings import settings

class GroundedGenerator:
    def __init__(self, vector_store: VectorStore):
        self.vector_store = vector_store
        self.groq_client = Groq(api_key=settings.groq_api_key, max_retries=3)
        self.THRESHOLD = 0.3
        self.MOCK_LLM = settings.mock_llm
        self.SYSTEM_PROMPT = settings.system_prompt
        
    def generate(self, query: str, collection: Collection, top_k: int = 5) -> str:
        # Step 1: Search the vector store for relevant chunks
        results = self.vector_store.search(collection, query, top_k=top_k)
        
        # Step 2: Check if the top result meets the threshold
        top_distance = results['distances'][0][0]
        similarity = 1 - top_distance
        
        if similarity < self.THRESHOLD:
            return "I don't know based on the available knowledge base."
        
        # Step 3: Retrieve the context from the top k results , only if they are above the threshold
        contexts = []
        for i in range(len(results["distances"][0])):
            if 1 - results["distances"][0][i] >= self.THRESHOLD:
                contexts.append(results["documents"][0][i])
        context = " ".join(contexts)
        
        # Step 4: Generate a response using the context
        if self.MOCK_LLM:
            response = self.mock_llm_response(query, context)
        else:
            response = self.groq_llm_response(query, context)
        
        return response
    
    def mock_llm_response(self, query: str, context: str) -> str:
        # This is a mock function to simulate an LLM response.
        # In a real implementation, you would call an actual LLM API here.
        return f"{context}."
    
    def groq_llm_response(self, query: str, context: str) -> str:
        user_prompt = f"""
            Context:
            {context}

            Question:
            {query}
        """
        response = self.groq_client.chat.completions.create(
                model=settings.groq_model,
                messages=[
                    {
                        "role": "system",
                        "content": self.SYSTEM_PROMPT
                },
                {
                    "role": "user",
                    "content": user_prompt
                }
            ],
            temperature=0
        )

        return response.choices[0].message.content
        
    
    
if __name__ == "__main__":
    from .embeddings import EmbeddingModel
    from .loader import load_documents
    from .chunking import fixed_size_chunks
    
    # Initialize embedding model and vector store
    embedding_model = EmbeddingModel()
    vector_store = VectorStore(embedding_model)
    
    # Load documents and create chunks
    documents = load_documents("knowledge_base")
    chunks = fixed_size_chunks(documents)
    
    # Create a collection and add chunks to it
    collection = vector_store.create_collection("test_collection")
    vector_store.add_chunks(collection, chunks)
    
    # Initialize the grounded generator
    grounded_generator = GroundedGenerator(vector_store)
    
    # Example query
    query = "Who is eligible for remote work?"
    response = grounded_generator.generate(query, collection, top_k=3)
    
    print(f"Query: {query}")
    print(f"Response: {response}")