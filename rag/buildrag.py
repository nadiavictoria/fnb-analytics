import time
import pandas as pd
from pinecone import Pinecone, ServerlessSpec
from google import genai
from sentence_transformers import SentenceTransformer

# ==========================================
# 1. SETUP & AUTHENTICATION
# ==========================================
PINECONE_API_KEY = "pcsk_3zG8k6_F9Q824EV3ahjnmYYYB15npzJX3WwXUd8jYxpGCUV2mBsDasqAT2vfDHhu3Mny63"
GEMINI_API_KEY = "AIzaSyBJgHlaXhAmzRtPOj26fk739bfmsxEQP08"

gemini_client = genai.Client(api_key=GEMINI_API_KEY)

# NEW: Initialize the Local Embedding Model
local_embed_model = SentenceTransformer('all-MiniLM-L6-v2')
pc = Pinecone(api_key=PINECONE_API_KEY)

index_name = "restaurant-index-10"

if index_name not in pc.list_indexes().names():
    print(f"Creating Pinecone index '{index_name}' with 384 dimensions...")
    pc.create_index(
        name=index_name,
        dimension=384, # The dimension for 'all-MiniLM-L6-v2'
        metric="cosine",
        spec=ServerlessSpec(cloud="aws", region="us-east-1")
    )
    time.sleep(10)

index = pc.Index(index_name)

# ==========================================
# 2. VECTORIZE AND UPLOAD
# ==========================================
def process_csv_and_upload(csv_path):
    print(f"Reading {csv_path} and generating local embeddings...")
    df = pd.read_csv(csv_path)
    
    batch_size = 10 
    for i in range(0, len(df), batch_size):
        print(f"Processing batch {i} to {i + batch_size}...")
        batch_df = df.iloc[i : i + batch_size]
        
        texts_to_embed = []
        ids_for_pinecone = []
        
        for row_idx, row in batch_df.iterrows():
            row_dict = row.dropna().to_dict()
            text_content = ", ".join([f"{key}: {value}" for key, value in row_dict.items()])
            text_content = text_content.encode('ascii', 'ignore').decode('ascii')
            
            texts_to_embed.append(text_content)
            ids_for_pinecone.append(f"doc_{row_idx}")
            
        # encode() returns a list of vectors
        embeddings = local_embed_model.encode(texts_to_embed).tolist()
        
        vectors = []
        for j in range(len(texts_to_embed)):
            vectors.append({
                "id": ids_for_pinecone[j], 
                "values": embeddings[j], 
                "metadata": {"text": texts_to_embed[j]} 
            })
            
        index.upsert(vectors=vectors)

    print("Successfully uploaded all data to Pinecone!")

# ==========================================
# 3. QUERYING
# ==========================================
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

# ==========================================
# 4. RUNNING THE SCRIPT
# ==========================================
if __name__ == "__main__":
    #process_csv_and_upload("final_restaurant.csv") #RUN ONCE ONLY
    ask_question("Find me a highly rated restaurant near yishun and give me the address.")