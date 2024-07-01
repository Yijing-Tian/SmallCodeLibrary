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
