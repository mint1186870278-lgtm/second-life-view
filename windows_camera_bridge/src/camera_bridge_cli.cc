#include <camera/camera.h>
#include <camera/device_discovery.h>

#ifdef SECOND_LIFE_WITH_MEDIA_SDK
#include <stitcher/ins_stitcher.h>
#endif

#include <algorithm>
#include <atomic>
#include <chrono>
#include <cctype>
#include <cstdlib>
#include <exception>
#include <filesystem>
#include <iomanip>
#include <iostream>
#include <memory>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

#ifdef _WIN32
#include <windows.h>
#include <shellapi.h>
#endif

namespace fs = std::filesystem;

namespace {

constexpr const char* kResultPrefix = "SECOND_LIFE_CAMERA_RESULT=";
std::atomic_uint64_t g_sequence{0};

struct Options {
    std::string command;
    fs::path output_dir;
    int service_port = 9099;
    std::string camera_serial;
    std::string remote_path;
    std::string raw_type = "off";
    int timeout_ms = 0;
    bool stitch = true;
    int output_width = 4096;
    int output_height = 2048;
    fs::path media_models_dir;
};

struct CameraIdentity {
    std::string serial;
    std::string camera_name;
    std::string firmware;
    int camera_type = 0;
};

fs::path path_from_utf8(const std::string& value) {
    return fs::u8path(value);
}

std::string path_to_utf8(const fs::path& value) {
    return value.u8string();
}

#ifdef _WIN32
std::vector<std::string> build_utf8_args(std::vector<char*>& output_args) {
    int argument_count = 0;
    LPWSTR* wide_args = CommandLineToArgvW(GetCommandLineW(), &argument_count);
    if (!wide_args) return {};

    std::vector<std::string> storage;
    storage.reserve(argument_count);
    for (int index = 0; index < argument_count; ++index) {
        const int byte_count = WideCharToMultiByte(CP_UTF8, 0, wide_args[index], -1, nullptr, 0, nullptr, nullptr);
        if (byte_count <= 0) {
            LocalFree(wide_args);
            return {};
        }
        std::vector<char> utf8(static_cast<size_t>(byte_count));
        if (!WideCharToMultiByte(
                CP_UTF8,
                0,
                wide_args[index],
                -1,
                utf8.data(),
                byte_count,
                nullptr,
                nullptr
            )) {
            LocalFree(wide_args);
            return {};
        }
        storage.emplace_back(utf8.data(), static_cast<size_t>(byte_count - 1));
    }
    LocalFree(wide_args);

    output_args.reserve(storage.size());
    for (auto& value : storage) output_args.push_back(value.data());
    return storage;
}
#endif

std::string json_escape(const std::string& value) {
    std::ostringstream output;
    for (const unsigned char character : value) {
        switch (character) {
        case '\\': output << "\\\\"; break;
        case '"': output << "\\\""; break;
        case '\b': output << "\\b"; break;
        case '\f': output << "\\f"; break;
        case '\n': output << "\\n"; break;
        case '\r': output << "\\r"; break;
        case '\t': output << "\\t"; break;
        default:
            if (character < 0x20) {
                output << "\\u" << std::hex << std::setw(4) << std::setfill('0')
                       << static_cast<int>(character) << std::dec << std::setfill(' ');
            } else {
                output << static_cast<char>(character);
            }
        }
    }
    return output.str();
}

std::string json_string(const std::string& value) {
    return "\"" + json_escape(value) + "\"";
}

std::string json_bool(bool value) {
    return value ? "true" : "false";
}

std::string json_array(const std::vector<std::string>& values) {
    std::ostringstream output;
    output << "[";
    for (size_t index = 0; index < values.size(); ++index) {
        if (index) output << ",";
        output << json_string(values[index]);
    }
    output << "]";
    return output.str();
}

std::string identity_json(const CameraIdentity& identity) {
    std::ostringstream output;
    output << "{"
           << "\"serial\":" << json_string(identity.serial) << ","
           << "\"camera_name\":" << json_string(identity.camera_name) << ","
           << "\"firmware\":" << json_string(identity.firmware) << ","
           << "\"camera_type\":" << identity.camera_type
           << "}";
    return output.str();
}

[[noreturn]] void fail(const std::string& message) {
    throw std::runtime_error(message);
}

int parse_integer(const std::string& value, const char* option) {
    try {
        size_t consumed = 0;
        const int parsed = std::stoi(value, &consumed, 10);
        if (consumed != value.size()) fail(std::string("invalid value for ") + option);
        return parsed;
    } catch (const std::exception&) {
        fail(std::string("invalid value for ") + option);
    }
}

bool parse_bool(const std::string& value, const char* option) {
    if (value == "true" || value == "1") return true;
    if (value == "false" || value == "0") return false;
    fail(std::string("invalid value for ") + option + "; expected true or false");
}

std::string require_value(int& index, int argc, char* argv[], const char* option) {
    if (++index >= argc) fail(std::string("missing value for ") + option);
    return argv[index];
}

void print_usage() {
    std::cerr
        << "Usage: camera_bridge_cli --command <status|list-files|capture|download> --output-dir <path> [options]\n"
        << "  --service-port <port>\n"
        << "  --camera-serial <serial>\n"
        << "  --remote <camera remote file path>          (download only)\n"
        << "  --raw-type <off|dng|pureshot|pureshot_raw> (capture only)\n"
        << "  --timeout-ms <milliseconds>\n"
        << "  --stitch <true|false>\n"
        << "  --output-width <pixels> --output-height <pixels>\n"
        << "  --media-models-dir <path>\n";
}

Options parse_options(int argc, char* argv[]) {
    Options options;
    for (int index = 1; index < argc; ++index) {
        const std::string argument = argv[index];
        if (argument == "--help" || argument == "-h") {
            print_usage();
            std::exit(0);
        }
        if (argument == "--json") continue;
        if (argument == "--command") {
            options.command = require_value(index, argc, argv, "--command");
        } else if (argument == "--output-dir") {
            options.output_dir = path_from_utf8(require_value(index, argc, argv, "--output-dir"));
        } else if (argument == "--service-port") {
            options.service_port = parse_integer(require_value(index, argc, argv, "--service-port"), "--service-port");
        } else if (argument == "--camera-serial") {
            options.camera_serial = require_value(index, argc, argv, "--camera-serial");
        } else if (argument == "--remote") {
            options.remote_path = require_value(index, argc, argv, "--remote");
        } else if (argument == "--raw-type") {
            options.raw_type = require_value(index, argc, argv, "--raw-type");
        } else if (argument == "--timeout-ms") {
            options.timeout_ms = parse_integer(require_value(index, argc, argv, "--timeout-ms"), "--timeout-ms");
        } else if (argument == "--stitch") {
            options.stitch = parse_bool(require_value(index, argc, argv, "--stitch"), "--stitch");
        } else if (argument == "--output-width") {
            options.output_width = parse_integer(require_value(index, argc, argv, "--output-width"), "--output-width");
        } else if (argument == "--output-height") {
            options.output_height = parse_integer(require_value(index, argc, argv, "--output-height"), "--output-height");
        } else if (argument == "--media-models-dir") {
            options.media_models_dir = path_from_utf8(require_value(index, argc, argv, "--media-models-dir"));
        } else {
            fail("unknown option: " + argument);
        }
    }

    if (options.command.empty()) fail("--command is required");
    if (options.command != "status" && options.command != "list-files" && options.command != "capture" &&
        options.command != "download") {
        fail("--command must be status, list-files, capture, or download");
    }
    if (options.command == "download" && options.remote_path.empty()) fail("--remote is required for download");
    if (options.output_dir.empty()) fail("--output-dir is required");
    if (options.service_port < 1 || options.service_port > 65535) fail("--service-port must be 1-65535");
    if (options.timeout_ms < 0 || options.timeout_ms > 600000) fail("--timeout-ms must be 0-600000");
    if (options.output_width < 512 || options.output_height < 256) fail("output dimensions are too small");
    return options;
}

CameraIdentity copy_identity(const ins_camera::DeviceDescriptor& descriptor) {
    return {
        descriptor.serial_number,
        descriptor.camera_name,
        descriptor.fw_version,
        static_cast<int>(descriptor.camera_type),
    };
}

class CameraSession {
public:
    explicit CameraSession(const Options& options) {
        ins_camera::SetLogLevel(ins_camera::LogLevel::ERR);
        ins_camera::DeviceDiscovery discovery;
        auto descriptors = discovery.GetAvailableDevices();
        if (descriptors.empty()) fail("no Insta360 camera was discovered; check USB mode and libusbK driver");

        auto selected = descriptors.begin();
        if (!options.camera_serial.empty()) {
            selected = std::find_if(descriptors.begin(), descriptors.end(), [&](const auto& descriptor) {
                return descriptor.serial_number == options.camera_serial;
            });
            if (selected == descriptors.end()) {
                discovery.FreeDeviceDescriptors(descriptors);
                fail("configured camera serial was not discovered: " + options.camera_serial);
            }
        }

        identity_ = copy_identity(*selected);
        try {
            camera_ = std::make_unique<ins_camera::Camera>(selected->info);
            camera_->SetServicePort(options.service_port);
            if (!camera_->Open()) fail("CameraSDK Open() failed");
        } catch (...) {
            discovery.FreeDeviceDescriptors(descriptors);
            throw;
        }
        discovery.FreeDeviceDescriptors(descriptors);
    }

