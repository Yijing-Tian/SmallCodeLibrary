"""
根据文件存在时间，判断删除
"""
import time
import os
from threading import Thread
# 文件存储时，避免文件名重复，可以使用 str(random.randint(0,100))+str(int(time.time()*1000000))+'.jpg'
def deletefile(path,N):
    for eachfile in os.listdir(path):
        filename = os.path.join(path, eachfile)
        if os.path.isfile(filename):
            lastmodifytime = os.stat(filename).st_mtime
            # print(lastmodifytime)
            # 设置删除多久之前的文件
            endfiletime = time.time() - 3600 * 24 * N
            if endfiletime > lastmodifytime:
                os.remove(filename)
                print("删除文件 %s 成功" % filename)
        # 如果是目录则递归调用当前函数
        elif os.path.isdir(filename):
            deletefile(filename,N)
            os.rmdir(filename)

def del_run (path,N):
    while True:
        try:
            deletefile(path,N)
        except:
            print('error')
            continue
        time.sleep(60*60*24)

if __name__ == '__main__':
    thread = Thread(target=del_run,args=([r'/local/tts_file',3]))
    thread.start()
    while True:
        pass





"""
根据sql，判断删除
"""
import os
N = 8 # 设置删除多少天前的文件
sql = f"""SELECT id , realUrl 
    FROM 
        trusteeship_enterprise_make_video 
    where 
        DATE_SUB(CURDATE(), INTERVAL {N} DAY) >= date(addDate) AND isDelete=1 order by id asc limit 100"""
date_del_data = select_db (sql, chiose='cha') # 从数据库查找过期的视频
for one_del_data in date_del_data:
    try:
        os.remove(os.path.basename(one_del_data['realUrl']))
        print(f"文件已过期，删除 {one_del_data['realUrl']} ")
    except:
        print(f"文件不存在{one_del_data['realUrl']}")
    sql = f"""delete from trusteeship_enterprise_make_video where id = {one_del_data['id']}"""
    select_db (sql)
