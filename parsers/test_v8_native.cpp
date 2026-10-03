#include <libplatform/libplatform.h>
#include <v8.h>

#include <fstream>
#include <iterator>
#include <limits>
#include <memory>
#include <string>

int main(int argc, char **argv) {
    if (argc != 2) return 2;
    std::ifstream file(argv[1], std::ios::binary);
    if (!file) return 2;
    const std::string input((std::istreambuf_iterator<char>(file)),
                            std::istreambuf_iterator<char>());
    if (file.bad()) return 2;

    v8::V8::InitializeICUDefaultLocation(argv[0]);
    v8::V8::InitializeExternalStartupData(argv[0]);
    std::unique_ptr<v8::Platform> platform = v8::platform::NewDefaultPlatform();
    v8::V8::InitializePlatform(platform.get());
    v8::V8::Initialize();
    v8::Isolate::CreateParams params;
    params.array_buffer_allocator = v8::ArrayBuffer::Allocator::NewDefaultAllocator();
    v8::Isolate *isolate = v8::Isolate::New(params);
    int result = 2;
    {
        v8::Isolate::Scope isolate_scope(isolate);
        v8::HandleScope handle_scope(isolate);
        v8::Local<v8::Context> context = v8::Context::New(isolate);
        v8::Context::Scope context_scope(context);
        v8::Local<v8::String> source;
        if (input.size() <= static_cast<size_t>(std::numeric_limits<int>::max()) &&
            v8::String::NewFromUtf8(isolate, input.data(), v8::NewStringType::kNormal,
                                    static_cast<int>(input.size())).ToLocal(&source)) {
            v8::TryCatch catch_scope(isolate);
            v8::Local<v8::Value> value;
            result = v8::JSON::Parse(context, source).ToLocal(&value) ? 0 : 1;
        }
    }
    isolate->Dispose();
    delete params.array_buffer_allocator;
    v8::V8::Dispose();
    v8::V8::DisposePlatform();
    return result;
}
