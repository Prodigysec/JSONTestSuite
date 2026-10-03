/* Adapter for YAJL 2.1.0 (ISC). The source archive retains its license. */
#include <stdio.h>
#include "api/yajl_parse.h"

int main(int argc, char **argv) {
    FILE *file;
    unsigned char bytes[8192];
    size_t count;
    yajl_handle parser;
    yajl_status status = yajl_status_ok;

    if (argc != 2) return 2;
    file = fopen(argv[1], "rb");
    if (!file) return 2;
    parser = yajl_alloc(NULL, NULL, NULL);
    if (!parser) { fclose(file); return 2; }
    while ((count = fread(bytes, 1, sizeof bytes, file)) != 0) {
        status = yajl_parse(parser, bytes, count);
        if (status != yajl_status_ok) break;
    }
    if (ferror(file)) { yajl_free(parser); fclose(file); return 2; }
    if (status == yajl_status_ok) status = yajl_complete_parse(parser);
    yajl_free(parser);
    if (fclose(file)) return 2;
    return status == yajl_status_ok ? 0 : 1;
}
