#!/usr/bin/env python3

import io
import os
import os.path
import subprocess
import sys
import json
import platform

from concurrent.futures import ThreadPoolExecutor
from contextlib import nullcontext
from html import escape
from time import strftime

BASE_DIR = os.path.dirname(os.path.realpath(__file__))
PARSERS_DIR = os.path.join(BASE_DIR, "parsers")
TEST_CASES_DIR_PATH = os.path.join(BASE_DIR, "test_parsing")
LOGS_DIR_PATH = os.path.join(BASE_DIR, "results")
LOG_FILENAME = "logs.txt"
LOG_FILE_PATH = os.path.join(LOGS_DIR_PATH, LOG_FILENAME)

INVALID_BINARY_FORMAT = 8
BAD_CPU_TYPE = 86

programs = {
    # "Awk JSON.awk busybox":
    #     {
    #         "url":"https://github.com/step-/JSON.awk",
    #         "commands":["/bin/busybox", "awk", "-f", os.path.join(PARSERS_DIR, "test_JSON.awk", "JSON-busybox.awk")]
    #     },
    # "Awk JSON.awk gawk POSIX":
    #     {
    #         "url":"https://github.com/step-/JSON.awk",
    #         "commands":["/usr/bin/gawk", "--posix", "-f", os.path.join(PARSERS_DIR, "test_JSON.awk", "JSON.awk")]
    #     },
    "Awk JSON.awk gawk":
        {
            "url":"https://github.com/step-/JSON.awk",
            "commands":["/usr/bin/gawk", "-f", os.path.join(PARSERS_DIR, "test_JSON.awk", "JSON.awk")]
        },
    # "Awk JSON.awk mawk":
    #     {
    #         "url":"https://github.com/step-/JSON.awk",
    #         "commands":["/usr/bin/mawk", "-f", os.path.join(PARSERS_DIR, "test_JSON.awk", "callbacks.awk"), "-f", os.path.join(PARSERS_DIR, "test_JSON.awk", "JSON.awk")]
    #     },
    "Bash JSON.sh 2016-08-12":
        {
            "url":"https://github.com/dominictarr/JSON.sh",
            "commands":[os.path.join(PARSERS_DIR, "test_Bash_JSON/JSON.sh")],
            "use_stdin":True
        },
    "R rjson":
        {
            "url":"",
            "commands":["/usr/local/bin/RScript", os.path.join(PARSERS_DIR, "test_rjson.r")]
        },
    "R jsonlite":
        {
            "url":"",
            "commands":["/usr/local/bin/RScript", os.path.join(PARSERS_DIR, "test_jsonlite.r")]
        },
   "Obj-C JSONKit":
       {
           "url":"",
           "commands":[os.path.join(PARSERS_DIR, "test_JSONKit/bin/test-JSONKit")]
       },
   "Obj-C Apple NSJSONSerialization":
       {
           "url":"",
           "commands":[os.path.join(PARSERS_DIR, "test_ObjCNSJSONSerializer/bin/test_ObjCNSJSONSerializer")]
       },
   "Obj-C TouchJSON":
       {
           "url":"https://github.com/TouchCode/TouchJSON",
           "commands":[os.path.join(PARSERS_DIR, "test_TouchJSON/bin/test_TouchJSON")]
       },
   "Obj-C SBJSON 4.0.3":
       {
           "url":"https://github.com/stig/json-framework",
           "commands":[os.path.join(PARSERS_DIR, "test_SBJSON_4_0_3/bin/test_sbjson")]
       },
   "Obj-C SBJSON 4.0.4":
       {
           "url":"https://github.com/stig/json-framework",
           "commands":[os.path.join(PARSERS_DIR, "test_SBJSON_4_0_4/bin/test_sbjson")]
       },
   "Obj-C SBJson 5.0.0":
       {
           "url":"https://github.com/stig/json-framework",
           "commands":[os.path.join(PARSERS_DIR, "test_SBJson_5_0_0/bin/test_sbjson")]
       },
   "Go 1.7.1":
       {
           "url":"",
           "commands":[os.path.join(PARSERS_DIR, "test_go/test_json")]
       },
    "Zig 0.8.0-dev.1354+081698156":
       {
           "url":"",
           "commands":[os.path.join(PARSERS_DIR, "test_zig/test_json")]
       },
   "Free Pascal fcl-json":
       {
           "url":"",
           "commands":[os.path.join(PARSERS_DIR, "test_fpc/test_json")]
       },
   "Xidel Internet Tools":
       {
           "url":"http://www.videlibri.de/xidel.html",
           "commands":["/usr/bin/env", "xidel", "--input-format=json-strict", "-e=."]
       },
   "Lua JSON 20160916.19":
       {
           "url":"http://regex.info/blog/lua/json",
           "commands":["/usr/local/bin/lua", os.path.join(PARSERS_DIR, "test_Lua_JSON/test_JSON.lua")]
       },
   "Lua dkjson":
       {
           "url":"http://dkolf.de/src/dkjson-lua.fsl/home",
           "commands":["/usr/local/bin/lua", os.path.join(PARSERS_DIR, "test_dkjson.lua")]
       },
   "Ruby":
       {
           "url":"",
           "commands":["/usr/bin/env", "ruby", os.path.join(PARSERS_DIR, "test_json.rb")]
       },
   "Ruby regex":
       {
           "url":"",
           "commands":["/usr/bin/env", "ruby", os.path.join(PARSERS_DIR, "test_json_re.rb")]
       },
   "Ruby Yajl":
       {
           "url":"https://github.com/brianmario/yajl-ruby",
           "commands":["/usr/bin/env", "ruby", os.path.join(PARSERS_DIR, "test_yajl.rb")]
       },
   "Ruby Oj (strict mode)":
       {
           "url":"https://github.com/ohler55/oj",
           "commands":["/usr/bin/env", "ruby", os.path.join(PARSERS_DIR, "test_oj_strict.rb")]
       },
   "Ruby Oj (compat mode)":
       {
           "url":"https://github.com/ohler55/oj",
           "commands":["/usr/bin/env", "ruby", os.path.join(PARSERS_DIR, "test_oj_compat.rb")]
       },
   "Crystal":
       {
           "url":"https://github.com/crystal-lang/crystal",
           "commands":[os.path.join(PARSERS_DIR, "test_json_cr")]
       },
   "JavaScript":
       {
           "url":"",
           "commands":["/usr/local/bin/node", os.path.join(PARSERS_DIR, "test_json.js")]
       },
   "Node.js V8 JSON.parse (strict UTF-8)":
       {
           "url":"https://nodejs.org/",
           "commands":["node", os.path.join(PARSERS_DIR, "test_node_json_utf8.js")],
           "observation_commands":["node", os.path.join(PARSERS_DIR, "observe_node_features.js")]
       },
   "C++ V8 10.2.154.26 (libnode 18.20.4)":
       {
           "url":"https://v8.dev/",
           "setup":["docker", "image", "inspect", "--format", "{{.Id}}", "jsonsuite-v8:local"],
           "commands":[sys.executable, os.path.join(PARSERS_DIR, "test_v8_native.py")]
       },
   "Firefox ESR 153.4.0 JSON.parse (headless)":
       {
           "url":"https://www.mozilla.org/firefox/",
           "setup":["docker", "image", "inspect", "--format", "{{.Id}}", "jsonsuite-firefox:local"],
           "commands":[sys.executable, os.path.join(PARSERS_DIR, "test_firefox.py")],
           "timeout":45,
       },
   "JavaScriptCore 2.50.6 JSON.parse (strict UTF-8)":
       {
           "url":"https://webkit.org/",
           "setup":["docker", "image", "inspect", "--format", "{{.Id}}", "jsonsuite-jsc:local"],
           "commands":["python3", os.path.join(PARSERS_DIR, "test_jsc.py")]
       },
   "Chromium 154.0.8037.92 JSON.parse (headless)":
       {
           "url":"https://www.chromium.org/",
           "setup":["docker", "image", "inspect", "--format", "{{.Id}}", "jsonsuite-chromium:local"],
           "commands":["python3", os.path.join(PARSERS_DIR, "test_chromium.py")]
       },
   "jq (raw-slurp fromjson)":
       {
           "url":"https://jqlang.org/jq/",
           "commands":["jq", "-Rs", "try (fromjson | empty) catch (halt_error(1))"]
       },
   "Python stdlib %s (%s, UTF-8, default constants)" % (platform.python_version(), platform.python_implementation()):
       {
           "url":"https://docs.python.org/3/library/json.html",
           "commands":[sys.executable, os.path.join(PARSERS_DIR, "test_python_json.py")],
           "observation_commands":[sys.executable, "-B", os.path.join(PARSERS_DIR, "observe_python_features.py")]
       },
   "Python stdlib %s (%s, UTF-8, nonfinite constants rejected)" % (platform.python_version(), platform.python_implementation()):
       {
           "url":"https://docs.python.org/3/library/json.html",
           "commands":[sys.executable, os.path.join(PARSERS_DIR, "test_python_json.py"), "--reject-nonfinite"],
           "observation_commands":[sys.executable, "-B", os.path.join(PARSERS_DIR, "observe_python_features.py"), "--reject-nonfinite"]
       },
   "Python 2.7.10":
       {
           "url":"",
           "commands":["/usr/bin/python", os.path.join(PARSERS_DIR, "test_json.py")]
       },
   "Python 3.5.2":
       {
           "url":"",
           "commands":["/usr/bin/env", "python3.5", os.path.join(PARSERS_DIR, "test_json.py")]
       },
   "Python cjson 1.10": # pip install cjson
       {
           "url":"https://pypi.python.org/pypi/python-cjson",
           "commands":["/usr/bin/python", os.path.join(PARSERS_DIR, "test_cjson.py")]
       },
   "Python ujson 1.35": # pip install ujson
       {
           "url":"https://pypi.python.org/pypi/ujson",
           "commands":["/usr/bin/python", os.path.join(PARSERS_DIR, "test_ujson.py")]
       },
   "Python simplejson 3.10": # pip install simplejson
       {
           "url":"https://pypi.python.org/pypi/simplejson",
           "commands":["/usr/bin/python", os.path.join(PARSERS_DIR, "test_simplejson.py")]
       },
   "Python demjson 2.2.4": # pip install demjson
       {
           "url":"https://pypi.python.org/pypi/demjson",
           "commands":["/usr/bin/python", os.path.join(PARSERS_DIR, "test_demjson.py")]
       },
   "Python demjson 2.2.4 (py3)": # pip install demjson
       {
           "url":"https://pypi.python.org/pypi/demjson",
           "commands":["/usr/bin/env", "python3.5", os.path.join(PARSERS_DIR, "test_demjson.py")]
       },
   "Python demjson 2.2.4 (jsonlint)": # pip install demjson
       {
           "url":"https://pypi.python.org/pypi/demjson",
           "commands":["/usr/bin/env", "jsonlint", "--quiet", "--strict", "--allow=non-portable,duplicate-keys,zero-byte"]
       },
   "Perl Cpanel::JSON::XS":
       {
           "url":"https://metacpan.org/pod/Cpanel::JSON::XS",
           "commands":["/usr/bin/perl", os.path.join(PARSERS_DIR, "test_cpanel_json_xs.pl")]
       },
   "Perl JSON::Parse":
       {
           "url":"https://metacpan.org/pod/JSON::Parse",
           "commands":["/usr/bin/perl", os.path.join(PARSERS_DIR, "test_json_parse.pl")]
       },
   "Perl JSON::PP": # part of default install in perl >= v5.14
       {
           "url":"https://metacpan.org/pod/JSON::PP",
           "commands":["/usr/bin/perl", os.path.join(PARSERS_DIR, "test_json_pp.pl")]
       },
   "Perl JSON::SL":
       {
           "url":"https://metacpan.org/pod/JSON::SL",
           "commands":["/usr/bin/perl", os.path.join(PARSERS_DIR, "test_json_sl.pl")]
       },
   "Perl JSON::Tiny":
       {
           "url":"https://metacpan.org/pod/JSON::Tiny",
           "commands":["/usr/bin/perl", os.path.join(PARSERS_DIR, "test_json_tiny.pl")]
       },
   "Perl JSON::XS":
       {
           "url":"https://metacpan.org/pod/JSON::XS",
           "commands":["/usr/bin/perl", os.path.join(PARSERS_DIR, "test_json_xs.pl")]
       },
   "Perl MarpaX::ESLIF::ECMA404":
       {
           "url":"http://metacpan.org/pod/MarpaX::ESLIF::ECMA404",
           "commands":["/usr/bin/perl", os.path.join(PARSERS_DIR, "test_marpax_eslif_ecma404.pl")]
       },
   "Perl Mojo::JSON":
       {
           "url":"http://metacpan.org/pod/Mojo::JSON",
           "commands":["/usr/bin/perl", os.path.join(PARSERS_DIR, "test_mojo_json.pl")]
       },
   "Perl Pegex::JSON":
       {
           "url":"http://metacpan.org/pod/Pegex::JSON",
           "commands":["/usr/bin/perl", os.path.join(PARSERS_DIR, "test_pegex_json.pl")]
       },
   "PHP 5.5.36":
       {
           "url":"",
           "commands":["/usr/bin/php", os.path.join(PARSERS_DIR, "test_json.php")]
       },
   "PHP 7.4.33 Docker":
       {
           "url":"https://www.php.net/manual/en/function.json-decode.php",
           "setup":["docker", "image", "inspect", "--format", "{{.Id}}", "php@sha256:620a6b9f4d4feef2210026172570465e9d0c1de79766418d3affd09190a7fda5"],
           "commands":["docker", "run", "--rm", "--network", "none", "--pull", "never",
                       "--mount", "type=bind,src=%s,dst=%s,readonly" % (BASE_DIR, BASE_DIR),
                       "php@sha256:620a6b9f4d4feef2210026172570465e9d0c1de79766418d3affd09190a7fda5",
                       "php", os.path.join(PARSERS_DIR, "test_json.php")]
       },
   "PHP 8.3.27 Docker":
       {
           "url":"https://www.php.net/manual/en/function.json-decode.php",
           "setup":["docker", "image", "inspect", "--format", "{{.Id}}", "php@sha256:01224f5f2e75fa43a326797d7b80552ca0bcfb37f60cbb81efdf63956b4d3fe4"],
           "commands":["docker", "run", "--rm", "--network", "none", "--pull", "never",
                       "--mount", "type=bind,src=%s,dst=%s,readonly" % (BASE_DIR, BASE_DIR),
                       "php@sha256:01224f5f2e75fa43a326797d7b80552ca0bcfb37f60cbb81efdf63956b4d3fe4",
                       "php", os.path.join(PARSERS_DIR, "test_json.php")]
       },
   "Swift Freddy 2.1.0":
       {
           "url":"",
           "commands":[os.path.join(PARSERS_DIR, "test_Freddy_2_1_0/bin/test_Freddy_2_1_0")]
       },
   "Swift Freddy 20160830":
       {
           "url":"",
           "commands":[os.path.join(PARSERS_DIR, "test_Freddy_20160830/bin/test_Freddy")]
       },
   "Swift Freddy 20161018":
       {
           "url":"",
           "commands":[os.path.join(PARSERS_DIR, "test_Freddy_20161018/bin/test_Freddy")]
       },
   "Swift Freddy 20170118":
       {
           "url":"",
           "commands":[os.path.join(PARSERS_DIR, "test_Freddy_20170118/bin/test_Freddy")]
       },
   "Swift PMJSON 1.1.0":
       {
           "url":"https://github.com/postmates/PMJSON",
           "commands":[os.path.join(PARSERS_DIR, "test_PMJSON_1_1_0/bin/test_PMJSON")]
       },
   "Swift PMJSON 1.2.0":
       {
           "url":"https://github.com/postmates/PMJSON",
           "commands":[os.path.join(PARSERS_DIR, "test_PMJSON_1_2_0/bin/test_PMJSON")]
       },
   "Swift PMJSON 1.2.1":
       {
           "url":"https://github.com/postmates/PMJSON",
           "commands":[os.path.join(PARSERS_DIR, "test_PMJSON_1_2_1/bin/test_PMJSON")]
       },
   "Swift STJSON":
       {
           "url":"",
           "commands":[os.path.join(PARSERS_DIR, "test_STJSON/bin/STJSON")]
       },
   "Swift Apple JSONSerialization":
       {
           "url":"",
           "commands":[os.path.join(PARSERS_DIR, "test-AppleJSONSerialization/bin/test-AppleJSONSerialization")]
       },
   "Swift Foundation 6.1.3 Linux Docker":
       {
           "url":"https://github.com/swiftlang/swift-corelibs-foundation",
           "setup":["docker", "image", "inspect", "--format", "{{.Id}}", "swift@sha256:19792fa7ef68fb0e0ca5763ec3dfd40d6461afca7c081eb689e2e374fa80c0be"],
           "commands":["docker", "run", "--rm", "--network", "none", "--pull", "never",
                       "--mount", "type=bind,src=%s,dst=%s,readonly" % (BASE_DIR, BASE_DIR),
                       "--entrypoint", os.path.join(PARSERS_DIR, ".build/swift-foundation-linux/test_swift_foundation_linux"),
                       "swift@sha256:19792fa7ef68fb0e0ca5763ec3dfd40d6461afca7c081eb689e2e374fa80c0be"]
       },
   "C pdjson 20170325":
       {
           "url":"https://github.com/skeeto/pdjson",
           "commands":[os.path.join(PARSERS_DIR, "test_pdjson/bin/test_pdjson")]
       },
   "C amjson 1e282121":
       {
           "url":"https://github.com/amwales-888/amjson",
           "commands":[os.path.join(PARSERS_DIR, ".build/amjson/test_amjson")]
       },
   "C YAJL 2.1.0":
       {
           "url":"https://github.com/lloyd/yajl",
           "commands":[os.path.join(PARSERS_DIR, ".build/yajl-c/test_yajl_c")]
       },
   "C++ simdjson 5.0.1 DOM":
       {
           "url":"https://github.com/simdjson/simdjson",
           "commands":[os.path.join(PARSERS_DIR, ".build/simdjson/test_simdjson")]
       },
   "C++ picojson 111c9be5":
       {
           "url":"https://github.com/kazuho/picojson",
           "commands":[os.path.join(PARSERS_DIR, ".build/picojson/test_picojson")]
       },
   "VHDL JSON-for-VHDL 2ab1ebc2 (GHDL 4.1)":
       {
           "url":"https://github.com/Paebbels/JSON-for-VHDL",
           "setup":[sys.executable, os.path.join(PARSERS_DIR, "test_vhdl_json.py"), "--check"],
           "commands":[sys.executable, os.path.join(PARSERS_DIR, "test_vhdl_json.py")]
       },
   "SQLite JSON1 (Python sqlite3)":
       {
           "url":"https://www.sqlite.org/json1.html",
           "commands":[sys.executable, os.path.join(PARSERS_DIR, "test_sqlite_json.py")]
       },
   "PostgreSQL 16 JSONB UTF8":
       {
           "url":"https://www.postgresql.org/docs/16/datatype-json.html",
           "commands":[sys.executable, os.path.join(PARSERS_DIR, "test_postgres_jsonb.py")],
           "setup":[sys.executable, os.path.join(PARSERS_DIR, "test_postgres_jsonb.py"), "--check"]
       },
   "C jsmn":
       {
           "url":"https://github.com/zserge/jsmn",
           "setup":["make", "-C", BASE_DIR, "parsers/.build/test_jsmn"],
           "commands":[os.path.join(PARSERS_DIR, ".build/test_jsmn")]
       },
   "C jansson":
       {
           "url":"",
           "commands":[os.path.join(PARSERS_DIR, "test_jansson/bin/test_jansson")]
       },
   "C JSON Checker":
       {
           "url":"http://www.json.org/JSON_checker/",
           "setup":["make", "-C", BASE_DIR, "parsers/.build/jsonChecker"],
           "commands":[os.path.join(PARSERS_DIR, ".build/jsonChecker")]
       },
   "C JSON Checker 2":
       {
           "url":"",
           "commands":[os.path.join(PARSERS_DIR, "test_jsonChecker2/bin/jsonChecker2")]
       },
   "C JSON Checker 20161111":
       {
           "url":"https://github.com/douglascrockford/JSON-c",
           "commands":[os.path.join(PARSERS_DIR, "test_jsonChecker20161111/bin/jsonChecker20161111")]
       },
   "C++ sajson 20170724":
       {
           "url":"https://github.com/chadaustin/sajson",
           "commands":[os.path.join(PARSERS_DIR, "test_sajson_20170724/bin/test_sajson")]
       },
   "C ccan":
       {
           "url":"",
           "setup":["make", "-C", BASE_DIR, "parsers/.build/test_ccan"],
           "commands":[os.path.join(PARSERS_DIR, ".build/test_ccan")]
       },
   "C cJSON 20160806":
       {
           "url":"https://github.com/DaveGamble/cJSON",
           "commands":[os.path.join(PARSERS_DIR, "test_cJSON_20160806/bin/test_cJSON")]
       },
   "C cJSON 1.7.3":
       {
           "url":"https://github.com/DaveGamble/cJSON",
           "setup":["make", "-C", BASE_DIR, "parsers/.build/test_cJSON_1_7_3"],
           "commands":[os.path.join(PARSERS_DIR, ".build/test_cJSON_1_7_3")]
       },
   "C JSON-C":
       {
           "url":"https://github.com/json-c/json-c",
           "commands":[os.path.join(PARSERS_DIR, "test_json-c/bin/test_json-c")]
       },
   "C JSON Parser by udp":
       {
           "url":"https://github.com/udp/json-parser",
           "commands":[os.path.join(PARSERS_DIR, "test_json-parser/bin/test_json-parser")]
       },
   "C++ nlohmann JSON 20190718":
       {
           "url":"https://github.com/nlohmann/json/",
           "commands":[os.path.join(PARSERS_DIR, "test_nlohmann_json_20190718/bin/test_nlohmann_json")]
       },
   "C++ RapidJSON 20170724":
       {
           "url":"https://github.com/miloyip/rapidjson",
           "commands":[os.path.join(PARSERS_DIR, "test_rapidjson_20170724/bin/test_rapidjson")]
       },
   "Rust json-rust":
       {
           "url":"https://github.com/maciejhirsz/json-rust",
           "commands":[os.path.join(PARSERS_DIR, "test_json-rust/target/debug/tj")]
       },
   "Rust rustc_serialize::json":
       {
           "url":"https://doc.rust-lang.org/rustc-serialize/rustc_serialize/json/index.html",
           "commands":[os.path.join(PARSERS_DIR, "test_json-rustc_serialize/rj/target/debug/rj")]
       },
   "Rust serde_json 1.0.145":
       {
           "url":"https://github.com/serde-rs/json",
           "commands":[os.path.join(PARSERS_DIR, ".build/rust-serde-json/debug/rj")]
       },
   "C++ JSON Spirit c7245a39":
       {
           "url":"https://github.com/cierelabs/json_spirit",
           "commands":[os.path.join(PARSERS_DIR, ".build/json-spirit/test_json_spirit")]
       },
   "C++ Folly v2025.09.29.00 parseJson (native defaults, NUL guard)":
       {
           "url":"https://github.com/facebook/folly",
           "setup":["docker", "image", "inspect", "--format", "{{.Id}}", "jsonsuite-folly:local"],
           "commands":[sys.executable, os.path.join(PARSERS_DIR, "test_folly.py")]
       },
   "Java json-simple 1.1.1":
       {
           "url":"",
           "commands":["/usr/bin/java", "-jar", os.path.join(PARSERS_DIR, "test_java_simple_json_1_1_1/TestJSONParsing.jar")]
       },
   "Java org.json 2016-08-15":
       {
           "url":"https://github.com/stleary/JSON-java",
           "commands":["/usr/bin/java", "-jar", os.path.join(PARSERS_DIR, "test_java_org_json_2016_08/TestJSONParsing.jar")]
       },
   "Java gson 2.7":
       {
           "url":"",
           "commands":["/usr/bin/java", "-jar", os.path.join(PARSERS_DIR, "test_java_gson_2_7/TestJSONParsing.jar")]
       },
   "Java BFO v1":
       {
           "url":"https://github.com/faceless2/json",
           "commands":["/usr/bin/java", "-jar", os.path.join(PARSERS_DIR, "test_java_bfo/TestJSONParsing.jar")]
       },
   "Java com.leastfixedpoint.json 1.0":
       {
           "url":"",
           "commands":["/usr/bin/java", "-jar", os.path.join(PARSERS_DIR, "test_java_com_leastfixedpoint_json_1_0/TestJSONParsing.jar")]
       },
   "Java Jackson 2.8.4":
       {
           "url":"",
           "commands":["/usr/bin/java", "-jar", os.path.join(PARSERS_DIR, "test_java_jackson_2_8_4/TestJSONParsing.jar")]
       },
   "Java JsonTree 0.5":
       {
           "url":"",
           "commands":["/usr/bin/java", "-jar", os.path.join(PARSERS_DIR, "test_java_json_tree/TestJSONParsing.jar")]
       },
   "Scala Dijon 0.3.0":
       {
           "url":"",
           "commands":["/usr/bin/java", "-jar", os.path.join(PARSERS_DIR, "test_scala_dijon_0.3.0/target/scala-2.13/TestJSONParsing.jar")]
       },
   "Java Mergebase Java2Json 2019.09.09":
       {
           "url":"https://github.com/mergebase/Java2Json",
           "commands":["/usr/bin/java", "-jar", os.path.join(PARSERS_DIR, "test_java_mergebase_json_2019_09_09/TestJSONParsing.jar")]
       },
   "Java nanojson 1.0":
       {
           "url":"",
           "commands":["/usr/bin/java", "-jar", os.path.join(PARSERS_DIR, "test_java_nanojson_1_0/TestJSONParsing.jar")]
       },
   "Java nanojson 1.1":
       {
           "url":"",
           "commands":["/usr/bin/java", "-jar", os.path.join(PARSERS_DIR, "test_java_nanojson_1_1/TestJSONParsing.jar")]
       },
    "Java Actson 1.2.0":
       {
           "url":"https://github.com/michel-kraemer/actson",
           "commands":["/usr/bin/java", "-jar", os.path.join(PARSERS_DIR, "test_java_actson_1_2_0/TestJSONParsing.jar")]
       },
   "Haskell Aeson 0.11.2.1":
       {
           "url":"https://github.com/bos/aeson",
           "commands":[os.path.join(PARSERS_DIR, "test_haskell-aeson/testaeson")]
       },
    "OCaml Yojson":
       {
           "url":"https://github.com/mjambon/yojson",
           "commands":[os.path.join(PARSERS_DIR, "test_ocaml-yojson/testyojson")]
       },
    "OCaml Orsetto":
       {
           "url":"https://bitbucket.org/jhw/orsetto",
           "commands":[os.path.join(PARSERS_DIR, "test_ocaml_orsetto/test_orsetto_json")]
       },
    "Qt JSON":
        {
            "url":"",
            "commands":[os.path.join(PARSERS_DIR, "test_qt/test_qt")]
        },
    "C ConcreteServer":
        {
            "url":" https://github.com/RaphaelPrevost/ConcreteServer",
            "commands":[os.path.join(PARSERS_DIR, "test_ConcreteServer/json_checker")]
        },
    "Squeak JSON-tonyg":
        {
            "url":"http://www.squeaksource.com/JSON.html",
            "commands":[
                    os.path.join(PARSERS_DIR, "test_Squeak_JSON_tonyg/Squeak.app/Contents/MacOS/Squeak"),
                    "-headless", #<--optional
                    os.path.join(PARSERS_DIR, "test_Squeak_JSON_tonyg/Squeak5.1-16549-32bit.image"),
                    "test_JSON.st"
            ]
        },
   ".NET Newtonsoft.Json 13.0.2":
       {
           "url":"http://www.newtonsoft.com/json",
           "setup":["dotnet", "build", "--configuration", "Release", os.path.join(PARSERS_DIR, "test_dotnet_newtonsoft/app.csproj")],
           "commands":["dotnet", os.path.join(PARSERS_DIR, "test_dotnet_newtonsoft/bin/Release/net5.0/app.dll")]
       },
   ".NET System.Text.Json 5.0.0":
       {
           "url":"https://docs.microsoft.com/en-us/dotnet/api/system.text.json",
           "setup":["dotnet", "build", "--configuration", "Release", os.path.join(PARSERS_DIR, "test_dotnet_system_text_json/app.csproj")],
           "commands":["dotnet", os.path.join(PARSERS_DIR, "test_dotnet_system_text_json/bin/Release/net5.0/app.dll")]
       },
   "Elixir Json":
         {
             "url":"https://github.com/cblage/elixir-json",
             "commands":[ os.path.join( PARSERS_DIR, "test_elixir_json/test_elixir_json") ]
         },
   "Elixir ExJSON":
         {
             "url":"https://github.com/guedes/exjson",
             "commands":[ os.path.join( PARSERS_DIR, "test_elixir_exjson/test_elixir_exjson") ]
         },
   "Elixir Poison":
         {
             "url":"https://github.com/devinus/poison",
             "commands":[ os.path.join( PARSERS_DIR, "test_elixir_poison/test_elixir_poison") ]
         },
   "Elixir Jason":
         {
             "url":"https://github.com/michalmuskala/jason",
             "commands":[ os.path.join( PARSERS_DIR, "test_elixir_jason/test_elixir_jason") ]
         },
   "Erlang Euneus":
         {
            "url":"https://github.com/williamthome/euneus",
            "commands":[ os.path.join( PARSERS_DIR, "test_erlang_euneus/test_erlang_euneus") ]
         },
   "Nim":
         {
             "url":"http://nim-lang.org",
             "commands":[ os.path.join( PARSERS_DIR, "test_nim/test_json") ]
         },
   "Swift JSON 20170522":
       {
           "url":"https://github.com/owensd/json-swift",
           "commands":[os.path.join(PARSERS_DIR, "test_json_swift_20170522/bin/json_swift")]
       },
   "C++ nlohmann JSON 20190718":
       {
           "url":"https://github.com/nlohmann/json",
           "commands":[os.path.join(PARSERS_DIR, "test_nlohmann_json_20190718/bin/test_nlohmann_json")]
       },
   "C++ JSONpp 0.1.1":
       {
           "url":"https://github.com/mikami-w/jsonpp",
           "commands":[os.path.join(PARSERS_DIR, "test_jsonpp_0_1_1/.build/test_jsonpp")]
       },
   "Java opack 0.2.1 (UTF-8)":
       {
           "url":"https://github.com/realtimetech-solution/opack",
           "commands":["java", "-cp", os.path.join(PARSERS_DIR, "test_java_opack_0_2_1/.build/classes"), "TestJSONParsing"]
       },
   "Java fastjson2 2.0.53 (native mode)":
       {
           "url":"https://github.com/alibaba/fastjson2",
           "commands":["java", "-cp", os.path.join(PARSERS_DIR, "test_java_fastjson2_2_0_53/.build/classes") + os.pathsep + os.path.join(PARSERS_DIR, "test_java_fastjson2_2_0_53/.build/fastjson2-2.0.53.jar"), "TestJSONParsing"]
       },
   "Tcl rl_json 0.17.6 (strict UTF-8, no comments)":
       {
           "url":"https://github.com/RubyLane/rl_json",
           "commands":["python3", os.path.join(PARSERS_DIR, "test_rl_json_0_17_6/TestJSONParsing.py")],
           "use_stdin": True
       },
   "C libfyaml 0.9.6 (JSON force, streaming)":
       {
           "url":"https://github.com/pantoniou/libfyaml",
           "commands":["sh", os.path.join(PARSERS_DIR, "test_libfyaml_0_9_6/run.sh")]
       },
   "Python jsoncgx 1.1 (comments off)":
       {
           "url":"https://github.com/cigix/jsoncgx",
           "commands":["python3", os.path.join(PARSERS_DIR, "test_jsoncgx_1_1/TestJSONParsing.py"), "off"]
       },
   "Python jsoncgx 1.1 (comments on)":
       {
           "url":"https://github.com/cigix/jsoncgx",
           "commands":["python3", os.path.join(PARSERS_DIR, "test_jsoncgx_1_1/TestJSONParsing.py"), "on"]
       },
   "Clojure data.json 1.0.0":
       {
           "url":"https://github.com/clojure/data.json",
           "commands":["sh", os.path.join(PARSERS_DIR, "test_clojure_data_json/run.sh"), "1.0.0"]
       },
   "Clojure data.json 2.2.0":
       {
           "url":"https://github.com/clojure/data.json",
           "commands":["sh", os.path.join(PARSERS_DIR, "test_clojure_data_json/run.sh"), "2.2.0"]
       }
}

