import os
import cv2
import insightface
import numpy as np
from sklearn import preprocessing
import base64
# import time
# import json
# from main_fun.my_other import chuanshu,upface_json,clock_app
# from main_fun.visualize import xiezhongwen
# from urllib import request
# import operator
# import utils.hksdk.hk_sdk as hk_sdk

import requests
import uvicorn
from fastapi import APIRouter,FastAPI
from pydantic import BaseModel, Field

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

app = FastAPI()
app.add_middleware( # 解决前端跨域
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"])
app.add_middleware(GZipMiddleware, minimum_size=1000)

import time
import random
import oss2
auth = oss2.Auth('LTAI5tMnUay3CDmBHM7owntw', 'KzNQd2yOq9n7LS1JhBiVVQQG8I2v2s')
endpoint = 'http://oss-cn-zhangjiakou.aliyuncs.com'
bucket = oss2.Bucket(auth, endpoint, 'yanxuezs')  

class FaceRecognition:
    def __init__(self, gpu_id=0, face_db='face', threshold=1.24, det_thresh=0.50, det_size=(640, 640)):
        """
        人脸识别工具类
        :param gpu_id: 正数为GPU的ID，负数为使用CPU
        :param face_db: 人脸库文件夹
        :param threshold: 人脸识别阈值
        :param det_thresh: 检测阈值
        :param det_size: 检测模型图片大小
        """
        self.gpu_id = gpu_id
        # self.face_db = face_db
        self.threshold = threshold
        self.det_thresh = det_thresh
        self.det_size = det_size

        # 加载人脸识别模型，当allowed_modules=['detection', 'recognition']时，只单纯检测和识别
        self.model = insightface.app.FaceAnalysis(allowed_modules=['detection', 'recognition'],providers=['CUDAExecutionProvider'])
        self.model.prepare(ctx_id=self.gpu_id, det_thresh=self.det_thresh, det_size=self.det_size)
        # 人脸库的人脸特征
        # self.faces_embedding = {}
        # 加载人脸库中的人脸
        # self.load_faces(face_db)

    # # 加载人脸库中的人脸
    # def load_faces(self, face_db_path):
    #     if not os.path.exists(face_db_path):
    #         os.makedirs(face_db_path)
    #     filename = os.listdir(face_db_path)
    #     for file in filename:
    #         img_list = os.listdir(os.path.join(face_db_path,file))
    #         if file not in self.faces_embedding: self.faces_embedding[file] = [] # 如果字典中没有这个摄像头，给这个ip的键值一个空数组
    #         for img_path in img_list:
    #             input_image = cv2.imdecode(np.fromfile(os.path.join(face_db_path, file,img_path), dtype=np.uint8), 1)
    #             # user_name = file.split(".")[0]
    #             face = self.model.get(input_image)[0]
    #             embedding = np.array(face.embedding).reshape((1, -1))
    #             embedding = preprocessing.normalize(embedding)
    #             self.faces_embedding[file].append({"user_name": img_path[:-4],"feature": embedding})

    # 人脸识别
    def recognition(self,input_source, input_target):
        status = "success"
        print(input_source)
        file = requests.get(input_source)
        face1 = cv2.imdecode(np.fromstring(file.content, np.uint8), cv2.COLOR_RGB2BGR)

        faces1 = self.model.get(face1,max_num=1)
        if faces1 == []: return "no face1" , -1, "defeat", ""
        # 开始人脸识别
        # bbox = np.array(faces[0].bbox).astype(np.int32).tolist()
        embedding = np.array(faces1[0].embedding).reshape((1, -1))
        embedding1 = preprocessing.normalize(embedding)

        for enm, one_face in enumerate(input_target):
            # base_img = base64.b64decode(face2)
            # face2 = cv2.imdecode(np.fromstring(base_img, np.uint8), cv2.COLOR_RGB2BGR)
            file = requests.get(one_face)
            face2Img = cv2.imdecode(np.fromstring(file.content, np.uint8), cv2.COLOR_RGB2BGR)
            faces2 = self.model.get(face2Img) # ,max_num=1
            if faces2 == []: continue
            for face2 in faces2:
                # bbox = np.array(face.bbox).astype(np.int32).tolist()
                embedding = np.array(face2.embedding).reshape((1, -1))
                embedding2 = preprocessing.normalize(embedding)
                r = self.feature_compare(embedding1, embedding2, self.threshold)
                if r == True:
                    faceBbox = list(face2.bbox)
                    crop_path = f"Temp/{random.randint(0,100)}{int(time.time()*1000000)}.jpg"
                    face2Img = face2Img[int(faceBbox[1]):int(faceBbox[3]),int(faceBbox[0]):int(faceBbox[2])]
                    cv2.imwrite(crop_path, face2Img)
                    # face2Img.crop((faceBbox[0], faceBbox[1], faceBbox[2], faceBbox[3])).save(save_path)
                    bucket.put_object_from_file(crop_path, crop_path)
                    os.remove(crop_path)
                    return one_face, enm, status, crop_path
        return '', -1, status, ""


    @staticmethod
    def feature_compare(feature1, feature2, threshold): # 人脸比对
        diff = np.subtract(feature1, feature2)
        dist = np.sum(np.square(diff), 1)
        if dist < threshold:
            return True
        else:
            return False

import threading

class FaceRec_ProcessingAPI(BaseModel):
    input_source: str = Field(default="",  description="face1")
    input_target: list = Field(default=[],  description="face2")

class result_Response(BaseModel):
    which_photo: str
    result: int
    status: str
    cropFace: str

class Api:
    def __init__(self, app: FastAPI):
        self.router = APIRouter()
        self.app = app
        self.queue_lock = threading.Lock()
        self.face_fun = FaceRecognition()

        self.add_api_route("/FaceRecognition", self.infer, methods=["POST"], response_model=result_Response)

    def add_api_route(self, path: str, endpoint, **kwargs):
        # if shared.cmd_opts.api_auth:return self.app.add_api_route(path, endpoint, dependencies=[Depends(self.auth)], **kwargs)
        return self.app.add_api_route(path, endpoint, **kwargs)

    def launch(self, server_name, port):
        self.app.include_router(self.router)
        uvicorn.run(self.app, host=server_name, port=port)

    def infer (self,face_list:FaceRec_ProcessingAPI):
        one_face, enm, status, cropFace = self.face_fun.recognition(face_list.input_source,face_list.input_target)
        print(one_face, enm, status)
        return result_Response(which_photo=one_face, result=enm, status=status, cropFace=cropFace)




api = Api(app)
api.launch(server_name="0.0.0.0" , port=9556)


# if __name__ == '__main__':
#     img = cv2.imdecode(np.fromfile('迪丽热巴.jpg', dtype=np.uint8), -1)
#     face_recognitio = FaceRecognition()
#     # # 人脸注册
#     # result = face_recognitio.register(img, user_name='迪丽热巴')
#     # print(result)

#     # 人脸识别
#     results = face_recognitio.recognition(img)
#     for result in results:
#         print("识别结果：{}".format(result))
