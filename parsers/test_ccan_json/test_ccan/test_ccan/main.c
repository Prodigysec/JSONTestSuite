//
//  main.c
//  test_ccan
//
//  Created by nst on 27/08/16.
//  Copyright © 2016 Nicolas Seriot. All rights reserved.
//

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "json.h"

typedef enum testStatus {PASS = 0, FAIL = 1, ERROR = 2} TestStatus;

TestStatus testFile(const char *filename) {
    FILE *f = fopen(filename, "rb");
    if (f == NULL) return ERROR;
    if (fseek(f, 0, SEEK_END) != 0) { fclose(f); return ERROR; }
    long length = ftell(f);
    if (length < 0 || fseek(f, 0, SEEK_SET) != 0) { fclose(f); return ERROR; }
    size_t len = (size_t)length;
    char *data = malloc(len + 1);
    if (data == NULL) { fclose(f); return ERROR; }
    size_t read_count = fread(data, 1, len, f);
    int close_status = fclose(f);
    if (read_count != len || close_status != 0) {
        free(data);
        return ERROR;
    }
    data[len] = '\0';

    /* json_validate takes a C string; an embedded NUL would hide trailing bytes. */
    bool isValid = memchr(data, '\0', len) == NULL && json_validate(data);
    free(data);
    return isValid ? PASS : FAIL;
}

int main(int argc, const char * argv[]) {
    if (argc != 2) return ERROR;
    return testFile(argv[1]);
}
