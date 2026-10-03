// Adapter for picojson (BSD-2-Clause). The pinned source archive keeps LICENSE.
#include <fstream>
#include <iterator>
#include <new>
#include <stdexcept>
#include <string>

#include "picojson.h"

int main(int argc, char **argv) {
  if (argc != 2) return 2;
  try {
    std::ifstream file(argv[1], std::ios::binary);
    if (!file) return 2;
    const std::string bytes(std::istreambuf_iterator<char>{file}, {});
    if (file.bad()) return 2;

    picojson::value value;
    std::string error;
    auto end = picojson::parse(value, bytes.cbegin(), bytes.cend(), &error);
    if (!error.empty()) return 1;
    while (end != bytes.cend() && (*end == ' ' || *end == '\t' ||
                                   *end == '\n' || *end == '\r')) {
      ++end;
    }
    return end == bytes.cend() ? 0 : 1;
  } catch (const std::overflow_error &) {
    return 1; // picojson's numeric range limit
  } catch (const std::bad_alloc &) {
    return 2;
  } catch (...) {
    return 2;
  }
}
