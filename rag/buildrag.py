import os
import time
import pandas as pd
from pinecone import Pinecone, ServerlessSpec
from google import genai
from sentence_transformers import SentenceTransformer
import json
from dotenv import load_dotenv

load_dotenv()

# ==========================================
# 1. SETUP & AUTHENTICATION
# ==========================================
PINECONE_API_KEY = os.environ["PINECONE_API_KEY"]
GEMINI_API_KEY   = os.environ["GEMINI_API_KEY"]

gemini_client = genai.Client(api_key=GEMINI_API_KEY)

# NEW: Initialize the Local Embedding Model
# local_embed_model = SentenceTransformer('all-MiniLM-L6-v2')
# pc = Pinecone(api_key=PINECONE_API_KEY)

# index_name = "restaurant-index-10"

# if index_name not in pc.list_indexes().names():
#     print(f"Creating Pinecone index '{index_name}' with 384 dimensions...")
#     pc.create_index(
#         name=index_name,
#         dimension=384, # The dimension for 'all-MiniLM-L6-v2'
#         metric="cosine",
#         spec=ServerlessSpec(cloud="aws", region="us-east-1")
#     )
#     time.sleep(10)

# index = pc.Index(index_name)

# ==========================================
# PARSER
# ==========================================
def parse_query(question):
    prompt = f"""
    Extract MRT stations and food category from the query.

    Return STRICT JSON format:
    {{
        "locations": ["mrt_station_1", "mrt_station_2"],
        "category": "food_category"
    }}

    Rules:
    - Convert MRT names to lowercase
    - Replace spaces with underscore (e.g. "jurong east" → "jurong_east")
    - If none found, return empty list []
    - Category should be simple (e.g. "hawker stall", "japanese", "cafe")

    Query: {question}
    """
    
    response = gemini_client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )
    
    try:
        parsed = json.loads(response.text)
        return parsed["locations"], parsed["category"]
    except:
        print(f"Parsing failed. Raw output: {response.text}")
        return [], ""

# ==========================================
# BUILD CONTEXT
# ==========================================
def build_context(results):
    if not results:
        return "No restaurants found."

    context_list = []
    for r in results:
        text = f"Name: {r['name']}, Rating: {r['rating']}, Address: {r['address']}"
        context_list.append(text)

    return "\n".join(context_list)


# ==========================================
# 2. VECTORIZE AND UPLOAD
# ==========================================
EMBED_BATCH_SIZE  = 64   # embedding throughput plateaus at ~64 on GPU (was 10)
UPSERT_BATCH_SIZE = 100  # Pinecone max per upsert call (was 10)

# Vectorized row serialisation: 4x faster than loop-based approach
def _serialise(df: pd.DataFrame) -> tuple[list[str], list[str]]:
    cols = df.columns.tolist()
    rows = df.to_numpy().astype(str)
    texts = [", ".join(f"{c}: {v}" for c, v in zip(cols, row)).replace("\n", " ")
             for row in rows]
    ids = [f"doc_{idx}" for idx in df.index]
    return texts, ids

def process_csv_and_upload(csv_path):
    print(f"Reading {csv_path} and generating local embeddings...")
    df = pd.read_csv(csv_path)

    all_texts, all_ids = _serialise(df)
    print(f"Serialised {len(all_texts)} rows. Embedding in batches of {EMBED_BATCH_SIZE}...")

    # Embed in batches of EMBED_BATCH_SIZE
    all_embeddings = []
    for i in range(0, len(all_texts), EMBED_BATCH_SIZE):
        chunk = all_texts[i : i + EMBED_BATCH_SIZE]
        all_embeddings.extend(local_embed_model.encode(chunk, show_progress_bar=False).tolist())

    # Build vectors and upsert in batches of UPSERT_BATCH_SIZE
    vectors = [
        {"id": all_ids[j], "values": all_embeddings[j], "metadata": {"text": all_texts[j]}}
        for j in range(len(all_texts))
    ]
    for i in range(0, len(vectors), UPSERT_BATCH_SIZE):
        batch = vectors[i : i + UPSERT_BATCH_SIZE]
        print(f"Upserting rows {i}–{i + len(batch) - 1}...")
        index.upsert(vectors=batch)

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
    # process_csv_and_upload("final_restaurant.csv") #RUN ONCE ONLY
    ask_question("Find me a highly rated restaurant near yishun and give me the address.")