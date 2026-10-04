from langchain_core.messages import HumanMessage

from app.agent.graph import graph


def main():
    user_request = input("Command: ")

    initial_state = {"messages": [HumanMessage(content=user_request)]}

    final_state = graph.invoke(initial_state)

    final_message = final_state["messages"][-1]

    print(final_message.content)


if __name__ == "__main__":
    main()
