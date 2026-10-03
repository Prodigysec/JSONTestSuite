/* Adapter for Angelo Masci's amjson (MIT). The source archive retains its license. */
#include <errno.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include "amjson.h"

int main(int argc, char **argv) {
    FILE *file;
    long length;
    char *bytes;
    struct jhandle handle;
    int result;
    int error;

    if (argc != 2) return 2;
    file = fopen(argv[1], "rb");
    if (!file) return 2;
    if (fseek(file, 0, SEEK_END) || (length = ftell(file)) < 0 ||
        fseek(file, 0, SEEK_SET) || (uint64_t)length > (bsize_t)-1) {
        fclose(file);
        return 2;
    }
    bytes = malloc((size_t)length + 1);
    if (!bytes) { fclose(file); return 2; }
    result = fread(bytes, 1, (size_t)length, file) == (size_t)length;
    if (fclose(file) || !result) {
        free(bytes);
        return 2;
    }
    if (amjson_alloc(&handle, NULL, JOBJECT_COUNT_GUESS((bsize_t)length))) {
        free(bytes);
        return 2;
    }
    result = amjson_decode(&handle, bytes, (bsize_t)length);
    error = errno;
    amjson_free(&handle);
    free(bytes);
    return result == 0 ? 0 : error == EINVAL ? 1 : 2;
}
