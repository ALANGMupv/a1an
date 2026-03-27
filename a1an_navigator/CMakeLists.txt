cmake_minimum_required(VERSION 3.8)
project(a1an_navigator)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)

# Instalar los launch files
install(DIRECTORY
  launch
  DESTINATION share/${PROJECT_NAME}
)

# Instalar los scripts de python
install(PROGRAMS
  scripts/nav_to_pose.py
  DESTINATION lib/${PROJECT_NAME}
)

ament_package()
