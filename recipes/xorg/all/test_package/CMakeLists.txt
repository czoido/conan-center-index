cmake_minimum_required(VERSION 2.8.12)
project(test_package)

find_package(xorg REQUIRED)

set(SOURCES test_package.c)

add_executable(${PROJECT_NAME} ${SOURCES})
target_link_libraries(${PROJECT_NAME} xorg::xorg)
