# A1AN – Robot Asistencial

A1AN es un proyecto de robótica cuyo objetivo es diseñar un robot asistente capaz de ayudar a personas con movilidad reducida dentro del hogar.

El robot está orientado a tareas como la **búsqueda de objetos, asistencia en actividades diarias y apoyo a ejercicios de rehabilitación**, utilizando tecnologías de navegación autónoma y visión artificial.

---

## Descripción del proyecto

El objetivo del proyecto es desarrollar un robot móvil que permita mejorar la **autonomía y seguridad del usuario en entornos domésticos**.

Entre las funcionalidades principales del sistema se encuentran:

* Navegación autónoma en interiores
* Localización de objetos mediante visión artificial
* Apoyo en tareas cotidianas
* Asistencia en rutinas de rehabilitación
* **Interfaz web de control remoto** (nueva)

El proyecto se centra en ofrecer una solución tecnológica accesible que ayude a personas que han perdido temporal o permanentemente parte de su movilidad.

---

## Tecnologías utilizadas

* **ROS 2 Jazzy**
* **Gazebo / simulación robótica**
* **Python**
* **Visión artificial**
* **Sistemas de navegación autónoma (Nav2)**
* **ROSBridge / roslibjs** — comunicación web ↔ ROS 2
* **HTML / CSS / JavaScript** — interfaz web desplegada en Vercel

---

## Instalación

Clonar el repositorio:

```bash
git clone https://github.com/ALANGMupv/a1an.git
cd ~/turtlebot3_ws
```

Instalar ROSBridge:

```bash
sudo apt install ros-jazzy-rosbridge-suite
```

Construir el workspace:

```bash
colcon build
```

Activar el entorno:

```bash
source install/setup.bash
```

---

## Ejecución

### Opción 1 — Script automático (recomendado)

Lanza todo el stack completo con un solo comando:

```bash
cd ~/turtlebot3_ws
./src/scripts/launch_a1an.sh
```

El script lanza automáticamente en terminales separadas y en el orden correcto:
1. Gazebo (mundo)
2. Localización y mapa
3. Navegación (Nav2)
4. Nodo de navegación web (`nav_service_node`)
5. ROSBridge WebSocket server

---

### Opción 2 — Lanzamiento manual

Abre 5 terminales y ejecuta los siguientes comandos (asegúrate de hacer `source install/setup.bash` en cada una):

**Terminal 1 — Mundo Gazebo:**
```bash
ros2 launch a1an_world a1an_world.launch.py
```

**Terminal 2 — Localización y Mapa:**
```bash
ros2 launch a1an_localization my_map_server.launch.py
```

**Terminal 3 — Navegación / Nav2:**
```bash
ros2 launch a1an_navigator navigation.launch.py
```

**Terminal 4 — Nodo de navegación web:**
```bash
ros2 run a1an_navigator nav_service_node
```

**Terminal 5 — ROSBridge:**
```bash
ros2 launch rosbridge_server rosbridge_websocket_launch.xml delay_between_messages:=0.0
```

---

## Interfaz Web

El proyecto incluye una interfaz web desplegada en Vercel que permite controlar el robot remotamente desde el navegador.

### Acceso

Abre la web en el navegador y conecta al ROSBridge introduciendo la dirección:

```
ws://localhost:9090
```

### Funcionalidades

* **Conexión** — Conecta y desconecta del ROSBridge con un botón
* **Control manual** — 4 botones direccionales + stop para mover el robot manualmente
* **Navegación por coordenadas** — Introduce X e Y y el robot navega hasta ese punto
* **Navegación por áreas** — Selector con áreas predefinidas (cocina, sala, habitación...)
* **Detener navegación** — Cancela la ruta activa y detiene el robot en su posición actual

### Cómo funciona

```
Web (Vercel) → WebSocket → ROSBridge (puerto 9090) → ROS 2 → TurtleBot
```

La navegación autónoma funciona a través de un nodo intermediario (`nav_service_node`) que recibe goals desde la web vía topic `/nav_goal` y los envía al action server de Nav2 `/navigate_to_pose`.

---

## Arquitectura del Sistema

El proyecto se basa en una arquitectura modular de **Nav2 (ROS 2 Navigation Stack)**:

* **Percepción** — Los nodos `/local_costmap` y `/global_costmap` procesan en tiempo real los datos del sensor LiDAR (`/scan`) para identificar obstáculos dinámicos y estáticos.
* **Planificación** — El `/planner_server` calcula la trayectoria óptima en el mapa global, mientras que el `/controller_server` ajusta la velocidad local para seguir el camino.
* **Gestión de Ciclo de Vida** — Los nodos `lifecycle_manager` coordinan la activación secuencial de todos los servicios para garantizar que el robot no se mueva hasta que los sensores y el mapa estén listos.
* **Interfaz de Misión** — El nodo `nav_service_node` (en `a1an_navigator`) actúa como puente entre la interfaz web y el action server de Nav2, suscribiéndose al topic `/nav_goal` y `/nav_cancel`.
* **Interfaz Web** — ROSBridge expone los topics y actions de ROS 2 vía WebSocket, permitiendo que la web interactúe con el robot usando la librería roslibjs.

---

## Equipo

Equipo A1AN – Proyecto de Robótica

* Alan Guevara
* Santiago Fuenmayor
* Nerea Aguilar
* Alejandro Vázquez
* Judit Espinoza
