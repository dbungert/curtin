#   Copyright (C) 2013 Canonical Ltd.
#
#   Author: Scott Moser <scott.moser@canonical.com>
#
#   Curtin is free software: you can redistribute it and/or modify it under
#   the terms of the GNU Affero General Public License as published by the
#   Free Software Foundation, either version 3 of the License, or (at your
#   option) any later version.
#
#   Curtin is distributed in the hope that it will be useful, but WITHOUT ANY
#   WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
#   FOR A PARTICULAR PURPOSE.  See the GNU Affero General Public License for
#   more details.
#
#   You should have received a copy of the GNU Affero General Public License
#   along with Curtin.  If not, see <http://www.gnu.org/licenses/>.

import os

import curtin.config
from curtin.log import LOG
import curtin.util

from . import populate_one_subcmd

CMD_ARGUMENTS = (
    ((('-t', '--target'),
      {'help': ('target directory to extract to (root) '
                '[default TARGET_MOUNT_POINT]'),
       'action': 'store', 'default': os.environ.get('TARGET_MOUNT_POINT')}),
     (('sources',),
      {'help': 'the sources to install [default read from CONFIG]',
       'nargs': '*'}),
     )
)


def extract_root_tgz(source, target):
    curtin.util.subp(args=['sh', '-c',
                           ('wget "$1" --progress=dot:mega -O - |'
                            'tar -C "$2" -Sxpzf -'),
                           '--', source, target])


def copy_to_target(source, target):
    if source.startswith("cp://"):
        source = source[5:]
    source = os.path.abspath(source)

    curtin.util.subp(args=['sh', '-c',
                           ('mkdir -p "$2" && cd "$2" && '
                            'cp --archive --one-file-system "$1/"* .'),
                           '--', source, target])


def extract(args):
    if not args.target:
        raise ValueError("Target must be defined or set in environment")

    cfgfile = os.environ.get('CONFIG')
    cfg = {}

    sources = args.sources
    target = args.target
    if not sources:
        if cfgfile:
            cfg = curtin.config.load_config(cfgfile)
        if not cfg.get('sources'):
            raise ValueError("'sources' must be on cmdline or in config")
        sources = cfg.get('sources')

    if isinstance(sources, dict):
        sources = [sources[k] for k in sorted(sources.keys())]

    LOG.debug("Installing sources: %s to target at %s" % (sources, target))

    for source in sources:
        if source.startswith("cp://"):
            copy_to_target(source, target)
        elif source.startswith("http://"):
            extract_root_tgz(source, target)
        else:
            raise TypeError("do not know how to extract '%s'", source)


def POPULATE_SUBCMD(parser):
    populate_one_subcmd(parser, CMD_ARGUMENTS, extract)

# vi: ts=4 expandtab syntax=python