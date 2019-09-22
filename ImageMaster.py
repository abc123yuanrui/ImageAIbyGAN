import numpy as np
import os, sys
from urllib.request import urlopen, Request
import cv2
import base64
from TF import *
# METHOD #1: OpenCV, NumPy, and urllib
def url_to_image(url):
    # download the image, convert it to a NumPy array, and then read
    # it into OpenCV format
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.3' }
    req = Request(url=url, headers=headers)
    image = np.asarray(bytearray(urlopen(req).read()), dtype="uint8")
    image = cv2.imdecode(image, cv2.IMREAD_COLOR)

    # return the image
    return image
def GANProcessor(imglist):
    counter=0   #for test
    imgs_out=[]
    for img_path in imglist:
        counter = counter+1
        url = img_path
        img_in = url_to_image(url)
        img_out = processImg(img_in)
        cv2.imwrite(str(counter)+'.png', img_out) #for test
        #convert to base64
        retval, buffer = cv2.imencode('.jpg', img_out)
        jpg_as_text = base64.b64encode(buffer)
        imgs_out.append(jpg_as_text)
        #Delete those lines between and unquote nnxt line if image object list are required
	    #imgs_out.append(img_out)
        print(str(counter)+'image processed')
    return imgs_out
