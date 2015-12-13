# -*- coding: utf-8 -*-
# © 2015 ACSONE SA/NV
# License LGPLv3 (http://www.gnu.org/licenses/lgpl-3.0-standalone.html)

import os
import subprocess
from pkg_resources import parse_version

from .manifest import (
    MANIFEST_NAMES, read_manifest, parse_manifest, NoManifestFound
)


def _run_git_command_exit_code(args, cwd=None):
    return subprocess.call(['git'] + args, cwd=cwd)


def _run_git_command_bytes(args, cwd=None):
    output = subprocess.check_output(['git'] + args, cwd=cwd)
    return output.strip()


def _run_git_command_lines(args, cwd=None):
    output = _run_git_command_bytes(args, cwd=cwd)
    return output.split('\n')


def is_git_controlled(path):
    return 0 == _run_git_command_exit_code(['rev-parse'], cwd=path)


def get_git_uncommitted(path):
    r = _run_git_command_exit_code(['diff', '--quiet', '--exit-code', path])
    return r != 0


def get_git_root(path):
    git_dir = _run_git_command_bytes(['rev-parse', '--git-dir'], cwd=path)
    return os.path.abspath(os.path.join(git_dir, '..'))


def git_log_iterator(path):
    """ yield commits using git log -- <dir> """
    N = 10
    count = 0
    while True:
        lines = _run_git_command_lines(['log', '--oneline',
                                        '-n', str(N),
                                        '--skip', str(count),
                                        '--', path])
        for line in lines:
            sha = line.split(' ', 1)[0]
            count += 1
            yield sha
        if len(lines) < N:
            break


def read_manifest_from_sha(sha, addon_dir):
    git_root = get_git_root(addon_dir)
    rel_addon_dir = os.path.relpath(addon_dir, git_root)
    for manifest_name in MANIFEST_NAMES:
        manifest_path = os.path.join(rel_addon_dir, manifest_name)
        try:
            s = _run_git_command_bytes(['show', sha + ':' + manifest_path],
                                       cwd=git_root)
        except subprocess.CalledProcessError:
            continue
        return parse_manifest(s)
    raise NoManifestFound("no manifest found is %s:%s" % (sha, addon_dir))


def get_git_postversion(addon_dir):
    """ return the addon version number, with a developmental version increment
    if there were git commits in the addon_dir after the last version change.

    If the last change to the addon correspond to the version number in the
    manifest it is used as is for the python package version. Otherwise a
    counter is incremented for each commit and resulting version number has
    the following form: [8|9].0.x.y.z.devN.sha1, N being the number of git
    commits since the version change.
    """
    SHA_UNCOMMITTED = '0'
    addon_dir = os.path.realpath(addon_dir)
    last_version = read_manifest(addon_dir).get('version')
    last_version_parsed = parse_version(last_version)
    if not is_git_controlled(addon_dir):
        return last_version
    last_sha = None
    count = 0
    if get_git_uncommitted(addon_dir):
        last_sha = SHA_UNCOMMITTED
    for sha in git_log_iterator(addon_dir):
        try:
            manifest = read_manifest_from_sha(sha, addon_dir)
        except NoManifestFound:
            break
        version = manifest.get('version')
        version_parsed = parse_version(version)
        if version_parsed != last_version_parsed:
            break
        if last_sha is None:
            last_sha = sha
        else:
            count += 1
    if count or last_sha == SHA_UNCOMMITTED:
        return last_version + ".1dev%s.%s" % (count, last_sha)
    else:
        return last_version
