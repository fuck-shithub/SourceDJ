import subprocess
import pyaudio
import soundfile as sf
import numpy as np
import io


class AudioQueue:
    def __init__(self, pa, output_device, frames_per_buffer=1024, volume=1):
        self.pa = pa
        self.output_device = output_device
        self.frames_per_buffer = frames_per_buffer
        self.volume = volume
        self.audiodata = None
        self.stream = None

    def play(self, format=pyaudio.paInt16, channels=2, rate=48000):
        self.stream = self.pa.open(format=format,
                                   channels=channels,
                                   rate=rate,
                                   output=True,
                                   stream_callback=self.callback,
                                   output_device_index=self.output_device,
                                   frames_per_buffer=self.frames_per_buffer)

    def add_to_queue(self, file):
        audio = subprocess.Popen(["ffmpeg", "-i", file, "-loglevel", "panic", "-vn", "-f", "wav", "-c:a", "pcm_s16le", "pipe:1"],
                                 stdout=subprocess.PIPE)

        audiofile = sf.SoundFile(io.BytesIO(audio.stdout.read()))
        if self.audiodata is None:
            self.audiodata = audiofile.read(dtype="int16")
        else:
            self.audiodata = np.concatenate((self.audiodata, audiofile.read(dtype="int16")))

        try:
            if not self.stream.is_active():
                self.play(format=pyaudio.paInt16, channels=audiofile.channels, rate=audiofile.samplerate)
        except AttributeError:
            self.play(format=pyaudio.paInt16, channels=audiofile.channels, rate=audiofile.samplerate)

    def callback(self, in_data, frame_count, time_info, status):
        size = frame_count
        data = self.audiodata[:size]
        self.audiodata = self.audiodata[size:]

        for i in range(len(data)):
            chunk = np.fromstring(data[i], np.int16)
            chunk = chunk * self.volume
            data[i] = chunk.astype(np.int16)
        return data, pyaudio.paContinue
