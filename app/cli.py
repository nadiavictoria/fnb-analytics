from src.agents.agent import create_agent

agent = create_agent()

while True:
    query = input("Ask: ")
    response = agent.run(query)
    print("\nAnswer:", response)