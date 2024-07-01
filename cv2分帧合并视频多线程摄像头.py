"""
pip install opencv-python
pip install natsort
"""



"""
视频分成图片
"""
import cv2
vidcap = cv2.VideoCapture('test.mp4')
count = 0
while True:
    success,image = vidcap.read()
    cv2.imwrite("output/frame%d.jpg" % count, image)
    if cv2.waitKey(1) == 27:
        break
    count += 1





"""
图片合成视频（使用opencv合成不能添加音频，可以使用moviepy或ffmpeg，在处理完之后添加音频。也可以看我另一篇ffmpeg的博客，使用ffmpeg进行视频合成）
"""
import cv2
import os
from natsort import ns, natsorted

img_file = 'dataset2/jpg/' # 图片路径
video_size = (1280,720) # 视频大小必须和图片大小相同，否则无法播放
#完成写入对象的创建，第一个参数是合成之后的视频的名称，第二个参数是可以使用的编码器，第三个参数是帧率即每秒钟展示多少张图片，第四个参数是图片大小信息
videowrite = cv2.VideoWriter('test.mp4',-1,5,video_size)
img_list=os.listdir(img_file)
img_list = natsorted(img_list,alg=ns.PATH) #对读取的路径，按照win排序方式，进行排序
for img_name in img_list:
    img = cv2.imread(img_file + img_name)
    #写入参数，参数是图片编码之前的数据
    videowrite.write(img)
print('end!')





"""
保存视频，各种编码格式 + 定时录像！！
"""
import cv2
import time
camera=cv2.VideoCapture('rtsp://admin:123456789.@192.168.2.43/MPEG-4/ch1/main/av_stream') # 网络摄像头，也可以使用本地0或1
video_size = (int(camera.get(cv2.CAP_PROP_FRAME_WIDTH)),int(camera.get(cv2.CAP_PROP_FRAME_HEIGHT))) # 获取摄像头w,h
fps = camera.get(cv2.CAP_PROP_FPS) # 获取摄像头帧率 ！！！！！！！！！！
# fps = 15 #                             或者自定义
# camera.set(3,1280) # 设置摄像头读取图像的宽度
# camera.set(4,720) # 高度，，，，不需要就不用设置
videowrite = cv2.VideoWriter('test.mp4',cv2.VideoWriter_fourcc(*'avc1'),fps,video_size) # 保存位置，编码，帧数，大小
# 0x00000021 h264编码
# cv2.VideoWriter_fourcc(*'mp4v') opencv官方版mp4,并不是h264编码
# cv2.VideoWriter_fourcc(*'XVID') opencv官方版avi，无压缩xvid编码
# cv2.VideoWriter_fourcc(*'avc1') openh264 mp4 h264编码，需要去官方
# https://github.com/cisco/openh264/releases下载openh264-1.8.0-win64.dll并添加环境变量

start = time.time() # 定义初始时间戳 ！！！！！！！！

while(True):
    ret,frame=camera.read()
    #写入参数，参数是图片编码之前的数据
    if time.time() - start > 60: # 录多长时间，以秒计算！！！！！！！
        videowrite = cv2.VideoWriter(str(time.time())+'.mp4',cv2.VideoWriter_fourcc(*'avc1'),fps,video_size) # 保存完继续保存
        start = time.time() # 重新计时
        # break # 保存完退出
    cv2.imshow('Dynamic',frame)
    videowrite.write(frame)
    #按下q键退出并保存
    if cv2.waitKey(1) & 0xff==ord('q'):
        break
camera.release()
cv2.destroyAllWindows()





"""
多线程读取摄像头并进行处理
"""
import cv2
from threading import Thread
import time

class LoadStreams:  # multiple IP or RTSP cameras
    def __init__(self, sources='streams.txt'):
        if os.path.isfile(sources):
    		try:
        		with open(sources, 'r') as f:
            		sources = [x.strip() for x in f.read().strip().splitlines() if len(x.strip())]
    		except:
        		sources = [sources]
		else:
    		sources = [sources]
		n = len(sources)
        self.imgs = [None] * n
        for i, s in enumerate(sources):
            # Start the thread to read frames from the video stream
            print('%g/%g: %s... ' % (i + 1, n, s), end='')
            cap = cv2.VideoCapture(eval(s) if s.isnumeric() else s)
            assert cap.isOpened(), 'Failed to open %s' % s
            w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = cap.get(cv2.CAP_PROP_FPS) % 100
            _, self.imgs[i] = cap.read()  # guarantee first frame
            thread = Thread(target=self.update, args=([i, cap]), daemon=True)
            print(' success (%gx%g at %.2f FPS).' % (w, h, fps))
            thread.start()

    def update(self, index, cap):
        # Read next stream frame in a daemon thread
        n = 0
        while cap.isOpened():
            n += 1
            # _, self.imgs[index] = cap.read()
            cap.grab()
            if n == 4:  # read every 4th frame
                _, self.imgs[index] = cap.retrieve()
                n = 0
            time.sleep(0.01)  # wait time

    def __iter__(self):
        self.count = -1
        return self

    def __next__(self):
        self.count += 1
        img0 = self.imgs.copy()
        if cv2.waitKey(1) == ord('q'):  # q to quit
            cv2.destroyAllWindows()
            raise StopIteration

        return img0

    def __len__(self):
        return 0  # 1E12 frames = 32 streams at 30 FPS for 30 years


dataset = LoadStreams('rtsp://admin:123456789.@192.168.2.112') # 多线程读取摄像头，可改为读取txt文本

for frame_list in dataset:
    for frame in frame_list :
        print('耗时任务')
        cv2.imshow('Dynamic',frame)
        #按下q键退出并保存
        if cv2.waitKey(1) & 0xff==ord('q'):
            break
