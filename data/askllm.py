
import json
import re
import os

from google import genai
from openai import OpenAI
from dotenv import load_dotenv
from neo4j import GraphDatabase

# ==========================================
# PARETO CONTEXT
# ==========================================
_pareto_cache: dict | None = None

def _load_pareto_cache() -> dict:
    global _pareto_cache
    if _pareto_cache is not None:
        return _pareto_cache
    try:
        import json as _json
        import pandas as pd
        from pathlib import Path as _Path
        from build_pareto_map_data_updated import (
            build_analysis_df, run_pareto,
            MASTER_DATASET, MASTER_DATASET_COLS,
        )
        archetypes_path = _Path(__file__).resolve().parent / "archetypes.json"
        with open(archetypes_path) as f:
            archetypes = _json.load(f)
        df = pd.read_csv(MASTER_DATASET, usecols=MASTER_DATASET_COLS)
        analysis_df = build_analysis_df(df)
        # Seed cache with all known planning areas (empty list = not Pareto-optimal)
        cache: dict = {area: [] for area in analysis_df["PLANNING_AREA"].unique()}
        for concept_key, cfg in archetypes.items():
            pareto_df = run_pareto(analysis_df, cfg)
            for area in pareto_df["PLANNING_AREA"].tolist():
                cache[area].append(cfg["description"])
        _pareto_cache = cache
    except Exception as e:
        print(f"Warning: Pareto cache unavailable: {e}")
        _pareto_cache = {}
    return _pareto_cache

_mrt_mapping: dict | None = None
_area_to_mrts: dict | None = None

def _load_mrt_mapping() -> dict:
    global _mrt_mapping
    if _mrt_mapping is not None:
        return _mrt_mapping
    try:
        import json as _json
        from pathlib import Path as _Path
        with open(_Path(__file__).resolve().parent / "mrt_to_planning_area.json") as f:
            _mrt_mapping = _json.load(f)
    except Exception as e:
        print(f"Warning: MRT mapping unavailable: {e}")
        _mrt_mapping = {}
    return _mrt_mapping

def _load_area_to_mrts() -> dict:
    global _area_to_mrts
    if _area_to_mrts is not None:
        return _area_to_mrts
    try:
        import json as _json
        from pathlib import Path as _Path
        with open(_Path(__file__).resolve().parent / "planning_area_to_mrts.json") as f:
            _area_to_mrts = _json.load(f)
    except Exception as e:
        print(f"Warning: Area-to-MRT mapping unavailable: {e}")
        _area_to_mrts = {}
    return _area_to_mrts


def expand_locations(locations: list) -> list:
    """Expand location names that have no matching MRT nodes to all MRT stations in their planning area."""
    mrt_map = _load_mrt_mapping()
    area_to_mrts = _load_area_to_mrts()
    expanded = []
    for loc in locations:
        area = mrt_map.get(loc)
        if not area:
            area = loc.replace("_", " ").upper()
        mrts = area_to_mrts.get(area, [loc])
        expanded.extend(mrts)
    return list(dict.fromkeys(expanded))  # deduplicate preserving order


def get_pareto_context(locations: list) -> str:
    cache = _load_pareto_cache()
    mrt_map = _load_mrt_mapping()
    if not cache:
        return ""

    lines = []
    seen_areas = set()

    # All planning areas known to Pareto or to the full master dataset
    all_known_areas = set(cache.keys())

    for loc in locations:
        # Resolve MRT station → one or more planning areas
        mapped = mrt_map.get(loc)
        if mapped:
            areas = [mapped]
        else:
            # Partial name: collect ALL planning areas that contain the normalised token
            normalised = loc.replace("_", " ").upper()
            areas = [a for a in all_known_areas if normalised in a]
            if not areas:
                areas = [normalised]  # best guess even if not in cache

        for area in areas:
            if area in seen_areas:
                continue
            seen_areas.add(area)

            concepts = cache.get(area, [])
            if concepts:
                lines.append(f"- {area} is Pareto-optimal for: {', '.join(concepts)}")
            else:
                lines.append(f"- {area} is NOT Pareto-optimal for any F&B concept in this analysis")

    if not lines:
        return ""
    return "Pareto Analysis for queried area(s):\n" + "\n".join(lines)

