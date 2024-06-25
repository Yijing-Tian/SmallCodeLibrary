
import oss2
auth = oss2.Auth('LTAIeOayNW4ZjgrY', '6cAhgzBXg1cvGrdek2sgdXz8Ws9Ppq')
endpoint = 'http://oss-cn-beijing.aliyuncs.com'
bucket = oss2.Bucket(auth, endpoint, 'yundao888') 

save_path = 'data/'+str(random.randint(0,100))+str(int(time.time()*1000000))+'.jpg'
bucket.put_object_from_file('H5-RES/2022/mxgc/'+save_path, save_path)

