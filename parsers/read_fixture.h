/* Shared binary-file reader for the source-built C adapters. */
#ifndef JSONSUITE_READ_FIXTURE_H
#define JSONSUITE_READ_FIXTURE_H

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

/* Return 2 for file or allocation errors; never turn them into rejection. */
static int read_fixture(const char *path, char **data, size_t *length)
{
    FILE *file = fopen(path, "rb");
    long size;
    char *buffer;
    if (file == NULL) return 2;
    if (fseek(file, 0, SEEK_END) != 0 || (size = ftell(file)) < 0 ||
        (uintmax_t)size >= SIZE_MAX || fseek(file, 0, SEEK_SET) != 0) {
        fclose(file);
        return 2;
    }
    buffer = malloc((size_t)size + 1);
    if (buffer == NULL) {
        fclose(file);
        return 2;
    }
    if (fread(buffer, 1, (size_t)size, file) != (size_t)size || ferror(file)) {
        free(buffer);
        fclose(file);
        return 2;
    }
    if (fclose(file) != 0) {
        free(buffer);
        return 2;
    }
    buffer[size] = '\0';
    *data = buffer;
    *length = (size_t)size;
    return 0;
}

#endif
