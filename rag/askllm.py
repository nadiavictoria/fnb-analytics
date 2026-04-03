
import json
import re
import os

from google import genai
from openai import OpenAI
from dotenv import load_dotenv
from neo4j import GraphDatabase
from utils import *

# ==========================================
# PARSER
# ==========================================
def parse_query(question, model, client):
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
    - Category should be simple (e.g. "hawker_stall", "japanese", "cafe")

    Query: {question}
    """
    
    # WITH GEMINI
    if model == "gemini":
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        
        raw_text = response.text.strip()
    
    # WITH GPT MODEL
    elif model == "gpt":
        response = client.chat.completions.create(
            model='gpt-4.1-mini',
            messages=[
                {"role": "system", "content": "Extract MRT stations and food category in JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0
        )

        raw_text = response.choices[0].message.content.strip()

        cleaned = re.sub(r"```json|```", "", raw_text).strip()
        
        try:
            parsed = json.loads(cleaned)
            return parsed.get("locations", []), parsed.get("category", "")
        except Exception as e:
            print("Parsing failed. Raw output:", raw_text)
            print("Cleaned output:", cleaned)
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

def ask_question(question, model="gemini"):
    print(f"\nQuestion: {question}")

    if model == "gemini":
        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))        
    elif model == "gpt":
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))    

    # Parse Query
    locations, category = parse_query(question, model=model, client=client)
    
    # Initiate driver for neo4j
    driver = GraphDatabase.driver(
        os.getenv("NEO4J_URI"),
        auth=(os.getenv("NEO4J_USERNAME"), os.getenv("NEO4J_PASSWORD"))
        )
    
    # Format location and category
    formatted_locations = format_locations_for_neo4j(locations)
    category = normalize_category(category)

    # Index graph from neo4j
    results = search_restaurants(driver, formatted_locations, category)
    
    # Build context for LLM prompt
    context = build_context(results)

    # Define the system prompt
    prompt = f"""
    You are a helpful food recommendation assistant.

    Use the restaurant data below to answer the question.

    Context:
    {context}

    Question: {question}

    Instructions:
    - Follow the user's request exactly (e.g. top, bottom, cheapest, etc.)
    - If the user asks for "top", return highest rated
    - If the user asks for "bottom", return lowest rated
    - Mention name, rating, and address
    - Be natural and helpful
    """
    
    if model == "gemini":
        
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        
        print("\nAnswer from Gemini:")
        print(response.text)
        
    elif model == "gpt":
    
        response = client.chat.completions.create(
            model='gpt-4.1-mini',
            messages=[
                {"role": "system", "content": "You extract structured data from queries."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )
    
        print("\nAnswer from GPT:")
        print(response.choices[0].message.content)
    

if __name__ == "__main__":
    
    # Make sure you have created .env and have either GEMINI_API_KEY or OPENAI_API_KEY
    load_dotenv()
    
    # Set model to either "GEMINI" or "GPT"
    ask_question("Find me the best 5 hawker stall near choa chu kang", model="gpt")