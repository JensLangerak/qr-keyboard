import os
import threading
import time

import qrcode

import tkinter as tk
from tkinter import filedialog as fd
import sys

from PIL import ImageTk
from Crypto.Cipher import AES
from base64 import b64encode
from getpass import getpass
import re

__VERSION = "1.0"


def encrypt(plain_text, key):
    """
    Encrypt the text with aes, using the key for the key.
    :param plain_text:
    :param key:
    :return: a dictionary {cipher_text, nonce, tag, combined}, where combined is that concatination of the other 3.
            All are in base64 encoding
    """
    # create cipher config
    cipher_config = AES.new(key, AES.MODE_GCM)

    # return a dictionary with the encrypted text
    cipher_text, tag = cipher_config.encrypt_and_digest(bytes(plain_text, 'utf-8'))
    concat = tag + cipher_config.nonce + cipher_text
    return {
        'cipher_text': b64encode(cipher_text).decode('utf-8'),
        'nonce': b64encode(cipher_config.nonce).decode('utf-8'),
        'tag': b64encode(tag).decode('utf-8'),
        'combined': b64encode(concat).decode('utf-8')
    }


def generate_key():
    """
    Generates a key of 256 bits
    :return:  a key of 256 bits
    """
    return os.urandom(32)


def store_key(key, location):
    """
    Store the key in the location
    :param key:
    :param location:
    """
    with open(location, "wb") as key_file:
        key_file.write(key)


def key_to_qr(key):
    """
    Create a qr code if the key.
    :param key: the key.
    :return: an image containing the qr code.
    """
    return create_qr(b64encode(key).decode('utf-8'))


def new_qr_key(location):
    """
    Crate a new key and store it at the given location.
    :param location:
    :return: an image of a qr code encoding the key.
    """
    key = generate_key()
    store_key(key, location)
    return key_to_qr(key)


def load_key(key_file):
    """
    Loads the key
    :param key_file: Location of the key
    :return: the key
    """
    return open(key_file, "rb").read()


def text_to_encrypted_qr(key_file, text):
    """
    Encrypt the text using the key from the given file. Returns a qr containing the encrypted text.
    :param key_file: location of the key
    :param text: text to encrypt.
    :return: a qr containing the encrypted text.
    """
    key = load_key(key_file)
    data = encrypt(text, key)
    return create_qr("mydata:" + data['combined'])


def create_qr(text):
    """
    Create a qr code that encodes the given text.
    :param text:
    :return: an image containing the qr code.
    """
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=5,
        border=4,
    )

    qr.add_data(text)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    return img