    ~CameraSession() {
        if (camera_) camera_->Close();
    }

    CameraSession(const CameraSession&) = delete;
    CameraSession& operator=(const CameraSession&) = delete;

    ins_camera::Camera& camera() { return *camera_; }
    const CameraIdentity& identity() const { return identity_; }

private:
    CameraIdentity identity_;
    std::unique_ptr<ins_camera::Camera> camera_;
};

std::vector<std::string> raw_type_candidates(const std::string& value) {
    if (value == "off") return {"OFF"};
    if (value == "dng") return {"DNG", "RAW"};
    if (value == "pureshot") return {"PURESHOT"};
    if (value == "pureshot_raw") return {"PURESHOT_RAW", "PURESHOT+RAW"};
    fail("--raw-type must be off, dng, pureshot, or pureshot_raw");
}

ins_camera::RawCaptureType configure_raw_capture(
    ins_camera::Camera& camera,
    ins_camera::CameraFunctionMode mode,
    const std::string& requested_type) {
    const auto supported = camera.GetSupportedAttrValues(mode, "raw_capture_type");
    if (supported.empty()) {
        if (requested_type == "off") return ins_camera::RawCaptureType::Off;
        fail("the connected camera does not expose the requested raw_capture_type capability");
    }

    const auto candidates = raw_type_candidates(requested_type);
    for (const auto& candidate : candidates) {
        if (std::find(supported.begin(), supported.end(), candidate) == supported.end()) continue;
        const int value = camera.GetAttrValueByName("raw_capture_type", candidate);
        if (value < 0) fail("CameraSDK could not map raw capture format " + candidate);
        const auto raw_type = static_cast<ins_camera::RawCaptureType>(value);
        if (!camera.SetRawCaptureType(mode, raw_type)) {
            fail("SetRawCaptureType failed for " + candidate);
        }
        return raw_type;
    }

    std::ostringstream error;
    error << "requested raw type " << requested_type << " is not supported; camera supports ";
    for (size_t index = 0; index < supported.size(); ++index) {
        if (index) error << ", ";
        error << supported[index];
    }
    fail(error.str());
}

std::string unique_frame_id() {
    const auto now = std::chrono::system_clock::now().time_since_epoch();
    const auto milliseconds = std::chrono::duration_cast<std::chrono::milliseconds>(now).count();
    return "frame-" + std::to_string(milliseconds) + "-" + std::to_string(++g_sequence);
}

std::string safe_file_name(const std::string& input) {
    const auto separator = input.find_last_of("/\\");
    const std::string base = separator == std::string::npos ? input : input.substr(separator + 1);
    std::string result;
    result.reserve(base.size());
    for (const unsigned char character : base) {
        result.push_back((std::isalnum(character) || character == '.' || character == '-' || character == '_')
                             ? static_cast<char>(character)
                             : '_');
    }
    return result.empty() ? "camera.insp" : result;
}

fs::path next_download_path(const Options& options, const std::string& frame_id, const std::string& remote_path,
                            size_t index) {
    fs::path file_name(safe_file_name(remote_path));
    std::string extension = file_name.extension().string();
    if (extension.empty()) extension = ".insp";
    return options.output_dir / (frame_id + "-" + std::to_string(index) + extension);
}

std::vector<std::string> media_urls(const ins_camera::MediaUrl& media_url) {
    if (media_url.Empty()) fail("camera returned no media URL");
    auto urls = media_url.OriginUrls();
    if (urls.empty() && media_url.IsSingleOrigin()) urls.push_back(media_url.GetSingleOrigin());
    if (urls.empty()) fail("camera returned an empty origin-media URL list");
    return urls;
}

std::vector<fs::path> download_files(CameraSession& session, const Options& options, const std::vector<std::string>& remotes,
                                     const std::string& frame_id) {
    fs::create_directories(options.output_dir);
    std::vector<fs::path> downloaded;
    downloaded.reserve(remotes.size());
    for (size_t index = 0; index < remotes.size(); ++index) {
        const fs::path local_path = next_download_path(options, frame_id, remotes[index], index);
        if (!session.camera().DownloadCameraFile(remotes[index], path_to_utf8(local_path))) {
            fail("DownloadCameraFile failed for " + remotes[index]);
        }
        if (!fs::is_regular_file(local_path)) fail("CameraSDK reported a download but no local file was created");
        downloaded.push_back(local_path);
    }
    return downloaded;
}

std::vector<fs::path> stitchable_image_inputs(const std::vector<fs::path>& paths) {
    std::vector<fs::path> inputs;
    for (const auto& path : paths) {
        std::string extension = path.extension().string();
        std::transform(extension.begin(), extension.end(), extension.begin(), [](unsigned char character) {
            return static_cast<char>(std::tolower(character));
        });
        if (extension == ".insp") inputs.push_back(path);
    }
    if (inputs.empty()) {
        fail("MediaSDK ImageStitcher requires a downloaded .insp image; use --stitch false for RAW/DNG-only files");
    }
    return inputs;
}

fs::path stitch_image(const Options& options, const std::vector<fs::path>& input_paths, const std::string& frame_id) {
#ifdef SECOND_LIFE_WITH_MEDIA_SDK
    if (input_paths.empty()) fail("cannot stitch an empty media list");
    ins::SetLogLevel(ins::InsLogLevel::ERR);
    ins::InitEnv();
    if (!options.media_models_dir.empty()) {
        if (!fs::is_directory(options.media_models_dir)) {
            fail("--media-models-dir does not exist: " + path_to_utf8(options.media_models_dir));
        }
        ins::SetModelFileRootDir(path_to_utf8(options.media_models_dir));
    }

    std::vector<std::string> inputs;
    inputs.reserve(input_paths.size());
    for (const auto& input : input_paths) inputs.push_back(path_to_utf8(input));

    const fs::path output_path = options.output_dir / (frame_id + ".jpg");
    ins::ImageStitcher stitcher;
    stitcher.SetInputPath(inputs);
    stitcher.SetOutputPath(path_to_utf8(output_path));
    stitcher.SetOutputSize(options.output_width, options.output_height);
    stitcher.SetStitchType(ins::STITCH_TYPE::TEMPLATE);
    stitcher.SetImageProcessingAccelType(ins::ImageProcessingAccel::kCPU);
    if (!stitcher.Stitch() || !fs::is_regular_file(output_path)) {
        fail("MediaSDK ImageStitcher::Stitch() failed");
    }
    return output_path;
#else
    (void)options;
    (void)input_paths;
    (void)frame_id;
    fail("this camera bridge was built without MediaSDK; use --stitch false or rebuild with MediaSDK");
#endif
}

std::string capture_or_download_json(const Options& options, bool capture) {
    CameraSession session(options);
    const std::string frame_id = unique_frame_id();
    std::vector<std::string> remotes;
    if (capture) {
        const auto mode = ins_camera::CameraFunctionMode::FUNCTION_MODE_NORMAL_IMAGE;
        if (!session.camera().SetPhotoSubMode(ins_camera::SubPhotoMode::PHOTO_SINGLE)) {
            fail("SetPhotoSubMode(PHOTO_SINGLE) failed; stop recording and make sure the camera is ready for photos");
        }
        const auto raw_type = configure_raw_capture(session.camera(), mode, options.raw_type);
        remotes = media_urls(session.camera().TakePhoto(raw_type, options.timeout_ms));
    } else {
        remotes.push_back(options.remote_path);
    }

    const auto downloaded = download_files(session, options, remotes, frame_id);
    const fs::path artifact = options.stitch ? stitch_image(options, stitchable_image_inputs(downloaded), frame_id) : downloaded.front();

    std::vector<std::string> local_paths;
    local_paths.reserve(downloaded.size());
    for (const auto& local_path : downloaded) local_paths.push_back(path_to_utf8(local_path));

    std::ostringstream output;
    output << "{"
           << "\"ok\":true,"
           << "\"frame_id\":" << json_string(frame_id) << ","
           << "\"camera\":" << identity_json(session.identity()) << ","
           << "\"remote_paths\":" << json_array(remotes) << ","
           << "\"local_paths\":" << json_array(local_paths) << ","
           << "\"artifact_path\":" << json_string(path_to_utf8(artifact)) << ","
           << "\"stitched\":" << json_bool(options.stitch)
           << "}";
    return output.str();
}

std::string status_json(const Options& options) {
    CameraSession session(options);
    ins_camera::BatteryStatus battery{};
    ins_camera::StorageStatus storage{};
    const bool has_battery = session.camera().GetBatteryStatus(battery);
    const bool has_storage = session.camera().GetStorageState(storage);

    std::ostringstream output;
    output << "{"
           << "\"ok\":true,"
           << "\"sdk_version\":" << json_string(ins_camera::GetSDKVersion()) << ","
           << "\"camera\":" << identity_json(session.identity()) << ","
           << "\"connected\":" << json_bool(session.camera().IsConnected()) << ","
           << "\"capture_active\":" << json_bool(session.camera().CaptureCurrentStatus()) << ","
           << "\"current_function_mode\":" << static_cast<int>(session.camera().GetCurrentFunctionMode()) << ","
           << "\"battery\":";
    if (has_battery) {
        output << "{"
               << "\"level\":" << battery.battery_level << ","
               << "\"scale\":" << battery.battery_scale << ","
               << "\"power_type\":" << static_cast<int>(battery.power_type)
               << "}";
    } else {
        output << "null";
    }
    output << ",\"storage\":";
    if (has_storage) {
        output << "{"
               << "\"state\":" << static_cast<int>(storage.state) << ","
               << "\"free_space\":" << storage.free_space << ","
               << "\"total_space\":" << storage.total_space << ","
               << "\"location\":" << static_cast<int>(storage.location)
               << "}";
    } else {
        output << "null";
    }
    output << "}";
    return output.str();
}

std::string list_files_json(const Options& options) {
    CameraSession session(options);
    const auto files = session.camera().GetCameraFilesList();
    std::ostringstream output;
    output << "{\"ok\":true,\"camera\":" << identity_json(session.identity()) << ",\"file_count\":"
           << files.size() << ",\"files\":" << json_array(files) << "}";
    return output.str();
}

void emit_result(const std::string& result) {
    std::cout << kResultPrefix << result << std::endl;
}

} // namespace

int main(int argc, char* argv[]) {
#ifdef _WIN32
    std::vector<char*> utf8_argv;
    const auto utf8_storage = build_utf8_args(utf8_argv);
    if (!utf8_argv.empty()) {
        argc = static_cast<int>(utf8_argv.size());
        argv = utf8_argv.data();
    }
#endif
    try {
        const Options options = parse_options(argc, argv);
        if (options.command == "status") {
            emit_result(status_json(options));
        } else if (options.command == "list-files") {
            emit_result(list_files_json(options));
        } else if (options.command == "capture") {
            emit_result(capture_or_download_json(options, true));
        } else {
            emit_result(capture_or_download_json(options, false));
        }
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "camera bridge error: " << error.what() << std::endl;
        emit_result(std::string("{\"ok\":false,\"error\":") + json_string(error.what()) + "}");
        return 1;
    }
}
