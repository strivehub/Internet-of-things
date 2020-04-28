# eyevator 客户端程序 2020-04-11
# encoding:utf-8
import socket
import threading
import time
import base64
import os
import json
import urllib.request as ur
import random
import sys
import oss2
from itertools import islice
import configparser as cfg


"""
待完成事项
1、接受数据的方式（需要和前端发送方式匹配）
2、图像压缩（在存储时压缩）
"""


"""
已完成事项
1、json打包数据
2、选择图像，发送完成并删除
3、断线重新连接
4、出现异常，忽略并重新连接
"""

def recv_data(sever,dest_ip):  #接收来自服务器的消息
    while True:
        re_data = sever.recv(2048).decode("utf-8")
        if re_data:
            print("接收到来自%s的消息:" % dest_ip, re_data)
            #print("type:",type(re_data))
            try:
                p_data = json.loads(re_data)
                return_recv_value(p_data)
            except BaseException as e:
                print("recv_error:",e)
        else:
            print("Error:sever is not online.")
            break

def read_config_file(config_path):  #读取配置文件
    config = cfg.ConfigParser()
    config.read(config_path)
    waiting_time = config['DEFAULT']['waiting_time']
    confidence = config['DEFAULT']['confidence']
    confirm_time = config['DEFAULT']['confirm_time']
    cycle_time = config['DEFAULT']['cycle_time']
    trigger_one = config['DEFAULT']['trigger_one']
    trigger_two = config['DEFAULT']['trigger_two']
    local_id = config['DEVICEINFO']['device_id']
    device_model = config['DEVICEINFO']['device_model']
    hardware_platform = config['DEVICEINFO']['hardware_platform']
    system_version = config['DEVICEINFO']['system_version']
    wifi_message = config['DEVICEINFO']['wifi_message']
    img_save_path_first = config['DEFAULT']['img_save_path_first']
    warimg_img = config['DEFAULT']['warimg_img']
    place_holder = config['DEFAULT']['place_holder']
    projectname = config['DEVICEINFO']['projectname']
    floor = config['DEVICEINFO']['floor']
    unit = config['DEVICEINFO']['unit']
    name = projectname+"/"+floor+"-"+unit
    return waiting_time,confidence,confirm_time,cycle_time,trigger_one,trigger_two,local_id,device_model,hardware_platform,system_version,wifi_message,img_save_path_first,warimg_img,place_holder,name

def change_file(path,write =True,dict_con=None,name=None,read_local=None,read_name=None):
    cg = cfg.ConfigParser()
    cg.read(path)
    if write:
        try:
            for key, value in dict_con.items():
                cg.set(name,key,str(value))
                with open(path,"r+") as f:
                    cg.write(f)
            print("write operate end.")
        except:
            print("cfg write error")
    else:
        try:
            content = cg[read_local][read_name]
            return content
        except:
            print("no such name!!")

def get_time(hour=False):  #获得当前时间
    local_time = time.localtime()
    time.strftime("%Y-%m-%d",local_time)
    if hour:
        return time.strftime("%H-%M-%S",local_time)
    else:
        return time.strftime("%Y-%m-%d",local_time)


def download_file(url,local):
    def callbackfunc(blocknum, blocksize, totalsize):
        '''''回调函数
        '''
        percent = 100.0 * blocknum * blocksize / totalsize
        if percent > 100:
            percent = 100
        print("%.2f%%" % percent)
    ur.urlretrieve(url, local, callbackfunc)

