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

El proyecto se centra en ofrecer una solución tecnológica accesible que ayude a personas que han perdido temporal o permanentemente parte de su movilidad.

---

## Tecnologías utilizadas

El proyecto utiliza principalmente:

* **ROS 2**
* **Gazebo / simulación robótica**
* **Python**
* **Visión artificial**
* **Sistemas de navegación autónoma**

---

## Instalación

Clonar el repositorio:

```bash
git clone https://github.com/ALANGMupv/a1an.git
cd ~/turtlebot3_ws
```

Construir el workspace (solo tras clonarlo):

```bash
colcon build
```

Activar el entorno:

```bash
source install/setup.bash
```

---

## Ejecución

Para lanzar la simulación completa (Mundo, Localización, Navegación y Rehabilitación), usa el launch general:

```bash
ros2 launch a1an a1an_full.launch.py
```

Este launch inicia mundo, localización, navegación y la ventana de rehabilitación con webcam. La cámara se autodetecta por
defecto; si es necesario, se puede forzar un índice concreto:

```bash
ros2 launch a1an a1an_full.launch.py camera_index:=0
```

Para lanzar todo sin la ventana de rehabilitación:

```bash
ros2 launch a1an a1an_full.launch.py launch_perception:=false
```

También se puede lanzar manualmente por terminales:

**Terminal 1 (Mundo Gazebo):**
```bash
ros2 launch a1an_world a1an_world.launch.py
```

**Terminal 2 (Localización y Mapa):**
```bash
ros2 launch a1an_localization my_map_server.launch.py
```

**Terminal 3 (Navegación / Nav2):**
```bash
ros2 launch a1an_navigator navigation.launch.py
```

**Terminal 4 (Opcional - Enviar meta mediante script):**
Para enviar un objetivo de navegación al robot automáticamente introduciendo coordenadas manualmente, ejecuta:
```bash
ros2 run a1an_navigator nav_to_pose.py <coordenada_x> <coordenada_y>
```
Ejemplo:
```bash
ros2 run a1an_navigator nav_to_pose.py 1 -1
```

**Terminal 5 (Opcional - Detección de pose humana con webcam):**
Para abrir una ventana con la cámara del ordenador y visualizar los puntos del cuerpo detectados, instala primero las dependencias:
```bash
pip install opencv-python mediapipe
```

Después reconstruye el workspace y lanza el nodo de percepción:
```bash
colcon build
source install/setup.bash
ros2 launch a1an_perception webcam_pose.launch.py
```

La ventana se puede cerrar pulsando `q`. Por defecto el nodo busca automáticamente una webcam disponible. Si se quiere forzar una
cámara concreta, se puede indicar su índice:
```bash
ros2 launch a1an_perception webcam_pose.launch.py camera_index:=1
```

Por defecto, el launch usa una configuración estable para Ubuntu nativo y VirtualBox: detección automática de cámara, 640x480,
15 FPS, formato MJPG con fallback a otros formatos y complejidad 1 de MediaPipe. Si se quiere indicar de forma explícita:
```bash
ros2 launch a1an_perception webcam_pose.launch.py camera_index:=-1 frame_width:=640 frame_height:=480 camera_fps:=15 camera_fourcc:=MJPG model_complexity:=1
```

Esta primera demo de rehabilitación analiza una rutina de dos ejercicios: elevación de brazos y flexión de codos. La
ventana muestra el esqueleto detectado, cuenta repeticiones y ofrece feedback básico si el movimiento no es simétrico o no alcanza
la posición esperada. El objetivo por defecto es de 10 repeticiones por ejercicio; al completar el primero, el sistema pasa
automáticamente al segundo. El ejercicio actual se puede reiniciar pulsando `e`, y la rutina completa pulsando `r`.

Para una demo más corta:
```bash
ros2 launch a1an_perception webcam_pose.launch.py target_repetitions:=5
```

---

## Arquitectura del Sistema (Nodos y Comunicación)

El proyecto se basa en una arquitectura modular de **Nav2 (ROS 2 Navigation Stack)**, organizada en los siguientes bloques funcionales:

*   **Percepción**: Los nodos `/local_costmap` y `/global_costmap` procesan en tiempo real los datos del sensor LiDAR (`/scan`) para identificar obstáculos dinámicos y estáticos.
*   **Planificación**: El `/planner_server` calcula la trayectoria óptima en el mapa global, mientras que el `/controller_server` ajusta la velocidad local avanzada para seguir el camino.
*   **Gestión de Ciclo de Vida**: Los nodos `lifecycle_manager` coordinan la activación secuencial de todos los servicios para garantizar que el robot no se mueva hasta que los sensores y el mapa estén listos.
*   **Interfaz de Misión**: El script personalizado `nav_to_pose.py` (en `a1an_navigator`) actúa como cliente de acción, enviando las coordenadas objetivo al `/bt_navigator` y supervisando el progreso de la misión.

---

## Equipo

Equipo A1AN – Proyecto de Robótica

* Alan Guevara
* Santiago Fuenmayor
* Nerea Aguilar
* Alejandro Vázquez
* Judit Espinoza

