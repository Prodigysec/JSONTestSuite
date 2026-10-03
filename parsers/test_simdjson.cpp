// Validate one complete JSON text with simdjson's DOM parser.
// The downloaded source archive retains simdjson's Apache-2.0 LICENSE.
#include "simdjson.h"

int main(int argc, char **argv) {
  if (argc != 2) return 2;

  simdjson::padded_string bytes;
  if (simdjson::padded_string::load(argv[1]).get(bytes) != simdjson::SUCCESS) {
    return 2;
  }

  simdjson::dom::parser parser;
  const simdjson::error_code error = parser.parse(bytes).error();
  if (error == simdjson::SUCCESS) return 0;
  if (error == simdjson::MEMALLOC || error == simdjson::UNINITIALIZED ||
      error == simdjson::UNSUPPORTED_ARCHITECTURE ||
      error == simdjson::UNEXPECTED_ERROR || error == simdjson::PARSER_IN_USE) {
    return 2;
  }
  return 1;
}
