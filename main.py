import threading
import uuid

from dotenv import load_dotenv

# Load environment variables before importing the graph.
# This enables LangSmith tracing configuration from .env.
load_dotenv()

from langchain_core.messages import HumanMessage
from langgraph.types import Command

from app.agent.graph import graph
from app.hotkey import listen_for_hotkey
from app.voice.recorder import record_audio
from app.voice.transcriber import transcribe_audio


# Prevent multiple agent executions from running at the same time.
agent_lock = threading.Lock()


def run_agent() -> None:
    """Run one complete voice-agent interaction."""

    # Do not start another request if the agent is already busy.
    if not agent_lock.acquire(blocking=False):
        print("Agent is already processing a command.")
        return

    try:
        # -------------------------------------------------
        # Voice input
        # -------------------------------------------------

        print("\nListening...")

        audio_path = record_audio()

        print("Transcribing...")

        user_request = transcribe_audio(audio_path)

        if not user_request:
            print("No speech detected.")
            return

        print(f"You: {user_request}")

        # -------------------------------------------------
        # LangGraph configuration
        # -------------------------------------------------

        # Every request gets its own LangGraph thread.
        # The same thread_id must be used when resuming
        # an interrupted graph.
        thread_id = str(uuid.uuid4())

        config = {
            "configurable": {
                "thread_id": thread_id,
            }
        }

        # -------------------------------------------------
        # Start agent
        # -------------------------------------------------

        print("Processing...")

        result = graph.invoke(
            {"messages": [HumanMessage(content=user_request)]},
            config=config,
        )

        # -------------------------------------------------
        # Human-in-the-loop approval
        # -------------------------------------------------

        while "__interrupt__" in result:
            interrupt_data = result["__interrupt__"][0].value

            print("\n--------------------------------")
            print("Approval required")
            print("--------------------------------")

            print(f"Tool: {interrupt_data['tool']}")

            print(f"Risk: {interrupt_data['risk']}")

            print(f"Arguments: {interrupt_data['arguments']}")

            print("--------------------------------")

            answer = input("Allow this action? (y/n): ").strip().lower()

            approved = answer in {
                "y",
                "yes",
            }

            # Resume the SAME LangGraph thread from
            # the saved checkpoint.
            result = graph.invoke(
                Command(
                    resume={
                        "approved": approved,
                    }
                ),
                config=config,
            )

        # -------------------------------------------------
        # Final response
        # -------------------------------------------------

        messages = result.get("messages", [])

        if messages:
            final_message = messages[-1]

            if final_message.content:
                print(f"Agent: {final_message.content}")

        # Show rejection/error if execution ended because
        # the user rejected an action.
        error = result.get("error")

        if error:
            print(f"Agent: {error}")

    except Exception as exc:
        print(f"Agent error: {exc}")

    finally:
        agent_lock.release()

        print("\nReady for next command.")


def main() -> None:
    """Start the macOS AI agent."""

    listen_for_hotkey(run_agent)


if __name__ == "__main__":
    main()