class Gui:
    def __init__(self, key_file, hide_input, encryption, auto_clear):
        self.auto_clear = auto_clear
        self.key_file = key_file
        self.encryption = encryption
        self.hide_input = hide_input
        self.clear_timer = None

        self.root = tk.Tk()
        self.content_frame = tk.Frame(self.root)
        self.content_frame.pack(padx=15, pady=10)
        self.menubar = tk.Menu(self.root)
        self.root.config(menu=self.menubar)
        self.create_top_menu()

        tk.Label(self.content_frame, text="QR text:").pack()

        self.text_input = tk.Entry(self.content_frame, width=25)
        self.text_input.pack()

        self.update_hide_input(self.hide_input)

        self.buttons_frame = tk.Frame(self.content_frame)
        self.buttons_frame.pack(fill=tk.X, expand=True, pady=10)
        tk.Button(self.buttons_frame,
                  text='Generate',
                  width=8,
                  command=self.generate_click).pack(side=tk.LEFT)
        tk.Button(self.buttons_frame,
                  text='Clear',
                  width=8,
                  command=self.clear_click).pack(side=tk.RIGHT)
        self.root.bind('<Return>', (lambda event: self.generate_click()))
        self.root.bind('<Escape>', (lambda event: self.clear_click()))
        self.img_label = tk.Label(self.root)
        self.img_label.pack()

        self.root.protocol("WM_DELETE_WINDOW", self.quit)

    def quit(self):
        self.update_clear_time(False)
        self.root.destroy()

    def update_hide_input(self, hide_input):
        """
        Set if the input should show the text or *
        :param hide_input: true if the input must show *
        :return:
        """
        self.hide_input = hide_input
        if hide_input:
            self.text_input.config(show="*")
        else:
            self.text_input.config(show="")

    def new_key_file(self):
        """
        Create a new key file, ask the user where to store it and show the qr code of the key.
        :return:
        """
        filename = fd.asksaveasfilename(initialdir="keys/", title="Save key file",
                                        initialfile="secret.key", defaultextension='.key',
                                        filetypes=(("key files", "*.key"), ("all files", "*.*")))
        self.key_file = filename
        self.show_image(new_qr_key(self.key_file))

    def select_key_file(self):
        """
        Let the user select a key file.
        :return:
        """
        filename = fd.askopenfilename(initialdir="keys", title="Select key file",
                                      filetypes=(("key files", "*.key"), ("all files", "*.*")))
        self.key_file = filename

    def set_encryption(self, encryption):
        """
        Set if encryption should be used
        :param encryption:
        :return:
        """
        self.encryption = encryption

    def create_top_menu(self):
        self.settings_menu = tk.Menu(self.menubar, tearoff=0)
        self.settings_menu.add_command(label="Load key", command=self.select_key_file)
        self.settings_menu.add_command(label="New key", command=self.new_key_file)
        self.settings_menu.add_separator()
        option_encryption = tk.BooleanVar()
        option_encryption.set(self.encryption)
        option_show_input = tk.BooleanVar()
        option_show_input.set(not self.hide_input)
        option_auto_clear = tk.BooleanVar()
        option_auto_clear.set(self.auto_clear)
        self.settings_menu.add_checkbutton(label="Encryption",
                                           command=lambda: self.set_encryption(option_encryption.get()),
                                           variable=option_encryption,
                                           onvalue=True, offvalue=False)
        self.settings_menu.add_checkbutton(label="Show input",
                                           command=lambda: self.update_hide_input(not (option_show_input.get())),
                                           variable=option_show_input,
                                           onvalue=True, offvalue=False)
        self.settings_menu.add_checkbutton(label="Auto clear after 10s",
                                           command=lambda: self.update_auto_clear(option_auto_clear.get()),
                                           variable=option_auto_clear,
                                           onvalue=True, offvalue=False)
        self.settings_menu.add_separator()
        self.settings_menu.add_command(label="Exit", command=self.quit)
        self.menubar.add_cascade(label="Settings", menu=self.settings_menu)

    def start(self):
        tk.mainloop()

    def generate_click(self):
        """
        Generate the qr code for the text and show the image.
        :return:
        """
        if self.encryption:
            img = text_to_encrypted_qr(self.key_file, self.text_input.get())
        else:
            img = create_qr(self.text_input.get())
        self.show_image(img)
        self.update_clear_time(self.auto_clear)

    def clear_click(self):
        """
        Clear the qr code and the input text.
        :return:
        """
        self.img_label.img = None
        self.img_label.config(image=self.img_label.img)
        self.text_input.delete(0, tk.END)
        self.update_clear_time(False)

    def show_image(self, image):
        """
        Set the image that must be shown
        :param image:
        :return:
        """
        img_t = ImageTk.PhotoImage(image)

        self.img_label.img = img_t
        self.img_label.config(image=self.img_label.img)

    def update_clear_time(self, state):
        """
        Enable or disable the clear timer
        :param state: true if the timer must be started, false if the timer must be canceled.
        :return:
        """
        if self.clear_timer is not None:
            self.clear_timer.cancel()

        if state:
            self.clear_timer = threading.Timer(10, self.clear_click)
            self.clear_timer.start()
        else:
            self.clear_timer = None

    def update_auto_clear(self, auto_clear):
        """
        Update the setting for autoclear. If needed start the timer.
        :param auto_clear:
        :return:
        """
        self.auto_clear = auto_clear
        if self.img_label.img is not None or auto_clear is False:
            self.update_clear_time(auto_clear)


def start_gui(key_file, hide_input, encryption, auto_clear, **kwargs):
    g = Gui(key_file, hide_input, encryption, auto_clear)
    g.start()


def print_help():
    print("""
Usage:
qr_generator [OPTIONS] [<text>]
qr_generator (--new-key | -n) [--no-qr] [<file>]
qr_generator --version | -v
qr_generator --help | -h
Options:
-k <file>, --key <file> Specify the keyfile that must be used.
-s, --show-input        Show the text that is typed as input for the generator. Otherwise it is threaded as a password.
-g, --gui               Launch the gui.     
-e, --no-encryption     Do not encrypt the text in the qr code.
-a, --auto-clear        Clear the qr code after 10 sec.

-n, --new-key           Generate a new key file.
--no-qr                 Do not show the qr code.

-v, --version           Display the version.
-h, --help              Display the usage.""")


