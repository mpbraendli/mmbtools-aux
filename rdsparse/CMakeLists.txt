########################################################################
# Project setup
########################################################################

cmake_minimum_required(VERSION 2.8)
project(rdsparse CXX)

# Select the release build type by default to get optimization flags
if(NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE "Debug")
    message(STATUS "Build type not specified: defaulting to debug.")
endif(NOT CMAKE_BUILD_TYPE)
set(CMAKE_BUILD_TYPE ${CMAKE_BUILD_TYPE} CACHE STRING "")

list(APPEND CMAKE_MODULE_PATH ${CMAKE_SOURCE_DIR}/cmake/Modules)

# Set the version information here
set(VERSION_INFO_MAJOR_VERSION 0)
set(VERSION_INFO_API_COMPAT    0)
set(VERSION_INFO_MINOR_VERSION 0)
set(VERSION_INFO_MAINT_VERSION git)


########################################################################
# Compiler specific setup
########################################################################

set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -g -W -Wall -Wno-unused-parameter -std=c++11")


########################################################################
# Find build dependencies
########################################################################

find_package(Boost COMPONENTS system REQUIRED)


########################################################################
# Setup apps
########################################################################

list(APPEND rdsparse_sources
    rdsparse.cc
    decoder_impl.cc
    parser_impl.cc
)

set_source_files_properties(${rdsparse_sources} PROPERTIES LANGUAGE "CXX")
add_executable(rdsparse ${rdsparse_sources})
target_link_libraries(rdsparse
  ${Boost_SYSTEM_LIBRARY}
)

install(TARGETS rdsparse DESTINATION bin)


########################################################################
# Create uninstall target
########################################################################

configure_file(
    "${CMAKE_CURRENT_SOURCE_DIR}/cmake/cmake_uninstall.cmake.in"
    "${CMAKE_CURRENT_BINARY_DIR}/cmake_uninstall.cmake"
    IMMEDIATE @ONLY)

add_custom_target(uninstall
    COMMAND ${CMAKE_COMMAND} -P ${CMAKE_CURRENT_BINARY_DIR}/cmake_uninstall.cmake)

