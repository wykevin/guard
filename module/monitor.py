#!/usr/bin/python
# coding:utf8
# Created by wangyikai at 19/04/08

from module.printf import Printf
from module.notify import NotifyClass
import threading
import socket
import requests
import commands
import pymysql
import redis
import pymongo


class Monitor(Printf, NotifyClass):

    def __init__(self, mail_receivers, number):
        # 初始化邮件类
        NotifyClass.__init__(self)
        Printf.__init__(self)
        self.mail_receivers = mail_receivers
        self.number = number

    def monitor_process(self, team_name, process_name):
        try:
            status, msg = commands.getstatusoutput("ps aux|grep %s|grep -v grep|wc -l" % process_name)
            self.write_stdout(msg)
            assert int(status) == 0
            assert int(msg) >= 1
            # 监控正常
            self.write_stderr("process ok")
        except Exception as e:
            # 触发告警
            warning_title = "%s monitor " % process_name
            warning_msg = "process is down  %s \n %s %s" % (e, self.host_ip, self.host_name)
            self.send_mail(self.mail_receivers, warning_title, warning_msg)
            self.send_wxwechat(team_name, warning_title, warning_msg)
            self.call(self.number, team_name, process_name)

        # 创建定时器
        timer = threading.Timer(180, self.monitor_process, [team_name, process_name])
        timer.start()

    def monitor_port(self, team_name, process_name, port):
        sk = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sk.settimeout(3)

        try:
            port = int(port)
            sk.connect((self.host_ip, port))
            # 监控正常
            self.write_stderr("port ok")
        except Exception as e:
            # 触发告警
            warning_title = "%s monitor " % process_name
            warning_msg = "%s port is down   %s \n %s %s" % (port, e, self.host_ip, self.host_name)
            self.send_mail(self.mail_receivers, warning_title, warning_msg)
            self.send_wxwechat(team_name, warning_title, warning_msg)
            # self.call(self.number, team_name, process_name)
        finally:
            sk.close()

        # 创建定时器
        timer = threading.Timer(180, self.monitor_port, [team_name, process_name, port])
        timer.start()

    def monitor_route(self, team_name, process_name, port, route):
        url = "http://%s:%s%s" % (self.host_ip, port, route)
        try:
            assert requests.get(url, timeout=3).status_code == 200
            # 监控正常
            self.write_stderr("url ok")
        except Exception as e:
            # 触发告警
            warning_title = "%s monitor " % process_name
            warning_msg = "http://%s:%s%s is down   %s \n %s" % (self.host_ip, port, route, e, self.host_name)
            self.send_mail(self.mail_receivers, warning_title, warning_msg)
            self.send_wxwechat(team_name, warning_title, warning_msg)
            # self.call(self.number, team_name, process_name)

        # 创建定时器
        timer = threading.Timer(180, self.monitor_route, [team_name, process_name, port, route])
        timer.start()

    def monitor_mysql(self, team_name, db_list):
        # insert_sql = "insert into test (dev_ops_test_monitor_check) values ('test')"
        # create_table_sql = "create table test ( dev_ops_test_monitor_check varchar(32) primary key default 'test')"
        for db_ip, db_info in db_list.iteritems():
            try:
                # 建立连接
                db = pymysql.connections.Connection(host=db_ip, user=db_info["user"], passwd=db_info["password"],
                                                    port=int(db_info["port"]),
                                                    db="yunwei_monitor", connect_timeout=3)
                try:
                    # 创建游标
                    cursor = db.cursor()
                    update_sql = "update test set dev_ops_test_monitor_check = 'test'"
                    select_sql = "select dev_ops_test_monitor_check from test"

                    # 先执行 select 操作
                    cursor.execute(select_sql)
                    db.commit()
                    select_result = cursor.fetchone()
                    # 如果 select 得到的不是 test 就抛出异常
                    assert select_result[0] == "test", "execute sql get '%s'" % select_result

                    # 执行 update 操作
                    cursor.execute(update_sql)
                    db.commit()

                    # 读写正常
                    self.write_stderr("%s ok" % db_info["source"])
                except Exception as e:
                    # 触发告警 先 db.rollback() 然后再发告警邮件
                    db.rollback()
                    warning_title = "%s mysql monitor " % db_info["source"]
                    warning_msg = "%s %s select/update error   %s \n %s %s" % (
                        db_ip, db_info["port"], e, self.host_ip, self.host_name)
                    self.send_mail(self.mail_receivers, warning_title, warning_msg)
                    self.send_wxwechat(team_name, warning_title, warning_msg)
                finally:
                    db.close()
            except Exception as e:
                # 触发告警
                warning_title = "%s mysql monitor " % db_info["source"]
                warning_msg = "%s %s connect error   %s \n %s %s" % (
                    db_ip, db_info["port"], e, self.host_ip, self.host_name)
                self.send_mail(self.mail_receivers, warning_title, warning_msg)
                self.send_wxwechat(team_name, warning_title, warning_msg)

        # 创建定时器
        timer = threading.Timer(300, self.monitor_mysql, [team_name, db_list])
        timer.start()

    def monitor_redis(self, team_name, db_list):
        for db_ip, db_info in db_list.iteritems():
            try:
                # 建立连接
                r = redis.Redis(host=db_ip, port=int(db_info["port"]), db=0, password=db_info["password"],
                                socket_timeout=3)

                # 更新数据
                set_result = r.set("dev_ops_test_monitor_check", "test")
                assert set_result, "redis set error"

                # 查询数据
                get_result = r.get("dev_ops_test_monitor_check")
                assert get_result == "test", "redis values error"

                self.write_stderr("%s ok" % db_info["source"])
            except Exception as e:
                # 触发告警
                warning_title = "%s redis monitor " % db_info["source"]
                warning_msg = "%s %s get/set error   %s \n %s %s" % (
                    db_ip, db_info["port"], e, self.host_ip, self.host_name)
                self.send_mail(self.mail_receivers, warning_title, warning_msg)
                self.send_wxwechat(team_name, warning_title, warning_msg)

        # 创建定时器
        timer = threading.Timer(300, self.monitor_redis, [team_name, db_list])
        timer.start()

    def monitor_mongo(self, team_name, db_list):
        for db_ip, db_info in db_list.iteritems():
            try:
                # 构造数据库连接
                mongodb_url = "mongodb://%s:%s@%s:%s/admin" % (
                    db_info["user"], db_info["password"], db_ip, int(db_info["port"]))
                cli = pymongo.MongoClient(mongodb_url, serverSelectionTimeoutMS=3)
                try:
                    db = cli.yunwei_monitor
                    conn = db.test

                    # 定义测试数据内容
                    k = "dev_ops_test_monitor_check"
                    v = "test"

                    # 每次先find下并判断是否存在测试数据
                    result = conn.find_one({k: v})

                    if result is None:
                        # 如果测试数据不存在就执行insert操作
                        conn.insert_one({k: v})

                        # 再次find并判断返回结果
                        result = conn.find_one({k: v})
                        assert result[k] == v, "code:40:find_result=%s" % result[k]

                    else:
                        # 如果find返回结果不是None,判断下find返回结果是否正确
                        assert result[k] == v, "code:44:find_result=%s" % result[k]

                        # 如果find返回结果正确,执行update并判断update返回结果
                        result = conn.replace_one({k: v}, {k: v})

                        # result.raw_result["updatedExisting"] == True 代表更新操作成功
                        assert result.raw_result["updatedExisting"], "code:49:update_result=%s" % result

                    self.write_stderr("%s ok" % db_info["source"])
                except Exception as e:
                    # 触发告警
                    warning_title = "%s mongo monitor " % db_info["source"]
                    warning_msg = "%s %s find/update error   %s \n %s %s" % (
                        db_ip, db_info["port"], e, self.host_ip, self.host_name)
                    self.send_mail(self.mail_receivers, warning_title, warning_msg)
                    self.send_wxwechat(team_name, warning_title, warning_msg)
                finally:
                    cli.close()
            except Exception as e:
                # 触发告警
                warning_title = "%s mongo monitor " % db_info["source"]
                warning_msg = "%s %s connect error   %s \n %s %s" % (
                    db_ip, db_info["port"], e, self.host_ip, self.host_name)
                self.send_mail(self.mail_receivers, warning_title, warning_msg)
                self.send_wxwechat(team_name, warning_title, warning_msg)

        # 创建定时器
        timer = threading.Timer(300, self.monitor_mongo, [team_name, db_list])
        timer.start()
