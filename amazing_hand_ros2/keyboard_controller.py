import select
import sys
import termios
import tty
from typing import Dict, Optional, Tuple

import rclpy
from rclpy.node import Node
from std_msgs.msg import String

GESTURE_BINDINGS: Dict[str, Tuple[str, str]] = {
    "o": ("open", "Open hand"),
    "c": ("close", "Close hand"),
    "s": ("spread", "Spread fingers"),
    "l": ("clench", "Clench fist"),
    "i": ("index_point", "Index pointing"),
    "n": ("nonono", "Index wag (nonono)"),
    "p": ("pinch", "Pinched fingers"),
    "v": ("victory", "Victory / peace"),
    "k": ("perfect", "Perfect / OK"),
    "g": ("scissors", "Scissors motion"),
    "m": ("middle_finger", "Middle finger"),
}


class NonBlockingKeyReader:
    """Utility that reads single keys without blocking the ROS2 executor."""

    def __init__(self) -> None:
        self.enabled = sys.stdin.isatty()
        self.fd = sys.stdin.fileno() if self.enabled else None
        self.settings = termios.tcgetattr(self.fd) if self.enabled else None
        if self.enabled:
            tty.setcbreak(self.fd)

    def read_key(self) -> Optional[str]:
        if not self.enabled:
            return None
        dr, _, _ = select.select([sys.stdin], [], [], 0)
        if not dr:
            return None
        return sys.stdin.read(1)

    def restore(self) -> None:
        if self.enabled and self.settings is not None:
            termios.tcsetattr(self.fd, termios.TCSADRAIN, self.settings)


class KeyboardController(Node):
    """
    Publishes Amazing Hand gestures from keyboard input and reports hand state.

    - Publishes ``amazing_hand/command`` (``std_msgs/String``)
    - Subscribes to ``amazing_hand/state`` for execution feedback
    """

    def __init__(self) -> None:
        super().__init__("amazing_hand_keyboard")

        self.publisher = self.create_publisher(String, "amazing_hand/command", 10)
        self.state_sub = self.create_subscription(
            String, "amazing_hand/state", self.state_callback, 10
        )
        self.key_reader = NonBlockingKeyReader()
        if not self.key_reader.enabled:
            self.get_logger().warning(
                "stdin is not a TTY - keyboard control disabled. Use ros2 topic pub instead."
            )
        self.timer = self.create_timer(0.05, self.poll_keyboard)
        self.print_help()

    def poll_keyboard(self) -> None:
        key = self.key_reader.read_key()
        if key is None:
            return

        if key in ("\x03", "\x1b", "q"):  # CTRL+C / ESC / q
            self.get_logger().info("Exit requested (key=%s), shutting down...", key)
            self.key_reader.restore()
            rclpy.shutdown()
            return

        if key in ("h", "?"):
            self.print_help()
            return

        entry = GESTURE_BINDINGS.get(key.lower())
        if entry is None:
            self.get_logger().info("No gesture mapped to key '%s' (press 'h' for help)", key)
            return

        command, description = entry
        msg = String()
        msg.data = command
        self.publisher.publish(msg)
        self.get_logger().info(f"Sent command '{command}' ({description})")

    def state_callback(self, msg: String) -> None:
        self.get_logger().info(f"Hand state: {msg.data}")

    def print_help(self) -> None:
        lines = [
            "",
            "Amazing Hand keyboard control",
            "-----------------------------------------",
        ]
        for key, (_, description) in GESTURE_BINDINGS.items():
            lines.append(f"  {key} : {description}")
        lines.append("  h/? : show this help")
        lines.append("  q   : quit")
        self.get_logger().info("\n".join(lines))

    def destroy_node(self) -> bool:
        self.key_reader.restore()
        return super().destroy_node()


def main(args=None) -> None:
    rclpy.init(args=args)
    node = KeyboardController()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()


