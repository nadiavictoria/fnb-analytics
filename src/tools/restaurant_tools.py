from langchain.tools import tool
from src.database.neo4j_queries import search_restaurants

@tool
def restaurant_search_tool(input: str) -> str:
    """
    Search restaurants by MRT and category.
    Input format: 'mrt_name, category'
    Example: 'bedok_north, hawker'
    """

    try:
        mrt, category = [x.strip() for x in input.split(",")]

        results = search_restaurants(mrt, category)

        if not results:
            return "No restaurants found."

        return "\n".join([
            f"{r['name']} (Rating: {r['rating']}) - {r['address']}"
            for r in results
        ])

    except Exception as e:
        return f"Error: {str(e)}"