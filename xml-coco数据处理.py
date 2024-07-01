"""
以xml文件，坐标裁切图片，并保存
"""
import cv2
import os
from natsort import ns, natsorted
from xml.etree.ElementTree import parse, Element
import time

main_file = 'cut_image/'
image_path = main_file + 'img' # 原图片路径
xml_path = main_file + 'xml' # xml文件路径
out_path = main_file + 'out' # 切出来的图片路径

img_list = os.listdir(image_path)
img_list = natsorted(img_list,alg=ns.PATH) #对读取的路径，按照win排序方式，进行排序
for img_name in img_list:
    frame = cv2.imread("%s/%s.jpg"%(image_path, img_name[:-4]))
    dom = parse("%s/%s.xml"%(xml_path, img_name[:-4]))
    root = dom.getroot()
    for obj in root.iter('object'):#获取object节点中的name子节点
        for bndbox in obj.iter('bndbox'):
            tmp_name = obj.find('name').text
            for xmin in obj.iter('xmin'):X1  = xmin.text
            for ymin in bndbox.iter('ymin'):Y1  = ymin.text
            for xmax in bndbox.iter('xmax'):X2 = xmax.text
            for ymax in bndbox.iter('ymax'):Y2 = ymax.text

            dir_path = os.path.join(out_path,tmp_name)
            if not os.path.exists(dir_path):  # os模块判断并创建
                os.mkdir(dir_path)
            cutimg = frame[int(Y1):int(Y2),int(X1):int(X2)]
            cv2.imwrite(os.path.join(dir_path,str(time.time())+'.jpg'),cutimg)



"""
修改xml、图片名和xml内容中的图片名
"""
import os
from natsort import ns, natsorted
import xml.dom.minidom

img_file = 'data/' # 图片路径
out_file = 'out/'
entry_name = 'Cat' # 文件前缀名称
img_list=os.listdir(img_file)
img_list = natsorted(img_list,alg=ns.PATH) #对读取的路径，按照win排序方式，进行排序
for num,img_name in enumerate(img_list):
    if img_name[-3:] =="jpg" or img_name[-3:] =="png" :
        new_img_name = out_file + entry_name+ str(num) + '.jpg'
        os.rename(img_file + img_name, new_img_name)

        new_xml_name = out_file + entry_name+ str(num) + '.xml'
        os.rename(img_file + img_name[:-3]+'xml', new_xml_name)

        try:
            print(new_xml_name)
            dom = xml.dom.minidom.parse(new_xml_name)
            newfilename = dom.documentElement.getElementsByTagName('filename')
            newfilename[0].firstChild.data = new_img_name
            with open(os.path.join(new_xml_name), 'w') as fh:
                dom.writexml(fh)
        except:
            pass




"""
修改xml标签名
"""
import os.path
from xml.etree.ElementTree import parse, Element

def changeName(xml_fold, origin_name_list, new_name_list):
    files = os.listdir(xml_fold)
    cnt = 0 
    for xmlFile in files:
        file_path = os.path.join(xml_fold, xmlFile)
        dom = parse(file_path)
        root = dom.getroot()
        for obj in root.iter('object'):#获取object节点中的name子节点
            tmp_name = obj.find('name').text
            for origin_name , new_name in zip(origin_name_list,new_name_list):
                if tmp_name == new_name: # 修改
                    obj.find('name').text = origin_name
                    print("change %s to %s." % (origin_name, new_name))
                    cnt += 1
        dom.write(file_path, xml_declaration=True)#保存到指定文件
    print("有%d个文件被成功修改。" % cnt)

xml_fold = 'data/' # # xml存放文件夹
origin_name_list = ['MZ','GZ'] # 原始名字
new_name_list = ['maozi','gongzhuang'] # 需要改成的正确的名字
changeName(xml_fold, origin_name_list, new_name_list)



"""
voc转coco
"""

import os
import json
from tqdm import tqdm
import xml.etree.ElementTree as ET

def voc_get_label_anno(ann_dir_path, ann_ids_path, labels_path):
    with open(labels_path, 'r') as f:
        labels_str = f.read().split()
    labels_ids = list(range(1, len(labels_str) + 1))

    with open(ann_ids_path, 'r') as f:
        ann_ids = [lin.strip().split(' ')[-1] for lin in f.readlines()]

    ann_paths = []
    for aid in ann_ids:
        if aid.endswith('xml'):
            ann_path = os.path.join(ann_dir_path, aid)
        else:
            ann_path = os.path.join(ann_dir_path, aid + '.xml')
        ann_paths.append(ann_path)

    return dict(zip(labels_str, labels_ids)), ann_paths

