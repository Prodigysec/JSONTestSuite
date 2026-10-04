#!/usr/bin/env python3
"""Build batch-three observers against checksum-pinned, source-reviewed release JARs."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / 'parsers/.build/java_batch_03'
SOURCE = ROOT / 'parsers/features/java_batch_03'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fetch(url, path, expected):
    if not path.exists():
        with urllib.request.urlopen(url, timeout=45) as response:
            path.write_bytes(response.read())
    if digest(path) != expected:
        raise ValueError('Artifact checksum mismatch: ' + str(path))


def java_home():
    value = os.environ.get('JSONSUITE_JAVA_HOME') or os.environ.get('JAVA_HOME')
    if value:
        return Path(value)
    compiler = shutil.which('javac')
    if compiler:
        return Path(compiler).resolve().parents[1]
    isolated = Path('/tmp/jsonsuite-parser-tools/runtime/usr/lib/jvm/java-21-openjdk-amd64')
    if (isolated / 'bin/javac').is_file():
        return isolated
    raise ValueError('JDK >=17 unavailable; set JSONSUITE_JAVA_HOME')


def build():
    pins = json.loads((SOURCE / 'sources.json').read_text())
    BUILD.mkdir(parents=True, exist_ok=True)
    jars = []
    for library in pins['libraries']:
        for artifact in library['artifacts']:
            fetch(artifact['url'], BUILD / artifact['filename'], artifact['sha256'])
        source_jar = BUILD / next(a['filename'] for a in library['artifacts'] if a['filename'].endswith('-sources.jar'))
        with zipfile.ZipFile(source_jar) as archive:
            for path, expected in library['reviewed_source_files'].items():
                if hashlib.sha256(archive.read(path)).hexdigest() != expected:
                    raise ValueError('Reviewed source mismatch: ' + path)
            for notice in library['licenses']:
                preserved = ROOT / notice['preserved']
                if digest(preserved) != notice['sha256']:
                    raise ValueError('Preserved license mismatch')
                if 'source_jar_path' in notice and archive.read(notice['source_jar_path']) != preserved.read_bytes():
                    raise ValueError('Source license mismatch')
                if 'source_url' in notice:
                    fetch(notice['source_url'], BUILD / preserved.name, notice['sha256'])
        for dependency in library.get('bundled_dependencies', []):
            fetch(dependency['source_url'], BUILD / 'asm-5.0.3.pom', dependency['source_sha256'])
            preserved = ROOT / dependency['notice']
            if digest(preserved) != dependency['notice_sha256']:
                raise ValueError('Bundled ASM notice mismatch')
        jars.append(BUILD / next(a['filename'] for a in library['artifacts'] if a['filename'].endswith('.jar') and not a['filename'].endswith('-sources.jar')))
    home = java_home()
    adapter = SOURCE / 'ObserveJavaBatch03.java'
    classpath = os.pathsep.join(map(str, jars))
    temporary = Path(tempfile.mkdtemp(prefix='classes-building-', dir=BUILD))
    try:
        command = [str(home / 'bin/javac'), '--release', '17', '-cp', classpath, '-d', str(temporary), str(adapter)]
        subprocess.run(command, check=True)
        class_hashes = {str(p.relative_to(temporary)): digest(p) for p in sorted(temporary.rglob('*.class'))}
        key = hashlib.sha256(json.dumps(class_hashes, sort_keys=True).encode()).hexdigest()
        published = BUILD / ('classes-' + key)
        if published.exists():
            shutil.rmtree(temporary)
        else:
            temporary.rename(published)
    finally:
        if temporary.exists():
            shutil.rmtree(temporary)
    report = {'method': pins['build_method'], 'compiler': subprocess.check_output([str(home/'bin/javac'), '-version'], stderr=subprocess.STDOUT, text=True).strip(),
              'java_version': subprocess.check_output([str(home/'bin/java'), '-version'], stderr=subprocess.STDOUT, text=True).strip(),
              'bytecode_release': 17, 'pins_sha256': digest(SOURCE/'sources.json'), 'adapter_sha256': digest(adapter),
              'classes_sha256': class_hashes, 'runtime_artifacts': {p.name: digest(p) for p in jars}}
    # Unique temporary names also avoid competing builders sharing publication files.
    for name, value in [('runtime.json', {'java': str(home/'bin/java'), 'classpath': str(published)+os.pathsep+classpath}), ('build.json', report)]:
        with tempfile.NamedTemporaryFile(mode='w', dir=BUILD, delete=False) as handle:
            json.dump(value, handle, indent=2); handle.write('\n'); path = Path(handle.name)
        path.replace(BUILD/name)
    print('Batch 03: three pinned release sources/runtimes and licenses verified; observer built with ' + report['compiler'])


if __name__ == '__main__':
    try:
        build()
    except (OSError, ValueError, subprocess.SubprocessError, zipfile.BadZipFile) as error:
        print('SKIPPED_SETUP_FAILED: ' + str(error), file=sys.stderr)
        sys.exit(2)
