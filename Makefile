# These four historical C adapters have checked-in source. Keep their
# rebuilt executables separate from the tracked platform-specific binaries.
CC ?= cc
CFLAGS ?= -O2
BUILD_DIR := parsers/.build
DIST_DIR ?= dist
CORPUS_REVISION = $(shell git rev-parse --short=12 HEAD)
CORPUS_ARCHIVE = $(DIST_DIR)/JSONTestSuite-corpus-$(CORPUS_REVISION).tar.gz

.PHONY: all c-parsers corpus-archive
.DELETE_ON_ERROR:

all: c-parsers

c-parsers: $(BUILD_DIR)/test_jsmn $(BUILD_DIR)/jsonChecker $(BUILD_DIR)/test_cJSON_1_7_3 $(BUILD_DIR)/test_ccan

$(BUILD_DIR):
	mkdir -p "$@"

$(BUILD_DIR)/test_jsmn: parsers/test_jsmn/test_jsmn/test_jsmn/main.c parsers/test_jsmn/jsmn.c parsers/test_jsmn/jsmn.h | $(BUILD_DIR)
	$(CC) $(CPPFLAGS) $(CFLAGS) -std=c99 -Iparsers/test_jsmn $(LDFLAGS) \
		parsers/test_jsmn/test_jsmn/test_jsmn/main.c parsers/test_jsmn/jsmn.c \
		-o "$@" $(LDLIBS)

$(BUILD_DIR)/jsonChecker: parsers/test_jsonChecker/jsonChecker/jsonChecker/main.c parsers/test_jsonChecker/jsonChecker/JSON_checker.c parsers/test_jsonChecker/jsonChecker/JSON_checker.h | $(BUILD_DIR)
	$(CC) $(CPPFLAGS) $(CFLAGS) -std=c99 -Iparsers/test_jsonChecker/jsonChecker $(LDFLAGS) \
		parsers/test_jsonChecker/jsonChecker/jsonChecker/main.c \
		parsers/test_jsonChecker/jsonChecker/JSON_checker.c -o "$@" $(LDLIBS)

$(BUILD_DIR)/test_cJSON_1_7_3: parsers/test_cJSON_1_7_3/test-cJSON/main.c parsers/test_cJSON_1_7_3/cJSON.c parsers/test_cJSON_1_7_3/cJSON.h | $(BUILD_DIR)
	$(CC) $(CPPFLAGS) $(CFLAGS) -std=c99 -Iparsers/test_cJSON_1_7_3 $(LDFLAGS) \
		parsers/test_cJSON_1_7_3/test-cJSON/main.c \
		parsers/test_cJSON_1_7_3/cJSON.c -o "$@" $(LDLIBS) -lm

$(BUILD_DIR)/test_ccan: parsers/test_ccan_json/test_ccan/test_ccan/main.c parsers/test_ccan_json/json/json.c parsers/test_ccan_json/json/json.h | $(BUILD_DIR)
	$(CC) $(CPPFLAGS) $(CFLAGS) -std=c99 -Iparsers/test_ccan_json/json $(LDFLAGS) \
		parsers/test_ccan_json/test_ccan/test_ccan/main.c \
		parsers/test_ccan_json/json/json.c -o "$@" $(LDLIBS)

# Git supplies the committed bytes and paths; gzip -n removes host/time fields.
corpus-archive:
	mkdir -p "$(DIST_DIR)"
	git archive --format=tar --output="$(CORPUS_ARCHIVE).tar.tmp" \
		HEAD LICENSE test_parsing test_transform
	gzip -n -c "$(CORPUS_ARCHIVE).tar.tmp" > "$(CORPUS_ARCHIVE).tmp"
	rm "$(CORPUS_ARCHIVE).tar.tmp"
	mv "$(CORPUS_ARCHIVE).tmp" "$(CORPUS_ARCHIVE)"
	@printf 'Created %s\n' "$(CORPUS_ARCHIVE)"
