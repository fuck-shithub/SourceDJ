import log_listener
import log_parser
import json
import gtts
import pyaudio
import youtube_dl
import subprocess
import wave
import io
import os

try:
    with open("config.json") as f:
        config = json.load(f)
except FileNotFoundError:
    print("Config missing.")

loglistener = log_listener.LogListener(config["logfile"])
logparser = log_parser.LogParser(loglistener, chat_command_prefix=config["chat_command_prefix"])

p = pyaudio.PyAudio()

if config["loopback"]:
    def loopback_callback(in_data, frame_count, time_info, status):
        return in_data, pyaudio.paContinue


    loopback_stream = p.open(format=p.get_format_from_width(2),
                             channels=config["loopback_channels"],
                             rate=config["loopback_rate"],
                             input=True,
                             output=True,
                             stream_callback=loopback_callback,
                             input_device_index=config["loopback_input_device"],
                             output_device_index=config["loopback_output_device"])

    loopback_stream.start_stream()


@logparser.chat_command
def tts(event):
    print(event.author, "->", event.command, event.args)
    gtts.gTTS(event.args).save("tts.mp3")
    play_from_ffmpeg("tts.mp3")


@logparser.chat_command
def play(event):
    print(event.author, "->", event.command, event.args)
    ydl = youtube_dl.YoutubeDL(config["youtube_dl_options"])
    with ydl:
        video_info = ydl.extract_info(event.args, download=True)
        filename = os.path.join("youtube-dl", video_info["entries"][0]["id"])

    play_from_ffmpeg(filename)


def play_from_ffmpeg(file):
    audio = subprocess.Popen("ffmpeg -i " + file + " -loglevel panic -vn -f wav -c:a pcm_s16le pipe:1",
                             stdout=subprocess.PIPE)

    wf = wave.open(io.BytesIO(audio.stdout.read()))

    def callback(in_data, frame_count, time_info, status):
        data = wf.readframes(frame_count)
        return data, pyaudio.paContinue

    stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                    channels=wf.getnchannels(),
                    rate=wf.getframerate(),
                    output=True,
                    stream_callback=callback,
                    output_device_index=config["output_device"])


logparser.start()
