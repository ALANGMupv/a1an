#!/bin/bash

# ============================================
# Safe&Sound Robotics — A1AN Launch Script
# Lanza todo el stack ROS 2 para el ROBOT REAL desde el PC
# ============================================

# Colores para los mensajes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo ""
echo -e "${CYAN}╔═══════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║    A1AN — Robot REAL — Iniciando stack en el PC...    ║${NC}"
echo -e "${CYAN}╚═══════════════════════════════════════════════════════╝${NC}"
echo ""

echo -e "${YELLOW}[INFO] Recordatorio: Debes haber lanzado el robot en la Raspberry Pi por SSH:${NC}"
echo -e "${YELLOW}       ssh ubuntu@IP_DEL_ROBOT${NC}"
echo -e "${YELLOW}       ros2 launch turtlebot3_bringup robot.launch.py${NC}"
echo ""

# Comprobar argumento
MAP_MODE=false
if [ "$1" == "--map" ]; then
    MAP_MODE=true
    echo -e "${YELLOW}[INFO] MODO MAPEO ACTIVADO (--map)${NC}"
fi

# ── Cargar el entorno de ROS 2 ──────────────────────────────────────────
source /opt/ros/jazzy/setup.bash
source ~/turtlebot3_ws/install/setup.bash

if [ "$MAP_MODE" = true ]; then
    # 1. SLAM (Mapeo)
    echo -e "${GREEN}[1/6] Lanzando SLAM Toolbox (Mapeo automático)...${NC}"
    gnome-terminal --title="SLAM Real" -- bash -c "
      source /opt/ros/jazzy/setup.bash
      source ~/turtlebot3_ws/install/setup.bash
      ros2 launch nav2_bringup slam_launch.py use_sim_time:=False
      exec bash"
else
    # 1. Localización — Mapa + AMCL
    echo -e "${GREEN}[1/6] Lanzando Localización (Map Server + AMCL) con use_sim_time:=false...${NC}"
    gnome-terminal --title="Localizacion Real" -- bash -c "
      source /opt/ros/jazzy/setup.bash
      source ~/turtlebot3_ws/install/setup.bash
      ros2 launch a1an_localization my_map_server.launch.py use_sim_time:=false
      exec bash"
fi

sleep 3

# 2. Navegación — Nav2
echo -e "${GREEN}[2/6] Lanzando Nav2 con use_sim_time:=false...${NC}"
gnome-terminal --title="Nav2 Real" -- bash -c "
  source /opt/ros/jazzy/setup.bash
  source ~/turtlebot3_ws/install/setup.bash
  ros2 launch a1an_navigator navigation.launch.py use_sim_time:=false
  exec bash"

sleep 5

# 3. Nodo de navegación web
echo -e "${GREEN}[3/6] Lanzando nav_service_node...${NC}"
gnome-terminal --title="NavService" -- bash -c "
  source /opt/ros/jazzy/setup.bash
  source ~/turtlebot3_ws/install/setup.bash
  ros2 run a1an_navigator nav_service_node --ros-args -p use_sim_time:=false
  exec bash"

sleep 2

# 4. ROSBridge
echo -e "${GREEN}[4/6] Lanzando ROSBridge...${NC}"
gnome-terminal --title="ROSBridge" -- bash -c "
  source /opt/ros/jazzy/setup.bash
  source ~/turtlebot3_ws/install/setup.bash
  ros2 launch rosbridge_server rosbridge_websocket_launch.xml delay_between_messages:=0.0
  exec bash"

sleep 2

# 5. Visión artificial: detección de objetos
echo -e "${GREEN}[5/6] Lanzando detector de objetos...${NC}"
gnome-terminal --title="A1ANVision" -- bash -c "
  source /opt/ros/jazzy/setup.bash
  source ~/turtlebot3_ws/install/setup.bash
  ros2 launch a1an_vision vision.launch.py
  exec bash"

sleep 2

# 6. Servidor web de video para la cámara
echo -e "${GREEN}[6/6] Lanzando web_video_server...${NC}"
gnome-terminal --title="CameraStream" -- bash -c "
  source /opt/ros/jazzy/setup.bash
  source ~/turtlebot3_ws/install/setup.bash
  ros2 run web_video_server web_video_server --ros-args -p port:=8081 -p use_sim_time:=false
  exec bash"

echo ""
echo -e "${CYAN}╔═══════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║              A1AN Robot REAL — ¡Todo listo!           ║${NC}"
echo -e "${CYAN}╠═══════════════════════════════════════════════════════╣${NC}"
echo -e "${CYAN}║${NC} WebSocket:  ${GREEN}ws://localhost:9090${NC}                      ${CYAN}║${NC}"
echo -e "${CYAN}║${NC} Cámara:     ${GREEN}http://localhost:8081/stream?topic=/camera/image_raw&type=mjpeg${NC}"
echo -e "${CYAN}║${NC} Visión:     ${GREEN}http://localhost:8081/stream?topic=/a1an_vision/debug_image&type=mjpeg${NC}"
echo -e "${CYAN}║${NC} Detecciones:${GREEN} /a1an_vision/detected_objects${NC}"
echo -e "${CYAN}╚═══════════════════════════════════════════════════════╝${NC}"