def print_version():
    print("Encrypted qr generator: " + __VERSION)


def parse_new_key_usage(args, config):
    show_qr = True
    file_arg_index = 1
    if args.__len__() > 1 and args[1] == "--no-qr":
        show_qr = False
        file_arg_index = 2
    if args.__len__() > file_arg_index:
        config['key_file'] = args[file_arg_index]
    img = new_qr_key(config['key_file'])
    if show_qr:
        img.show()


def expand_combined_options(args):
    """
    Replace -abc with -a -b -c
    :param args:
    :return: the update args list
    """
    i = 0
    while i < args.__len__():
        if re.search("^-[a-zA-Z][a-zA-Z]+$", args[i]):
            group = args[i]
            args[i] = "-" + group[1]
            for j in range(2, group.__len__()):
                i += 1
                args.insert(i, "-" + group[j])
        i += 1
    return args


def split_assignment_options(args):
    """
    replace -a=b with -a b and --arg=b with --arg b
    :param args:
    :return: returns the updated arg list
    """
    i = 0
    p = re.compile('((-[a-zA-Z]=)|(--[a-zA-Z\-]+=))')
    while i < args.__len__():
        m = p.match(args[i])
        if m:
            e = m.end()
            option = args[i][:e - 1]
            value = args[i][e:]
            args[i] = option
            i += 1
            args.insert(i, value)
        i += 1
    return args


def handle_command_line(text_input, key_file, hide_input, encryption, auto_clear, **kwargs):
    """
    Do not start the gui and retrieve the text from the command line (or the arg).
    :param text_input:
    :param key_file:
    :param hide_input:
    :param encryption:
    :param auto_clear:
    :param kwargs:
    :return:
    """
    if text_input is None:
        if hide_input:
            text_input = getpass("Password: ")
        else:
            text_input = str(input("Data: "))
    if encryption:
        img = text_to_encrypted_qr(key_file, text_input)
    else:
        img = create_qr(text_input)

    if auto_clear:
        root = tk.Tk()
        img_label = tk.Label(root)
        img_t = ImageTk.PhotoImage(img)
        img_label.img = img_t
        img_label.config(image=img_label.img)
        img_label.pack()
        root.update()
        time.sleep(10)
        root.destroy()
    else:
        img.show()


def parse_normal_usage(args, config):
    """
    Parse the options
    :param args:
    :param config:
    :return:
    """
    args = expand_combined_options(args)
    args = split_assignment_options(args)

    i = 0
    while i < args.__len__():
        if args[i] == "--gui" or args[i] == "-g":
            config['gui'] = True
        elif args[i] == "--key" or args[i] == "-k":
            if i + 1 >= args.__len__():
                raise SystemExit("Missing file name; Usage -k file_name")
            config['key_file'] = args[i + 1]
            i += 1
        elif args[i] == "-s" or args[i] == "--show-input":
            config['hide_input'] = False
        elif args[i] == "-a" or args[i] == "--auto-clear":
            config['auto_clear'] = True
        elif args[i] == "-e" or args[i] == "--no-encryption":
            config['encryption'] = False
        elif i == args.__len__() - 1:
            config['text_input'] = args[i]
        else:
            raise SystemExit("Unexpected argument: " + args[i])
        i += 1
    if config['gui']:
        start_gui(**config)
    else:
        handle_command_line(**config)


def parse_usage(args, config):
    """
    Check if the usage is version, help, new-key or normal
    :param args:
    :param config:
    :return:
    """
    if args.__len__() > 0:
        if args[0] == "--version" or args[0] == "-v":
            print_version()
        elif args[0] == "--help" or args[0] == "-h":
            print_help()
        elif args[0] == "--new-key" or args[0] == "-n":
            parse_new_key_usage(args, config)
        else:
            parse_normal_usage(args, config)


def main():
    config = {
        'gui': False,
        'key_file': "keys/secret2.key",
        'hide_input': True,
        'text_input': None,
        'encryption': True,
        'auto_clear': False
    }
    parse_usage(sys.argv[1:], config)


if __name__ == "__main__":
    main()
