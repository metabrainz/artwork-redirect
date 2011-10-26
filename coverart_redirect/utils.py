# Copyright (C) 2011 Lukas Lalinsky
# Distributed under the MIT license, see the LICENSE file for details.

import re
import syslog
from logging import Handler
from logging.handlers import SysLogHandler


class LocalSysLogHandler(Handler):
    """
    Logging handler that logs to the local syslog using the syslog module
    """

    facility_names = {
        "auth":     syslog.LOG_AUTH,
        "cron":     syslog.LOG_CRON,
        "daemon":   syslog.LOG_DAEMON,
        "kern":     syslog.LOG_KERN,
        "lpr":      syslog.LOG_LPR,
        "mail":     syslog.LOG_MAIL,
        "news":     syslog.LOG_NEWS,
        "syslog":   syslog.LOG_SYSLOG,
        "user":     syslog.LOG_USER,
        "uucp":     syslog.LOG_UUCP,
        "local0":   syslog.LOG_LOCAL0,
        "local1":   syslog.LOG_LOCAL1,
        "local2":   syslog.LOG_LOCAL2,
        "local3":   syslog.LOG_LOCAL3,
        "local4":   syslog.LOG_LOCAL4,
        "local5":   syslog.LOG_LOCAL5,
        "local6":   syslog.LOG_LOCAL6,
        "local7":   syslog.LOG_LOCAL7,
    }

    priority_map = {
        "DEBUG": syslog.LOG_DEBUG,
        "INFO": syslog.LOG_INFO,
        "WARNING": syslog.LOG_WARNING,
        "ERROR": syslog.LOG_ERR,
        "CRITICAL": syslog.LOG_CRIT
    }

    def __init__(self, ident=None, facility=syslog.LOG_USER, log_pid=False):
        Handler.__init__(self)
        self.facility = facility
        if isinstance(facility, basestring):
            self.facility = self.facility_names[facility]
        options = 0
        if log_pid:
            options |= syslog.LOG_PID
        syslog.openlog(ident, options, self.facility)
        self.formatter = None

    def close(self):
        Handler.close(self)
        syslog.closelog()

    def emit(self, record):
        try:
            msg = self.format(record)
            if isinstance(msg, unicode):
                msg = msg.encode('utf-8')
            priority = self.priority_map[record.levelname]
            for m in msg.splitlines():
                syslog.syslog(self.facility | priority, m)
        except StandardError:
            self.handleError(record)

