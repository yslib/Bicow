from PIL import Image, ImageDraw, ImageFont
import sys

if __name__ == "__main__":
    fileNames = sys.argv[1:]
    count = len(sys.argv)
    for name in fileNames:
        img = Image.open(name).convert("RGBA")

        nsize = (int(img.size[0] * 0.4),int(img.size[1] * 0.4))
        img = img.resize(nsize,Image.BILINEAR)

        text = "YSLucida"
        txtImage = Image.new("RGBA",nsize,(0,0,0,0))
        fnt = ImageFont.truetype("C:\Windows\Fonts\msyhbd.ttc",100)
        d = ImageDraw.Draw(txtImage)
        size = txtImage.size
        d.text((size[0] - 400,size[1] - 150),text,(255,255,255,100),fnt)

        out = Image.alpha_composite(img,txtImage)
        out.convert("RGB").save(name + "_wm.jpg")
        #layer = img.convert('RGBA')