from parsers.features.registry import go_batch_01_programs, batch_02_programs
programs.update(go_batch_01_programs(PARSERS_DIR))
programs.update(batch_02_programs(PARSERS_DIR))

STATUS_LABELS = {
    "EXPECTED_RESULT": "expected result",
    "SHOULD_HAVE_PASSED": "parsing should have succeeded but failed",
    "SHOULD_HAVE_FAILED": "parsing should have failed but succeeded",
    "IMPLEMENTATION_PASS": "implementation-dependent, parsing succeeded",
    "IMPLEMENTATION_FAIL": "implementation-dependent, parsing failed",
    "CRASH": "parser crashed",
    "TIMEOUT": "timeout",
    "SKIPPED_UNAVAILABLE": "skipped: parser could not be started",
    "SKIPPED_SETUP_FAILED": "skipped: parser setup failed",
    "NOT_RECORDED": "not recorded (execution unknown)",
}
SKIPPED_STATUSES = {"SKIPPED_UNAVAILABLE", "SKIPPED_SETUP_FAILED"}


class SelectionError(ValueError):
    """Invalid parser or fixture selection, detected before run side effects."""


CI_FAILURE_STATUSES = frozenset((
    "SHOULD_HAVE_PASSED", "SHOULD_HAVE_FAILED", "CRASH", "TIMEOUT",
    "SKIPPED_UNAVAILABLE", "SKIPPED_SETUP_FAILED",
))


