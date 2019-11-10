class LogParser:
    def __init__(self, loglistener, chat_command_prefix="."):
        self.loglistener = loglistener
        self.chat_command_event_funcs = []
        self.chat_command_prefix = chat_command_prefix

    def chat_command(self, func):
        self.chat_command_event_funcs.append([func.__name__, func])
        return func

    def start(self):
        self.loglistener.start()

        for line in self.loglistener.log:
            self.handle_events(line)

    def handle_events(self, content):
        content = content.strip()

        if content.find(" : ") > -1:
            split_chat_message = content.split(" : ", 1)
            if split_chat_message[1].startswith(self.chat_command_prefix):
                prefix = self.chat_command_prefix
                command = split_chat_message[1][len(prefix):]
                if command.find(" ") > -1:
                    command = command[:command.find(" ")]
                author = split_chat_message[0]

                args = ""
                args_array = []
                if split_chat_message[1][len(prefix)+len(command):] != "":
                    args = split_chat_message[1][len(prefix)+len(command)+1:]
                    args_array = args.split(" ")
                for chat_command_event_reg in self.chat_command_event_funcs:
                    if command == chat_command_event_reg[0]:
                        command_event_object = CommandEvent(author, command, args, args_array)
                        chat_command_event_reg[1](command_event_object)


class CommandEvent:
    def __init__(self, author, command, args, args_array):
        self.author = author
        self.command = command
        self.args = args
        self.args_array = args_array