def up_down_file_oss(yourObjectName, yourLocalFile,up=True):  #用来上传数据或则下载数据，具体是上传还是下载，是根据服务器下发的指令来执行
    # 阿里云主账号AccessKey拥有所有API的访问权限，风险很高。强烈建议您创建并使用RAM账号进行API访问或日常运维，请登录 https://ram.console.aliyun.com 创建RAM账号。
    auth = oss2.Auth('<yourAccessKeyId>', '<yourAccessKeySecret>')
    # 通过指定Endpoint和存储空间名称，您可以在指定的地域创建新的存储空间。Endpoint以杭州为例，其它Region请按实际情况填写。
    bucket = oss2.Bucket(auth, 'http://oss-cn-hangzhou.aliyuncs.com', '<yourBucketName>')    
    # <yourObjectName>上传文件到OSS时需要指定包含文件后缀在内的完整路径，例如abc/efg/123.jpg。
    # <yourLocalFile>由本地文件路径加文件名包括后缀组成，例如/users/local/myfile.txt。
    def percentage(consumed_bytes, total_bytes):
            if total_bytes:
                rate = int(100 * (float(consumed_bytes) / float(total_bytes)))
                print('\r{0}% '.format(rate), end='')
    if up:  # 上传文件
        bucket.put_object_from_file(yourObjectName, yourLocalFile,progress_callback=percentage)
        print("uploading img success.")  
        while True:
            time.sleep(1)
            if bucket.object_exists(yourObjectName):
                time.sleep(1)
                os.remove(yourLocalFile)
                break
            
        
    else:  # 下载文件
        def percentage(consumed_bytes, total_bytes):
            if total_bytes:
                rate = int(100 * (float(consumed_bytes) / float(total_bytes)))
                print('\r{0}% '.format(rate), end='')
                sys.stdout.flush()
        print("yourObjectName:",yourObjectName)
        #oss_file_size = int(bucket.get_object_meta(yourObjectName).headers["Content-Length"])
        #print("oss_file_size:",oss_file_size)
        bucket.get_object_to_file(yourObjectName, yourLocalFile,progress_callback=percentage)
        #while True:
        #    print("waitting download.")
        #    time.sleep(2)
        #    local_size = os.path.getsize(yourLocalFile)
        #    if local_size>=oss_file_size-10:
        #        break
        print("downloading img success.")

def create_space(name=None,delete=False):  #创建云端的桶，用来存储数据
    # 阿里云主账号AccessKey拥有所有API的访问权限，风险很高。强烈建议您创建并使用RAM账号进行API访问或日常运维，请登录 https://ram.console.aliyun.com 创建RAM账号。
    auth = oss2.Auth('<yourAccessKeyId>', '<yourAccessKeySecret>')
    # 通过指定Endpoint和存储空间名称，您可以在指定的地域创建新的存储空间。Endpoint以杭州为例，其它Region请按实际情况填写。
    bucket = oss2.Bucket(auth, 'http://oss-cn-hangzhou.aliyuncs.com', '<yourBucketName>')    
    service = oss2.Service(auth, 'http://oss-cn-beijing.aliyuncs.com')       #查看存储空间
    print([b.name for b in oss2.BucketIterator(service)])  # 列出所有存在的桶

    def read_object(delete_obj=False):  # oss2.ObjectIteratorr用于遍历文件。遍历桶内每个文件
        for b in islice(oss2.ObjectIterator(bucket), 1, None):
            print(b.key)
            if delete_obj:
                bucket.delete_object(b.key)
                print("delete %s success" % b.key)
    def does_bucket_exist(bucket):#判断存储空间是否存在
        try:
            bucket.get_bucket_info()
        except oss2.exceptions.NoSuchBucket:
            return False
        except:
            raise
        return True
    if delete:
        try:
            # 删除存储空间。
            bucket.delete_bucket()
        except oss2.exceptions.BucketNotEmpty:
            print('bucket is not empty.')
        except oss2.exceptions.NoSuchBucket:
            print('bucket does not exist')
    else:
        if does_bucket_exist(bucket):  # 如果存在此桶，则不创建存储空间
            print("sorry bucket %s has exist." % name)
        else:  # 不存在则创建
            bucket.create_bucket()
            print("creat bucket %s success." % name)

