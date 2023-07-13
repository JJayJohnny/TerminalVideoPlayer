import av
from createASCII import createASCII
import shutil
import time
from colorama import Cursor
import os
import numpy as np
import sounddevice as sd
import queue

FPS = True

def play(src: str):
    video = av.open(src)

    vStream = video.streams.video[0]
    vStream.codec_context.skip_frame = "DEFAULT"
    vStream.thread_type = 'AUTO'
    timeBase = vStream.time_base

    aStream = video.streams.audio[0]
    sample_rate = aStream.sample_rate
    channels = aStream.channels
    frameSize = aStream.frame_size
    audioTimeBase = aStream.time_base
    audioQueue = queue.Queue()

    def callback(outdata, frames, time, status):
        if status:
            print(status)
        try:
            data = audioQueue.get_nowait()
            outdata[:] = data
        except queue.Empty as e:
            data = np.zeros((frameSize, channels), dtype=np.float32)
            outdata[:] = data      

    os.system('clear')

    timeZero = time.time()

    with sd.OutputStream(samplerate=sample_rate, channels=channels, callback=callback, blocksize=frameSize):
        for packet in video.demux(vStream, aStream):
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
                if type == 'audio':
                    if (time.time() - timeZero) < frame.pts*audioTimeBase:
                        time.sleep(max(frame.pts*audioTimeBase - (time.time() - timeZero), 0))
                    audioQueue.put_nowait(frame.to_ndarray().T)