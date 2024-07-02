"""
pip install oss2
"""


import oss2
auth = oss2.Auth('LTAI******', '6cAh******')
endpoint = 'http://oss-cn-beijing.aliyuncs.com'
bucket = oss2.Bucket(auth, endpoint, 'password') 

save_path = 'data/'+str(random.randint(0,100))+str(int(time.time()*1000000))+'.jpg'
bucket.put_object_from_file('save_dir/'+save_path, save_path)

