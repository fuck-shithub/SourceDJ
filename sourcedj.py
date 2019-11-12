import log_listener
import log_parser
import json
import gtts
import pyaudio
import youtube_dl
import subprocess
import wave
import io
import urllib.request
import urllib.parse
import re

try:
    with open("config.json") as f:
        config = json.load(f)
except FileNotFoundError:
    print("Config missing.")

play_regex = re.compile(r"(youtu\.be)|(youtube\.com)")

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


tts_stream = None
youtube_dl_stream = None


@logparser.chat_command
def tts(event):
    tts_play(event.args)

    print(event.author, "->", event.command, event.args)


@logparser.chat_command
def play(event):
    if play_regex.match(event.args):
        video_link = event.args
    else:
        video_link = get_youtube_video(event.args)

    ydl = youtube_dl.YoutubeDL(config["youtube_dl_options"])
    with ydl:
        result = ydl.extract_info(
            video_link,
            download=True
        )

    youtube_dl_play("youtube_dl")

def get_youtube_video(search_query):
    query_string = urllib.parse.urlencode({"search_query": search_query})
    html_content = urllib.request.urlopen("http://www.youtube.com/results?" + query_string)
    search_results = re.findall(r'href=\"\/watch\?v=(.{11})', html_content.read().decode())
    return "http://www.youtube.com/watch?v=" + search_results[0]


def tts_play(text):
    gtts.gTTS(text).save("tts.mp3")

    tts_audio = subprocess.Popen("ffmpeg -i tts.mp3 -loglevel panic -vn -f wav -c:a pcm_s16le pipe:1",
                                 stdout=subprocess.PIPE)

    wf = wave.open(io.BytesIO(tts_audio.stdout.read()))

    def tts_callback(in_data, frame_count, time_info, status):
        data = wf.readframes(frame_count)
        return data, pyaudio.paContinue

    global tts_stream
    tts_stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                        channels=wf.getnchannels(),
                        rate=wf.getframerate(),
                        output=True,
                        stream_callback=tts_callback,
                        output_device_index=config["output_device"])


def youtube_dl_play(file):
    tts_audio = subprocess.Popen("ffmpeg -i "+file+" -loglevel panic -vn -f wav -c:a pcm_s16le pipe:1",
                                 stdout=subprocess.PIPE)

    wf = wave.open(io.BytesIO(tts_audio.stdout.read()))

    def youtube_dl_callback(in_data, frame_count, time_info, status):
        data = wf.readframes(frame_count)
        return data, pyaudio.paContinue

    global youtube_dl_stream
    youtube_dl_stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                        channels=wf.getnchannels(),
                        rate=wf.getframerate(),
                        output=True,
                        stream_callback=youtube_dl_callback,
                        output_device_index=config["output_device"])


logparser.start()
