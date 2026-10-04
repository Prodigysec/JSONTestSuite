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
