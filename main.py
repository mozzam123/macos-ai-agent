from dotenv import load_dotenv

load_dotenv()
import threading

from langchain_core.messages import HumanMessage

from app.agent.graph import graph
from app.hotkey import listen_for_hotkey
from app.voice.recorder import record_audio
from app.voice.transcriber import transcribe_audio


agent_lock = threading.Lock()


def run_agent() -> None:
    if not agent_lock.acquire(blocking=False):
        print("Agent is already processing a command.")
        return

    try:
        print("\nListening...")

        audio_path = record_audio()

        print("Transcribing...")
        user_request = transcribe_audio(audio_path)

        if not user_request:
            print("No speech detected.")
            return

        print(f"You: {user_request}")
        print("Processing...")

        final_state = graph.invoke({"messages": [HumanMessage(content=user_request)]})

        final_message = final_state["messages"][-1]

        print(f"Agent: {final_message.content}")

    except Exception as exc:
        print(f"Agent error: {exc}")

    finally:
        agent_lock.release()
        print("\nReady for next command.")


def main() -> None:
    listen_for_hotkey(run_agent)


if __name__ == "__main__":
    main()
