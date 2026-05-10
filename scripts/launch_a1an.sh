#!/bin/bash

# ============================================
# Safe&Sound Robotics — A1AN Launch Script
# Lanza todo el stack de ROS 2 en orden
# ============================================

# Colores para los mensajes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}A1AN Robot Stack — Iniciando...${NC}"

# 0. Matar procesos de Gazebo anteriores
echo -e "${YELLOW}[0/6] Limpiando procesos de Gazebo...${NC}"
pkill -f gazebo && pkill -f gzserver && pkill -f gzclient
sleep 2

# Cargar el entorno de ROS 2
source /opt/ros/jazzy/setup.bash
source ~/turtlebot3_ws/install/setup.bash

# 1. Gazebo — mundo
echo -e "${GREEN}[1/6] Lanzando Gazebo con camara...${NC}"
gnome-terminal --title="Gazebo" -- bash -c "
  source /opt/ros/jazzy/setup.bash
  source ~/turtlebot3_ws/install/setup.bash
  ros2 launch a1an_world a1an_world.launch.py
  exec bash"

sleep 5

# 2. Localización — mapa
echo -e "${GREEN}[2/6] Lanzando Localización...${NC}"
gnome-terminal --title="Localizacion" -- bash -c "
  source /opt/ros/jazzy/setup.bash
  source ~/turtlebot3_ws/install/setup.bash
  ros2 launch a1an_localization my_map_server.launch.py
  exec bash"

sleep 3

# 3. Navegación — Nav2
echo -e "${GREEN}[3/6] Lanzando Nav2...${NC}"
gnome-terminal --title="Nav2" -- bash -c "
  source /opt/ros/jazzy/setup.bash
  source ~/turtlebot3_ws/install/setup.bash
  ros2 launch a1an_navigator navigation.launch.py
  exec bash"

sleep 5

# 4. Nodo de navegación web
echo -e "${GREEN}[4/6] Lanzando nav_service_node...${NC}"
gnome-terminal --title="NavService" -- bash -c "
  source /opt/ros/jazzy/setup.bash
  source ~/turtlebot3_ws/install/setup.bash
  ros2 run a1an_navigator nav_service_node
  exec bash"

sleep 2

# 5. ROSBridge
echo -e "${GREEN}[5/6] Lanzando ROSBridge...${NC}"
gnome-terminal --title="ROSBridge" -- bash -c "
  source /opt/ros/jazzy/setup.bash
  source ~/turtlebot3_ws/install/setup.bash
  ros2 launch rosbridge_server rosbridge_websocket_launch.xml delay_between_messages:=0.0
  exec bash"

sleep 2

# 6. Servidor web de video para mostrar /camera/image_raw en la web
echo -e "${GREEN}[6/6] Lanzando web_video_server...${NC}"
gnome-terminal --title="CameraStream" -- bash -c "
  source /opt/ros/jazzy/setup.bash
  source ~/turtlebot3_ws/install/setup.bash
  ros2 run web_video_server web_video_server
  exec bash"

echo -e "${GREEN}Todo lanzado. WebSocket: ws://localhost:9090 | Camara: http://localhost:8080/stream?topic=/camera/image_raw&type=mjpeg${NC}"