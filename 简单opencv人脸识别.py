"""
调用摄像头，进行人脸识别
"""

import cv2

def generator():
    #创建一个级联分类器  !!!!注意目录要改为自己的xml文件目录，一般会在虚拟环境Lib\site-packages\cv2\data中
    face_casecade=cv2.CascadeClassifier('E:/Anaconda3/envs/face_/Lib/site-packages/cv2/data/haarcascade_frontalface_default.xml')
    #打开摄像头
    camera=cv2.VideoCapture(0)
    
    while(True):
        #读取一帧图像
        ret,frame=camera.read()
        if ret:
            #转换为灰度图
            gray_img=cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)
            #人脸检测
            face=face_casecade.detectMultiScale(gray_img,1.3,5)
            for (x,y,w,h) in face:
                #在原图上绘制矩形
                cv2.rectangle(frame,(x,y),(x+w,y+h),(0,0,255),2)
                #调整图像大小
                new_frame=cv2.resize(frame[y:y+h,x:x+w],(92,112))
            cv2.imshow('Dynamic',frame)
            #按下q键退出
            if cv2.waitKey(100) & 0xff==ord('q'):
                break
    camera.release()
    cv2.destroyAllWindows()

generator()





"""
调用本地图片进行人脸识别
"""
import cv2

def image_save(img_path):
    #创建一个级联分类器  !!!!注意目录要改为自己的xml文件目录，一般会在虚拟环境Lib\site-packages\cv2\data中
    face_casecade=cv2.CascadeClassifier('E:/Anaconda3/envs/face_/Lib/site-packages/cv2/data/haarcascade_frontalface_default.xml')
    frame = cv2.imread(img_path)
    
    #转换为灰度图
    gray_img=cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)
    #人脸检测
    face=face_casecade.detectMultiScale(gray_img,1.3,5)
    for (x,y,w,h) in face:
        #在原图上绘制矩形
        cv2.rectangle(frame,(x,y),(x+w,y+h),(0,0,255),2)
        #调整图像大小
        new_frame=cv2.resize(frame[y:y+h,x:x+w],(92,112))
    cv2.imshow('Dynamic',frame)
    cv2.waitKey(0)
    
img_path = '1.jpg'
image_save(img_path)
