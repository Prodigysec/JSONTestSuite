"""Pinned feature-parser modes; runtime/library versions come from observers."""
from pathlib import Path

GO_BATCH_01_MODES = [
    ('goccy-default','Go goccy/go-json v0.11.2 (default)'),
    ('goccy-number','Go goccy/go-json v0.11.2 (UseNumber)'),
    ('sonic-default','Go sonic v1.15.4 (ConfigDefault)'),
    ('sonic-std','Go sonic v1.15.4 (ConfigStd)'),
    ('sonic-fastest','Go sonic v1.15.4 (ConfigFastest)'),
    ('sonic-unicode-errors','Go sonic v1.15.4 (ValidateString + UseUnicodeErrors)'),
    ('sonic-number','Go sonic v1.15.4 (UseNumber)'),
    ('sonic-int64','Go sonic v1.15.4 (UseInt64)'),
    ('jsoniter-default','Go json-iterator/go v1.1.12 (ConfigDefault)'),
    ('jsoniter-std','Go json-iterator/go v1.1.12 (ConfigCompatibleWithStandardLibrary)'),
    ('jsoniter-fastest','Go json-iterator/go v1.1.12 (ConfigFastest)'),
    ('jsoniter-number','Go json-iterator/go v1.1.12 (UseNumber)'),
]


def go_batch_01_programs(parsers_dir):
    directory=Path(parsers_dir)
    binary=str(directory/'.build/feature_go_batch_01')
    modes={}
    for mode,name in GO_BATCH_01_MODES:
        url='https://github.com/'+('goccy/go-json' if mode.startswith('goccy') else 'bytedance/sonic' if mode.startswith('sonic') else 'json-iterator/go')
        modes[name]=dict(url=url,setup=['sh',str(directory/'features/build_batch_01.sh')],
                         commands=[binary,mode], observation_commands=[binary,'--observe',mode],
                         observation_source_files=[str(directory/'features/go_batch_01'/file)
                                                   for file in ('main.go','go.mod','go.sum','sources.json')],
                         observation_build_artifacts=[binary,binary+'.build.json'])
    return modes

GO_BATCH_02_MODES = [
    ('jsonparser-default','Go buger/jsonparser v1.6.1 (DefaultConfig + native numeric conversion)'),
    ('jsonparser-lenient','Go buger/jsonparser v1.6.1 (Lenient + native numeric conversion)'),
    ('jsonparser-single-quotes','Go buger/jsonparser v1.6.1 (single quotes + native numeric conversion)'),
    ('jsonparser-unknown-escapes','Go buger/jsonparser v1.6.1 (unknown escapes + native numeric conversion)'),
    ('gojay-native','Go gojay v1.2.13 (native typed callbacks)'),
]
JSON_SMART_MODES = [('default','default'),('permissive','MODE_PERMISSIVE'),('incomplete','MODE_PERMISSIVE_WITH_INCOMPLETE'),
                    ('rfc4627','MODE_RFC4627'),('json-simple','MODE_JSON_SIMPLE'),('strictest','MODE_STRICTEST')]


def batch_02_programs(parsers_dir):
    import sys
    directory=Path(parsers_dir)
    modes={}
    binary=str(directory/'.build/feature_go_batch_02')
    for mode,name in GO_BATCH_02_MODES:
        library='buger/jsonparser' if mode.startswith('jsonparser') else 'francoispqt/gojay'
        modes[name]=dict(url='https://github.com/'+library,setup=[sys.executable,'-B',str(directory.parent/'tools/build_go_feature_batch.py'),'02'],
            commands=[binary,mode],observation_commands=[binary,'--observe',mode],
            observation_source_files=[str(directory/'features/go_batch_02'/file) for file in ('main.go','go.mod','go.sum','sources.json')],
            observation_build_artifacts=[binary,binary+'.build.json'])
    wrapper=str(directory/'features/json_smart/run.py')
    for mode,preset in JSON_SMART_MODES:
        name='Java json-smart source v2.6.0 (POM SNAPSHOT, %s, whole input)'%preset
        modes[name]=dict(url='https://github.com/netplex/json-smart-v2',setup=[sys.executable,'-B',str(directory.parent/'tools/build_json_smart_features.py')],
            commands=[sys.executable,'-B',wrapper,mode],observation_commands=[sys.executable,'-B',wrapper,'--observe',mode],
            observation_source_files=[str(directory/'features/json_smart/ObserveJsonSmart.java')],
            observation_build_artifacts=[str(directory/'.build/json_smart/build.json'),str(directory/'.build/json_smart/asm-9.7.1.jar')])
    return modes

JAVA_BATCH_03_MODES = [
    ('fastjson-default', 'Java Fastjson 1.2.83 (default features, SafeMode, whole input)'),
    ('fastjson-extension-flags-off', 'Java Fastjson 1.2.83 (extension flags off, SafeMode, whole input)'),
    ('fastjson-comments', 'Java Fastjson 1.2.83 (AllowComment, SafeMode, whole input)'),
    ('fastjson-double', 'Java Fastjson 1.2.83 (UseBigDecimal off, SafeMode, whole input)'),
    ('genson-default', 'Java Genson 1.6 (default, native encoding detection, whole input)'),
    ('genson-utf8', 'Java Genson 1.6 (default, explicit native UTF-8 API, whole input)'),
    ('genson-strict-double', 'Java Genson 1.6 (strict double conversion, explicit native UTF-8 API, whole input)'),
    ('jsoniter-default', 'Java jsoniter 0.9.23 (generic read, default reflection serializer, whole input)'),
]


def batch_03_programs(parsers_dir):
    import sys
    directory = Path(parsers_dir)
    source = directory / 'features/java_batch_03'
    wrapper = str(source / 'run.py')
    build = directory / '.build/java_batch_03'
    modes = {}
    for mode, name in JAVA_BATCH_03_MODES:
        library = mode.split('-')[0]
        repository = {'fastjson': 'alibaba/fastjson', 'genson': 'owlike/genson', 'jsoniter': 'json-iterator/java'}[library]
        modes[name] = dict(url='https://github.com/' + repository,
            setup=[sys.executable, '-B', str(directory.parent / 'tools/build_java_feature_batch_03.py')],
            commands=[sys.executable, '-B', wrapper, mode],
            observation_commands=[sys.executable, '-B', wrapper, '--observe', mode],
            observation_source_files=[str(source / 'ObserveJavaBatch03.java'), str(source / 'sources.json'),
                                      str(directory.parent / 'tools/build_java_feature_batch_03.py')],
            observation_build_artifacts=[str(build / 'build.json')] +
                [str(build / artifact) for artifact in ('fastjson-1.2.83.jar', 'genson-1.6.jar', 'jsoniter-0.9.23.jar')])
    return modes
