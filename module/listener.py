#!/usr/bin/python
# coding:utf8
# Created by wangyikai at 19/04/12

from time import strftime
from module.notify import NotifyClass
from module.printf import Printf
import sys
import threading


class Listener(NotifyClass, Printf):

    def __init__(self, mail_receivers, number):
        NotifyClass.__init__(self)
        Printf.__init__(self)
        self.mail_receivers = mail_receivers
        self.number = number

    def __main(self, team_name, process_name):
        while 1:
            # transition from ACKNOWLEDGED to READY
            self.write_stdout('READY\n')

            # read header line and print it to stderr
            line = sys.stdin.readline()
            self.write_stderr(">>> time:%s " % strftime("%Y-%m-%d_%H_%M_%S") + line)

            # read event payload and print it to stderr
            headers = dict([x.split(':') for x in line.split()])

            data = sys.stdin.read(int(headers['len'] + "\n"))

            self.write_stderr("    %s\n" % data)

            nowstate = headers["eventname"]

            if nowstate in ["PROCESS_STATE_EXITED"]:
                data = dict([x.split(':') for x in data.split()])
                # 触发告警
                warning_title = "%s monitor " % process_name
                warning_msg = "%s process from %s to %s\n%s %s" % (
                    data["processname"], data["from_state"], nowstate, self.host_ip, self.host_name)
                self.send_mail(self.mail_receivers, warning_title, warning_msg, self.crash_log_path)
                self.send_wxwechat(team_name, warning_title, warning_msg)

            # transition from READY to ACKNOWLEDGED
            self.write_stdout('RESULT 2\nOK')

    def run_listener(self, team_name, process_name, crash_log_path):
        self.crash_log_path = crash_log_path
        listener_thread = threading.Thread(target=self.__main, args=(team_name, process_name,))
        listener_thread.start()
