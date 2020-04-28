# eyevator 上传数据 2020-04-11
# encoding:utf-8
import time
import os
import sys
import oss2
import configparser as cfg


def read_config_file(config_path):  #读取配置文件的一些内容
    config = cfg.ConfigParser()
    config.read(config_path)
    img_save_path_first = config['DEFAULT']['img_save_path_first']
    projectname = config['DEVICEINFO']['projectname']
    floor = config['DEVICEINFO']['floor']
    unit = config['DEVICEINFO']['unit']
    name = projectname+"/"+floor+"-"+unit
    
    return img_save_path_first,name

def get_time():
    local_time = time.localtime()
    formate_time = time.strftime("%Y-%m-%d",local_time)
    return formate_time

def up_down_file_oss(bucket,yourObjectName, yourLocalFile,up=True):  #将数据发送至云端，并显示上传进度
    def percentage(consumed_bytes, total_bytes):
        if total_bytes:
            rate = int(100 * (float(consumed_bytes) / float(total_bytes)))
            print('\r{0}% '.format(rate), end='')

            sys.stdout.flush()
    if up:  # 上传文件
        
        bucket.put_object_from_file(yourObjectName, yourLocalFile,progress_callback=percentage)
        if bucket.object_exists(yourObjectName):
            time.sleep(1)
            os.remove(yourLocalFile)
            print("uploading img %s success." % yourObjectName)
        else:
            print("uploading img error!!")
    else:  # 下载文件
        
        bucket.get_object_to_file(yourObjectName, yourLocalFile,progress_callback=percentage)
        print("downloading img success.")

def create_space(bucket,service,name=None,delete=False):  #创建一个桶，用来存放数据，如果桶已经存在，则不创建
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



def slect_file(file_path):  #用来检查文件是否有图像，并删除储存不完全的数据
    file_list = os.listdir(file_path)
    file_name = None
    file_size = None
    for file_name in file_list:
        file_size = os.stat(os.path.join(file_path, file_name)).st_size
        if file_size > 10000:
            break
        elif value and file_size < 100:
            os.remove(os.path.join(file_path, file_name))
        else:
            file_name = None
    return file_name, file_size


def main():  #我这里是用的阿里云OSS进行的云端数据存储，其账号和密码在购买后便知道
    # 阿里云主账号AccessKey拥有所有API的访问权限，风险很高。强烈建议您创建并使用RAM账号进行API访问或日常运维，请登录 https://ram.console.aliyun.com 创建RAM账号。
    auth = oss2.Auth('<yourAccessKeyId>', '<yourAccessKeySecret>')
    # 通过指定Endpoint和存储空间名称，您可以在指定的地域创建新的存储空间。Endpoint以杭州为例，其它Region请按实际情况填写。
    bucket = oss2.Bucket(auth, 'http://oss-cn-hangzhou.aliyuncs.com', '<yourBucketName>')
    # <yourObjectName>上传文件到OSS时需要指定包含文件后缀在内的完整路径，例如abc/efg/123.jpg。
    # <yourLocalFile>由本地文件路径加文件名包括后缀组成，例如/users/local/myfile.txt。
    service = oss2.Service(auth, 'http://oss-cn-beijing.aliyuncs.com')  #查看存储空间
    create_space(bucket,service,name="all-waring-img")
    while True:
        try:
            name,_ = slect_file(img_save_path_first)
            if name:
                time.sleep(10)
                up_path = os.path.join("all-waring-img",projectname,get_time(),name)
                up_down_file_oss(bucket,up_path,os.path.join(img_save_path_first,name))
            else:
                print("folder is empty!!")
                time.sleep(2)
        except BaseException as e:
            print("error:",e)
            time.sleep(2)


if __name__ == "__main__":
    path = "/home/pi/tools/darknet2ncnn/model_data/test.txt"  #这是我配置文件地址
    img_save_path_first,projectname = read_config_file(path)
    time.sleep(10)  ##为了防止设备联网不及时，先等待一段时间
    while True:  #如果联网不成功，继续尝试，直至链接成功
        try:
            main()
        except BaseException as e:
            print("Network error:",e)
            time.sleep(2)
