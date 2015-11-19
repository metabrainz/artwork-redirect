#!/usr/bin/env python
# -*- coding: UTF-8 -*-

from distutils.core import setup
from coverart_redirect import __version__

setup(
    name='coverart_redirect',
    version=__version__,
    author='Robert Kaye',
    author_email='rob@musicbrainz.org',
    packages=['coverart_redirect'],
    scripts=['coverart_redirect'],
    description='The MusicBrainz CoverArt redirect service',
)
