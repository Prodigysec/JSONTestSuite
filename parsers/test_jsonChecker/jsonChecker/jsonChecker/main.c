#include "JSON_checker.h"
#include "../../../read_fixture.h"

int main(int argc, const char *argv[])
{
    char *data;
    size_t length, i;
    JSON_checker checker;
    int accepted;
    if (argc != 2) return 2;
    if (read_fixture(argv[1], &data, &length) != 0) return 2;
    checker = new_JSON_checker(20); /* Preserve the historical stack limit. */
    if (checker == NULL) {
        free(data);
        return 2;
    }
    for (i = 0; i < length; i++) {
        if (!JSON_checker_char(checker, (unsigned char)data[i])) {
            /* JSON_checker_char frees the checker on rejection. */
            free(data);
            return 1;
        }
    }
    accepted = JSON_checker_done(checker); /* Also frees the checker. */
    free(data);
    return accepted ? 0 : 1;
}
