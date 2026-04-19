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

Para lanzar la simulación completa (Mundo, Localización y Navegación), es necesario abrir 3 terminales y ejecutar los siguientes comandos (asegúrate de hacer `source install/setup.bash` en cada una):

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
ros2 run a1an_navigator nav_to_pose <coordenada_x> <coordenada_y>
```
Ejemplo:
```bash
ros2 run a1an_navigator nav_to_pose 1 -1
```

---

## Arquitectura del Sistema (Nodos y Comunicación)

El proyecto se basa en una arquitectura modular de **Nav2 (ROS 2 Navigation Stack)**, organizada en los siguientes bloques funcionales:

*   **Percepción**: Los nodos `/local_costmap` y `/global_costmap` procesan en tiempo real los datos del sensor LiDAR (`/scan`) para identificar obstáculos dinámicos y estáticos.
*   **Planificación**: El `/planner_server` calcula la trayectoria óptima en el mapa global, mientras que el `/controller_server` ajusta la velocidad local avanzada para seguir el camino.
*   **Gestión de Ciclo de Vida**: Los nodos `lifecycle_manager` coordinan la activación secuencial de todos los servicios para garantizar que el robot no se mueva hasta que los sensores y el mapa estén listos.
*   **Interfaz de Misión**: El nodo personalizado `nav_to_pose` (en `a1an_navigator`) actúa como cliente de acción, enviando las coordenadas objetivo al `/bt_navigator` y supervisando el progreso de la misión.

---

## Equipo

Equipo A1AN – Proyecto de Robótica

* Alan Guevara
* Santiago Fuenmayor
* Nerea Aguilar
* Alejandro Vázquez
* Judit Espinoza

