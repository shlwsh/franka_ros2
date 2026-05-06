cmake_minimum_required(VERSION 3.8)
project(franka_jazzy_compat)

find_package(ament_cmake REQUIRED)

install(DIRECTORY include/
  DESTINATION include/
)

ament_export_include_directories(include)
ament_package()
