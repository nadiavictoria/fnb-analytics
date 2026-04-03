def format_locations_for_neo4j(locations):
    if not locations:
        return "[]"
    
    # Step 1: wrap each location with single quotes
    quoted = [f"'{loc}'" for loc in locations]
    
    # Step 2: join them with comma
    joined = ",".join(quoted)
    
    # Step 3: wrap with brackets
    return f"[{joined}]"

def normalize_category(category):
    return category.replace("_", " ")

# Copied from neo4j queries
def search_restaurants(driver, mrt_name, category_name):
    with driver.session() as session:
        result = session.run("""
            MATCH (r:Restaurant)-[:IS_NEAR_TO]->(m:MRT),
                  (r)-[:FOOD_CATEGORIZED_AS]->(c:FoodCategory)
            WHERE m.name = $mrt AND c.name = $category
            RETURN r.name AS name, r.rating AS rating, r.address AS address
        """, mrt=mrt_name, category=category_name)

        return [record.data() for record in result]