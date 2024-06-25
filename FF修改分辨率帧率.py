# 数据库查询读取，删除损坏音频
import pymysql
import time
# from pydub import AudioSegment
# from io import BytesIO
import os
import subprocess
import shutil
import random
import requests
import json


def select_db (sql, chiose='none'):
    db = pymysql.connect(host='rm-8vbq6ojr4rmscc34qqo.mysql.zhangbei.rds.aliyuncs.com', port=3306, # 链接地址 # 端口号
                            user='ydbusiness',passwd='EVD!wuj@uA3q', # 用户名 # 密码
                            db='ydbusiness',autocommit=True) # 数据库名
    # for i in range(10):
    try:
        with db.cursor() as cur:
            if chiose != 'cha': # 执行 SQL  提交
                db.ping(reconnect=True)
                cur.execute(sql)
                # if cur.rowcount < 0: continue
                db.commit()
                return
            else: # 获取查询结果
                db.ping(reconnect=True)
                cur.execute(sql)
                # data = cur.fetchall()
                data = [dict(line) for line in [zip([column[0] for column in cur.description], row) for row in cur.fetchall()]]
                return data
    except pymysql.Error as e: # pymysql潜在异常
        print("Error:", e)
        try:
            db = pymysql.connect(host='rm-8vbq6ojr4rmscc34qqo.mysql.zhangbei.rds.aliyuncs.com', port=3306, # 链接地址 # 端口号
                                    user='ydbusiness',passwd='EVD!wuj@uA3q', # 用户名 # 密码
                                    db='ydbusiness',autocommit=True) # 数据库名
            time.sleep(1)
        except:
            pass


Mixed_out_lin = "G:/Mixed_shear_source/"
uploadUrl = "https://qjbb.onlineweixin.com/MixedAiVideo/"
srtState = 0
type = 1


reId = 1172 # 素材包Id
width = 1920 # 宽度
height = 1080 # 高度
fps = 30 # 帧率

Material_dir = 'data/'
img_list = os.listdir(Material_dir)
for file_name in img_list:
    new_file_name = str(random.randint(0,100))+str(int(time.time()*1000000))+file_name[-4:]
    local_path = Mixed_out_lin + new_file_name  

    shutil.move(Material_dir+file_name, local_path) # 161712909875461901.mp4
    print(local_path)
    if local_path[-3:] == 'mp4' or local_path[-3:] == 'MP4' or local_path[-3:] == 'wav' or local_path[-3:] == 'WAV' or local_path[-3:] == 'mp3' or local_path[-3:] == 'MP3' or local_path[-3:] == 'mov' or local_path[-3:] == 'MOV':
        try:
            vid_duration = subprocess.check_output(['ffprobe', '-i', local_path, '-show_entries', 'format=duration', '-v', 'quiet', '-of', 'csv=%s' % ("p=0")])
            vid_duration = float(vid_duration)
        except:
            print('素材同步失败，视频文件损坏')
            # select_db (f"""update trusteeship_enterprise_mixed_shear_re_details set uploadState = 3 where id = {one_data['id']}""")
            os.remove(local_path)
            continue
    else:
        vid_duration = 0
    
    networkAddress = "http://192.168.1.4:8922/scaleVideo"
    headers = {'Content-Type': 'application/json'}
    payload = json.dumps({"fileName": new_file_name, "width": width, "height": height, "fps":fps})
    response = requests.request("POST", networkAddress, headers=headers, data=payload)
    print(response, response.text)
    print(json.loads(response.text))
    result = json.loads(response.text)
    if result['code'] == 200 :
        sql = f"""
        SELECT MAX(usedCount) AS max_usedCount
        FROM trusteeship_enterprise_mixed_shear_re_details
        WHERE reId = {reId}"""
        max_usedCount = select_db (sql, chiose='cha')[0]['max_usedCount']
        if max_usedCount == None : max_usedCount = 0
        # sql = f"""update trusteeship_enterprise_mixed_shear_re_details set  uploadSuccessDate = now(), uploadState = 1, sumSecond = {vid_duration}, usedCount = {max_usedCount} where id = {one_data['id']}"""
        # print(sql,'have updata')
        sql = f"""INSERT INTO 
        trusteeship_enterprise_mixed_shear_re_details 
            (url, uploadUrl, addDate, uploadState, uploadSuccessDate, reAliasName, residueSecond, sumSecond, usedCount, serviceId, reId, type) 
        VALUES 
            ('{uploadUrl+result['result']}', '{uploadUrl+result['result']}', now(), 1, now(), '{file_name[:-4]}', -1, {vid_duration}, {max_usedCount}, 32, {reId}, {type});"""
        select_db (sql) # 同步成功
        try:
            os.remove(local_path)
            print(local_path,"is delete")
        except:
            print(local_path,"删除失败")





@app.route("/scaleVideo",methods=["POST",])
def scaleVideo():
    data = request.get_json() # 接收json格式
    print(data)
    Mixed_shear_dir = "/home/all_data/Mixed_shear_source/"
    last_out_video = str(random.randint(0,100))+str(int(time.time()*1000000))+'.mp4'

    res = subprocess.check_output(['ffprobe','-i',Mixed_shear_dir+data["fileName"],'-select_streams','v','-show_entries','stream=width,height','-of','json'])
    res = res.decode('utf8')
    video_info = json.loads(res)
    if video_info['streams'][0]['width'] < video_info['streams'][0]['height'] :
        streamsHeight = video_info['streams'][0]['width']*data["height"]/data["width"]
        strcmd = f'ffmpeg -hwaccel_device 0  -i {Mixed_shear_dir+data["fileName"]} -filter_complex "crop=min(iw\,{video_info["streams"][0]["width"]}):min(ih\,{streamsHeight}),scale={data["width"]}:{data["height"]}" -c:v h264_nvenc -global_quality 23 -r {data["fps"]} -b:a 193K -pix_fmt yuv420p -shortest -y {Mixed_shear_dir+last_out_video}'
    else:
        strcmd = f'ffmpeg -hwaccel_device 0  -i {Mixed_shear_dir+data["fileName"]} -filter_complex "scale={data["width"]}:{data["height"]},setsar=1:1" -c:v h264_nvenc -global_quality 23 -r {data["fps"]} -b:a 193K -pix_fmt yuv420p -shortest -y {Mixed_shear_dir+last_out_video}'
    print(strcmd)
    start = time.time()
    subprocess.call(strcmd, shell=True)
    print(time.time()-start)
    
    return jsonify({"code": 200, "msg": 'success', "result": last_out_video})




# all_data = [
#     {'url':"" , 'uploadUrl':"", 'type':"", 'srtState':"", 'reId':"1009"},
#     {'url':"" , 'uploadUrl':"", 'type':"", 'srtState':"", 'reId':"1009"}
# ]
