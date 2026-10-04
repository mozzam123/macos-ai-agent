from app.agent.graph import graph


def main():
    user_request = input("Command: ")

    initial_state = {
        "user_request": user_request,
        "action": None,
        "target": None,
        "result": None,
        "error": None,
    }

    final_state = graph.invoke(initial_state)

    if final_state.get("error"):
        print(f"Error: {final_state['error']}")
    else:
        print(final_state["result"])


if __name__ == "__main__":
    main()
