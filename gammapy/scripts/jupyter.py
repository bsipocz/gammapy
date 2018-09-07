# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""Command line tool to perform devel management actions on jupyter notebooks."""

from __future__ import absolute_import, division, print_function, unicode_literals
from black import format_str
import click
import logging
import nbformat
import subprocess
import sys
import testipynb
import time
from unittest import TestCase
from ..extern.pathlib import Path


log = logging.getLogger(__name__)


@click.command(name='black')
@click.pass_context
def cli_jupyter_black(ctx):
    """Format code cells with black."""

    nblist = build_nblist(ctx)

    for notebook in nblist:

        try:
            nb = nbformat.read(str(notebook), as_version=nbformat.NO_CONVERT)
        except Exception as ex:
            log.error('Error parsing file {}'.format(str(notebook)))
            log.error(ex)
            sys.exit()

        # paint cells in black
        for cellnumber, cell in enumerate(nb.cells):
            fmt = nb.cells[cellnumber]['source']
            if nb.cells[cellnumber]['cell_type'] == 'code':
                try:
                    semicolon = 0
                    fmt = comment_magics(fmt)
                    if fmt.endswith(';'):
                        semicolon = 1
                    fmt = format_str(src_contents=fmt,
                                     line_length=79).rstrip()
                    if semicolon:
                        fmt += ';'
                except Exception as ex:
                    logging.info(ex)
                fmt = fmt.replace("###-MAGIC COMMAND-", "")
            nb.cells[cellnumber]['source'] = fmt

        # write formatted notebook
        nbformat.write(nb, str(notebook))

        # inform
        print('Jupyter notebook {} painted in black.'.format(str(notebook)))


@click.command(name='stripout')
@click.pass_context
def cli_jupyter_stripout(ctx):
    """Strip output cells."""

    nblist = build_nblist(ctx)

    for notebook in nblist:

        try:
            subprocess.call("nbstripout '{}'".format(notebook), shell=True)
            print('Jupyter notebook {} stripped out.'.format(str(notebook)))
        except Exception as ex:
            log.error('Error stripping file {}'.format(str(notebook)))
            log.error(ex)


@click.command(name='execute')
@click.pass_context
def cli_jupyter_execute(ctx):
    """Execute jupyter notebook."""

    nblist = build_nblist(ctx)

    for notebook in nblist:

        try:
            t = time.time()
            subprocess.call(
                "jupyter nbconvert --allow-errors --ExecutePreprocessor.timeout=None --ExecutePreprocessor.kernel_name=python3 --to notebook --execute '{}'.format(notebook) --inplace",
                shell=True)
            t = (time.time() - t) / 60
            print('Executing duration: {:.2f} mn'.format(t))
        except Exception as ex:
            log.error('Error executing file {}'.format(str(notebook)))
            log.error(ex)


@click.command(name='test')
@click.pass_context
def cli_jupyter_test(ctx):
    """Check if jupyter notebook is broken."""

    notebook = Path(ctx.obj['file'])
    folder = Path(ctx.obj['fold'])
    ignorelist = []

    if ctx.obj['file']:
        # ignore all files except jupyterfile
        for f in notebook.parent.iterdir():
            if notebook.name != f.name and f.name.endswith('.ipynb'):
                nbname = f.name.replace('.ipynb', '')
                ignorelist.append(nbname)
        folder = notebook.parent

        print('oups')

    testnb = testipynb.TestNotebooks(
        directory=str(folder), ignore=ignorelist)
    TestCase.assertTrue(testnb, testnb.run_tests())


def comment_magics(input):
    """Comment magic commands when formatting cells."""

    lines = input.splitlines(True)
    output = ""
    for line in lines:
        new_line = ""
        if line.startswith("%") or line.startswith("!"):
            new_line = new_line + "###-MAGIC COMMAND-" + line
        if new_line:
            output = output + new_line
        else:
            output = output + line
    return output


def build_nblist(ctx):
    """Fill list of notebooks in a the given folder."""

    nblist = []
    if ctx.obj['file']:
        nblist.append(Path(ctx.obj['file']))
    else:
        for f in Path(ctx.obj['fold']).iterdir():
            if f.name.endswith('.ipynb'):
                nblist.append(f)
    return nblist
