import av
from createASCII import createASCII
import shutil
import time
from threading import Thread
from queue import Queue, Empty
from colorama import Cursor
import os
import numpy as np
import sounddevice as sd

FPS = True

class Player:
    def __init__(self, src: str):
        self.frameQueue = Queue()
        self.asciiQueue = Queue()
        self.decodedAudio = Queue()

        decoder = Thread(target=self.decode, args=(src,))
        decoder.start()

        transformers = [Thread(target=self.transform) for i in range(1)]
        for transformer in transformers:
            transformer.start()

        displayer = Thread(target=self.display)
        displayer.start()

        audioPlayer = Thread(target=self.playAudio)
        audioPlayer.start()

        decoder.join()
        for transformer in transformers:
            transformer.join()
        displayer.join()
        audioPlayer.join()


    def transform(self):   
        while True:
            message = self.frameQueue.get()
            if message == 'END':
                self.asciiQueue.put(message)
                break
            timeStamp, imageData = message
            termSize = shutil.get_terminal_size()
            ascii = createASCII(imageData, termSize.columns, termSize.lines-1)
            self.asciiQueue.put((timeStamp, ascii))

    def display(self):
        if self.asciiQueue.get() != 'START':
            return
        
        stop = time.time()
        os.system('clear')
        while True:
            message = self.asciiQueue.get()
            if message == 'END':
                break
            if FPS:
                start = time.time()
            timeStamp, ascii = message
            if (time.time() - self.timeZero) < timeStamp:
                time.sleep(max(timeStamp - (time.time()-self.timeZero), 0))
            print(Cursor.POS(1,1) + ascii)
            if FPS:
                stop = time.time()
            print(Cursor.POS(1,1) + f"Frame time: {stop-start} FPS: {int(1.0/(stop-start))}")
            print(Cursor.POS(1,2) + str(round(timeStamp, 2)))


    def decode(self, src: str):
        video = av.open(src)

        vStream = video.streams.video[0]
        vStream.codec_context.skip_frame = "DEFAULT"
        vStream.thread_type = 'AUTO'
        timeBase = vStream.time_base

        aStream = video.streams.audio[0]
        self.sample_rate = aStream.sample_rate
        self.channels = aStream.channels
        self.frameSize = aStream.frame_size
        audioTimeBase = aStream.time_base

        self.timeZero = time.time()
        self.asciiQueue.put('START')
        self.decodedAudio.put('START')
                   
        for packet in video.demux(vStream, aStream):
            if packet.dts is None:
                continue

            type = packet.stream.type
            for frame in packet.decode():
                if type == 'video':
                    self.frameQueue.put((float(frame.pts*timeBase), frame.to_image()))
                    # self.frameQueue.put(frame.to_image())
                if type == 'audio':
                    self.decodedAudio.put((float(frame.pts*audioTimeBase), frame.to_ndarray().T))
                    # self.decodedAudio.put(frame.to_ndarray().T)
        self.frameQueue.put('END')
        self.decodedAudio.put('END')
                
    def playAudio(self):
        audioQueue = Queue()

        if self.decodedAudio.get() != 'START':
            return
        
        def callback(outdata, frames, time, status):
            if status:
                print(status)
            try:
                data = audioQueue.get_nowait()
                outdata[:] = data
            except Empty as e:
                data = np.zeros((self.frameSize, self.channels), dtype=np.float32)
                outdata[:] = data

        
        with sd.OutputStream(samplerate=self.sample_rate, channels=self.channels, callback=callback, blocksize=self.frameSize):
            while True:
                message = self.decodedAudio.get()
                if message == 'END':
                    break
                timeStamp, audioFrame = message
                if (time.time() - self.timeZero) < timeStamp:
                    time.sleep(max(timeStamp - (time.time() - self.timeZero), 0))
                audioQueue.put_nowait(audioFrame)