cmake_minimum_required(VERSION 3.21)

project(second_life_camera_bridge LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

set(CAMERA_SDK_ROOT "" CACHE PATH "Extracted Insta360 CameraSDK Windows directory")
set(MEDIA_SDK_ROOT "" CACHE PATH "Extracted Insta360 MediaSDK Windows directory")
option(SECOND_LIFE_ENABLE_MEDIA_SDK "Build JPEG stitching support with MediaSDK" ON)

if(NOT WIN32)
    message(FATAL_ERROR "camera_bridge_cli must be built on Windows because it links CameraSDK.dll")
endif()

if(NOT EXISTS "${CAMERA_SDK_ROOT}/include/camera/camera.h")
    message(FATAL_ERROR "Set CAMERA_SDK_ROOT to the extracted CameraSDK Windows package")
endif()

add_executable(camera_bridge_cli src/camera_bridge_cli.cc)
target_include_directories(camera_bridge_cli PRIVATE "${CAMERA_SDK_ROOT}/include")
target_link_libraries(camera_bridge_cli PRIVATE "${CAMERA_SDK_ROOT}/lib/CameraSDK.lib")
target_compile_definitions(camera_bridge_cli PRIVATE WIN32 WIN32_LEAN_AND_MEAN NOMINMAX)

add_custom_command(
    TARGET camera_bridge_cli
    POST_BUILD
    COMMAND ${CMAKE_COMMAND} -E copy_directory
        "${CAMERA_SDK_ROOT}/bin"
        "$<TARGET_FILE_DIR:camera_bridge_cli>"
)

if(SECOND_LIFE_ENABLE_MEDIA_SDK)
    if(NOT EXISTS "${MEDIA_SDK_ROOT}/include/stitcher/ins_stitcher.h")
        message(FATAL_ERROR "Set MEDIA_SDK_ROOT to the extracted MediaSDK Windows package, or pass -DSECOND_LIFE_ENABLE_MEDIA_SDK=OFF")
    endif()
    target_include_directories(camera_bridge_cli PRIVATE "${MEDIA_SDK_ROOT}/include")
    target_link_libraries(camera_bridge_cli PRIVATE "${MEDIA_SDK_ROOT}/lib/MediaSDK.lib")
    target_compile_definitions(camera_bridge_cli PRIVATE SECOND_LIFE_WITH_MEDIA_SDK=1)
    add_custom_command(
        TARGET camera_bridge_cli
        POST_BUILD
        COMMAND ${CMAKE_COMMAND} -E copy_directory
            "${MEDIA_SDK_ROOT}/bin"
            "$<TARGET_FILE_DIR:camera_bridge_cli>"
    )
endif()
