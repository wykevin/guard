#!/usr/bin/python
# coding:utf8
# Created by wangyikai at 19/04/12

from module.printf import Printf
import time
import requests
import random
import hashlib
import email
import smtplib
import socket
import os
import json


class NotifyClass(Printf):

    def __init__(self):
        Printf.__init__(self)

        # 获取 主机名 IP
        self.host_name = socket.gethostname()
        self.host_ip = socket.gethostbyname(socket.gethostname())

        # 定义notify方法里所需变量信息
        with open("../config/config.json") as jsonfile:
            self.config = json.load(jsonfile)

        self.call_appid = self.config["call"]["appid"]
        self.call_appkey = self.config["call"]["appkey"]
        self.call_tpl_id = self.config["call"]["tpl_id"]
        self.call_callback_url = self.config["call"]["callback_url"]
        self.mail_sender = self.config["mail"]["sender"]
        self.mail_password = self.config["mail"]["password"]
        self.wxwechat_url = self.config["wxwechat"]["url"]

    def __call(self, mobile, team_name, program):
        random_number = random.randint(1, 99999)
        url = "https://cloud.tim.qq.com/v5/tlsvoicesvr/sendtvoice?sdkappid=%s&random=%s" % (
            self.call_appid, random_number)

        def get_sig():
            sig = "appkey=%s&random=%s&time=%s&mobile=%s" % (self.call_appkey, random_number, int(time.time()), mobile)
            sig = hashlib.sha256(sig).hexdigest()
            return sig

        data = {
            "tpl_id": self.call_tpl_id,  # 语音模板id
            # 您好，{1}项目{2}程序有告警，请及时处理，谢谢。
            "params": [team_name, program],
            "playtimes": 2,
            "sig": get_sig(),
            "tel": {
                "mobile": mobile,
                "nationcode": "86"
            },
            "time": int(time.time()),
            "ext": "%s,%s" % (team_name, program)
        }

        result = requests.post(url, data=json.dumps(data))  # 请求腾讯云触发电话通知
        result = result.json()
        self.write_stderr(str(result))
        # 定义当前告警内容,并调用回调接口保存当前告警内容
        call_info = {"callid": result["callid"], "ext": result["ext"], "event": "custom"}
        requests.post(self.call_callback_url, data=json.dumps(call_info))

    def call(self, mobile_list, team_name, program):
        current_time = int(time.strftime("%H"))
        # 早10点 - 晚8点 不触发电话告警
        # if current_time > 10 and current_time < 20:
        #     return
        for i in mobile_list:
            self.__call(i, team_name, program)

    def send_mail(self, mail_receivers, title, msg, file_path=None):
        server = smtplib.SMTP("smtp.exmail.qq.com")

        server.login(self.mail_sender, self.mail_password)
        main_msg = email.MIMEMultipart.MIMEMultipart()
        text_msg = email.MIMEText.MIMEText(msg)
        main_msg.attach(text_msg)
        if file_path != None:
            contype = 'application/octet-stream'
            maintype, subtype = contype.split('/', 1)
            data = open(file_path, 'rb')
            file_msg = email.MIMEBase.MIMEBase(maintype, subtype)
            file_msg.set_payload(data.read())
            data.close()
            email.Encoders.encode_base64(file_msg)
            basename = os.path.basename(file_path)
            file_msg.add_header('Content-Disposition',
                                'attachment', filename=basename)
            main_msg.attach(file_msg)
        main_msg['From'] = self.mail_sender
        main_msg['To'] = mail_receivers
        main_msg['Subject'] = title
        main_msg['Date'] = email.Utils.formatdate()
        fullText = main_msg.as_string()
        try:
            server.sendmail(self.mail_sender, mail_receivers, fullText)
        finally:
            server.quit()

    def send_wxwechat(self, team_name, title, msg):
        title = team_name + "-" + title
        jsondata = {
            "afrom": title,
            "msg": msg
        }
        jsondata = json.dumps(jsondata, ensure_ascii=False)
        requests.post(self.wxwechat_url, data=jsondata)