def run_tests(restrict_to_path=None, restrict_to_program=None, jobs=1):
    if isinstance(jobs, bool) or not isinstance(jobs, int) or jobs < 1:
        raise SelectionError("jobs must be a positive integer")
    has_filter = restrict_to_program is not None
    if isinstance(restrict_to_program, io.TextIOBase):
        try:
            restrict_to_program = json.load(restrict_to_program)
        except (ValueError, UnicodeError) as error:
            raise SelectionError("Invalid JSON filter: %s" % error) from error
    prog_names = sorted(programs)
    if has_filter:
        if (not isinstance(restrict_to_program, list) or not restrict_to_program
                or not all(isinstance(name, str) for name in restrict_to_program)):
            raise SelectionError("Filter must be a non-empty JSON array of parser names")
        unknown = sorted(set(restrict_to_program) - programs.keys())
        if unknown:
            raise SelectionError("Unknown parser name(s): %s" % ", ".join(repr(name) for name in unknown))
        prog_names = [name for name in prog_names if name in restrict_to_program]
    if not prog_names:
        raise SelectionError("No parsers selected")

    selected_basename = None
    selected_path = None
    if restrict_to_path is not None:
        selector = os.fspath(restrict_to_path)
        if not os.path.isabs(selector) and not os.path.dirname(selector):
            # Retain the historic shorthand, including nested name matches.
            selected_basename = selector
        else:
            corpus_root = os.path.realpath(TEST_CASES_DIR_PATH)
            if os.path.isabs(selector):
                candidate = os.path.realpath(selector)
            else:
                relative = selector
                while relative.startswith("." + os.sep):
                    relative = relative[2:]
                if ".." in relative.split(os.sep):
                    raise SelectionError("Fixture selector is outside test_parsing: %r" % selector)
                if relative == "test_parsing":
                    relative = "."
                elif relative.startswith("test_parsing" + os.sep):
                    relative = relative[len("test_parsing") + 1:]
                candidate = os.path.realpath(os.path.join(corpus_root, relative))
            try:
                inside_corpus = os.path.commonpath((corpus_root, candidate)) == corpus_root
            except ValueError:
                inside_corpus = False
            if not inside_corpus:
                raise SelectionError("Fixture selector is outside test_parsing: %r" % selector)
            selected_path = os.path.relpath(candidate, corpus_root)

    # Snapshot the selected corpus so each selected pair gets one outcome.
    cases = []
    for root, dirs, files in os.walk(TEST_CASES_DIR_PATH):
        dirs.sort()
        for filename in sorted(files):
            if not filename.endswith(".json"):
                continue
            file_path = os.path.join(root, filename)
            relative_path = os.path.relpath(file_path, TEST_CASES_DIR_PATH)
            if selected_basename is not None and filename != selected_basename:
                continue
            if selected_path is not None and relative_path != selected_path:
                continue
            cases.append((relative_path, file_path))

    if not cases:
        if restrict_to_path is not None:
            raise SelectionError("No corpus fixture matches selector: %r" % restrict_to_path)
        raise SelectionError("No JSON fixtures found in corpus: %s" % TEST_CASES_DIR_PATH)

    failures = 0
    with open(os.devnull, 'w') as FNULL, open(LOG_FILE_PATH, 'w') as log_file:
        def replay(events):
            nonlocal failures
            for event in events:
                if event[0] == "row":
                    _, prog_name, status, filename = event
                    failures += status in CI_FAILURE_STATUSES
                    row = "%s\t%s\t%s" % (prog_name, status, filename)
                    print(row)
                    log_file.write(row + "\n")
                else:
                    print(*event[1:])

        def prepare(prog_name):
            setup = programs[prog_name].get("setup")
            if setup is None:
                return False, []
            events = [("message", "--", " ".join(setup))]
            try:
                failed = subprocess.call(setup) != 0
            except (OSError, subprocess.SubprocessError) as error:
                events.append(("message", "-- skip setup", error))
                failed = True
            if failed:
                events.extend(("row", prog_name, "SKIPPED_SETUP_FAILED", filename)
                              for filename, _ in cases)
            return failed, events

        def execute(prog_name):
            d = programs[prog_name]
            commands = d["commands"]
            use_stdin = d.get("use_stdin", False)
            timeout = d.get("timeout", 5)
            events = []
            for index, (filename, file_path) in enumerate(cases):
                command = commands if use_stdin else commands + [file_path]
                events.append(("message", "--", " ".join(command)))
                stream = open(file_path, "rb") if use_stdin else nullcontext(FNULL)
                with stream as my_stdin:
                    try:
                        status = subprocess.call(command, stdin=my_stdin, stdout=FNULL,
                                                 stderr=subprocess.STDOUT, timeout=timeout)
                    except subprocess.TimeoutExpired:
                        events.append(("row", prog_name, "TIMEOUT", filename))
                        events.append(("message", "RESULT:", "TIMEOUT"))
                        continue
                    except OSError as error:
                        # A process that never starts has no JSON parsing verdict.
                        events.append(("message", "-- skip unavailable", error))
                        events.extend(("row", prog_name, "SKIPPED_UNAVAILABLE", skipped_filename)
                                      for skipped_filename, _ in cases[index:])
                        break

                prefix = os.path.basename(filename)[:2]
                if status not in (0, 1):
                    result = "CRASH"
                elif prefix == "i_":
                    result = "IMPLEMENTATION_PASS" if status == 0 else "IMPLEMENTATION_FAIL"
                elif prefix == "y_":
                    result = "EXPECTED_RESULT" if status == 0 else "SHOULD_HAVE_PASSED"
                elif prefix == "n_":
                    result = "EXPECTED_RESULT" if status == 1 else "SHOULD_HAVE_FAILED"
                else:
                    raise ValueError("Unknown fixture prefix: " + filename)
                events.append(("row", prog_name, result, filename))
            return events

        if jobs == 1:
            for prog_name in prog_names:
                failed, events = prepare(prog_name)
                replay(events)
                if not failed:
                    replay(execute(prog_name))
        else:
            # Setups are serialized because configurations may share build output.
            prepared = {name: prepare(name) for name in prog_names}
            with ThreadPoolExecutor(max_workers=jobs) as executor:
                futures = {name: executor.submit(execute, name) for name in prog_names
                           if not prepared[name][0]}
                # Only the main thread writes logs, in sorted parser order.
                for prog_name in prog_names:
                    failed, events = prepared[prog_name]
                    replay(events)
                    if not failed:
                        replay(futures[prog_name].result())
    return failures


