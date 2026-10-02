"""Checks for committed corpus modes and the opt-in corpus-only artifact."""

import hashlib
from pathlib import Path
import os
import shutil
import subprocess
import tarfile
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
GIT = shutil.which("git")
MAKE = os.environ.get("MAKE") or shutil.which("make")


@unittest.skipUnless(GIT, "Git is required to inspect tracked fixtures")
class CorpusDistributionTests(unittest.TestCase):
    def git(self, *arguments):
        return subprocess.check_output([GIT, "-C", str(ROOT), *arguments])

    def test_fixtures_are_not_executable(self):
        tracked = self.git("ls-files", "--stage", "-z", "--",
                           "test_parsing", "test_transform")
        modes = [entry.split(b" ", 1)[0] for entry in tracked.split(b"\0") if entry]
        self.assertTrue(modes)
        self.assertEqual(set(modes), {b"100644"})

    @unittest.skipUnless(MAKE, "make is required for the archive target")
    def test_archive_contains_only_committed_corpus_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            output_dir = Path(directory) / "corpus outputs"
            command = [MAKE, "-C", str(ROOT), "corpus-archive",
                       "DIST_DIR=" + str(output_dir)]
            subprocess.run(command, check=True, capture_output=True, timeout=30)
            archive, = output_dir.glob("*.tar.gz")
            first_digest = hashlib.sha256(archive.read_bytes()).digest()

            tracked = set(self.git("ls-tree", "-r", "--name-only", "HEAD", "--",
                                   "LICENSE", "test_parsing", "test_transform")
                          .decode().splitlines())
            with tarfile.open(archive, "r:gz") as bundle:
                members = {member.name: member for member in bundle if member.isfile()}
                self.assertEqual(set(members), tracked)
                for name, member in members.items():
                    with self.subTest(name=name):
                        self.assertEqual(bundle.extractfile(member).read(),
                                         self.git("show", "HEAD:" + name))

            subprocess.run(command, check=True, capture_output=True, timeout=30)
            self.assertEqual(hashlib.sha256(archive.read_bytes()).digest(), first_digest)


if __name__ == "__main__":
    unittest.main()
