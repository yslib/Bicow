import os
from PIL import Image, ImageDraw, ImageFont
import sys
import json


def open_config(filename):

    """
    default json file
    {
        "thumbnailDir":"thumbnail",
        "originalDir":"original",
        "resultDir":"result"
        "database":"image_info.json",
        "deleteAfterFinish":False

        "uploadConfiguration":{

        }
    }
    """
    with open(filename,'r') as f:
        jtext = f.readlines()
        jdict = json.loads(jtext)
    return jdict



if __name__ == "__main__":
    fileNames = sys.argv[1:]
    count = len(sys.argv)
    count = 0
    text = "YSLucida"

    conf = open_config("./config.json")



    for name in os.listdir("./original"):
        img = Image.open("./original/"+name).convert("RGBA")

        (path,fullname) = os.path.split(name)
        (fname,ext) = os.path.splitext(fullname)
        print(path,fullname,fname,ext)


        thumbsize = (int(img.size[0] * 0.1),int(img.size[1] * 0.1))
        thumbImg = img.resize(thumbsize,Image.BILINEAR)
        thumbImg.convert("RGB").save("./thumbnails/"+fname+"_thum.jpg")
        count+=1
        
        txtImage = Image.new("RGBA",img.size,(0,0,0,0))
        fnt = ImageFont.truetype("C:\Windows\Fonts\STXINGKA.TTF",100)
        d = ImageDraw.Draw(txtImage)
        size = txtImage.size
        d.text((size[0] - 400,size[1] - 150),text,(255,255,255,100),fnt)

        out = Image.alpha_composite(img,txtImage)
        out.convert("RGBA").save("./watermark/"+fname+"_wm.png")
        