def f_underline_non_printable_bytes(data):
    # Truncate bytes before escaping, never in the middle of an HTML entity/tag.
    preview = data[:36]
    rendered = "".join("<U>%02X</U>" % b if b < 0x20 or b > 0x7E
                       else escape(chr(b)) for b in preview)
    if any(b < 0x20 or b > 0x7E for b in preview):
        rendered += " &lt;=&gt; " + escape(preview.decode("utf-8", errors="replace"))
    if len(data) > 36:
        rendered += "(...)"
    return rendered


def f_status_for_lib_for_file(json_dir, results_dir):
    """Read new or historical three-column logs, without inferring successes."""
    by_file = {}
    libs = []
    with open(os.path.join(results_dir, LOG_FILENAME)) as log_file:
        for line_number, line in enumerate(log_file, 1):
            fields = line.rstrip("\r\n").split("\t")
            if len(fields) != 3 or fields[1] not in STATUS_LABELS:
                raise ValueError("Invalid log record at line %d" % line_number)
            lib, status, filename = fields
            if lib not in libs:
                libs.append(lib)
            json_path = os.path.join(json_dir, filename)
            by_file.setdefault(json_path, {})[lib] = status
    return by_file, libs


def f_status_for_path_for_lib(json_dir, results_dir):
    by_file, _ = f_status_for_lib_for_file(json_dir, results_dir)
    return results_by_parser(by_file)


