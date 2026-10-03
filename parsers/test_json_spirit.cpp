#include <ciere/json/io.hpp>

#include <fstream>
#include <iterator>
#include <string>

int main(int argc, char **argv) {
    if (argc != 2) return 2;
    std::ifstream stream(argv[1], std::ios::binary);
    if (!stream) return 2;
    const std::string input((std::istreambuf_iterator<char>(stream)),
                            std::istreambuf_iterator<char>());
    if (stream.bad()) return 2;
    try {
        ciere::json::value value;
        return ciere::json::construct(input, value, true) ? 0 : 1;
    } catch (const ciere::json::parse_error &) {
        return 1;
    } catch (...) {
        return 2;
    }
}
