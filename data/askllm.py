
import json
import re
import os

from google import genai
from openai import OpenAI
from dotenv import load_dotenv
from neo4j import GraphDatabase

# ==========================================
# PARSER
# ==========================================
def parse_query(question, model, client):
    prompt = f"""
    Extract MRT station names and food category from the query.

    Return STRICT JSON format:
    {{
        "locations": ["mrt_station_1", "mrt_station_2"],
        "category": "food_category"
    }}

    Rules:
    - Extract any place name that refers to an MRT station or area in Singapore (e.g. "jurong", "tampines", "bedok", "orchard", "choa chu kang")
    - Convert location names to lowercase and replace spaces with underscores (e.g. "choa chu kang" → "choa_chu_kang")
    - Partial names are valid: "jurong" is a valid location even if the full name is "jurong east"
    - Category must be a specific food type (e.g. "hawker stall", "japanese", "cafe", "korean", "chinese")
    - Generic words like "restaurant", "restaurants", "food", "place", "stall" are NOT a category — set category to ""
    - If no food category found, return ""

    Query: {question}
    """
    
    # WITH GEMINI
    if model == "gemini":
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        
        raw_text = response.text.strip()
        cleaned = re.sub(r"```json|```", "", raw_text).strip()

        try:
            parsed = json.loads(cleaned)
            return parsed.get("locations", []), parsed.get("category", "")
        except Exception as e:
            print("Parsing failed. Raw output:", raw_text)
            return [], ""

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
    # print(f"Parsed locations: {locations}, category: {category}")

    # Initiate driver for neo4j
    driver = GraphDatabase.driver(
        os.getenv("NEO4J_URI"),
        auth=(os.getenv("NEO4J_USERNAME"), os.getenv("NEO4J_PASSWORD"))
        )

    # Format location and category
    category = normalize_category(category)

    # Index graph from neo4j
    results = search_restaurants(driver, locations, category)
    # print(f"Results count: {len(results)}")
    
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
    - No blank lines between list items
    - Always add a blank line before the closing sentence
    """
    
    if model == "gemini":
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        return response.text

    elif model == "gpt":
        response = client.chat.completions.create(
            model='gpt-4.1-mini',
            messages=[
                {"role": "system", "content": "You extract structured data from queries."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )
        return response.choices[0].message.content
    
def normalize_category(category):
    return category.replace("_", " ")

# Copied from neo4j queries
def search_restaurants(driver, mrt_names, category_name):
    with driver.session() as session:
        if category_name:
            result = session.run("""
                MATCH (r:Restaurant)-[:IS_NEAR_TO]->(m:MRT),
                      (r)-[:FOOD_CATEGORIZED_AS]->(c:FoodCategory)
                WHERE any(mrt IN $mrts WHERE m.name CONTAINS mrt) AND c.name = $category
                RETURN DISTINCT r.name AS name, r.rating AS rating, r.address AS address
                ORDER BY r.rating DESC
            """, mrts=mrt_names, category=category_name)
            rows = [record.data() for record in result]
            if rows:
                return rows

        # Fallback: no category filter
        result = session.run("""
            MATCH (r:Restaurant)-[:IS_NEAR_TO]->(m:MRT)
            WHERE any(mrt IN $mrts WHERE m.name CONTAINS mrt)
            RETURN DISTINCT r.name AS name, r.rating AS rating, r.address AS address
            ORDER BY r.rating DESC
        """, mrts=mrt_names)
        return [record.data() for record in result]

if __name__ == "__main__":

    # Make sure you have created .env and have either GEMINI_API_KEY or OPENAI_API_KEY
    from pathlib import Path
    from dotenv import find_dotenv
    load_dotenv(find_dotenv(usecwd=True), override=True)

    # Set model to either "GEMINI" or "GPT"
    answer = ask_question("Find me the best 5 hawker stall near choa chu kang", model="gemini")
    print(answer)
