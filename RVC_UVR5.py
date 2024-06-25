from configs.config import Config
from infer.modules.vc.modules import VC

from dotenv import load_dotenv
load_dotenv()

config = Config()
vc = VC(config)
# https://github.com/karaokenerds/python-audio-separator
from audio_separator.separator import Separator
# Initialize the Separator class (with optional configuration properties below)
separator = Separator()
# Load a machine learning model (if unspecified, defaults to 'UVR-MDX-NET-Inst_HQ_3.onnx')
separator.load_model()


import soundfile as sf
import random
import time
import subprocess
import os

class RVC_class:
    def __init__(self):
        self.out_lin = '/home/all_data/tts_data/'
        self.current_dubname = ""
        # self.reload_model (self.current_dubname)

    def wav2vaw(self, input_audio, dub_name, gender, keepBg):

        if keepBg == 1: # 主音频分离背景音
            main_audio, bg_audio = self.uvr5_infer(input_audio)

        # 变调(整数, 半音数量, 升八度12降八度-12)
        if gender == 1: vc_transform0 = 12 # 女
        else: vc_transform0 = -12 # 男

        sid = 0
        f0method0 = "rmvpe" # 选择音高提取算法,输入歌声可用pm提速,harvest低音好但巨慢无比,crepe效果好但吃GPU,rmvpe效果最好且微吃GPU
        filter_radius0 = 3 # >=3则使用对harvest音高识别的结果使用中值滤波，数值为滤波半径，使用可以削弱哑音
        resample_sr0 = 0 # 后处理重采样至最终采样率，0为不进行重采样
        rms_mix_rate0 = 0.25 # 输入源音量包络替换输出音量包络融合比例，越靠近1越使用输出包络
        protect0 = 0.33 # 保护清辅音和呼吸声，防止电音撕裂等artifact，拉满0.5不开启，调低加大保护力度但可能降低索引效果
        protect1 = 0.33
        index_rate1 = 0.75 # 检索特征占比
        f0_file = None
        file_index1 = f"logs/{dub_name}.index"
        file_index2 = ""
        if self.current_dubname != dub_name:
            spk_item, get_protect0, get_protect1, file_index2, file_index4 = vc.get_vc(dub_name + '.pth', protect0, protect1)
            self.current_dubname = dub_name

        if keepBg == 1: # 合并分离出来的背景音
            vc_output1,vc_output2 = vc.vc_single(sid, main_audio, vc_transform0, f0_file, f0method0, file_index1, file_index2, 
                        index_rate1, filter_radius0, resample_sr0, rms_mix_rate0, protect0)
            os.remove(main_audio)
        else:
            vc_output1,vc_output2 = vc.vc_single(sid, input_audio, vc_transform0, f0_file, f0method0, file_index1, file_index2, 
                        index_rate1, filter_radius0, resample_sr0, rms_mix_rate0, protect0)

        out_tts_name = str(random.randint(0,100))+str(int(time.time()*1000000)) +'.wav'
        out_path = out_tts_name # self.out_lin + 
        print(out_path, vc_output2[1], vc_output2[0])
        
        if keepBg == 1: # 合并分离出来的背景音
            tmp_path = str(random.randint(0,100))+str(int(time.time()*1000000)) +'.wav' # self.out_lin + 
            sf.write(tmp_path, vc_output2[1], vc_output2[0])
            strcmd = f"ffmpeg -i {tmp_path} -i {bg_audio} -filter_complex amix=inputs=2:duration=shortest {out_path}"
            subprocess.call(strcmd, shell=True)
            os.remove(tmp_path)
            os.remove(bg_audio)
        else:
            sf.write(out_path, vc_output2[1], vc_output2[0])
        
        return out_tts_name   


    def uvr5_infer(self, input_audio):
        # Perform the separation on specific audio files without reloading the model
        output_files = separator.separate(input_audio)
        print(f"Separation complete! Output file(s): {' '.join(output_files)}")
        return output_files



import uvicorn
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from fastapi import File,UploadFile,Form # 上传文件需要使用，格式为form-data
from pydantic import BaseModel # 上传json时使用   
# from typing import Optional # 用于可选参数

app = FastAPI() # 初始化 
app.add_middleware( # 解决前端跨域
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"])

class fun_Base(BaseModel):
    input_audio: str
    dub_name: str
    gender: int # 1女2男
    keepBg: int # 1保留背景音2不保留背景音

local_http = 'https://qjbb.onlineweixin.com/tts_infer/'
internal_http = 'http://192.168.1.8:8008/tts_infer/'
rvc_fun = RVC_class()


# 接收 form-data 格式
@app.post("/rvc_wav")
async def upsampler_fun (text_base: fun_Base ):

    out_path = rvc_fun.wav2vaw(text_base.input_audio, text_base.dub_name, text_base.gender, text_base.keepBg)

    return {"code": 200, "msg": 'success', "result": local_http+out_path, "internal_url":internal_http+out_path}

if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=8086)





