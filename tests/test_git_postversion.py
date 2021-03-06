# -*- coding: utf-8 -*-
# Copyright © 2015-2018 ACSONE SA/NV
# License LGPLv3 (http://www.gnu.org/licenses/lgpl-3.0-standalone.html)

import os
import textwrap

import pytest

from setuptools_odoo import git_postversion
from setuptools_odoo import manifest

from . import DATA_DIR


def test_addon1():
    """ addon1 has 2 commit after version 8.0.1.0.0 """
    addon1_dir = os.path.join(DATA_DIR, 'addon1')
    version = git_postversion.get_git_postversion(addon1_dir)
    assert version == '8.0.1.0.0.99.dev3'


def test_addon2():
    """ addon2 has not changed since 8.0.1.0.1 """
    addon2_dir = os.path.join(DATA_DIR, 'addon2')
    version = git_postversion.get_git_postversion(addon2_dir)
    assert version == '8.0.1.0.1'


def test_addon2_uncommitted_version_change():
    """ test with a local uncommitted version change """
    addon2_dir = os.path.join(DATA_DIR, 'addon2')
    manifest_path = os.path.join(addon2_dir, '__openerp__.py')
    with open(manifest_path) as f:
        manifest = f.read()
    try:
        with open(manifest_path, "w") as f:
            f.write(manifest.replace("8.0.1.0.1", "8.0.1.0.2"))
        version = git_postversion.get_git_postversion(addon2_dir)
        assert version == '8.0.1.0.2.dev1'
    finally:
        with open(manifest_path, "w") as f:
            f.write(manifest)


def test_addon1_uncommitted_change():
    """ test with a local uncommitted change without version change """
    addon1_dir = os.path.join(DATA_DIR, 'addon1')
    manifest_path = os.path.join(addon1_dir, '__openerp__.py')
    with open(manifest_path) as f:
        manifest = f.read()
    try:
        with open(manifest_path, "w") as f:
            f.write(manifest.replace("summary", "great summary"))
        version = git_postversion.get_git_postversion(addon1_dir)
        assert version == '8.0.1.0.0.99.dev4'
    finally:
        with open(manifest_path, "w") as f:
            f.write(manifest)


def test_no_git(tmpdir):
    """ get version outisde of git repo, get it from manifest """
    tmpdir.join('__openerp__.py').write(textwrap.dedent("""\
        {
           'version': '10.0.1.2.3',
        }
    """))
    version = git_postversion.get_git_postversion(str(tmpdir))
    assert version == '10.0.1.2.3'


def test_no_manifest():
    with pytest.raises(manifest.NoManifestFound):
        git_postversion.get_git_postversion(DATA_DIR)
