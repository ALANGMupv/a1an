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
cd a1an
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

Para lanzar la simulación:

```bash
ros2 launch a1an_world a1an_world.launch.py
```

---

## Equipo

Equipo A1AN – Proyecto de Robótica

* Alan Guevara
* Santiago Fuenmayor
* Nerea Aguilar
* Alejandro Vázquez
* Judit Espinoza

