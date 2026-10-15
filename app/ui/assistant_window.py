from PySide6.QtCore import (
    QEasingCurve,
    Property,
    QPropertyAnimation,
    Qt,
    QTimer,
    Signal,
)
from PySide6.QtGui import (
    QColor,
    QKeyEvent,
    QPainter,
    QRadialGradient,
)
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


# ---------------------------------------------------------
# Animated Orb
# ---------------------------------------------------------


class AssistantOrb(QWidget):
    """Simple Siri-style animated orb."""

    def __init__(self) -> None:
        super().__init__()

        self.setFixedSize(70, 70)

        self._pulse = 0.0

        self._state = "idle"

        self.animation = QPropertyAnimation(
            self,
            b"pulse",
        )

        self.animation.setDuration(900)

        self.animation.setStartValue(0.0)
        self.animation.setEndValue(1.0)

        self.animation.setEasingCurve(QEasingCurve.InOutSine)

        self.animation.setLoopCount(-1)

    # -----------------------------------------------------
    # Animated property
    # -----------------------------------------------------

    def get_pulse(self) -> float:
        return self._pulse

    def set_pulse(
        self,
        value: float,
    ) -> None:
        self._pulse = value

        self.update()

    pulse = Property(
        float,
        get_pulse,
        set_pulse,
    )

    # -----------------------------------------------------
    # State
    # -----------------------------------------------------

    def set_state(
        self,
        state: str,
    ) -> None:
        self._state = state

        if state in {
            "listening",
            "processing",
            "transcribing",
        }:
            if self.animation.state() != QPropertyAnimation.Running:
                self.animation.start()

        else:
            self.animation.stop()

            self._pulse = 0.3

            self.update()

    # -----------------------------------------------------
    # Drawing
    # -----------------------------------------------------

    def paintEvent(
        self,
        event,
    ) -> None:
        painter = QPainter(self)

        painter.setRenderHint(QPainter.Antialiasing)

        size = min(
            self.width(),
            self.height(),
        )

        center = self.rect().center()

        base_radius = size * 0.28

        pulse_radius = base_radius + self._pulse * 8

        # ---------------------------------------------
        # State-specific appearance
        # ---------------------------------------------

        if self._state == "listening":
            inner = QColor(
                235,
                235,
                255,
            )

            outer = QColor(
                90,
                120,
                255,
                35,
            )

        elif self._state in {
            "processing",
            "transcribing",
        }:
            inner = QColor(
                220,
                220,
                230,
            )

            outer = QColor(
                255,
                255,
                255,
                30,
            )

        elif self._state == "done":
            inner = QColor(
                235,
                235,
                235,
            )

            outer = QColor(
                255,
                255,
                255,
                20,
            )

        else:
            inner = QColor(
                210,
                210,
                215,
            )

            outer = QColor(
                255,
                255,
                255,
                15,
            )

        # ---------------------------------------------
        # Outer glow
        # ---------------------------------------------

        glow = QRadialGradient(
            center,
            pulse_radius + 15,
        )

        glow.setColorAt(
            0.0,
            inner,
        )

        glow.setColorAt(
            0.55,
            QColor(
                inner.red(),
                inner.green(),
                inner.blue(),
                160,
            ),
        )

        glow.setColorAt(
            1.0,
            outer,
        )

        painter.setPen(Qt.NoPen)

        painter.setBrush(glow)

        painter.drawEllipse(
            center,
            int(pulse_radius + 12),
            int(pulse_radius + 12),
        )

        # ---------------------------------------------
        # Core
        # ---------------------------------------------

        core = QRadialGradient(
            center,
            pulse_radius,
        )

        core.setColorAt(
            0.0,
            QColor(
                255,
                255,
                255,
                245,
            ),
        )

        core.setColorAt(
            0.65,
            inner,
        )

        core.setColorAt(
            1.0,
            QColor(
                inner.red(),
                inner.green(),
                inner.blue(),
                150,
            ),
        )

        painter.setBrush(core)

        painter.drawEllipse(
            center,
            int(pulse_radius),
            int(pulse_radius),
        )