def results_by_parser(by_file):
    by_parser = {}
    for path, outcomes in by_file.items():
        for lib, status in outcomes.items():
            by_parser.setdefault(lib, {})[path] = status
    return by_parser


def status_cell(status):
    return '<TD class="%s" title="%s">%s</TD>' % (
        status, escape(STATUS_LABELS[status]),
        "?" if status == "NOT_RECORDED" else ("skip" if status in SKIPPED_STATUSES else ""))


def fixture_preview(path):
    try:
        with open(path, "rb") as fixture:
            return f_underline_non_printable_bytes(fixture.read())
    except FileNotFoundError:
        return "(MISSING FILE)"


def f_tests_with_same_results(libs, status_for_lib_for_file):

    tests_with_same_results = {} #{ {lib1:status, lib2:status, lib3:status} : { filenames } }

    files = list(status_for_lib_for_file.keys())
    files.sort()

    for f in files:
        prefix = os.path.basename(f)[:1]
        lib_status_for_file = []
        for l in libs:
            if l in status_for_lib_for_file[f]:
                status = status_for_lib_for_file[f][l]
                lib_status = "%s_%s" % (status, l)
                lib_status_for_file.append(lib_status)
        results = " || ".join(lib_status_for_file)
        if results not in tests_with_same_results:
            tests_with_same_results[results] = set()
        tests_with_same_results[results].add(f)

    r = []
    for k,v in tests_with_same_results.items():
        r.append((k,v))
    r.sort()

    return r

