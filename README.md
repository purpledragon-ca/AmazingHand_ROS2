## amazing_hand_ros2

ROS2 package that mirrors the original `AmazingHand_Demo.py` gestures and exposes:

- `amazing_hand_node`: subscribes to `amazing_hand/command` and drives the hardware.
- `amazing_hand_keyboard`: publishes commands from the keyboard and listens to `amazing_hand/state`.

### Build

```bash
cd ~/AmazingHand
colcon build --packages-select amazing_hand_ros2
source install/setup.bash
```

### Run the hardware node

```bash
ros2 run amazing_hand_ros2 amazing_hand_node \
  --ros-args \
    -p serial_port:=/dev/ttyACM0 \
    -p baudrate:=1000000 \
    -p timeout:=0.5 \
    -p side:=1
```

### Keyboard mappings

| Key | Command        | Description        |
|-----|----------------|--------------------|
| `o` | `open`         | Open hand          |
| `c` | `close`        | Close hand         |
| `s` | `spread`       | Spread fingers     |
| `l` | `clench`       | Clench fist        |
| `i` | `index_point`  | Index pointing     |
| `n` | `nonono`       | Index wag          |
| `p` | `pinch`        | Pinched fingers    |
| `v` | `victory`      | Victory/peace      |
| `k` | `perfect`      | Perfect / OK       |
| `g` | `scissors`     | Scissors motion    |
| `m` | `middle_finger`| Middle finger      |

Launch the keyboard node (in a terminal with the workspace sourced):

```bash
ros2 run amazing_hand_ros2 amazing_hand_keyboard
```

Press `h` for help or `q` to quit. Each key publishes the matching command to `amazing_hand/command`.


