import time
from typing import Callable, Dict, Optional

import numpy as np
import rclpy
from rclpy.node import Node
from std_msgs.msg import String

from rustypot import Scs0009PyController


class AmazingHandNode(Node):
    """
    ROS2 node that exposes the Amazing Hand hardware via gesture commands.

    Subscribes to ``amazing_hand/command`` (``std_msgs/String``) for commands such as
    ``open``, ``close``, ``spread``, etc. Publishes execution feedback to
    ``amazing_hand/state``.
    """

    MAX_SPEED = 7
    CLOSE_SPEED = 3

    def __init__(self) -> None:
        super().__init__("amazing_hand_node")

        # Parameters mirroring the original AmazingHand_Demo defaults.
        self.declare_parameter("serial_port", "/dev/ttyACM0")
        self.declare_parameter("baudrate", 1_000_000)
        self.declare_parameter("timeout", 0.5)
        self.declare_parameter("side", 1)  # 1 => Right, 2 => Left

        serial_port = (
            self.get_parameter("serial_port").get_parameter_value().string_value
        )
        baudrate = self.get_parameter("baudrate").get_parameter_value().integer_value
        timeout = self.get_parameter("timeout").get_parameter_value().double_value
        self.side = int(self.get_parameter("side").get_parameter_value().integer_value)

        self.controller: Optional[Scs0009PyController] = None
        try:
            self.controller = Scs0009PyController(
                serial_port=serial_port,
                baudrate=baudrate,
                timeout=timeout,
            )
            self.controller.write_torque_enable(1, 1)
            self.get_logger().info(
                f"Amazing Hand connected on {serial_port} @ {baudrate} baud"
            )
        except Exception as exc:  # pragma: no cover - hardware specific
            self.get_logger().error(f"Failed to initialize controller: {exc}")

        # Middle pose offsets copied from AmazingHand_Demo.py
        self.middle_pos = [3, 0, -5, -8, -2, 5, -12, 0]

        self.state_pub = self.create_publisher(String, "amazing_hand/state", 10)
        self.command_sub = self.create_subscription(
            String, "amazing_hand/command", self.command_callback, 10
        )

        self.command_table: Dict[str, Callable[[], None]] = {
            "open": self.open_hand,
            "close": self.close_hand,
            "spread": self.spread_hand,
            "clench": self.clench_hand,
            "index_point": self.index_pointing,
            "nonono": self.nonono,
            "perfect": self.perfect,
            "victory": self.victory,
            "pinch": self.pinched,
            "scissors": self.scissors,
            "middle_finger": self.middle_finger,
        }

        self._publish_state("ready")
        self.get_logger().info(
            "AmazingHandNode ready. Publish commands to 'amazing_hand/command'."
        )

    # ------------------------------------------------------------------ callbacks
    def command_callback(self, msg: String) -> None:
        
        command = msg.data.strip().lower()
        print(f"Command: {command}")
        handler = self.command_table.get(command)
        if self.controller is None:
            self._publish_state(f"error:no_controller:{command}")
            self.get_logger().error(
                "Cannot execute command '%s': controller not available", command
            )
            return

        if handler is None:
            self._publish_state(f"unknown:{command}")
            self.get_logger().warning("Unknown Amazing Hand command: %s", command)
            return

        try:
            handler()
            self._publish_state(f"executed:{command}")
            self.get_logger().info(f"Executed gesture: {command}")
        except Exception as exc:  # pragma: no cover - hardware specific
            self._publish_state(f"error:{command}:{exc}")
            self.get_logger().error(f"Command '{command}' failed: {exc}")

    def _publish_state(self, text: str) -> None:
        msg = String()
        msg.data = text
        self.state_pub.publish(msg)

    # ---------------------------------------------------------------- gestures
    def open_hand(self) -> None:
        self.move_index(-35, 35, self.MAX_SPEED)
        self.move_middle(-35, 35, self.MAX_SPEED)
        self.move_ring(-35, 35, self.MAX_SPEED)
        self.move_thumb(-35, 35, self.MAX_SPEED)

    def close_hand(self) -> None:
        self.move_index(90, -90, self.CLOSE_SPEED)
        self.move_middle(90, -90, self.CLOSE_SPEED)
        self.move_ring(90, -90, self.CLOSE_SPEED)
        self.move_thumb(90, -90, self.CLOSE_SPEED + 1)

    def spread_hand(self) -> None:
        if self.side == 1:
            self.move_index(4, 90, self.MAX_SPEED)
            self.move_middle(-32, 32, self.MAX_SPEED)
            self.move_ring(-90, -4, self.MAX_SPEED)
            self.move_thumb(-90, -4, self.MAX_SPEED)
        else:
            self.move_index(-60, 0, self.MAX_SPEED)
            self.move_middle(-35, 35, self.MAX_SPEED)
            self.move_ring(-4, 90, self.MAX_SPEED)
            self.move_thumb(-4, 90, self.MAX_SPEED)

    def clench_hand(self) -> None:
        if self.side == 1:
            self.move_index(-60, 0, self.MAX_SPEED)
            self.move_middle(-35, 35, self.MAX_SPEED)
            self.move_ring(0, 70, self.MAX_SPEED)
            self.move_thumb(-4, 90, self.MAX_SPEED)
        else:
            self.move_index(0, 60, self.MAX_SPEED)
            self.move_middle(-35, 35, self.MAX_SPEED)
            self.move_ring(-70, 0, self.MAX_SPEED)
            self.move_thumb(-90, -4, self.MAX_SPEED)

    def index_pointing(self) -> None:
        self.move_index(-40, 40, self.MAX_SPEED)
        self.move_middle(90, -90, self.MAX_SPEED)
        self.move_ring(90, -90, self.MAX_SPEED)
        self.move_thumb(90, -90, self.MAX_SPEED)

    def nonono(self) -> None:
        self.index_pointing()
        for _ in range(3):
            time.sleep(0.2)
            self.move_index(-10, 80, self.MAX_SPEED)
            time.sleep(0.2)
            self.move_index(-80, 10, self.MAX_SPEED)
        self.move_index(-35, 35, self.MAX_SPEED)
        time.sleep(0.4)

    def perfect(self) -> None:
        if self.side == 1:
            self.move_index(50, -50, self.MAX_SPEED)
            self.move_middle(0, 0, self.MAX_SPEED)
            self.move_ring(-20, 20, self.MAX_SPEED)
            self.move_thumb(65, 12, self.MAX_SPEED)
        else:
            self.move_index(50, -50, self.MAX_SPEED)
            self.move_middle(0, 0, self.MAX_SPEED)
            self.move_ring(-20, 20, self.MAX_SPEED)
            self.move_thumb(-12, -65, self.MAX_SPEED)

    def victory(self) -> None:
        if self.side == 1:
            self.move_index(-15, 65, self.MAX_SPEED)
            self.move_middle(-65, 15, self.MAX_SPEED)
            self.move_ring(90, -90, self.MAX_SPEED)
            self.move_thumb(90, -90, self.MAX_SPEED)
        else:
            self.move_index(-65, 15, self.MAX_SPEED)
            self.move_middle(-15, 65, self.MAX_SPEED)
            self.move_ring(90, -90, self.MAX_SPEED)
            self.move_thumb(90, -90, self.MAX_SPEED)

    def pinched(self) -> None:
        if self.side == 1:
            self.move_index(90, -90, self.MAX_SPEED)
            self.move_middle(90, -90, self.MAX_SPEED)
            self.move_ring(90, -90, self.MAX_SPEED)
            self.move_thumb(0, -75, self.MAX_SPEED)
        else:
            self.move_index(90, -90, self.MAX_SPEED)
            self.move_middle(90, -90, self.MAX_SPEED)
            self.move_ring(90, -90, self.MAX_SPEED)
            self.move_thumb(75, 5, self.MAX_SPEED)

    def scissors(self) -> None:
        self.victory()
        for _ in range(3):
            time.sleep(0.2)
            self.move_index(-50, 20, self.MAX_SPEED)
            self.move_middle(-20, 50, self.MAX_SPEED)
            time.sleep(0.2)
            self.victory()

    def middle_finger(self) -> None:
        if self.side == 1:
            self.move_index(90, -90, self.MAX_SPEED)
            self.move_middle(-35, 35, self.MAX_SPEED)
            self.move_ring(90, -90, self.MAX_SPEED)
            self.move_thumb(0, -75, self.MAX_SPEED)
        else:
            self.move_index(90, -90, self.MAX_SPEED)
            self.move_middle(-35, 35, self.MAX_SPEED)
            self.move_ring(90, -90, self.MAX_SPEED)
            self.move_thumb(75, 0, self.MAX_SPEED)

    # --------------------------------------------------------------- helpers
    def move_index(self, angle_1: float, angle_2: float, speed: int) -> None:
        if self.controller is None:
            return
        self.controller.write_goal_speed(1, speed)
        time.sleep(0.0002)
        self.controller.write_goal_speed(2, speed)
        time.sleep(0.0002)
        pos_1 = np.deg2rad(self.middle_pos[0] + angle_1)
        pos_2 = np.deg2rad(self.middle_pos[1] + angle_2)
        self.controller.write_goal_position(1, pos_1)
        self.controller.write_goal_position(2, pos_2)
        time.sleep(0.005)

    def move_middle(self, angle_1: float, angle_2: float, speed: int) -> None:
        if self.controller is None:
            return
        self.controller.write_goal_speed(3, speed)
        time.sleep(0.0002)
        self.controller.write_goal_speed(4, speed)
        time.sleep(0.0002)
        pos_1 = np.deg2rad(self.middle_pos[2] + angle_1)
        pos_2 = np.deg2rad(self.middle_pos[3] + angle_2)
        self.controller.write_goal_position(3, pos_1)
        self.controller.write_goal_position(4, pos_2)
        time.sleep(0.005)

    def move_ring(self, angle_1: float, angle_2: float, speed: int) -> None:
        if self.controller is None:
            return
        self.controller.write_goal_speed(5, speed)
        time.sleep(0.0002)
        self.controller.write_goal_speed(6, speed)
        time.sleep(0.0002)
        pos_1 = np.deg2rad(self.middle_pos[4] + angle_1)
        pos_2 = np.deg2rad(self.middle_pos[5] + angle_2)
        self.controller.write_goal_position(5, pos_1)
        self.controller.write_goal_position(6, pos_2)
        time.sleep(0.005)

    def move_thumb(self, angle_1: float, angle_2: float, speed: int) -> None:
        if self.controller is None:
            return
        self.controller.write_goal_speed(7, speed)
        time.sleep(0.0002)
        self.controller.write_goal_speed(8, speed)
        time.sleep(0.0002)
        pos_1 = np.deg2rad(self.middle_pos[6] + angle_1)
        pos_2 = np.deg2rad(self.middle_pos[7] + angle_2)
        self.controller.write_goal_position(7, pos_1)
        self.controller.write_goal_position(8, pos_2)
        time.sleep(0.005)


def main(args=None) -> None:
    rclpy.init(args=args)
    node = AmazingHandNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()