def generate_report(report_path, keep_only_first_result_in_set = False):

    (status_for_lib_for_file, libs) = f_status_for_lib_for_file(TEST_CASES_DIR_PATH, LOGS_DIR_PATH)

    status_for_path_for_lib = results_by_parser(status_for_lib_for_file)

    tests_with_same_results = f_tests_with_same_results(libs, status_for_lib_for_file)

    with open(report_path, 'w', encoding='utf-8') as f:

        f.write("""<!DOCTYPE html>

        <HTML>

        <HEAD>
            <TITLE>JSON Parsing Tests</TITLE>
            <LINK rel="stylesheet" type="text/css" href="style.css">
            <META charset="UTF-8">
        </HEAD>

        <BODY>
        """)

        prog_names = sorted(libs)

        libs = list(status_for_path_for_lib.keys())
        libs.sort()

        title = "JSON Parsing Tests"
        if keep_only_first_result_in_set:
            title += ", Pruned"
        else:
            title += ", Full"
        f.write("<H1>%s</H1>\n" % title)
        f.write('<P>Appendix to: seriot.ch <A HREF="http://www.seriot.ch/parsing_json.php">Parsing JSON is a Minefield</A> http://www.seriot.ch/parsing_json.php</P>\n')
        f.write("<PRE>%s</PRE>\n" % strftime("%Y-%m-%d %H:%M:%S"))

        f.write("""<H4>Contents</H4>
        <OL>
        <LI><A HREF="#color_scheme">Color Scheme</A>
        <LI><A HREF="#all_results">Full Results</A>
        <LI><A HREF="#results_by_parser">Results by Parser</A>""")
        f.write("<UL>\n")
        for i, prog in enumerate(prog_names):
            f.write('    <LI><A HREF="#%d">%s</A></LI>\n' % (i, escape(prog)))
        f.write("</UL></LI></OL>\n")

        f.write('<A NAME="color_scheme"></A><H4>1. Color scheme</H4><TABLE>')
        for status, label in STATUS_LABELS.items():
            f.write('<TR><TD class="%s">%s</TD></TR>' % (status, escape(label)))
        f.write('</TABLE>')
        f.write('<H4>Recorded outcomes by parser</H4>')
        f.write('<P>Historical logs omit successful tests and skips. Counts below '
                'cover recorded outcomes only; missing records are unknown, not successes. '
                'Not recorded counts refer only to cases present in this log. '
                'Pruning does not change these counts.</P>')
        f.write('<TABLE><TR><TH>Parser</TH><TH>Executed (recorded)</TH>'
                '<TH>Skipped (recorded)</TH><TH>Not recorded</TH></TR>')
        for lib in libs:
            outcomes = list(status_for_path_for_lib[lib].values())
            skipped = sum(status in SKIPPED_STATUSES for status in outcomes)
            unknown = len(status_for_lib_for_file) - len(outcomes) + outcomes.count("NOT_RECORDED")
            executed = len(outcomes) - skipped - outcomes.count("NOT_RECORDED")
            f.write('<TR><TD>%s</TD><TD>%d</TD><TD>%d</TD><TD>%d</TD></TR>' %
                    (escape(lib), executed, skipped, unknown))
        f.write('</TABLE>')

        f.write('<A NAME="all_results"></A>\n')
        f.write("<H4>2. Full Results</H4>\n")
        f.write("<TABLE>\n")

        f.write("    <TR>\n")
        f.write("        <TH></TH>\n")
        for lib in libs:
            f.write('        <TH class="vertical"><DIV>%s</DIV></TH>\n' % escape(lib))
        f.write("        <TH></TH>\n")
        f.write("    </TR>\n")

        for (k, file_set) in tests_with_same_results:

            ordered_file_set = list(file_set)
            ordered_file_set.sort()

            if keep_only_first_result_in_set:
                ordered_file_set = [ordered_file_set[0]]

            for path in ordered_file_set:

                f.write("    <TR>\n")
                f.write('        <TD>%s</TD>' % escape(os.path.relpath(path, TEST_CASES_DIR_PATH)))

                status_for_lib = status_for_lib_for_file[path]

                for lib in libs:
                    f.write(status_cell(status_for_lib.get(lib, "NOT_RECORDED")))
                f.write('        <TD>%s</TD>' % fixture_preview(path))
                f.write("    </TR>")

        f.write("</TABLE>\n")


        ###

        f.write('<A NAME="results_by_parser"></A>\n')
        f.write("<H4>3. Results by Parser</H4>")
        for i, prog in enumerate(prog_names):
            url = programs.get(prog, {}).get("url", "")
            f.write("<P>\n")
            f.write('<A NAME="%d"></A>' % i)
            if len(url) > 0:
                f.write('<H4><A HREF="%s">%s</A></H4>\n' % (escape(url, quote=True), escape(prog)))
            else:
                f.write('<H4>%s</H4>\n' % escape(prog))

            ###

            if prog not in status_for_path_for_lib:
                continue
            status_for_path = status_for_path_for_lib[prog]

            paths = list(status_for_path.keys())
            paths.sort()

            f.write('<TABLE>\n')

            f.write("    <TR>\n")
            f.write("        <TH></TH>\n")
            f.write('        <TH class="space"><DIV></DIV></TH>\n')
            f.write("        <TH></TH>\n")
            f.write("    </TR>\n")

            for path in paths:

                f.write("    <TR>\n")
                f.write("        <TD>%s</TD>" % escape(os.path.relpath(path, TEST_CASES_DIR_PATH)))

                f.write(status_cell(status_for_path[path]))
                f.write("        <TD>%s</TD>" % fixture_preview(path))
                f.write("    </TR>")

            f.write('</TABLE>\n')
            f.write("</P>\n")

        ###

        f.write("""

        </BODY>

        </HTML>
        """)
    if os.path.exists('/usr/bin/open'):
        os.system('/usr/bin/open "%s"' % report_path)

###

def main(argv=None):
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('restrict_to_path', nargs='?', type=str, default=None)
    parser.add_argument('--filter', dest='restrict_to_program', type=argparse.FileType('r'), default=None)
    parser.add_argument('--jobs', type=int, default=1,
                        help='run this many independent parsers concurrently (default: 1)')
    parser.add_argument('--fail-on-discrepancy', action='store_true',
                        help='exit 1 for unexpected results, crashes, timeouts, or skipped cases')

    args = parser.parse_args(argv)
    try:
        failures = run_tests(args.restrict_to_path, args.restrict_to_program, args.jobs)
    except SelectionError as error:
        parser.error(str(error))
    finally:
        if args.restrict_to_program is not None and args.restrict_to_program is not sys.stdin:
            args.restrict_to_program.close()

    generate_report(os.path.join(BASE_DIR, "results/parsing.html"), keep_only_first_result_in_set = False)
    generate_report(os.path.join(BASE_DIR, "results/parsing_pruned.html"), keep_only_first_result_in_set = True)
    return 1 if args.fail_on_discrepancy and failures else 0


if __name__ == '__main__':
    sys.exit(main())