def return_recv_value(dict):  #解析服务器下发的数据
    global is_info,receive_data
    command_type = dict["command_type"]
    print('receive type:',command_type)
    device_id = dict["device_id"]
    # if command_type == "operate":
    #     run_status = dict["run_status"]
    #     discharged_time = dict["discharged_time"]
    # elif command_type == "paramSetting":
    #     buzzer_pin = dict["deviceBasicInfo"]["buzzer_pin"]
    #     clear_num = dict["deviceBasicInfo"].get("clear_num")
    #     confidence = dict["deviceBasicInfo"]["confidence"]
    #     confirm_time = dict["deviceBasicInfo"]["confirm_time"]
    #     cycle_time = dict["deviceBasicInfo"]["cycle_time"]
    #     device_model = dict["deviceBasicInfo"]["device_model"]
    #     hardware_platform = dict["deviceBasicInfo"]["hardware_platform"]
    #     img_save_any = dict["deviceBasicInfo"].get("img_save_any")
    #     img_save_path_first = dict["deviceBasicInfo"]["img_save_path_first"]
    #     img_save_path_second = dict["deviceBasicInfo"]["img_save_path_second"]
    #     impulse_pin = dict["deviceBasicInfo"]["impulse_pin"]
    #     num = dict["deviceBasicInfo"].get("num")
    #     output_pin = dict["deviceBasicInfo"]["output_pin"]
    #     speaker_output_pin = dict["deviceBasicInfo"]["speaker_output_pin"]
    #     system_version = dict["deviceBasicInfo"]["system_version"]
    #     trigger_one = dict["deviceBasicInfo"]["trigger_one"]
    #     trigger_two = dict["deviceBasicInfo"]["trigger_two"]
    #     waiting_time = dict["deviceBasicInfo"]["waiting_time"]
    #     wifi_message = dict["deviceBasicInfo"]["wifi_message"]
    # elif command_type == "updateModel":
    #     file_input_stream = dict["file_input_stream"]
    if device_id == local_id:
        #print("ID true.")
        if command_type == "operate":  # 操作指令
            #run_status = dict["run_status"]  # 具体命令
            #discharged_time = dict.get("discharged_time")  # 放行时间
            change_file(path=path,dict_con=dict,name="SEVERICE")
        elif command_type == "paramSetting":  # 参数设置  
            paramSetting_dict = dict["deviceBasicInfo"]
            change_file(path=path,dict_con=paramSetting_dict,name="DEFAULT")
            dic_con = {"paramSetting":"True"}
            change_file(path=path,dict_con=dic_con,name="SEVERICE")
        # elif command_type == "updateModel":  # 更新模型到网站自己get文件
        #     version = dict["version"]
        #     print("ready download model version is %s." % str(version))
        #     # url = "39.100.130.0:8083/file/upload/model"
        #     # save_path = "./wigths.h5"
        #     url = str(dict["url"].decode('ascii'))
        #     save_path = "./"+dict["file_name"]
        #     try:
        #         download_file(url, save_path)
        #     except:
        #         print("download model error!!")
        elif command_type == "updateModel":  # 更新模型到阿里云下载问题，还没有写
            version = dict["version"]
            print("ready download model version is %s." % str(version))
            name = dict["url"][13:]
            save_path = "./"+name.split("/")[-1]
            print("name:",name,"save_path:",save_path)
            #try:
            receive_data = True
            up_down_file_oss(name,save_path,up=False)
            dic_con = {"model_update":"True"}
            change_file(path=path,dict_con=dic_con,name="SEVERICE")
            receive_data = False
            #except:
             #   print("download model error!!")
        elif command_type == "heartbeat":
            is_info = 0
            print("is_info",is_info)
            #print("receive heartbeat.")
        elif command_type == "deviceLocaltion":  
            deviceCommunityInfo = dict["deviceCommunityInfo"]
            service_reset_info = {"run_status":"1","discharged_time":"null","model_update":"False","paramsetting":"False",}
            change_file(path=path,dict_con=deviceCommunityInfo,name="DEVICEINFO")
            change_file(path=path,dict_con=service_reset_info,name="SEVERICE")
            #create_space(name=deviceCommunityInfo["projectname"])
        else:
            print("recieve input_error")

    else:
        print("ID false.can't command this device.")


