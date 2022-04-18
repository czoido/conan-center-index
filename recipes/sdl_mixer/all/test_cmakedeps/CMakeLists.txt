cmake_minimum_required(VERSION 3.15)
project(test_package CXX)

find_package(SDL2_mixer REQUIRED CONFIG)

add_executable(${PROJECT_NAME} test_package.cpp)
target_link_libraries(${PROJECT_NAME} SDL2_mixer::SDL2_mixer)
