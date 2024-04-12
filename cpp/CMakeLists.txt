cmake_minimum_required(VERSION 3.10)
project(BattleBotDriveSystem)

# Specify the C++ standard
set(CMAKE_CXX_STANDARD 11)
set(CMAKE_CXX_STANDARD_REQUIRED True)

# Add the libwebrtc directory
# Ensure that the libwebrtc is correctly cloned in your project or properly installed
# You may need to adjust this path according to where libwebrtc is in your project
add_subdirectory(libwebrtc)

# Include directories
include_directories(${CMAKE_CURRENT_SOURCE_DIR}/src)
include_directories(${CMAKE_CURRENT_SOURCE_DIR}/libwebrtc/include)

# Find all source files in the src directory
file(GLOB SOURCES "src/*.cpp")

# Define the executable for the project
add_executable(BattleBot ${SOURCES})

# Link the executable with the libwebrtc library
# You might need to link with specific libraries from libwebrtc or its dependencies
target_link_libraries(BattleBot webrtc)
