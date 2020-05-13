# -*- coding: utf-8 -*-
import os
import base64
import cv2
import torch
import numpy as np
from PIL import Image
from io import BytesIO
from chineseocr_lite.crnn import LiteCrnn, CRNNHandle
from chineseocr_lite.psenet import PSENet, PSENetHandel
from chineseocr_lite.application import idcard, trainTicket
from chineseocr_lite.crnn.keys import alphabetChinese as alphabet
from chineseocr_lite.angle_class import AangleClassHandle, shufflenet_v2_x0_5


# 调用CPU或GPU
gpu_id = 0
if gpu_id and isinstance(gpu_id, int) and torch.cuda.is_available():
    device = torch.device("cuda:{}".format(gpu_id))
else:
    device = torch.device("cpu")
# print('device:', device)


# psenet相关
pse_scale = 1
pse_long_size = 960  # 图片长边
pse_model_type = "mobilenetv2"
pse_model_path = "chineseocr_lite/models/psenet_lite_mbv2.pth"
text_detect_net = PSENet(backbone=pse_model_type, pretrained=False, result_num=6, scale=pse_scale)
text_handle = PSENetHandel(pse_model_path, text_detect_net, pse_scale, gpu_id=gpu_id)

# crnn相关
nh = 256
crnn_model_path = "chineseocr_lite/models/crnn_lite_lstm_dw_v2.pth"
crnn_net = LiteCrnn(32, 1, len(alphabet) + 1, nh, n_rnn=2, leakyRelu=False, lstmFlag=True)
crnn_handle = CRNNHandle(crnn_model_path, crnn_net, gpu_id=gpu_id)
crnn_vertical_model_path = "chineseocr_lite/models/crnn_dw_lstm_vertical.pth"
crnn_vertical_net = LiteCrnn(32, 1, len(alphabet) + 1, nh, n_rnn=2, leakyRelu=False, lstmFlag=True)
crnn_vertical_handle = CRNNHandle(crnn_vertical_model_path, crnn_vertical_net, gpu_id=gpu_id)

# angle_class相关
lable_map_dict = {0: "hengdao", 1: "hengzhen", 2: "shudao", 3: "shuzhen"}  # hengdao: 文本行横向倒立 其他类似
rotae_map_dict = {"hengdao": 180, "hengzhen": 0, "shudao": 180, "shuzhen": 0}  # 文本行需要旋转的角度
angle_model_path = "chineseocr_lite/models/shufflenetv2_05.pth"
angle_net = shufflenet_v2_x0_5(num_classes=len(lable_map_dict), pretrained=False)
angle_handle = AangleClassHandle(angle_model_path, angle_net, gpu_id=gpu_id)

def crop_rect(img, rect, alph=0.15):
    img = np.asarray(img)
    center, size, angle = rect[0], rect[1], rect[2]
    min_size = min(size)
    if (angle > -45):
        center, size = tuple(map(int, center)), tuple(map(int, size))
        size = (int(size[0] + min_size * alph), int(size[1] + min_size * alph))
        height, width = img.shape[0], img.shape[1]
        M = cv2.getRotationMatrix2D(center, angle, 1)
        img_rot = cv2.warpAffine(img, M, (width, height))
        img_crop = cv2.getRectSubPix(img_rot, size, center)
    else:
        center = tuple(map(int, center))
        size = tuple([int(rect[1][1]), int(rect[1][0])])
        size = (int(size[0] + min_size * alph), int(size[1] + min_size * alph))
        angle -= 270
        height, width = img.shape[0], img.shape[1]
        M = cv2.getRotationMatrix2D(center, angle, 1)
        img_rot = cv2.warpAffine(img, M, (width, height))
        img_crop = cv2.getRectSubPix(img_rot, size, center)
    img_crop = Image.fromarray(img_crop)
    return img_crop


def crnnRec(im, rects_re, f=1.0):
    results = []
    im = Image.fromarray(im)
    for index, rect in enumerate(rects_re):
        degree, w, h, cx, cy = rect
        partImg = crop_rect(im, ((cx, cy), (h, w), degree))
        newW, newH = partImg.size
        partImg_array = np.uint8(partImg)
        if newH > 1.5 * newW:
            partImg_array = np.rot90(partImg_array, 1)
        angel_index = angle_handle.predict(partImg_array)
        angel_class = lable_map_dict[angel_index]
        rotate_angle = rotae_map_dict[angel_class]
        if rotate_angle != 0:
            partImg_array = np.rot90(partImg_array, rotate_angle // 90)
        partImg = Image.fromarray(partImg_array).convert("RGB")
        partImg_ = partImg.convert('L')
        try:
            if crnn_vertical_handle is not None and angel_class in ["shudao", "shuzhen"]:
                simPred = crnn_vertical_handle.predict(partImg_)
            else:
                simPred = crnn_handle.predict(partImg_)  # 识别的文本
        except:
            continue
        if simPred.strip() != u'':
            results.append({'cx': cx * f, 'cy': cy * f, 'text': simPred, 'w': newW * f, 'h': newH * f,
                            'degree': degree})
    return results


def text_predict(img):
    '''文本预测'''
    preds, boxes_list, rects_re, t = text_handle.predict(img, long_size=pse_long_size)
    result = crnnRec(np.array(img), rects_re)
    return result

def result(img):
    back = {}
    img = Image.open(BytesIO(img)).convert('RGB')
    img = np.array(img)
    result = text_predict(img)
    back['文本'] = list(map(lambda x: x['text'], result))
    res = trainTicket.trainTicket(result)
    back['火车票'] = str(res)
    res = idcard.idcard(result)
    back['身份证'] = str(res)
    return back

def resultBase64(imgBase64):
    back = {}
    resB = []

    imgData = base64.b64decode(imgBase64.replace('data:image/jpg;base64,', ''))
    nparr = np.fromstring(imgData, np.uint8)
    img_np = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    img = Image.fromarray(cv2.cvtColor(img_np, cv2.COLOR_BGR2RGB))

    img = np.array(img)
    result = text_predict(img)
    back['str'] = list(map(lambda x: x['text'], result))
    back['x'] = list(map(lambda x: int(x['cx']), result))
    back['y'] = list(map(lambda x: int(x['cy']), result))

    for i in range(0,len(back['str'])):
        re = {}
        re['word'] = back['str'][i]
        re['pos'] = {}
        re['pos']['x'] = str(back['x'][i])
        re['pos']['y'] = str(back['y'][i])
        resB.append(re)

    return resB

if __name__ == '__main__':
    # imgage = 'C:/Users/kfadmin/Desktop/test2.jpg'
    # img = Image.open(imgage).convert('RGB')
    # # img.show()
    # img = np.array(img)
    # text = text_predict(img)
    # # print('文本预测:', list(map(lambda x: x['text'], text)))
    #
    # for str in text:
    #     chr = str['text']
    #     (x,y) = (int(str['cx']),int(str['cy']))
    #     print(chr, (x,y))

    imgBase64 = 'data:image/jpg;base64,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'
    print(resultBase64(imgBase64))