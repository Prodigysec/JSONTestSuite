#include "jsonpp.hpp"

#include <fstream>
#include <iostream>
#include <iterator>
#include <string>

int main(int argc, const char **argv) {
    if (argc != 2) {
        std::cerr << "Usage: test_jsonpp FILE\n";
        return 2;
    }
    try {
        std::ifstream file(argv[1], std::ios::binary);
        if (!file) {
            std::cerr << "Cannot open input file\n";
            return 2;
        }
        std::string data((std::istreambuf_iterator<char>(file)),
                         std::istreambuf_iterator<char>());
        if (file.bad()) {
            std::cerr << "Cannot read input file\n";
            return 2;
        }
        auto result = JSONpp::json::parse(data);
        // empty() denotes monostate (no JSON text), not null or an empty container.
        return result.empty() ? 1 : 0;
    } catch (const JSONpp::JsonParseError& error) {
        std::cerr << error.what() << '\n';
        return 1;
    } catch (const JSONpp::JsonDepthLimitExceeded& error) {
        std::cerr << error.what() << '\n';
        return 1;
    } catch (const std::exception& error) {
        std::cerr << error.what() << '\n';
        return 2;
    } catch (...) {
        return 2;
    }
}
