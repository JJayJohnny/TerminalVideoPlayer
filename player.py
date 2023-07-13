import av
from createASCII import createASCII
import shutil
import time
from colorama import Cursor
import os

FPS = True

def play(src: str):
    video = av.open(src)

    vStream = video.streams.video[0]
    vStream.codec_context.skip_frame = "DEFAULT"
    vStream.thread_type = 'AUTO'
    timeBase = vStream.time_base
    os.system('clear')

    timeZero = time.time()

    for packet in video.demux(vStream):
        if packet.dts is None:
            continue

        type = packet.stream.type

        for frame in packet.decode():
            if type == 'video':
                if FPS:
                    start = time.time()
                imageData = frame.to_image()
                termSize = shutil.get_terminal_size()
                ascii = createASCII(imageData, termSize.columns, termSize.lines-2)
                if (time.time() - timeZero) < frame.pts*timeBase:
                    time.sleep(max(frame.pts*timeBase - (time.time() - timeZero), 0))
                print(Cursor.POS(1,1))
                print(ascii)   
                if FPS:
                    stop = time.time()
                    print(Cursor.POS(1,1) + f"Frame time: {stop-start} FPS: {1.0/(stop-start)}")
                    print(Cursor.POS(1,2) + str(round(float(frame.pts*timeBase), 2)))

                


                
    # for frame in container.decode(video=0):
    #     frame.to_image().save("frame.jpg", quality=50)