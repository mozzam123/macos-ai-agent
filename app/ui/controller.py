import threading
import uuid

from PySide6.QtCore import QObject, Signal

from langchain_core.messages import HumanMessage
from langgraph.types import Command

from app.agent.graph import graph
from app.voice.recorder import record_audio
from app.voice.transcriber import transcribe_audio


SESSION_THREAD_ID = str(uuid.uuid4())


class AssistantController(QObject):
    """Coordinates UI, voice input, and LangGraph."""

    status_changed = Signal(
        str,
        str,
    )

    result_ready = Signal(str)

    error_occurred = Signal(str)

    approval_required = Signal(
        str,
        object,
    )

    def __init__(self) -> None:
        super().__init__()

        self._lock = threading.Lock()

        self._approval_event = threading.Event()

        self._approval_decision = False

        self._cancel_event = threading.Event()

    def activate(self) -> None:
        if self._lock.locked():
            return

        self._cancel_event.clear()

        thread = threading.Thread(
            target=self._run_agent,
            daemon=True,
        )

        thread.start()

    def submit_approval(
        self,
        approved: bool,
    ) -> None:
        """Receive approval decision from UI."""

        self._approval_decision = approved

        self._approval_event.set()

    def _run_agent(self) -> None:
        if not self._lock.acquire(blocking=False):
            return

        try:
            self.status_changed.emit(
                "Listening...",
                "Speak now",
            )

            audio_path = record_audio(stop_event=self._cancel_event)

            if self._cancel_event.is_set() or audio_path is None:
                return

            self.status_changed.emit(
                "Transcribing...",
                "",
            )

            user_request = transcribe_audio(audio_path)

            if self._cancel_event.is_set():
                return

            if not user_request:
                self.error_occurred.emit("No speech detected.")
                return

            self.status_changed.emit(
                "Processing...",
                user_request,
            )

            config = {
                "configurable": {
                    "thread_id": (SESSION_THREAD_ID),
                }
            }

            if self._cancel_event.is_set():
                return

            result = graph.invoke(
                {"messages": [HumanMessage(content=user_request)]},
                config=config,
            )

            while "__interrupt__" in result:
                interrupt_data = result["__interrupt__"][0].value

                self._approval_event.clear()

                self.approval_required.emit(
                    interrupt_data["tool"],
                    interrupt_data["arguments"],
                )

                # Worker thread pauses here.
                # Qt UI remains fully responsive.
                self._approval_event.wait()

                if self._cancel_event.is_set():
                    return

                result = graph.invoke(
                    Command(resume={"approved": (self._approval_decision)}),
                    config=config,
                )

            error = result.get("error")

            if error:
                self.error_occurred.emit(str(error))
                return

            messages = result.get(
                "messages",
                [],
            )

            if not messages:
                self.result_ready.emit("Done.")
                return

            final_message = messages[-1]

            final_text = final_message.content or "Done."

            self.result_ready.emit(str(final_text))

        except Exception as exc:
            self.error_occurred.emit(str(exc))

        finally:
            self._lock.release()

    def cancel(self) -> None:
        """Cancel the active assistant interaction."""

        self._cancel_event.set()

        # Also unblock approval if currently waiting.
        self._approval_decision = False
        self._approval_event.set()
