#!/usr/bin/env python3
"""Compile pinned json-smart/accessors-smart source with ASM 9.7.1 and JDK >=17."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import tempfile
import urllib.request

ROOT=Path(__file__).resolve().parents[1]
BUILD=ROOT/'parsers/.build/json_smart'
ASM_SHA='8cadd43ac5eb6d09de05faecca38b917a040bb9139c7edeb4cc81c740b713281'


def java_home():
    value=os.environ.get('JSONSUITE_JAVA_HOME') or os.environ.get('JAVA_HOME')
    if value:return Path(value)
    compiler=shutil.which('javac')
    if compiler:return Path(compiler).resolve().parents[1]
    isolated=Path('/tmp/jsonsuite-parser-tools/runtime/usr/lib/jvm/java-21-openjdk-amd64')
    if (isolated/'bin/javac').is_file():return isolated
    raise ValueError('JDK >=17 unavailable; set JSONSUITE_JAVA_HOME')


def build():
    home=java_home()
    source=next(s for s in json.loads((ROOT/'docs/roadmap/feature-batch-02-sources.json').read_text())['sources'] if s['repository']=='netplex/json-smart-v2')
    BUILD.mkdir(parents=True,exist_ok=True)
    archive=BUILD/'source.tar.gz'
    if not archive.exists():urllib.request.urlretrieve('https://codeload.github.com/'+source['repository']+'/tar.gz/'+source['commit'],archive)
    if hashlib.sha256(archive.read_bytes()).hexdigest()!=source['archive_sha256']:raise ValueError('json-smart source checksum mismatch')
    extracted=BUILD/'sources'
    if not extracted.exists():
        with tarfile.open(archive) as tar:tar.extractall(extracted,filter='data')
    base=next(extracted.iterdir())
    if (base/'LICENSE').read_bytes()!=(ROOT/source['preserved_license']).read_bytes():raise ValueError('json-smart license mismatch')
    asm=BUILD/'asm-9.7.1.jar'
    if not asm.exists():urllib.request.urlretrieve('https://repo.maven.apache.org/maven2/org/ow2/asm/asm/9.7.1/asm-9.7.1.jar',asm)
    if hashlib.sha256(asm.read_bytes()).hexdigest()!=ASM_SHA:raise ValueError('ASM artifact checksum mismatch')
    temporary_classes=Path(tempfile.mkdtemp(prefix='classes-building-',dir=BUILD))
    classes=temporary_classes
    files=sorted((base/'accessors-smart/src/main/java').rglob('*.java'))+sorted((base/'json-smart/src/main/java').rglob('*.java'))
    adapter=ROOT/'parsers/features/json_smart/ObserveJsonSmart.java';files.append(adapter)
    argfile=BUILD/'javac.args';argfile.write_text('\n'.join('"'+str(p)+'"' for p in files)+'\n')
    javac=str(home/'bin/javac');version=subprocess.check_output([javac,'-version'],stderr=subprocess.STDOUT,text=True).strip()
    command=[javac,'--release','17','-cp',str(asm),'-d',str(classes),'@'+str(argfile)]
    subprocess.run(command,check=True)
    digest=hashlib.sha256()
    for path in sorted(classes.rglob('*.class')):
        digest.update(str(path.relative_to(classes)).encode());digest.update(path.read_bytes())
    published=BUILD/('classes-'+digest.hexdigest())
    if published.exists():shutil.rmtree(classes)
    else:classes.rename(published)
    classes=published
    runtime_tmp=BUILD/'runtime.json.tmp'
    runtime_tmp.write_text(json.dumps({'java':str(home/'bin/java'),'classpath':str(classes)+os.pathsep+str(asm)},indent=2)+'\n')
    runtime_tmp.replace(BUILD/'runtime.json')
    report={'compiler':version,'java_version':subprocess.check_output([str(home/'bin/java'),'-version'],stderr=subprocess.STDOUT,text=True).strip(),
            'source_revision':source['commit'],'source_archive_sha256':source['archive_sha256'],'pom_version':'2.6.0-SNAPSHOT','asm_version':'9.7.1','asm_sha256':ASM_SHA,
            'adapter_sha256':hashlib.sha256(adapter.read_bytes()).hexdigest(),'classes_sha256':{str(p.relative_to(classes)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(classes.rglob('*.class'))}}
    (BUILD/'build.json').write_text(json.dumps(report,indent=2)+'\n')
    print('json-smart/accessors-smart source revision %s built with %s; ASM 9.7.1 verified.'%(source['commit'],version))


if __name__=='__main__':
    try:build()
    except (OSError,ValueError,subprocess.SubprocessError) as error:
        print('SKIPPED_SETUP_FAILED: '+str(error),file=sys.stderr);sys.exit(2)