# ==========================================
# PARSER
# ==========================================
def parse_query(question, model, client):
    prompt = f"""
    Extract MRT station names, food category, sort order, and result limit from the query.

    Return STRICT JSON format:
    {{
        "locations": ["mrt_station_1", "mrt_station_2"],
        "categories": ["food_category_1", "food_category_2"],
        "category_match": "all",
        "sort_order": "desc",
        "limit": 10
    }}

    Rules:
    - Extract any place name that refers to an MRT station or area in Singapore (e.g. "jurong", "tampines", "bedok", "orchard", "choa chu kang")
    - Convert location names to lowercase and replace spaces with underscores (e.g. "choa chu kang" → "choa_chu_kang")
    - Partial names are valid: "jurong" is a valid location even if the full name is "jurong east"
    - categories is a list of specific food types the user wants (e.g. ["chinese", "halal"], ["japanese"], ["cafe"])
    - Generic words like "restaurant", "restaurants", "food", "place", "stall" are NOT a category — omit them
    - If no food category found, return []
    - category_match: "all" if the user wants restaurants matching ALL categories (e.g. "chinese halal", "chinese and halal"), "any" if the user wants restaurants matching ANY category (e.g. "chinese or halal", "chinese or japanese")
    - sort_order: "asc" if the user asks for worst, lowest rated, cheapest, bottom, otherwise "desc"
    - limit: the number the user asks for (e.g. "top 5" → 5, "3 restaurants" → 3), default to 10 if not specified

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
            return (
                parsed.get("locations", []),
                parsed.get("categories", []),
                parsed.get("category_match", "all"),
                parsed.get("sort_order", "desc"),
                int(parsed.get("limit", 10)),
            )
        except Exception as e:
            print("Parsing failed. Raw output:", raw_text)
            return [], [], "all", "desc", 10

    # WITH GPT MODEL
    elif model == "gpt":
        response = client.chat.completions.create(
            model='gpt-4.1-mini',
            messages=[
                {"role": "system", "content": "Extract MRT stations, food categories (list), sort order, and limit in JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0
        )

        raw_text = response.choices[0].message.content.strip()

        cleaned = re.sub(r"```json|```", "", raw_text).strip()

        try:
            parsed = json.loads(cleaned)
            return (
                parsed.get("locations", []),
                parsed.get("categories", []),
                parsed.get("category_match", "all"),
                parsed.get("sort_order", "desc"),
                int(parsed.get("limit", 10)),
            )
        except Exception as e:
            print("Parsing failed. Raw output:", raw_text)
            print("Cleaned output:", cleaned)
            return [], [], "all", "desc", 10

# ==========================================
# BUILD CONTEXT
# ==========================================
def build_context(results):
    if not results:
        return "No restaurants found."

    context_list = []
    for i, r in enumerate(results, 1):
        category_label = f", Category: {r['category']}" if r.get('category') else ""
        text = f"{i}. {r['name']}, Rating: {r['rating']}, Address: {r['address']}{category_label}"
        context_list.append(text)

    return "\n".join(context_list)

def ask_question(question, model="gemini"):
    #print(f"\nQuestion: {question}")

    if model == "gemini":
        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))        
    elif model == "gpt":
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))    

    # Parse Query
    locations, categories, category_match, sort_order, limit = parse_query(question, model=model, client=client)
    # print(f"Parsed locations: {locations}, categories: {categories}, match: {category_match}, sort: {sort_order}, limit: {limit}")

    # Guard: no location extracted
    if not locations:
        return (
            "I can help with food recommendations and F&B location insights near any MRT station in Singapore.\n\n"
            "Try asking something like:\n"
            "- \"Best hawker stalls near Tampines\"\n"
            "- \"Should I open a cafe near Jurong East?\"\n"
            "- \"Top rated restaurants near Woodlands\""
        )

    # Initiate driver for neo4j
    driver = GraphDatabase.driver(
        os.getenv("NEO4J_URI"),
        auth=(os.getenv("NEO4J_USERNAME"), os.getenv("NEO4J_PASSWORD"))
        )

    # Normalize categories
    categories = normalize_categories(categories)

    # Index graph from neo4j
    results = search_restaurants(driver, locations, categories, category_match=category_match, sort_order=sort_order, limit=limit)
    if not results:
        # Fallback: expand planning-area name to its constituent MRT stations
        expanded = expand_locations(locations)
        if expanded != locations:
            results = search_restaurants(driver, expanded, categories, category_match=category_match, sort_order=sort_order, limit=limit)

    # Build the restaurant list directly in Python — LLM must not filter or reorder
    restaurant_list = build_context(results)
    pareto_context = get_pareto_context(locations)

    sort_label = "lowest rated first" if sort_order == "asc" else "highest rated first"

    # Standard RAG: pass retrieved data as context, LLM generates narrative only
    prompt = f"""
    You are an F&B location intelligence assistant. You answer questions strictly based on
    restaurant data and Pareto analysis. You do NOT give general business advice such as
    permits, marketing, staffing, or menu planning — redirect those questions back to
    your scope if asked.

    The user asked: {question}

    Retrieved restaurant data (sorted {sort_label}, showing {limit} results):
    {restaurant_list}

    {pareto_context}

    Instructions:
    - Write ONE short intro sentence summarising the data or addressing the location question
    - Do NOT reproduce the restaurant list — it will be inserted automatically
    - Do not write any numbered lines (e.g. "1.", "2.")
    - After the list, write a "Using Pareto Analysis:" section:
        * If the area IS Pareto-optimal: explain which F&B concepts it excels at and what that means for the location
        * If the area is NOT Pareto-optimal: state it did not make the shortlist and what that implies for the competitive landscape
        * One paragraph per area, each separated by a blank line
        * Never combine multiple areas into one paragraph
    - End with a short closing sentence — only suggest follow-up questions within your scope (restaurant data and Pareto analysis), not generic business advice
    - Separate the intro, Pareto section, and closing with blank lines
    - You may reference specific restaurants from the data to strengthen the Pareto justification
    """

    if model == "gemini":
        from google.genai import types as _gtypes
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=_gtypes.GenerateContentConfig(
                system_instruction=(
                    "You are an F&B location intelligence assistant. You answer questions strictly "
                    "based on restaurant data and Pareto analysis. You do not give general business "
                    "advice such as permits, marketing, staffing, or menu planning."
                )
            )
        )
        llm_text = response.text

    elif model == "gpt":
        response = client.chat.completions.create(
            model='gpt-4.1-mini',
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an F&B location intelligence assistant. "
                        "You answer questions strictly based on restaurant data and Pareto analysis. "
                        "You do not give general business advice such as permits, "
                        "marketing, staffing, or menu planning."
                    ),
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )
        llm_text = response.choices[0].message.content

    # Strip any restaurant list lines the LLM reproduced (numbered items or lines with "Rating:")
    def _is_list_line(line):
        return bool(re.match(r'^\s*\d+\.\s+', line)) or 'Rating:' in line

    llm_lines = [l for l in llm_text.strip().split('\n') if not _is_list_line(l)]
    # Remove leading/trailing blank lines
    while llm_lines and not llm_lines[0].strip():
        llm_lines.pop(0)
    while llm_lines and not llm_lines[-1].strip():
        llm_lines.pop()

    intro = llm_lines[0].strip() if llm_lines else ""
    rest = '\n'.join(llm_lines[1:]).strip()

    if results:
        parts = [intro, restaurant_list]
        if rest:
            parts.append(rest)
        return '\n\n'.join(parts)
    else:
        return llm_text.strip()
    
def _build_category_synonyms() -> dict:
    import json as _json
    from pathlib import Path as _Path
    # group values in category_map.json that differ from Neo4j category_clean names
    group_fixes = {"hawker": "hawker stall", "fast_food": "fast food"}
    try:
        with open(_Path(__file__).resolve().parent / "category_map.json") as f:
            raw = _json.load(f)
        synonyms = {k: group_fixes.get(v, v) for k, v in raw.items()}
    except Exception:
        synonyms = {}
    return synonyms

_CATEGORY_SYNONYMS = _build_category_synonyms()

def normalize_category(category: str) -> str:
    cat = category.replace("_", " ").lower().strip()
    return _CATEGORY_SYNONYMS.get(cat, cat)

def normalize_categories(categories: list) -> list:
    return [normalize_category(c) for c in categories if c]

# Copied from neo4j queries
def search_restaurants(driver, mrt_names, categories, category_match="all", sort_order="desc", limit=10):
    order = "ASC" if sort_order == "asc" else "DESC"
    cypher_quantifier = "all" if category_match == "all" else "any"
    with driver.session() as session:
        if categories:
            result = session.run(f"""
                MATCH (r:Restaurant)-[:IS_NEAR_TO]->(m:MRT)
                WHERE any(mrt IN $mrts WHERE m.name CONTAINS mrt)
                  AND r.rating IS NOT NULL AND NOT isNaN(r.rating)
                  AND {cypher_quantifier}(cat IN $categories WHERE
                      EXISTS {{
                          MATCH (r)-[:FOOD_CATEGORIZED_AS]->(c:FoodCategory)
                          WHERE toLower(c.name) = cat
                      }}
                  )
                WITH r, [(r)-[:FOOD_CATEGORIZED_AS]->(c:FoodCategory) | c.name] AS cats
                RETURN r.name AS name, r.rating AS rating, r.address AS address,
                       cats[0] AS category
                ORDER BY r.rating {order} LIMIT $limit
            """, mrts=mrt_names, categories=categories, limit=limit)
            return [record.data() for record in result]

        # Fallback: no category filter (only used when no categories were requested)
        result = session.run(f"""
            MATCH (r:Restaurant)-[:IS_NEAR_TO]->(m:MRT)
            WHERE any(mrt IN $mrts WHERE m.name CONTAINS mrt)
              AND r.rating IS NOT NULL AND NOT isNaN(r.rating)
            RETURN DISTINCT r.name AS name, r.rating AS rating, r.address AS address
            ORDER BY r.rating {order} LIMIT $limit
        """, mrts=mrt_names, limit=limit)
        return [record.data() for record in result]

if __name__ == "__main__":

    # Make sure you have created .env and have either GEMINI_API_KEY or OPENAI_API_KEY
    from pathlib import Path
    from dotenv import find_dotenv
    load_dotenv(find_dotenv(usecwd=True), override=True)

    # Set model to either "GEMINI" or "GPT"
    answer = ask_question("Find me the best 5 hawker stall near choa chu kang", model="gemini")
    print(answer)
