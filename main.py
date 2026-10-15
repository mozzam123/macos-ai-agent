import sys

from PySide6.QtWidgets import QApplication

from app.config import HOTKEY
from app.hotkey import start_hotkey_listener
from app.ui.assistant_window import AssistantWindow
from app.ui.controller import AssistantController


def main() -> None:
    app = QApplication(sys.argv)

    app.setQuitOnLastWindowClosed(False)

    # Create UI and controller first
    window = AssistantWindow()
    controller = AssistantController()

    # -----------------------------------------
    # Controller → UI
    # -----------------------------------------

    controller.status_changed.connect(window.set_status)

    controller.result_ready.connect(window.show_result)

    controller.error_occurred.connect(window.show_error)

    controller.approval_required.connect(
        lambda tool, arguments: (
            window.request_approval(
                tool,
                arguments,
                controller.submit_approval,
            )
        )
    )

    # -----------------------------------------
    # UI → Controller
    # -----------------------------------------

    window.cancel_requested.connect(controller.cancel)

    # -----------------------------------------
    # Global hotkey
    # -----------------------------------------

    hotkey_listener = start_hotkey_listener(controller.activate)

    print(f"macOS AI Agent running in background. " f"Press {HOTKEY}.")

    exit_code = app.exec()

    hotkey_listener.stop()

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
