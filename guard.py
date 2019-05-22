#!/usr/bin/python
# coding:utf8
# Created by wangyikai at 19/04/08


from module.monitor import Monitor
from module.listener import Listener
import json
import commands


class Guard(Monitor, Listener):

    def __init__(self):
        # 从系统环境变量获得 Server Name / Team Name
        self.server_name = commands.getoutput("echo $SERVER_NAME")
        self.team_name = commands.getoutput("echo $TEAM_NAME")
        assert self.server_name != "", "$SERVER_NAME not found"
        assert self.team_name != "", "$TEAM_NAME not found"

        if self.server_name == "db_monitor":
            # 加载 Server 配置文件
            with open("config/db.json") as jsonfile:
                self.config = json.load(jsonfile)
        else:
            with open("config/program.json") as jsonfile:
                self.config = json.load(jsonfile)

        # 获取已有的 Server List
        self.server_list = self.config.keys()

        # 判断当前主机 Server 是否在 Server List 里 , 如果不在就退出程序
        assert self.server_name in self.server_list, "%s not in self.server_list" % self.server_name

        # 获取 Server 对应的监控信息   self.server_config is Dict
        self.server_config = self.config[self.server_name]

        # 初始化 Monitor、Listener 类
        if self.server_name != "db_monitor":
            Listener.__init__(self, self.server_config["mail_receivers"], self.server_config["number"])
        Monitor.__init__(self, self.server_config["mail_receivers"], self.server_config["number"])

        self.go_guard = self.guard_db if self.server_name == "db_monitor" else self.guard_game

    def guard_game(self):
        # 判断监控信息格式是否正确
        for i in ["port", "route", "crash_log_path"]:
            assert i in self.server_config.keys(), "not found %s in self.server_config.keys()" % i

        port = self.server_config["port"]
        route = self.server_config["route"]

        self.monitor_route(self.team_name, self.server_name, port, route)
        self.monitor_port(self.team_name, self.server_name, port)
        self.monitor_process(self.team_name, self.server_name)
        self.run_listener(self.team_name, self.server_name, self.server_config["crash_log_path"])

    def guard_db(self):
        # 判断监控信息格式是否正确
        for db_type, db_list in self.server_config.iteritems():
            for db_ip, db_info in db_list.iteritems():
                assert sorted(["source", "password", "port", "user"]) == sorted(
                    db_info.keys()), "%s db_info error" % db_ip

        mysql_db_list = self.server_config["mysql"]
        redis_db_list = self.server_config["redis"]
        mongo_db_list = self.server_config["mongo"]

        self.monitor_mysql(self.team_name, mysql_db_list)
        self.monitor_redis(self.team_name, redis_db_list)
        self.monitor_mongo(self.team_name, mongo_db_list)


if __name__ == "__main__":
    # start monitor
    a = Guard()
    a.go_guard()
