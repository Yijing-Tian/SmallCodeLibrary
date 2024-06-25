import pymysql
import time
import traceback
import os
import subprocess
import requests
import json
import threading
from tqdm import tqdm
from datetime import datetime
import logging
from logging.handlers import TimedRotatingFileHandler

# # 设置logging的配置
# logging.basicConfig(filename='log.txt', level=logging.DEBUG)
# 配置日志记录
log_formatter = logging.Formatter('%(asctime)s [%(levelname)s]: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# 设置TimedRotatingFileHandler，每两天轮转一次
file_handler = TimedRotatingFileHandler('download.log', when='midnight', interval=1, backupCount=0)
file_handler.setFormatter(log_formatter)
logger.addHandler(file_handler)


class oss_down_source:
    def __init__(self):
        self.sql_lock = threading.Lock()
        self.db = pymysql.connect(host='rm-8vbq6ojr4rmscc34qqo.mysql.zhangbei.rds.aliyuncs.com', port=3306, # 链接地址 # 端口号
                                user='ydbusiness',passwd='EVD!wuj@uA3q', # 用户名 # 密码
                                db='ydbusiness',autocommit=True) # 数据库名
        self.Mixed_out_lin = "G:/Mixed_shear_source/"

        self.oss_url = 'http://yundao888.oss-cn-beijing.aliyuncs.com/'


    def select_db (self, sql, chiose='none'):
        for i in range(10):
            try:
                with self.sql_lock :
                    with self.db.cursor() as cur:
                        if chiose != 'cha': # 执行 SQL  提交
                            self.db.ping(reconnect=True)
                            cur.execute(sql)
                            if cur.rowcount < 0: continue
                            self.db.commit()
                            return
                        else: # 获取查询结果
                            self.db.ping(reconnect=True)
                            cur.execute(sql)
                            # data = cur.fetchall()
                            data = [dict(line) for line in [zip([column[0] for column in cur.description], row) for row in cur.fetchall()]]
                            return data
            except pymysql.Error as e: # pymysql潜在异常
                print("Error:", e)
                try:
                    self.db = pymysql.connect(host='rm-8vbq6ojr4rmscc34qqo.mysql.zhangbei.rds.aliyuncs.com', port=3306, # 链接地址 # 端口号
                                            user='ydbusiness',passwd='EVD!wuj@uA3q', # 用户名 # 密码
                                            db='ydbusiness',autocommit=True) # 数据库名
                    # self.db = pymysql.connect(host='111.231.23.132', port=3306, # 链接地址 # 端口号
                    #                         user='yundao123',passwd='yundao123', # 用户名 # 密码
                    #                         db='micrapp_test',autocommit=True) # 数据库名
                    time.sleep(1)
                except:
                    pass


    def down_oss_file (self):
        del_start = time.time()
        while True:
            try:
                if time.time() - del_start > 10:
                    self.delete_del()
                    del_start = time.time()
                
                sql = """
                SELECT
                    id, url , uploadUrl, type, srtState, reId
                FROM
                    trusteeship_enterprise_mixed_shear_re_details 
                WHERE
                    uploadState = 1 AND state = 1 AND type != 4 AND srtState = 1
                ORDER BY
                    uploadDate ASC  LIMIT 10
                """ # 排队的优先拉取
                
                all_data = self.select_db (sql,chiose='cha')
                # print(all_data,'down_oss_file')
                logging.info(all_data)
                logging.info('down_oss_file')
                for one_data in all_data:
                    oss_file_name = os.path.basename(one_data['url'])
                    local_path = self.Mixed_out_lin+oss_file_name
                    strcmd = f"ffmpeg -i {local_path} -vn -f wav {local_path[:-3] + 'wav'}"
                    subprocess.call(strcmd, shell=True)
                    self.whisper_api_sql(one_data, oss_file_name[:-3] + 'wav')

                sql = """
                SELECT
                    id, url , uploadUrl, type, srtState, reId
                FROM
                    trusteeship_enterprise_mixed_shear_re_details 
                WHERE
                    uploadState = 5 AND state = 1 
                ORDER BY
                    uploadDate ASC  LIMIT 10
                """ # 排队的优先拉取
                
                all_data = self.select_db (sql,chiose='cha')
                # print(all_data,'down_oss_file')
                logging.info(all_data)
                for one_data in all_data:
                    self.down_oss_updata (one_data)
                if all_data != []: continue

                sql = """
                SELECT
                    id, url , uploadUrl, type, srtState, reId
                FROM
                    trusteeship_enterprise_mixed_shear_re_details 
                WHERE
                    uploadState = 0 AND state = 1 
                ORDER BY
                    uploadDate ASC  LIMIT 10
                """ # 排队的优先拉取
                all_data = self.select_db (sql,chiose='cha')
                for one_data in all_data:
                    self.down_oss_updata (one_data)

                

                time.sleep(3)
            except Exception as e:
                # print(traceback.format_exc(),e)
                logging.error(traceback.format_exc())
                logging.error(e)


    def down_oss_updata (self, one_data):
        oss_file_name = os.path.basename(one_data['url'])
        local_path = self.Mixed_out_lin+oss_file_name
        logging.info(one_data['url'])
        logging.info(oss_file_name)

        if oss_file_name[-3:] == 'mp4' or oss_file_name[-3:] == 'MP4' or oss_file_name[-3:] == 'wav' or oss_file_name[-3:] == 'WAV' or oss_file_name[-3:] == 'mp3' or oss_file_name[-3:] == 'MP3':
            try:
                vid_duration = subprocess.check_output(['ffprobe', '-i', one_data['url'], '-show_entries', 'format=duration', '-v', 'quiet', '-of', 'csv=%s' % ("p=0")])
                vid_duration = float(vid_duration)
            except:
                print('素材同步失败，视频文件损坏')
                self.select_db (f"""update trusteeship_enterprise_mixed_shear_re_details set uploadState = 3 where id = {one_data['id']}""")
                os.remove(local_path)
        else:
            vid_duration = 0

        if not os.path.exists(local_path): # 判断文件在本地是否存在
            self.start_oss = time.time()
            # sql = f"""update trusteeship_enterprise_mixed_shear_re_details set uploadState = 5 where id = {one_data['id']}""" 
            # self.select_db (sql) # 同步中
            self.download_file(one_data['url'], local_path)
            sql = f"""
            SELECT MAX(usedCount) AS max_usedCount
            FROM trusteeship_enterprise_mixed_shear_re_details
            WHERE reId = {one_data['reId']} AND isDelete = 1"""
            max_usedCount = self.select_db (sql, chiose='cha')[0]['max_usedCount']
            sql = f"""update trusteeship_enterprise_mixed_shear_re_details set  uploadSuccessDate = now(), uploadState = 1, sumSecond = {vid_duration}, usedCount = {max_usedCount} where id = {one_data['id']}"""
            # print(sql,'have updata')
            self.select_db (sql) # 同步成功
            logging.info('have updata')
        else: # 如果存在就把文件删除
            if self.is_video_corrupted(local_path):
                os.remove(local_path)
                time.sleep(10)
            else:
                sql = f"""
                SELECT MAX(usedCount) AS max_usedCount
                FROM trusteeship_enterprise_mixed_shear_re_details
                WHERE reId = {one_data['reId']} AND isDelete = 1"""
                max_usedCount = self.select_db (sql, chiose='cha')[0]['max_usedCount']
                sql = f"""update trusteeship_enterprise_mixed_shear_re_details set  uploadSuccessDate = now(), uploadState = 1, sumSecond = {vid_duration}, usedCount = {max_usedCount} where id = {one_data['id']}"""
                # print(sql,'no have updata')
                self.select_db (sql) # 同步成功
                logging.info('no have updata')
        
        if one_data['srtState'] == 1:
            strcmd = f"ffmpeg -i {local_path} -vn -f wav {local_path[:-3] + 'wav'}"
            subprocess.call(strcmd, shell=True)
            self.whisper_api_sql(one_data, oss_file_name[:-3] + 'wav')

    def download_file(self, url, dest_filename):
        with requests.get(url, stream=True) as response:
            total_size = int(response.headers.get('content-length', 0))
            block_size = 1024  # 1 KB
            t = tqdm(total=total_size, unit='B', unit_scale=True)

            start = time.time()
            with open(dest_filename, 'wb') as file:
                start_time = datetime.now()
                for data in response.iter_content(block_size):
                    t.update(len(data))
                    file.write(data)
                    speed = t.n / max(1, (datetime.now() - start_time).seconds)
                    t.set_postfix(speed=f'{speed:.2f} B/s')
                    if time.time() - start > 5:
                        # 记录下载速度到日志文件
                        logging.info(f'Downloaded {t.n}/{total_size} bytes at {speed:.2f} B/s')
                        start = time.time()
            logging.info(f'Downloaded success {t.n}/{total_size} ')# bytes at {speed:.2f} B/s
            t.close()


    def only_whisper (self):
        while True:
            try:
                sql = """
                SELECT
                    id, url , uploadUrl, type
                FROM
                    trusteeship_enterprise_mixed_shear_re_details 
                WHERE
                    (uploadState = 0 OR uploadState = 5 OR uploadState = 1) AND state = 1 AND srtState = 1 AND type = 4
                ORDER BY
                    uploadDate ASC  LIMIT 10
                """ # 直拉取配音，待同步和同步中的一块拉取
                srt_data = self.select_db (sql,chiose='cha')
                for one_srt in srt_data:
                    oss_file_name = os.path.basename(one_srt['url'])
                    local_path = self.Mixed_out_lin+oss_file_name
                    # if not os.path.exists(local_path):
                    self.download_file(one_srt['url'], local_path)
                    self.whisper_api_sql(one_srt, oss_file_name)
            except Exception as e:
                logging.error(traceback.format_exc())
                logging.error(e)

    def whisper_api_sql (self, one_srt, oss_file_name):
            try:
                response = requests.request("POST", 'http://192.168.1.4:8194/whisper', headers={'Content-Type': 'application/json'}, 
                                            data=json.dumps({"filename":oss_file_name}))
                logging.info(response.text)
                result_json = json.loads(response.text)
                sql = f"""update 
                    trusteeship_enterprise_mixed_shear_re_details 
                set  
                    uploadSuccessDate = now(), uploadState = 1, srtState = 2, sumSecond = {result_json['sound_time']} , srtConfig = "{result_json['out_srt_list']}"
                where id = {one_srt['id']}"""
                self.select_db (sql) # 配音生成成功
            except Exception as e:
                logging.error(traceback.format_exc())
                logging.error(e)
                self.select_db (f"""update trusteeship_enterprise_mixed_shear_re_details set srtState = 3 where id = {one_srt['id']}""")


    def is_video_corrupted(self, file_path):
        try:
            command = ['ffmpeg', '-v', 'error', '-i', file_path, '-f', 'null', '-']
            subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return False  # 如果没有报错，视频文件正常
        except subprocess.CalledProcessError:
            return True  # 视频文件损坏


    def delete_del (self): # 删除数据库已删除数据
        sql = """
        SELECT
            id, url , uploadUrl
        FROM
            trusteeship_enterprise_mixed_shear_re_details 
        WHERE
            uploadState = 1  AND state = 1 AND (useState = 1 OR isDelete = 0) 
        ORDER BY
            id DESC LIMIT 200
        """ # 素材过一个小时删除  AND DATE_SUB(NOW(), INTERVAL 1 HOUR) > modificationTime
        del_data = self.select_db (sql, chiose='cha')
        for one_del_data in del_data:
            local_path = self.Mixed_out_lin + os.path.basename(one_del_data['url'])
            try:
                os.remove(local_path)
                logging.info(f'{local_path}需要被删除，已删除成功')
            except Exception as e:
                logging.error(traceback.format_exc())
                logging.error(e)

            sql = """
            update trusteeship_enterprise_mixed_shear_re_details set uploadState = 4 , isDelete = 0 where id = %s
            """ % (one_del_data['id'])
            self.select_db (sql)



if __name__ == "__main__":
    down_fun = oss_down_source()
    sql_th = threading.Thread(target=down_fun.only_whisper)
    sql_th.start()
    down_fun.down_oss_file()








# # 输出log信息
# logging.debug('这是debug级别的信息')
# logging.info('这是info级别的信息')
# logging.warning('这是warning级别的信息')
# logging.error('这是error级别的信息')
# logging.critical('这是critical级别的信息')


        # auth = oss2.Auth('LTAIeOayNW4ZjgrY', '6cAhgzBXg1cvGrdek2sgdXz8Ws9Ppq')
        # endpoint = 'http://oss-cn-beijing.aliyuncs.com'
        # self.bucket = oss2.Bucket(auth, endpoint, 'yundao888')  


        # limit_speed = (10000 * 1024 * 8) # 在headers中设置限速100 KB/s，即819200 bit/s。
        # self.headers = dict()
        # self.headers[OSS_TRAFFIC_LIMIT] = str(limit_speed)


            # result = self.bucket.get_object_to_file(oss_file_path, local_path, progress_callback=self.percentage) # headers=self.headers, 
            # print('http response status:', result.status)
            # sql = """
            # update trusteeship_enterprise_mixed_shear_re_details set uploadUrl = "%s", uploadSuccessDate = now(), uploadState = 1, sumSecond = %s where id = %s
            # """ % (self.Mixe
            # d_internal_http+oss_file_name, vid_duration, one_data[0])
    


            # else:
            #     # print("is down local",local_path)
            #     logging.info("is down local")
            #     logging.info(local_path)
            #     file_url = one_data[2]
            #     r = requests.get(file_url)
            #     with open(local_path, "wb") as file_a:
            #         file_a.write(r.content)


                # sql = """
                # update trusteeship_enterprise_mixed_shear_re_details set uploadUrl = "%s", uploadSuccessDate = now(), uploadState = 1, sumSecond = %s where id = %s
                # """ % (self.Mixed_internal_http+oss_file_name, vid_duration, one_data[0])
                # sql = """
                # update trusteeship_enterprise_mixed_shear_re_details set uploadSuccessDate = now(), uploadState = 1, sumSecond = %s where id = %s
                # """ % (vid_duration, one_data[0])
                # self.select_db (sql)
                # print('no have updata')
    

    # def download_file(self, url, dest_filename):
    #     with requests.get(url, stream=True) as response:
    #         total_size = int(response.headers.get('content-length', 0))
    #         block_size = 10240  # 1 KB
    #         t = tqdm(total=total_size, unit='B', unit_scale=True)
    #         start = time.time()
    #         with open(dest_filename, 'wb') as file:
    #             start_time = datetime.now()
    #             for data in response.iter_content(block_size):
    #                 t.update(len(data))
    #                 file.write(data)
    #                 speed = t.n / max(1, (datetime.now() - start_time).seconds)
    #                 if time.time() - start > 1:
    #                     logging.info(data)
    #                     logging.info(f'{speed:.2f} B/s')
    #                 # t.set_postfix(speed=f'{speed:.2f} B/s')
    #                 # logging.info(t.set_postfix(speed=f'{speed:.2f} B/s'))

    #         t.close()

    # def percentage(self, consumed_bytes, total_bytes):
    #     if total_bytes and time.time() - self.start_oss > 1:
    #         rate = int(100 * (float(consumed_bytes) / float(total_bytes)))
    #         self.start_oss = time.time()
    #         # rate表示下载进度。
    #         print('\r{0}% '.format(rate), end='')
    #         sys.stdout.flush()