def send_content(flag, string=None, path=None, run_status=None):  #将发送到服务器的数据统一打包为json格式
    #random_num = random.randint(1000,9999)
    #random_num = 1111
    print("send type:",flag)
    if flag == "updateStatus":
        content = json.dumps({
                                "device_id": local_id,
                                "command_type": "updateStatus",
                                "run_status": run_status,
                                "file_input_stream": path})
        # end_content = json.dumps({
        #     "head_data": random_num,
        #     "content_length": sys.getsizeof(content),
        #     "content": content
        # })
        # print("content_length:",sys.getsizeof(content))
        # return end_content
        return content
    elif flag == "connection":
        content = json.dumps({
                                "device_id": local_id,
                                "command_type": "connection",
                                "deviceBasicInfo": {
                                    #"buzzer_pin": "33",  # string
                                    #"clear_num": "none",  # string
                                    "confidence": confidence,  # string
                                    "confirm_time": confirm_time,  # string
                                    "cycle_time": cycle_time,  # string
                                    "device_model": device_model,  # string
                                    "device_id": local_id,  # string
                                    "hardware_platform": hardware_platform,  # string
                                    #"img_save_any": "none",  # string
                                    "img_save_path_first": "/eyevator/img_save_first/",  # string
                                    "img_save_path_second": "/eyevator/img_save_second/",  # string
                                    #"impulse_pin": "31",  # string
                                    #"num": "none",  # string
                                    #"output_pin": "32",  # string
                                    #"speaker_output_pin": "27",  # string
                                    "system_version": system_version,  # string
                                    "trigger_one": trigger_one,  # string
                                    "trigger_two": trigger_two,  # string
                                    "waiting_time": waiting_time, # string
                                    "wifi_message": wifi_message}  # string
                                })
        # end_content = json.dumps({
        #     "head_data": random_num,
        #     "content_length": sys.getsizeof(content),
        #     "content": content
        # })
        # return end_content
        return content
    elif flag == "heartbeat":
        content = json.dumps({
            "device_id": local_id,
            "command_type": "heartbeat",
        }
        )
        #print(type(json.loads(content)))
        # end_content = json.dumps({
        #     "head_data": random_num,
        #     "content_length": sys.getsizeof(content),
        #     "content": content
        # })
        # return end_content
        return content
    elif flag == "placeholderImage":
        content = json.dumps(
            {"device_id": local_id,
             "command_type": "placeholderImage",
             "file_input_stream": path
             }
        )
        # end_content = json.dumps({
        #     "head_data": random_num,
        #     "content_length": sys.getsizeof(content),
        #     "content": content
        # })
        # return end_content
        return content
    elif flag == "up_img_oss":
        content = json.dumps(
            {"device_id": local_id,
             "command_type": "placeholderImage",
             "file_input_stream": path
             }
        )
        # end_content = json.dumps({
        #     "head_data": random_num,
        #     "content_length": sys.getsizeof(content),
        #     "content": content
        # })
        # return end_content
        return content
    else:
        print("input errot!!")
    

def waring_info(path):  #用来判断是否有报警信息出现，若有，则将情况发送到服务器
    config = cfg.ConfigParser()
    config.read(path)
    run_status = config['LOCAL']['run_status']
    img_name = config['LOCAL']['img_name']
    is_down = False
    is_status = False
    if run_status!="6":
        dict_content = {"run_status":"6"}
        change_file(path=path,dict_con=dict_content,name="LOCAL")
        is_status = True
    elif config['LOCAL']['down'] == "False":
        dict_content = {"down":"True"}
        change_file(path=path,dict_con=dict_content,name="LOCAL")
        is_down = True
    return img_name,is_status,is_down

def send_msg(sever,start_time):
    global is_info,receive_data
    num = 0
    upimg_time = time.time()
    while int(len(threading.enumerate())) > 1:
        if receive_data:  #判断服务器是否在下发大型数据文件，如果是，等待接收完，再发送其他数据
            print("waiting download!!")
            time.sleep(5)
            continue
        # print("threading num:", len(threading.enumerate()))
        #file_path = os.path.join(os.getcwd(),"test_file")
        try:
            file_name = slect_file(place_holder)
            if file_name or is_info == 0:
                if is_info == 0 and num == 0:
                    content = send_content(flag="connection")  #向服务器发送本地硬件信息
                    sever.send(content.encode("utf-8"))
                    #print("content:",content)
                    #print("send basic info success.")
                    is_info += 1
                    num += 1
                    file_name = None
                elif file_name and is_info == 0:   ##update placeholder
                    #上传图像到阿里云
                    up_path = os.path.join("state-img", name,"placeholderImage",get_time(),file_name)
                    print("up_path:",up_path)
                    up_down_file_oss(up_path,os.path.join(place_holder, file_name))
                    #print("oss_path:",os.path.join("state-img", file_name))
                    sever.send(send_content(flag="placeholderImage",path=up_path).encode("utf-8"))
                    #直接socket传送图片
                    # send_data = file2json(os.path.join(file_path, file_name))
                    # sever.sendall(send_content(flag="updateStatus", string=send_data).encode("utf-8"))
                    print("sending %s success" % file_name)
                    is_info += 1
                #print("is_info:",is_info)
                time.sleep(2)
            is_waring,is_status,is_down = waring_info(path)
            #print("is_waring:",is_waring)
            if is_status:
                up_path = os.path.join("state-img", name,"waringImage",get_time(),is_waring)
                print("up_path:",up_path)
                print("local_path:",os.path.join(waring_img, is_waring))
                up_down_file_oss(up_path,os.path.join(waring_img, is_waring))
                sever.send(send_content(flag="updateStatus",path=up_path,run_status="4").encode("utf-8"))
                #直接socket传送图片
                # send_data = file2json(os.path.join(file_path, file_name))
                # sever.sendall(send_content(flag="updateStatus", string=send_data).encode("utf-8"))
            elif is_down:
                up_path = os.path.join("state-img", name,"waringImage",get_time(),is_waring)
                sever.send(send_content(flag="updateStatus",path=up_path,run_status="6").encode("utf-8"))

            else:
                # send_data = send_content(flag="heartbeat")
                # sever.send(send_data.encode("utf-8"))
                print("waring:img folder is empty!!")
                time.sleep(2)
        except BaseException as e:
            print("BaseException:",e)
            print("file encode error!!")
            #send_data = "hello"
            #sever.send(send_data.encode("utf-8"))
            time.sleep(2)
        finally:
            end_time = time.time()
            if end_time-start_time > 10:
                send_data = send_content(flag="heartbeat")
                sever.send(send_data.encode("utf-8"))
                #print("send heartbeat")
                #print("send_data:",send_data)
                start_time = end_time
            if end_time-upimg_time > upimg_time:
                #send_data = file2json(os.path.join(file_path, file_name))  #解决当时待定
                sever.sendall(send_content(flag="placeholderImage", path=os.path.join("state-img", file_name)).encode("utf-8"))
                print("updata img,sending %s success" % file_name)
                upimg_time = end_time


        #if file_name:
        #    os.remove(os.path.join(file_path, file_name))


