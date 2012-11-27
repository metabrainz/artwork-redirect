# Copyright (C) 2011 Lukas Lalinsky
# Distributed under the MIT license, see the LICENSE file for details.

import os.path
import ConfigParser
from sqlalchemy.engine.url import URL

class S3Config(object):
    def __init__(self):
        self.prefix = None

    def read(self, parser, section):
        self.prefix = parser.get(section, 'prefix')

class ListenConfig(object):
    def __init__(self):
        self.addr = None
        self.port = None

    def read(self, parser, section):
        self.addr = parser.get(section, 'address')
        self.port = parser.get(section, 'port')

class DatabaseConfig(object):

    def __init__(self):
        self.user = None
        self.superuser = 'postgres'
        self.name = None
        self.host = None
        self.port = None
        self.password = None
        self.static_path = None

    def create_url(self, superuser=False):
        kwargs = {}
        if superuser:
            kwargs['username'] = self.superuser
        else:
            kwargs['username'] = self.user
        kwargs['database'] = self.name
        if self.host is not None:
            kwargs['host'] = self.host
        if self.port is not None:
            kwargs['port'] = self.port
        if self.password is not None:
            kwargs['password'] = self.password
        return URL('postgresql', **kwargs)

    def read(self, parser, section):
        self.user = parser.get(section, 'user')
        self.name = parser.get(section, 'name')
        if parser.has_option(section, 'host'):
            self.host = parser.get(section, 'host')
        if parser.has_option(section, 'port'):
            self.port = parser.getint(section, 'port')
        if parser.has_option(section, 'password'):
            self.password = parser.get(section, 'password')


class Config(object):

    def __init__(self, path, static_path, test=False):
        self.static_path = static_path
        parser = ConfigParser.RawConfigParser()
        parser.read(path)
        self.database = DatabaseConfig()
        if test:
            self.database.read(parser, 'testdatabase')
        else:
            self.database.read(parser, 'database')
        self.listen = ListenConfig()
        self.listen.read(parser, 'listen')
        self.s3 = S3Config()
        self.s3.read(parser, 's3')


