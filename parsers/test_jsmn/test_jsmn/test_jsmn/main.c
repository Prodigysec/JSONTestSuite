// Original adapter by Nicolas Seriot, 30/08/16.
// Copyright © 2016 Nicolas Seriot. All rights reserved.
#include <limits.h>
#include <string.h>
#include "jsmn.h"
#include "../../../read_fixture.h"

static int json_space(char c)
{
    return c == ' ' || c == '\t' || c == '\r' || c == '\n';
}

int main(int argc, const char *argv[])
{
    char *data;
    size_t length, start, end, i;
    jsmn_parser parser;
    jsmntok_t *tokens;
    int parsed, verdict = 1;
    if (argc != 2) return 2;
    if (read_fixture(argv[1], &data, &length) != 0) return 2;
    /* Token positions are signed int; literal NUL must not end parsing early. */
    if (length >= INT_MAX || memchr(data, '\0', length) != NULL) {
        free(data);
        return 1;
    }
    /* At most one token per input byte, with space for an empty input. */
    if (length + 1 > SIZE_MAX / sizeof(*tokens)) {
        free(data);
        return 2;
    }
    tokens = malloc((length + 1) * sizeof(*tokens));
    if (tokens == NULL) {
        free(data);
        return 2;
    }
    jsmn_init(&parser);
    /* The vendored library is compiled in its native non-strict mode. */
    parsed = jsmn_parse(&parser, data, length, tokens, (unsigned int)(length + 1));
    if (parsed > 0 && parser.pos == length) {
        start = (size_t)tokens[0].start;
        end = (size_t)tokens[0].end;
        if (tokens[0].type == JSMN_STRING) {
            start--;
            end++; /* String token boundaries exclude the quotes. */
        }
        for (i = 0; i < start && json_space(data[i]); i++) {}
        if (i == start) {
            for (i = end; i < length && json_space(data[i]); i++) {}
            if (i == length) verdict = 0;
        }
    } else if (parsed == JSMN_ERROR_NOMEM) {
        verdict = 2; /* Exhausting the per-byte budget is an adapter failure. */
    }
    free(tokens);
    free(data);
    return verdict;
}
