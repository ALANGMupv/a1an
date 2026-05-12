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

Instalar ROSBridge y el servidor de video para la camara:

```bash
sudo apt install ros-jazzy-rosbridge-suite
sudo apt install ros-jazzy-web-video-server
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

Lanza todo el stack completo con un solo comando (asegúrate de hacer source primero):

```bash
cd ~/turtlebot3_ws
source install/setup.bash
./src/a1an/scripts/launch_a1an.sh
```

El script lanza automáticamente en terminales separadas y en el orden correcto:
1. Gazebo (mundo)
2. Localización y mapa
3. Navegación (Nav2)
4. Nodo de navegación web (`nav_service_node`)
5. ROSBridge WebSocket server
6. Detector de objetos (`a1an_vision`)
7. Servidor de video de la camara (`web_video_server`)

---

### Opción 2 — Lanzamiento manual

Abre 7 terminales y ejecuta los siguientes comandos (asegúrate de hacer `source install/setup.bash` en cada una):

**Terminal 1 — Mundo Gazebo:**
```bash
export TURTLEBOT3_MODEL=burger_cam
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

**Terminal 6 - Vision artificial:**
```bash
ros2 launch a1an_vision vision.launch.py
```

**Terminal 7 - Servidor de video de la camara:**
```bash
ros2 run web_video_server web_video_server --ros-args -p port:=8081
```

---

## Interfaz Web

El proyecto incluye una interfaz web desplegada en Vercel que permite controlar el robot remotamente desde el navegador.

### Acceso

Abre la web en el navegador y conecta al ROSBridge introduciendo la dirección:

```
ws://localhost:9090
```

La imagen de la camara se sirve mediante `web_video_server` desde:

```
http://localhost:8081/stream?topic=/camera/image_raw&type=mjpeg
```

La imagen procesada por vision artificial, con bounding boxes y etiquetas, se sirve desde:

```
http://localhost:8081/stream?topic=/a1an_vision/debug_image&type=mjpeg
```

`localhost` solo funciona cuando el navegador se abre en el mismo ordenador que esta ejecutando ROS 2 y `web_video_server`. Si se usa la web desplegada o se accede desde otro equipo, hay que sustituirlo por la IP del ordenador del robot/simulador:

```
http://IP_DEL_ROBOT_O_PC_ROS:8081/stream?topic=/camera/image_raw&type=mjpeg
```

Para la imagen procesada desde otro equipo:

```
http://IP_DEL_ROBOT_O_PC_ROS:8081/stream?topic=/a1an_vision/debug_image&type=mjpeg
```

### Funcionalidades

* **Conexión** — Conecta y desconecta del ROSBridge con un botón
* **Control manual** — 4 botones direccionales + stop para mover el robot manualmente
* **Navegación por coordenadas** — Introduce X e Y y el robot navega hasta ese punto
* **Navegación por áreas** — Selector con áreas predefinidas (cocina, sala, habitación...)
* **Detener navegación** — Cancela la ruta activa y detiene el robot en su posición actual
* **Camara del robot** - Muestra en streaming la imagen publicada en `/camera/image_raw`
* **Vision artificial** - Puede mostrar `/a1an_vision/debug_image` y leer detecciones desde `/a1an_vision/detected_objects`

### Cómo funciona

```
Web (Vercel) → WebSocket → ROSBridge (puerto 9090) → ROS 2 → TurtleBot
```

La navegación autónoma funciona a través de un nodo intermediario (`nav_service_node`) que recibe goals desde la web vía topic `/nav_goal` y los envía al action server de Nav2 `/navigate_to_pose`.

### Pruebas y Troubleshooting (Paso 5)

Si al conectar la interfaz web el plano de la casa no carga, asegúrate de que ROS 2 está publicando el mapa.

1. Ejecuta ROSBridge y verifica que el topic existe:
   ```bash
   ros2 topic list
   ```
   *(Debe aparecer `/map` entre los resultados).*

2. Comprueba que está emitiendo los datos del grid:
   ```bash
   ros2 topic echo /map --once
   ```
   *(Debería mostrarte una enorme lista de números `-1`, `0` o `100`).*

3. En la web:
   - Haz clic en *Conectar* a `ws://localhost:9090`.
   - Si el topic `/map` funciona pero la pantalla sigue negra, revisa inspeccionando los estilos del `<canvas id="rosMapCanvas">` en modo desarrollador de Google Chrome.

El video de la camara no se envia por ROSBridge. La web carga directamente el stream MJPEG publicado por `web_video_server`, que lee el topic `/camera/image_raw`.

La imagen con detecciones tampoco se envia por ROSBridge. La web debe cargar el stream MJPEG de `/a1an_vision/debug_image` desde `web_video_server`. Los datos estructurados de deteccion si se consumen por ROSBridge leyendo `/a1an_vision/detected_objects`.

### Contrato para la web

La web debe conectarse a ROSBridge:

```text
ws://localhost:9090
```

Si la web se abre desde otro equipo:

```text
ws://IP_DEL_ROBOT_O_PC_ROS:9090
```

Topic de detecciones:

```text
/a1an_vision/detected_objects
```

Tipo:

```text
std_msgs/String
```

El campo `data` contiene un JSON con esta estructura:

```json
{
  "detected": true,
  "message": "Objetos relevantes detectados",
  "image_width": 320,
  "image_height": 240,
  "objects": [
    {
      "label": "Botella",
      "confidence": 1.0,
      "center_x": 160,
      "center_y": 120,
      "bbox": [120, 60, 50, 120],
      "position": "centro-centro"
    }
  ]
}
```

Valores posibles de `label`:

```text
Botella
Telefono
Medicinas
```

Stream recomendado para mostrar vision en la web:

```text
http://localhost:8081/stream?topic=/a1an_vision/debug_image&type=mjpeg
```

### Comprobacion de la camara

Con Gazebo lanzado usando `burger_cam`, se puede comprobar que la camara esta disponible con:

```bash
ros2 topic list | grep camera
ros2 topic info /camera/image_raw -v
```

Debe aparecer al menos:

```text
/camera/camera_info
/camera/image_raw
```

Para probar el stream antes de abrir la web:

```text
http://localhost:8081/snapshot?topic=/camera/image_raw
http://localhost:8081/stream?topic=/camera/image_raw&type=mjpeg
```

### Comprobacion de vision artificial

El nodo de vision se lanza con:

```bash
ros2 launch a1an_vision vision.launch.py
```

Publica las detecciones en:

```bash
ros2 topic echo /a1an_vision/detected_objects
```

Tambien publica una imagen procesada con los bounding boxes en:

```bash
ros2 topic info /a1an_vision/debug_image
```

Si `web_video_server` esta activo, la imagen procesada se puede comprobar en:

```text
http://localhost:8081/stream?topic=/a1an_vision/debug_image&type=mjpeg
```

---

## Arquitectura del Sistema

El proyecto se basa en una arquitectura modular de **Nav2 (ROS 2 Navigation Stack)**:

* **Camara** - El robot se lanza como `burger_cam` para publicar imagen en `/camera/image_raw`; `web_video_server` expone ese topic como stream MJPEG para la interfaz web.
* **Vision artificial** - El paquete `a1an_vision` procesa `/camera/image_raw`, detecta objetos domesticos por color y publica resultados en `/a1an_vision/detected_objects`.
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
