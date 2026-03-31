from .neo4j_driver import driver

def get_graph_summary():
    with driver.session() as session:
        result = session.run("""
            MATCH (n)
            RETURN count(n) AS total_nodes
        """)
        total_nodes = result.single()["total_nodes"]

        result = session.run("""
            MATCH (r:Restaurant) RETURN count(r) AS count
        """)
        restaurants = result.single()["count"]

        result = session.run("""
            MATCH (m:MRT) RETURN count(m) AS count
        """)
        mrt = result.single()["count"]

        result = session.run("""
            MATCH (c:FoodCategory) RETURN count(c) AS count
        """)
        categories = result.single()["count"]

        result = session.run("""
            MATCH ()-[rel]->()
            RETURN type(rel) AS type, count(rel) AS count
        """)

        relationships = [record.data() for record in result]

        return {
            "total_nodes": total_nodes,
            "restaurants": restaurants,
            "mrt_stations": mrt,
            "categories": categories,
            "relationships": relationships
        }
        
def preview_nodes(label, limit=10):
    with driver.session() as session:
        result = session.run(f"""
            MATCH (n:{label})
            RETURN n
            LIMIT $limit
        """, limit=limit)

        return [record["n"] for record in result]
        
def check_isolated_restaurants():
    with driver.session() as session:
        result = session.run("""
            MATCH (r:Restaurant)
            WHERE NOT (r)-[:IS_NEAR_TO]->(:MRT)
               OR NOT (r)-[:FOOD_CATEGORIZED_AS]->(:FoodCategory)
            RETURN r.name AS name
        """)
        
        return [record["name"] for record in result]
        
def search_restaurants(mrt_name, category_name):
    with driver.session() as session:
        result = session.run("""
            MATCH (r:Restaurant)-[:IS_NEAR_TO]->(m:MRT),
                  (r)-[:FOOD_CATEGORIZED_AS]->(c:FoodCategory)
            WHERE m.name = $mrt AND c.name = $category
            RETURN r.name AS name, r.rating AS rating, r.address AS address
        """, mrt=mrt_name, category=category_name)

        return [record.data() for record in result]