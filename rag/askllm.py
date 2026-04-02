import time
import pandas as pd
from pinecone import Pinecone, ServerlessSpec
from google import genai
from sentence_transformers import SentenceTransformer

PINECONE_API_KEY = "pcsk_3zG8k6_F9Q824EV3ahjnmYYYB15npzJX3WwXUd8jYxpGCUV2mBsDasqAT2vfDHhu3Mny63"
GEMINI_API_KEY = "AIzaSyBJgHlaXhAmzRtPOj26fk739bfmsxEQP08"

gemini_client = genai.Client(api_key=GEMINI_API_KEY)

local_embed_model = SentenceTransformer('all-MiniLM-L6-v2')
pc = Pinecone(api_key=PINECONE_API_KEY)

index_name = "restaurant-index-10"
index = pc.Index(index_name)

def ask_question(question):
    print(f"\nQuestion: {question}")
    
    # A. Generate the query vector LOCALLY
    query_vector = local_embed_model.encode(question).tolist()

    # B. Search Pinecone
    search_results = index.query(
        vector=query_vector,
        top_k=3,
        include_metadata=True
    )

    # C. Extract Context
    retrieved_texts = [match['metadata']['text'] for match in search_results['matches']]
    context = "\n---\n".join(retrieved_texts)
    
    # D. Send context to Gemini for the human-like answer
    prompt = f"""
    Use the following restaurant data to answer the question.
    
    Context:
    {context}
    
    Question: {question}
    """
    
    response = gemini_client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt
    )
    
    print("\nAnswer from Gemini:")
    print(response.text)

if __name__ == "__main__":
    ask_question("Find me a highly rated restaurant near yishun and give me the address.")