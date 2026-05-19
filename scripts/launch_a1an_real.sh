#!/bin/bash

# ============================================
# Safe&Sound Robotics — A1AN Launch Script
# MAPEO del entorno REAL con Cartographer (use_sim_time:=False)
# ============================================
# Sigue el flujo del colab ROS2-SLAM-01:
#   1. turtlebot3_cartographer  → construye el mapa con /scan + /odom
#   2. turtlebot3_teleop        → mueve el robot con el teclado
#
# Una vez recorrido el entorno, guardar el mapa con map_saver_cli
# (ver instrucciones al final del script).
# ============================================

# Colores para los mensajes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo ""
echo -e "${CYAN}╔═══════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║   A1AN — Robot REAL — Iniciando MAPEO en el PC...     ║${NC}"
echo -e "${CYAN}╚═══════════════════════════════════════════════════════╝${NC}"
echo ""

echo -e "${YELLOW}[INFO] Antes de ejecutar este script, lanza el robot en la Raspberry Pi por SSH:${NC}"
echo -e "${YELLOW}       ssh ubuntu@IP_DEL_ROBOT${NC}"
echo -e "${YELLOW}       export TURTLEBOT3_MODEL=burger${NC}"
echo -e "${YELLOW}       ros2 launch turtlebot3_bringup robot.launch.py${NC}"
echo ""

# ── Cargar el entorno de ROS 2 ──────────────────────────────────────────
source /opt/ros/jazzy/setup.bash
source ~/turtlebot3_ws/install/setup.bash
export TURTLEBOT3_MODEL=burger

# ════════════════════════════════════════════════════════════════════════
# 1. Cartographer (SLAM) — use_sim_time:=False porque es el robot real
# ════════════════════════════════════════════════════════════════════════
echo -e "${GREEN}[1/2] Lanzando Cartographer (SLAM) con use_sim_time:=False...${NC}"
gnome-terminal --title="Cartographer" -- bash -c "
  source /opt/ros/jazzy/setup.bash
  source ~/turtlebot3_ws/install/setup.bash
  export TURTLEBOT3_MODEL=burger
  ros2 launch turtlebot3_cartographer cartographer.launch.py use_sim_time:=False
  exec bash"

sleep 3

# ════════════════════════════════════════════════════════════════════════
# 2. Teleoperación por teclado para mover el robot durante el escaneo
# ════════════════════════════════════════════════════════════════════════
echo -e "${GREEN}[2/2] Lanzando Teleop (teleop_keyboard)...${NC}"
gnome-terminal --title="Teleop" -- bash -c "
  source /opt/ros/jazzy/setup.bash
  source ~/turtlebot3_ws/install/setup.bash
  export TURTLEBOT3_MODEL=burger
  ros2 run turtlebot3_teleop teleop_keyboard
  exec bash"

echo ""
echo -e "${CYAN}╔═══════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║      Mapeo en marcha. Usa la terminal Teleop para     ║${NC}"
echo -e "${CYAN}║      mover el robot y construir el mapa en RViz.      ║${NC}"
echo -e "${CYAN}╠═══════════════════════════════════════════════════════╣${NC}"
echo -e "${CYAN}║  Cuando termines de mapear, abre otra terminal y      ║${NC}"
echo -e "${CYAN}║  guarda el mapa directamente en el paquete:           ║${NC}"
echo -e "${CYAN}║                                                       ║${NC}"
echo -e "${CYAN}║  ${GREEN}source /opt/ros/jazzy/setup.bash${NC}                     ${CYAN}║${NC}"
echo -e "${CYAN}║  ${GREEN}source ~/turtlebot3_ws/install/setup.bash${NC}            ${CYAN}║${NC}"
echo -e "${CYAN}║  ${GREEN}ros2 run nav2_map_server map_saver_cli -f \\${NC}          ${CYAN}║${NC}"
echo -e "${CYAN}║    ${GREEN}~/turtlebot3_ws/src/a1an/a1an_localization/map/my_map_real${NC} ${CYAN}║${NC}"
echo -e "${CYAN}╚═══════════════════════════════════════════════════════╝${NC}"
