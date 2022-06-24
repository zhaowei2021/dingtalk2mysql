# -*- coding: utf-8 -*-
# This file is auto-generated, don't edit it. Thanks.
import requests
import ast
import pymysql
import time
import datetime
import json

#获取当天零点时间戳

t_time = str(int(time.mktime(datetime.date.today().timetuple()))*1000)

#获取acdess_token

gettokenurl = "https://api.dingtalk.com/v1.0/oauth2/accessToken"

appinfo = "{\n\t\"appKey\":\"dingqnxjxrsnz32y3rdp\",\n\t\"appSecret\":\"OZLEv0bnfDZEUJ1s1N7-dYhRv0u367nBRi_MyI7rb8j9hit-upZTXfFgFou0IN5f\"\n}"

headers = {

    'content-type': "application/json",
    'cache-control': "no-cache",
    'postman-token': "8524eeeb-bc48-6fe3-167e-35c8da2fdb3f"

    }

token = requests.request("POST", gettokenurl, data=appinfo, headers=headers)

token_dict = ast.literal_eval(token.text)

token = token_dict["accessToken"]

querystring = {"access_token":token}

#通过process_code获取审批实例列表

proc_url = "https://oapi.dingtalk.com/topapi/processinstance/listids"

proc_code = "{\n\t\"process_code\":\"PROC-5C54F0A5-93DD-4502-B753-1C3272C90BB4\",\n\t\"start_time\":" + t_time + "\n}"

proc_response = requests.request("POST", proc_url, data=proc_code, headers=headers, params=querystring)

data = ast.literal_eval(proc_response.text)

result = data["result"]

proc_list = result['list']

for i in proc_list:

    #通过审批实例ID获取审批详情

    url = "https://oapi.dingtalk.com/topapi/processinstance/get"

    payload = "{\n\t\"process_instance_id\":\""+ i +"\"\n}"


    response = requests.request("POST", url, data=payload, headers=headers, params=querystring)

    #获取实例详情

    process_instance = ast.literal_eval(response.text)["process_instance"]

    #从实例表单获取操作记录

    opration = process_instance["operation_records"]

    #获取审批人userid

    execute_userid= opration[1]["userid"]

    #获取发起人userid

    start_userid = opration[0]["userid"]

    #通过user_id判断用户是否在职

    get_user_url = "https://oapi.dingtalk.com/topapi/v2/user/get"

    user_payload = "{\n\t\"userid\":\""+start_userid+"\"\n}"

    user_response = requests.request("POST", get_user_url, data=user_payload, headers=headers, params=querystring)

    user_status = int(user_response.text.split(",")[0].split(":")[1])

    #获取审批结果

    instance_result = process_instance["result"]

    #员工在职且审批通过执行下一步

    if user_status == 0 and instance_result == "agree":

        #获取表单内容

        instance_summry_list = process_instance["form_component_values"]

        #获取用户姓名

        user_name = instance_summry_list[0]["value"]

        #获取Mac地址

        mac_info = instance_summry_list[1]
        
        mac_info_value = mac_info["value"][2:-2].split(",")

        ll = [s for s in mac_info_value if '"value"' in s]

        for m in ll:

            macaddress = m[9:-1].replace(":","-").replace(" ","")

            upper_macaddress = macaddress.upper()


            #连接数据库

            db = pymysql.connect(

                host = '10.0.3.5',
                port = 3306,
                user = 'root',
                passwd = '1234',
                db = 'radius',
                charset = 'utf8')

            cursor = db.cursor()

            sql_chekck_mac = "select username from radcheck"

            cursor.execute(sql_chekck_mac)

            mac_list = []

            for line in cursor.fetchall():

                a = ''.join(line)

                mac_list.append(a)

            if upper_macaddress not in mac_list and instance_result=="agree":

                attribute = "Auth-Type"

                op = ":="

                value = "Accept"

                sql_insert_mac = "insert into radcheck(username, attribute, op, value, dingtalkuid) values('%s','%s','%s','%s','%s')" % (upper_macaddress, attribute, op, value, start_userid)
                
                cursor.execute(sql_insert_mac)
                
                sql_insert_user = "insert into userinfo(username, firstname, dingtalkuid) values('%s', '%s', '%s')" % (upper_macaddress, user_name, start_userid)
                
                cursor.execute(sql_insert_user)
                
                db.commit()

                sql_check_result = "select username from radcheck"

                cursor.execute(sql_check_result)

                result_list = []

                for mac in cursor.fetchall():

                    u = ''.join(mac)

                    result_list.append(u)

                    if upper_macaddress in result_list:

                        notice_url = "https://oapi.dingtalk.com/topapi/message/corpconversation/asyncsend_v2"

                        text = "您好，" + user_name + "，您Mac地址为：" + upper_macaddress + "的设备已经成功开通入网权限！"

                        notice_payload = {

                            "agent_id":1680888979,

                            "msg":{
                            
                                "msgtype":"text",

                            "oa":{

                                "body":{

                                    "content":text

                                    }

                                },

                            "text":{

                                "content":text

                                    }

                                },

                            "userid_list":start_userid

                            }

                        payload_notice = json.dumps(notice_payload)

                        notice_response = requests.request("POST", notice_url, data=payload_notice, headers=headers, params=querystring)

                        text1 = user_name + "的Mac地址为：" + upper_macaddress + "的设备已经成功开通入网权限！"

                        notice_payload1 = {

                            "agent_id":1680888979,

                            "msg":{
                            
                                "msgtype":"text",

                            "oa":{

                                "body":{

                                    "content":text1

                                    }

                                },

                            "text":{

                                "content":text1

                                    }

                                },

                            "userid_list":execute_userid

                            }

                        payload_notice1 = json.dumps(notice_payload1)

                        notice_response1 = requests.request("POST", notice_url, data=payload_notice1, headers=headers, params=querystring)

           
                db.close()
