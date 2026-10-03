#include <folly/Conv.h>
#include <folly/json/json.h>

#include <fstream>
#include <iterator>
#include <string>

int main(int argc, char **argv) {
    if (argc != 2) return 2;
    std::ifstream file(argv[1], std::ios::binary);
    if (!file) return 2;
    const std::string input((std::istreambuf_iterator<char>(file)),
                            std::istreambuf_iterator<char>());
    if (file.bad()) return 2;
    // parseJson's final check treats literal NUL as an end marker. A literal
    // NUL is invalid in every position in a JSON text; escaped \u0000 is fine.
    if (input.find('\0') != std::string::npos) return 1;
    try {
        folly::json::serialization_opts options;
        const auto value = folly::parseJson(folly::StringPiece(input), options);
        (void)value;
        return 0;
    } catch (const folly::json::parse_error &) {
        return 1;
    } catch (const folly::ConversionErrorBase &) {
        // Numeric syntax or the configured numeric representation limit.
        return 1;
    } catch (...) {
        return 2;
    }
}