def voc_xmls_to_cocojson(annotation_paths, label2id, output_dir, output_file):
    output_json_dict = {
        "images": [],
        "type": "instances",
        "annotations": [],
        "categories": []
    }
    bnd_id = 1  # bounding box start id
    im_id = 0
    print('Start converting !')
    for a_path in tqdm(annotation_paths):
        # Read annotation xml
        ann_tree = ET.parse(a_path)
        ann_root = ann_tree.getroot()

        img_info = voc_get_image_info(ann_root, im_id)
        output_json_dict['images'].append(img_info)

        for obj in ann_root.findall('object'):
            ann = voc_get_coco_annotation(obj=obj, label2id=label2id)
            ann.update({'image_id': im_id, 'id': bnd_id})
            output_json_dict['annotations'].append(ann)
            bnd_id = bnd_id + 1
        im_id += 1

    for label, label_id in label2id.items():
        category_info = {'supercategory': 'none', 'id': label_id, 'name': label}
        output_json_dict['categories'].append(category_info)
    output_file = os.path.join(output_dir, output_file)
    with open(output_file, 'w') as f:
        output_json = json.dumps(output_json_dict)
        f.write(output_json)

def voc_get_image_info(annotation_root, im_id):
    filename = annotation_root.findtext('filename')
    assert filename is not None
    img_name = os.path.basename(filename)

    size = annotation_root.find('size')
    width = float(size.findtext('width'))
    height = float(size.findtext('height'))

    image_info = {
        'file_name': filename,
        'height': height,
        'width': width,
        'id': im_id
    }
    return image_info

def voc_get_coco_annotation(obj, label2id):
    label = obj.findtext('name')
    assert label in label2id, "label is not in label2id."
    category_id = label2id[label]
    bndbox = obj.find('bndbox')
    xmin = float(bndbox.findtext('xmin'))
    ymin = float(bndbox.findtext('ymin'))
    xmax = float(bndbox.findtext('xmax'))
    ymax = float(bndbox.findtext('ymax'))
    assert xmax > xmin and ymax > ymin, "Box size error."
    o_width = xmax - xmin
    o_height = ymax - ymin
    anno = {
        'area': o_width * o_height,
        'iscrowd': 0,
        'bbox': [xmin, ymin, o_width, o_height],
        'category_id': category_id,
        'ignore': 0,
    }
    return anno

voc_anno_dir = 'path/to/VOCdevkit/VOC2007/Annotations/'
voc_anno_list = 'path/to/VOCdevkit/VOC2007/ImageSets/Main/trainval.txt'
voc_label_list = 'dataset/voc/label_list.txt'
output_dir = './cocome/' 
voc_out_name = 'voc_train.json'

label2id, ann_paths = voc_get_label_anno(
    voc_anno_dir, voc_anno_list, voc_label_list)
voc_xmls_to_cocojson(
    annotation_paths=ann_paths,
    label2id=label2id,
    output_dir=output_dir,
    output_file=voc_out_name)


"""
语义分割，不规则裁剪，并将其他区域填充黑色
"""
import cv2
import numpy as np

def ROI_byMouse(img,lsPointsChoose):
    mask = np.zeros(img.shape, np.uint8)
    pts = np.array(lsPointsChoose, np.int32)  # pts是多边形的顶点列表（顶点集）
    col0 , col1 = pts[:,0] , pts[:,1]
    x1 , y1 , x2 , y2 = np.min(col0) , np.min(col1) , np.max(col0) , np.max(col1)
    pts = pts.reshape((-1, 1, 2))
    # 这里 reshape 的第一个参数为-1, 表明这一维的长度是根据后面的维度的计算出来的。
    # OpenCV中需要先将多边形的顶点坐标变成顶点数×1×2维的矩阵，再来绘制
 
    # --------------画多边形---------------------
    mask = cv2.polylines(mask, [pts], True, (255, 255, 255))
    ##-------------填充多边形---------------------
    mask2 = cv2.fillPoly(mask, [pts], (255, 255, 255))
    ROI = cv2.bitwise_and(mask2, img)
    return  ROI[y1:y2,x1:x2]
 
zuobiao=[
    [[110,167],[3,362],[624,379],[503,189]]
]
image_path = '2.jpg'
img = cv2.imread(image_path)

for i , xyxy in enumerate(zuobiao):
    image  = img.copy()
    image = ROI_byMouse(image,xyxy)
    cv2.imwrite("output/"+ str(i)+'.jpg',image)
