import cv2
import sys
import os

def make_video_cv(params):
    fps = params.get('fps', 24)
    output = params.get('output_file', 'video.avi')
    resl = params.get('resolution', (3840, 1920))
    files = params.get('files', [])
    ind = 0
    total = len(files)
    imgs = []
    for f in files:
        print("Read {} of {} images -- %{}".format(ind + 1,total, float(ind+1)/total * 100))
        img = cv2.imread(f)
        if img is None:
            print('Failed to read img {}'.format(f))
            continue
        img = cv2.resize(img,resl)
        imgs.append(img)
        ind += 1

    total = len(imgs)
    vw = cv2.VideoWriter(output,cv2.VideoWriter_fourcc(*'MJPG'),fps,resl)
    for img in imgs:
        print('progress: {} of {} at %{}\n'.format(ind+1,total, float(ind+1)/total) * 100)
        vw.write(img)
        ind += 1

    vw.release()

def read_image_files(params):
    input_dir = params.get('input_dir', '.')
    for root, dirs, files in os.walk(input_dir, topdown=False):
        files = list(filter(lambda x: x.endswith('.tif'), files))
        files = sorted(files, key=lambda x: int(x.split('.')[0][7:]))
        files = list(map(lambda x: os.path.join(input_dir, x), files))
    return files


def video(params):
    files = read_image_files(params)
    print(files)
    params['files'] = files
    make_video_cv(params)

if __name__ == '__main__':
    params = {}
    params['input_dir'] = '.'
    if len(sys.argv) > 1:
        params['input_dir'] = sys.argv[1]
    params['resolution'] = (7968, 5320)
    params['output_file'] = 'D:\\photo\\2021-6-25\\output\\output.avi'
    params['fps'] = 30
    video(params)