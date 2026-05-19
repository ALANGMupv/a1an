#!/bin/bash

# ============================================
# Safe&Sound Robotics — A1AN Launch Script (MAPPING)
# Lanza el nodo de SLAM para mapear el entorno real con el PC
# ============================================

# Colores para los mensajes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo ""
echo -e "${CYAN}╔═══════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║ A1AN — Robot REAL — Iniciando Mapeo (SLAM) en PC...   ║${NC}"
echo -e "${CYAN}╚═══════════════════════════════════════════════════════╝${NC}"
echo ""

echo -e "${YELLOW}[INFO] Recordatorio: Debes haber lanzado el robot en la Raspberry Pi por SSH:${NC}"
echo -e "${YELLOW}       ssh ubuntu@IP_DEL_ROBOT${NC}"
echo -e "${YELLOW}       ros2 launch turtlebot3_bringup robot.launch.py${NC}"
echo ""

# ── Cargar el entorno de ROS 2 ──────────────────────────────────────────
source /opt/ros/jazzy/setup.bash
source ~/turtlebot3_ws/install/setup.bash

# 1. SLAM (Cartographer)
echo -e "${GREEN}[1/3] Lanzando Cartographer (SLAM) con use_sim_time:=false...${NC}"
gnome-terminal --title="SLAM Real" -- bash -c "
  source /opt/ros/jazzy/setup.bash
  source ~/turtlebot3_ws/install/setup.bash
  ros2 launch turtlebot3_cartographer cartographer.launch.py use_sim_time:=False
  exec bash"

sleep 3

# 2. Teleoperación
echo -e "${GREEN}[2/3] Lanzando Teleoperación por teclado...${NC}"
gnome-terminal --title="Teleop" -- bash -c "
  source /opt/ros/jazzy/setup.bash
  source ~/turtlebot3_ws/install/setup.bash
  ros2 run turtlebot3_teleop teleop_keyboard
  exec bash"

# 3. Servidor web de video para la cámara (Opcional, pero útil)
echo -e "${GREEN}[3/3] Lanzando web_video_server...${NC}"
gnome-terminal --title="CameraStream" -- bash -c "
  source /opt/ros/jazzy/setup.bash
  source ~/turtlebot3_ws/install/setup.bash
  ros2 run web_video_server web_video_server --ros-args -p port:=8081 -p use_sim_time:=false
  exec bash"

echo ""
echo -e "${CYAN}╔═══════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║         Mapeo Iniciado. Usa la terminal de Teleop     ║${NC}"
echo -e "${CYAN}║         para mover el robot y mapear la casa.         ║${NC}"
echo -e "${CYAN}╠═══════════════════════════════════════════════════════╣${NC}"
echo -e "${CYAN}║ Para guardar el mapa abre otra terminal y ejecuta:    ║${NC}"
echo -e "${CYAN}║ ${GREEN}ros2 run nav2_map_server map_saver_cli -f ~/turtlebot3_ws/src/a1an/a1an_localization/map/my_map${NC} ║${NC}"
echo -e "${CYAN}╚═══════════════════════════════════════════════════════╝${NC}"
