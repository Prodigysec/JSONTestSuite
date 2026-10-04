#!/usr/bin/env python3
"""Build reviewed Go feature sources with a checksum-pinned isolated toolchain."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import tarfile
import urllib.request

ROOT=Path(__file__).resolve().parents[1]
BUILD=ROOT/'parsers/.build'


def build(batch):
    project=ROOT/'parsers/features'/('go_batch_'+batch)
    pins=json.loads((project/'sources.json').read_text())
    if platform.system()!='Linux' or platform.machine() not in {'x86_64','amd64'}:
        raise ValueError('Pinned bootstrap currently supports Linux amd64; other platforms are untested')
    supplied=os.environ.get('JSONSUITE_GO')
    if supplied:
        go=Path(supplied)
    else:
        toolchain=BUILD/'toolchains'/pins['go_version']
        go=toolchain/'go/bin/go'
        if not go.exists():
            toolchain.mkdir(parents=True,exist_ok=True)
            archive=toolchain/pins['toolchain_archive']
            if not archive.exists():
                urllib.request.urlretrieve('https://go.dev/dl/'+pins['toolchain_archive'],archive)
            if hashlib.sha256(archive.read_bytes()).hexdigest()!=pins['toolchain_sha256']:
                archive.unlink()
                raise ValueError('Go toolchain archive checksum mismatch')
            with tarfile.open(archive) as tar:tar.extractall(toolchain,filter='data')
    go=go.resolve()
    version=subprocess.check_output([str(go),'version'],text=True).strip()
    if version!='go version '+pins['go_version']+' linux/amd64':
        raise ValueError('Unexpected Go toolchain: '+version)
    BUILD.mkdir(parents=True,exist_ok=True)
    env=os.environ.copy()
    env.update(GOTOOLCHAIN='local',CGO_ENABLED='0',GOOS='linux',GOARCH='amd64',GOAMD64='v1',
               GOMAXPROCS='2',GOFLAGS='-p=2',GOPROXY='https://proxy.golang.org',GOSUMDB='sum.golang.org',
               GOPATH=str(Path(env.get('JSONSUITE_GO_MOD_CACHE',BUILD/'go-module-cache')).resolve()),
               GOCACHE=str(BUILD/'go-compile-cache'))
    command=[str(go),'build','-mod=readonly','-trimpath','-o',str(BUILD/('feature_go_batch_'+batch)),'.']
    subprocess.run(command,cwd=project,env=env,check=True)
    modules=[]
    for pin in pins['modules']:
        info=json.loads(subprocess.check_output([str(go),'list','-m','-json',pin['module']],cwd=project,env=env,text=True))
        if info['Version']!=pin['version']:
            raise ValueError('Dependency version mismatch: '+pin['module'])
        license_path=Path(info['Dir'])/'LICENSE'
        license_hash=hashlib.sha256(license_path.read_bytes()).hexdigest()
        if license_hash!=pin['license_sha256']:
            raise ValueError('Primary-source license differs from reviewed archive: '+pin['module'])
        modules.append(dict(module=info['Path'],version=info['Version'],license_sha256=license_hash))
    subprocess.run([str(go),'mod','verify'],cwd=project,env=env,check=True)
    report=dict(batch=batch,toolchain=version,command=command,modules=modules,
                binary_sha256=hashlib.sha256((BUILD/('feature_go_batch_'+batch)).read_bytes()).hexdigest(),
                go_mod_sha256=hashlib.sha256((project/'go.mod').read_bytes()).hexdigest(),
                go_sum_sha256=hashlib.sha256((project/'go.sum').read_bytes()).hexdigest(),
                source_sha256=hashlib.sha256((project/'main.go').read_bytes()).hexdigest())
    (BUILD/('feature_go_batch_'+batch+'.build.json')).write_text(json.dumps(report,indent=2)+'\n')
    print('Go batch %s built with %s; %d primary dependency pins and licenses verified.'%(batch,pins['go_version'],len(modules)))
    return report


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('batch',choices=['01','02'])
    args=parser.parse_args(argv)
    try:build(args.batch)
    except (OSError,ValueError,subprocess.SubprocessError) as error:
        print('SKIPPED_SETUP_FAILED: '+str(error),file=sys.stderr);return 2
    return 0


if __name__=='__main__':sys.exit(main())
