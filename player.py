import av
from createASCII import createASCII
import os
import shutil
import time

FPS = True

def play(src: str):
    video = av.open(src)

    vStream = video.streams.video[0]
    vStream.codec_context.skip_frame = "DEFAULT"
    vStream.thread_count = 10

    for packet in video.demux(vStream):
        if packet.dts is None:
            continue

        type = packet.stream.type

        for frame in packet.decode():
            if type == 'video':
                if FPS:
                    start = time.time()
                imageData = frame.to_image()
                # image = Image.open(io.BytesIO(imageData))
                termSize = shutil.get_terminal_size()
                ascii = createASCII(imageData, termSize.columns, termSize.lines)
                os.system('clear')
                print(ascii)
                if FPS:
                    stop = time.time()
                print(f"Frame time: {stop-start} FPS: {1.0/(stop-start)}")

                


                
    # for frame in container.decode(video=0):
    #     frame.to_image().save("frame.jpg", quality=50)