# ---------------------------------------------------------
# Assistant Window
# ---------------------------------------------------------


class AssistantWindow(QWidget):
    """Floating macOS assistant window."""

    cancel_requested = Signal()

    def __init__(self) -> None:
        super().__init__()

        self._approval_callback = None

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)

        self.setAttribute(Qt.WA_TranslucentBackground)

        self.setFixedSize(
            460,
            240,
        )

        self._build_ui()

        # ---------------------------------------------
        # Fade animation
        # ---------------------------------------------

        # Fade-in animation
        self.fade_in_animation = QPropertyAnimation(
            self,
            b"windowOpacity",
        )

        self.fade_in_animation.setDuration(220)
        self.fade_in_animation.setStartValue(0.0)
        self.fade_in_animation.setEndValue(1.0)

        self.fade_in_animation.setEasingCurve(QEasingCurve.InOutQuad)

        # Fade-out animation
        self.fade_out_animation = QPropertyAnimation(
            self,
            b"windowOpacity",
        )

        self.fade_out_animation.setDuration(220)
        self.fade_out_animation.setStartValue(1.0)
        self.fade_out_animation.setEndValue(0.0)

        self.fade_out_animation.setEasingCurve(QEasingCurve.InOutQuad)

        self.fade_out_animation.finished.connect(self.hide)
        self.setFocusPolicy(Qt.StrongFocus)

    # -----------------------------------------------------
    # UI
    # -----------------------------------------------------

    def keyPressEvent(
        self,
        event: QKeyEvent,
    ) -> None:
        if event.key() == Qt.Key_Escape:
            self.cancel_requested.emit()
            self.fade_out()
            return

        super().keyPressEvent(event)

    def _build_ui(self) -> None:
        container = QFrame()

        container.setObjectName("assistantContainer")

        layout = QVBoxLayout(container)

        layout.setContentsMargins(
            26,
            20,
            26,
            20,
        )

        layout.setSpacing(8)

        # ---------------------------------------------
        # Orb
        # ---------------------------------------------

        self.orb = AssistantOrb()

        orb_layout = QHBoxLayout()

        orb_layout.addStretch()

        orb_layout.addWidget(self.orb)

        orb_layout.addStretch()

        # ---------------------------------------------
        # Labels
        # ---------------------------------------------

        self.status_label = QLabel("Ready")

        self.status_label.setAlignment(Qt.AlignCenter)

        self.status_label.setObjectName("statusLabel")

        self.text_label = QLabel()

        self.text_label.setAlignment(Qt.AlignCenter)

        self.text_label.setWordWrap(True)

        self.text_label.setObjectName("textLabel")

        # ---------------------------------------------
        # Approval buttons
        # ---------------------------------------------

        self.approval_frame = QWidget()

        approval_layout = QHBoxLayout(self.approval_frame)

        approval_layout.setContentsMargins(
            0,
            4,
            0,
            0,
        )

        self.reject_button = QPushButton("Reject")

        self.approve_button = QPushButton("Allow")

        approval_layout.addStretch()

        approval_layout.addWidget(self.reject_button)

        approval_layout.addWidget(self.approve_button)

        approval_layout.addStretch()

        self.approval_frame.hide()

        # ---------------------------------------------
        # Layout
        # ---------------------------------------------

        layout.addLayout(orb_layout)

        layout.addWidget(self.status_label)

        layout.addWidget(self.text_label)

        layout.addWidget(self.approval_frame)

        root_layout = QVBoxLayout(self)

        root_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        root_layout.addWidget(container)

        # ---------------------------------------------
        # Signals
        # ---------------------------------------------

        self.approve_button.clicked.connect(lambda: self._submit_approval(True))

        self.reject_button.clicked.connect(lambda: self._submit_approval(False))

        # ---------------------------------------------
        # Styling
        # ---------------------------------------------

        self.setStyleSheet(
            """
            #assistantContainer {
                background-color: rgba(20, 20, 24, 238);
                border-radius: 30px;
                border: 1px solid rgba(255, 255, 255, 28);
            }

            #statusLabel {
                color: white;
                font-size: 17px;
                font-weight: 600;
            }

            #textLabel {
                color: rgba(255, 255, 255, 175);
                font-size: 13px;
            }

            QPushButton {
                background-color: rgba(255, 255, 255, 28);
                color: white;
                border: none;
                border-radius: 10px;
                padding: 8px 20px;
                font-size: 13px;
            }

            QPushButton:hover {
                background-color: rgba(255, 255, 255, 48);
            }
            """
        )

    # -----------------------------------------------------
    # Positioning
    # -----------------------------------------------------

    def show_centered(self) -> None:
        screen = self.screen()

        if screen is None:
            self.show()
            return

        geometry = screen.availableGeometry()

        x = geometry.x() + (geometry.width() - self.width()) // 2

        y = geometry.y() + 70

        self.move(
            x,
            y,
        )

        # Stop an active fade-out in case
        # the user activates the assistant again quickly.
        self.fade_out_animation.stop()

        # Only perform fade-in when window was hidden.
        if not self.isVisible():
            self.setWindowOpacity(0.0)

            self.show()
            self.raise_()
            self.activateWindow()
            self.setFocus()

            self.fade_in_animation.stop()
            self.fade_in_animation.start()

        else:
            # Window is already visible because its
            # status changed (Listening → Processing, etc.).
            self.setWindowOpacity(1.0)

            self.raise_()

    # -----------------------------------------------------
    # Status handling
    # -----------------------------------------------------

    def set_status(
        self,
        status: str,
        text: str = "",
    ) -> None:
        self.approval_frame.hide()

        self.status_label.setText(status)

        self.text_label.setText(text)

        normalized = status.lower()

        if "listening" in normalized:
            self.orb.set_state("listening")

        elif "transcribing" in normalized:
            self.orb.set_state("transcribing")

        elif "processing" in normalized:
            self.orb.set_state("processing")

        else:
            self.orb.set_state("idle")

        self.show_centered()

    # -----------------------------------------------------
    # Result
    # -----------------------------------------------------

    def show_result(
        self,
        text: str,
    ) -> None:
        self.status_label.setText("Done")

        self.text_label.setText(text)

        self.orb.set_state("done")

        self.show_centered()

        QTimer.singleShot(
            2500,
            self.fade_out,
        )

    # -----------------------------------------------------
    # Error
    # -----------------------------------------------------

    def show_error(
        self,
        text: str,
    ) -> None:
        self.status_label.setText("Something went wrong")

        self.text_label.setText(text)

        self.orb.set_state("idle")

        self.show_centered()

        QTimer.singleShot(
            3500,
            self.fade_out,
        )

    # -----------------------------------------------------
    # Approval
    # -----------------------------------------------------

    def request_approval(
        self,
        tool: str,
        arguments: dict,
        callback,
    ) -> None:
        self._approval_callback = callback

        self.status_label.setText("Approval required")

        self.text_label.setText(f"{tool}\n{arguments}")

        self.orb.set_state("idle")

        self.approval_frame.show()

        self.show_centered()

    def _submit_approval(
        self,
        approved: bool,
    ) -> None:
        callback = self._approval_callback

        self._approval_callback = None

        self.approval_frame.hide()

        self.set_status(
            "Processing...",
        )

        if callback:
            callback(approved)

    # -----------------------------------------------------
    # Fade Out
    # -----------------------------------------------------

    def fade_out(self) -> None:
        self.fade_in_animation.stop()
        self.fade_out_animation.stop()

        self.fade_out_animation.setStartValue(self.windowOpacity())

        self.fade_out_animation.setEndValue(0.0)

        self.fade_out_animation.start()
