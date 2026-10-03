// Original adapter by Nicolas Seriot, 06/08/16.
// Copyright © 2016 Nicolas Seriot. All rights reserved.
#include <string.h>
#include "cJSON.h"
#include "../../read_fixture.h"

static int allocation_failed;

static void *parser_malloc(size_t size)
{
    void *result = malloc(size);
    if (result == NULL) allocation_failed = 1;
    return result;
}

int main(int argc, const char *argv[])
{
    char *data;
    size_t length;
    const char *end = NULL;
    cJSON *value;
    cJSON_Hooks hooks = {parser_malloc, free};
    int verdict;
    if (argc != 2) return 2;
    if (read_fixture(argv[1], &data, &length) != 0) return 2;
    /* The string API would otherwise ignore all bytes after a literal NUL. */
    if (memchr(data, '\0', length) != NULL) {
        free(data);
        return 1;
    }
    cJSON_InitHooks(&hooks);
    value = cJSON_ParseWithOpts(data, &end, 1);
    verdict = allocation_failed ? 2 : (value != NULL && end == data + length ? 0 : 1);
    cJSON_Delete(value);
    free(data);
    return verdict;
}
