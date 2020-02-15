import time


class LogListener:
    def __init__(self, logfile):
        self.logfile = logfile
        self.log = None

    def start(self):
        logfile = open(self.logfile, "r", encoding="utf8")
        self.log = follow(logfile)


def follow(file):
    file.seek(0, 2)
    while True:
        line = file.readline()
        if not line:
            time.sleep(0.1)
            continue
        yield line
