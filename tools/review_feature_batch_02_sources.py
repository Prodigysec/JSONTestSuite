#!/usr/bin/env python3
"""Verify reviewed source archives and native API findings for feature batch 02."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import tarfile
import urllib.request

ROOT=Path(__file__).resolve().parents[1]


def verify(cache):
    manifest=json.loads((ROOT/'docs/roadmap/feature-batch-02-sources.json').read_text())
    cache=Path(cache);cache.mkdir(parents=True,exist_ok=True)
    for source in manifest['sources']:
        archive=cache/(source['repository'].replace('/','-')+'.tar.gz')
        if not archive.exists():
            urllib.request.urlretrieve('https://codeload.github.com/'+source['repository']+'/tar.gz/'+source['commit'],archive)
        if hashlib.sha256(archive.read_bytes()).hexdigest()!=source['archive_sha256']:
            raise ValueError('Archive hash mismatch: '+source['repository'])
        with tarfile.open(archive) as tar:
            prefix=tar.getmembers()[0].name.split('/')[0]+'/'
            for path,digest in source['reviewed_files'].items():
                data=tar.extractfile(prefix+path).read()
                if hashlib.sha256(data).hexdigest()!=digest:
                    raise ValueError('Reviewed source file hash mismatch: '+path)
            license_bytes=tar.extractfile(prefix+'LICENSE').read()
            local=ROOT/source['preserved_license']
            if local.read_bytes()!=license_bytes:
                raise ValueError('Preserved license differs: '+source['repository'])
            for finding in source['findings']:
                text=tar.extractfile(prefix+finding['file']).read().decode('utf-8')
                if any(fragment not in text for fragment in finding['required_fragments']):
                    raise ValueError('Native API finding changed: '+finding['id'])
        print('%s %s: archive, %d reviewed files, license and %d API findings verified.'%(source['repository'],source['tag'],len(source['reviewed_files']),len(source['findings'])))
    return 0


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cache',type=Path,default=Path('/tmp/jsonsuite-feature-source-review-cache'))
    args=parser.parse_args()
    try:return verify(args.cache)
    except (OSError,ValueError,KeyError) as error:parser.error(str(error))


if __name__=='__main__':raise SystemExit(main())
