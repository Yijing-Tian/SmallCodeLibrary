import os
import cv2
import insightface
import numpy as np
from sklearn import preprocessing
import base64
import requests
# import time
# import json
# from main_fun.my_other import chuanshu,upface_json,clock_app
# from main_fun.visualize import xiezhongwen
# from urllib import request
# import operator
# import utils.hksdk.hk_sdk as hk_sdk

import uvicorn
from fastapi import APIRouter,FastAPI
from pydantic import BaseModel, Field
import traceback
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

class FaceRec_singleAPI(BaseModel):
    face1: str = Field(default="",  description="face1")
    face2: str = Field(default="",  description="face2")

class result_Response(BaseModel):
    result: bool
    status: str

class registerAPI(BaseModel):
    addFace: str = Field(default="",  description="face")
    userName: str = Field(default="",  description="face")

class FaceRec_libraryAPI(BaseModel):
    userFaceHttp: str = Field(default="",  description="face")
    userFaceBase64: str = Field(default="",  description="face")

class result_libraryAPI(BaseModel):
    result: str
    status: str

class FaceRecognition:
    def __init__(self, app: FastAPI, gpu_id=0, face_db='face', threshold=1.24, det_thresh=0.50, det_size=(640, 640)):
        """
        人脸识别工具类
        :param gpu_id: 正数为GPU的ID，负数为使用CPU
        :param face_db: 人脸库文件夹
        :param threshold: 人脸识别阈值
        :param det_thresh: 检测阈值
        :param det_size: 检测模型图片大小
        """
        self.gpu_id = gpu_id
        self.face_db = face_db
        self.threshold = threshold
        self.det_thresh = det_thresh
        self.det_size = det_size

        # 加载人脸识别模型，当allowed_modules=['detection', 'recognition']时，只单纯检测和识别
        self.model = insightface.app.FaceAnalysis(allowed_modules=['detection', 'recognition'],providers=['CUDAExecutionProvider'])
        self.model.prepare(ctx_id=self.gpu_id, det_thresh=self.det_thresh, det_size=self.det_size)
        # 人脸库的人脸特征
        self.faces_embedding = []
        # 加载人脸库中的人脸
        self.load_faces()

        self.router = APIRouter()
        self.app = app
        self.add_api_route("/addNewFace", self.register, methods=["POST"], response_model=result_Response)
        self.add_api_route("/FaceRecognition", self.single_recognition, methods=["POST"], response_model=result_Response)
        self.add_api_route("/FaceRecLibrary", self.library_recognition, methods=["POST"], response_model=result_libraryAPI)
        self.add_api_route("/FaceLibraryDel", self.face_library_del, methods=["POST"], response_model=result_Response)

    def add_api_route(self, path: str, endpoint, **kwargs):
        # if shared.cmd_opts.api_auth:return self.app.add_api_route(path, endpoint, dependencies=[Depends(self.auth)], **kwargs)
        return self.app.add_api_route(path, endpoint, **kwargs)

    def launch(self, server_name, port):
        self.app.include_router(self.router)
        uvicorn.run(self.app, host=server_name, port=port)

    def register(self, registerP: registerAPI):
        # base_img = base64.b64decode(registerP.addFace)
        # cv_img = cv2.imdecode(np.fromstring(base_img, np.uint8), 1)
        # if registerP.addFace == "":

        # else:
        file = requests.get(registerP.addFace)
        cv_img = cv2.imdecode(np.fromstring(file.content, np.uint8), 1)
        faces = self.model.get(cv_img)
        if len(faces) != 1:
            return result_Response(result=False, status="no face")
        # 判断人脸是否存在
        embedding = np.array(faces[0].embedding).reshape((1, -1))
        embedding = preprocessing.normalize(embedding)
        is_exits = False
        for com_face in self.faces_embedding:
            r = self.feature_compare(embedding, com_face["feature"], self.threshold)
            if r:
                is_exits = True
        if is_exits:
            return result_Response(result=False, status="user is in library")
        # 符合注册条件保存图片，同时把特征添加到人脸特征库中
        cv2.imencode('.png', cv_img)[1].tofile(os.path.join(self.face_db, '%s.png' % registerP.userName))
        self.faces_embedding.append({
            "user_name": registerP.userName,
            "feature": embedding
        })
        return result_Response(result=True, status="success")

    def face_library_del(self, registerP: registerAPI):
        try:
            os.remove(os.path.join(self.face_db, registerP.userName + ".png"))
            for i in self.faces_embedding:
                if i["user_name"] == registerP.userName:
                    self.faces_embedding.remove(i)
            return result_Response(result=True, status="success")
        except Exception as e:
            print(traceback.format_exc(),e)
            return result_Response(result=True, status="no face")
        
    

    # 加载人脸库中的人脸
    def load_faces(self):
        if not os.path.exists(self.face_db):
            os.makedirs(self.face_db)
        img_list = os.listdir(self.face_db)
        # for file in filename:
        #     img_list = os.listdir(os.path.join(self.face_db,file))
        #     if file not in self.faces_embedding: self.faces_embedding[file] = [] # 如果字典中没有这个摄像头，给这个ip的键值一个空数组
        for img_path in img_list:
            input_image = cv2.imdecode(np.fromfile(os.path.join(self.face_db, img_path), dtype=np.uint8), 1)
            # user_name = file.split(".")[0]
            face = self.model.get(input_image)[0]
            embedding = np.array(face.embedding).reshape((1, -1))
            embedding = preprocessing.normalize(embedding)
            self.faces_embedding.append({"user_name": img_path[:-4],"feature": embedding})


    # 人脸识别
    def library_recognition(self, userFace: FaceRec_libraryAPI):
        # base_img = base64.b64decode(userFace.userFace)
        # cv_img = cv2.imdecode(np.fromstring(base_img, np.uint8), 1)
        if userFace.userFaceHttp != "":
            file = requests.get(userFace.userFaceHttp)
            cv_img = cv2.imdecode(np.fromstring(file.content, np.uint8), 1)
        elif userFace.userFaceBase64 != "":
            base_img = base64.b64decode(userFace.userFaceBase64)
            cv_img = cv2.imdecode(np.fromstring(base_img, np.uint8), 1)
        faces = self.model.get(cv_img)
        # results = list()
        user_name = "unknown"
        for face in faces:
            # 开始人脸识别
            embedding = np.array(face.embedding).reshape((1, -1))
            embedding = preprocessing.normalize(embedding)
            
            for com_face in self.faces_embedding:
                r = self.feature_compare(embedding, com_face["feature"], self.threshold)
                if r:
                    user_name = com_face["user_name"]
            # results.append(user_name)
        return result_libraryAPI(result=user_name, status="success")


    # 人脸识别
    def single_recognition(self, face_list: FaceRec_singleAPI):
        face1, face2 = face_list.face1,face_list.face2
        status = "success"
        base_img = base64.b64decode(face1)
        face1 = cv2.imdecode(np.fromstring(base_img, np.uint8), cv2.COLOR_RGB2BGR)
        faces1 = self.model.get(face1,max_num=1)
        if faces1 == []: return False, "no face1" 
        # 开始人脸识别
        # bbox = np.array(faces[0].bbox).astype(np.int32).tolist()
        embedding = np.array(faces1[0].embedding).reshape((1, -1))
        embedding1 = preprocessing.normalize(embedding)

        base_img = base64.b64decode(face2)
        face2 = cv2.imdecode(np.fromstring(base_img, np.uint8), cv2.COLOR_RGB2BGR)
        faces2 = self.model.get(face2,max_num=1)
        if faces2 == []: return False, "no face2" 
        # bbox = np.array(face.bbox).astype(np.int32).tolist()
        embedding = np.array(faces2[0].embedding).reshape((1, -1))
        embedding2 = preprocessing.normalize(embedding)

        r = self.feature_compare(embedding1, embedding2, self.threshold)
        return result_Response(result=r, status=status)


    @staticmethod
    def feature_compare(feature1, feature2, threshold): # 人脸比对
        diff = np.subtract(feature1, feature2)
        dist = np.sum(np.square(diff), 1)
        if dist < threshold:
            return True
        else:
            return False


# import threading

# class Api:
#     def __init__(self, app: FastAPI):
#         self.router = APIRouter()
#         self.app = app
#         self.queue_lock = threading.Lock()
#         self.face_fun = FaceRecognition()
#         self.add_api_route("/addNewFace", self.infer, methods=["POST"], response_model=result_Response)
#         self.add_api_route("/FaceRecognition", self.infer, methods=["POST"], response_model=result_Response)

#     def add_api_route(self, path: str, endpoint, **kwargs):
#         # if shared.cmd_opts.api_auth:return self.app.add_api_route(path, endpoint, dependencies=[Depends(self.auth)], **kwargs)
#         return self.app.add_api_route(path, endpoint, **kwargs)

#     def launch(self, server_name, port):
#         self.app.include_router(self.router)
#         uvicorn.run(self.app, host=server_name, port=port)

#     def infer (self,face_list:FaceRec_ProcessingAPI):
#         text_res,status = self.face_fun.recognition(face_list.face1,face_list.face2)
#         print(text_res,status)
#         return result_Response(result=text_res,status=status)




api = FaceRecognition(app)
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