def send_hb(sever):
    while True:
        send_data = send_content(flag="heartbeat")
        sever.send(send_data.encode("utf-8"))
        print("ready send heartbeat.")
        time.sleep(10)


def file2json(file_path):  #将图像打包成json数据
    with open(file_path, 'rb') as f:
        image_byte = base64.b64encode(f.read())
        #print(type(image_byte))
    image_str = image_byte.decode('ascii')  # byte类型转换为str
    print("image_str_type:",type(image_str))
    return image_str


def slect_file(file_path): #检查是否有报警数据，并删除错误数据
    file_list = os.listdir(file_path)
    file_name = None
    for file_name in file_list:
        value = file_name.endswith(".jpg")
        file_size = os.stat(os.path.join(file_path, file_name)).st_size
        if value and file_size > 10000:
            break
        elif value and file_size < 100:
            os.remove(os.path.join(file_path, file_name))
        else:
            file_name = None
    return file_name


def main():
    while True:
        while True:  #简历socket通信
            try:
                # 创建TCP套接字
                tcp_socket_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

                # 连接服务器
                dest_ip = "39.100.130.0"  #服务器IP
                dest_port = 8092  #服务器接收的端口号
                # dest_ip = "192.168.0.101"  #本地调试
                # dest_port = 8080  #本地调试
                tcp_socket_client.connect((dest_ip, dest_port))
                print("成功连接到%s" % dest_ip)
                tcp_socket_client.send(send_content(flag="heartbeat").encode("utf-8"))
                #print("send heartbeat")
                #print("send_data:",send_content(flag="heartbeat"))
                break
            except:
                print("sever is reject connect or network is disconnect!!,try again.")
                time.sleep(2)

        # 接受数据  这里为了实现同时收发数据的功能，使用了多线程t1代表接收来自服务器的数据，send_msg代表发送到服务器的数据
        t1 = threading.Thread(target=recv_data, args=(tcp_socket_client, dest_ip))
        t1.start()
        # t2 = threading.Thread(target=send_hb,args=(tcp_socket_client,))
        # t2.start()

        # 发送数据
        start_time = time.time()
        send_msg(tcp_socket_client, start_time)
        print("threading num:", len(threading.enumerate()))
        # 关闭
        # tcp_socket_client.close()


if __name__ == "__main__":   #这是一个socket实现的客户端，主要用来将本地识别的一些数据发送至服务器，同时将识别的目标图像上传至阿里云端，进行存储
    path = os.path.join(os.getcwd(),"test.txt")
    #operate_file_path = "/home/pi/tools/darknet2ncnn/model_data/command.txt"
    waiting_time,confidence,confirm_time,cycle_time,trigger_one,trigger_two,local_id,device_model,hardware_platform,system_version,wifi_message,img_save_path_first, waring_img, place_holder, name = read_config_file(path)
    upimg_time = 3600*12
    is_info = -1
    receive_data = False
    #time.sleep(20)
    while True:
        try:
            main()
        except BaseException as e:
            print("error:",e)
            print("connect error!!")
            time.sleep(2)
