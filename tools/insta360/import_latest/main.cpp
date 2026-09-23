// import_latest — skeleton for Camera SDK file import (no TakePhoto).
// Fill in DeviceDiscovery / Open using the official CameraSDKDemo as reference.
//
// Build: see README.md in this folder.

#include <iostream>
#include <string>

// After wiring include paths:
// #include "camera/camera.h"
// #include "camera/device_discovery.h"

static void print_usage() {
    std::cerr
        << "Usage:\n"
        << "  import_latest --health\n"
        << "  import_latest --download-latest --out <local.jpg>\n"
        << "\n"
        << "Product flow: user shoots on camera body, then this tool downloads.\n"
        << "Do NOT call TakePhoto here.\n";
}

int main(int argc, char** argv) {
    if (argc < 2) {
        print_usage();
        return 2;
    }

    std::string cmd = argv[1];
    if (cmd == "--health") {
        // TODO: DeviceDiscovery + try Open
        // On success:
        std::cout
            << "{\"camera_connected\":false,"
            << "\"camera_model\":\"X4 Air\","
            << "\"firmware\":null,"
            << "\"detail\":\"import_latest skeleton — implement DeviceDiscovery/Open\"}"
            << std::endl;
        return 0;
    }

    if (cmd == "--download-latest") {
        std::string out;
        for (int i = 2; i + 1 < argc; ++i) {
            if (std::string(argv[i]) == "--out") {
                out = argv[++i];
            }
        }
        if (out.empty()) {
            std::cerr << "DOWNLOAD_FAILED: missing --out\n";
            return 1;
        }

        // TODO:
        // 1. Open camera (Android/USB mode)
        // 2. auto files = cam.GetCameraFilesList();
        // 3. pick newest .jpg / .insp panorama path
        // 4. cam.DownloadCameraFile(remote, out);
        // 5. print JSON with local_path, camera_file, width, height

        std::cerr
            << "SDK_INIT_FAILED: import_latest.exe is a skeleton. "
            << "Implement GetCameraFilesList + DownloadCameraFile "
            << "(see CameraSDK example / Demo). Out=" << out << "\n";
        return 1;
    }

    print_usage();
    return 2;
}
