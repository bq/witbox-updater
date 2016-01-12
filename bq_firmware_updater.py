# coding=utf-8

__author__ = "Nicanor Romero Venier <nicanor.romerovenier@bq.com>"


import os
from Tkinter import *
from Tkinter import _setit
import logging
import logging.handlers
import platform



class FirmwareUpdaterApp():

    def __init__(self):
        # Init Loggers
        self.logger = logging.getLogger("Logger")
        self._init_loggers()

    def _init_loggers(self):
        logging_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging_formatter)
        console_handler.setLevel(logging.DEBUG)
        self.logger.addHandler(console_handler)

        self.logger.setLevel(logging.DEBUG)
        rot_handler = logging.handlers.RotatingFileHandler("bq_firmware_updater.log", maxBytes=10*1024*1024, backupCount=10)
        rot_handler.setFormatter(logging_formatter)
        rot_handler.setLevel(logging.DEBUG)
        self.logger.addHandler(rot_handler)

    def start_gui(self):

        # Main Window
        self.top = Tk()
        w = 360
        h = 480
        self.top.geometry("%dx%d+%d+%d" % (w, h, 0, 0))
        self.top.resizable(0,0)
        self.top.title("BQ - 3D Printers Firmware Updater")

        # GUI elements
        self.gui_title = Label(self.top, font=('Verdana', '20', 'bold'), text="Firmware Updater")
        self.gui_title_line = Frame(height=2, bd=1, relief=SUNKEN)
        self.gui_printer_title = Label(self.top, font=('Verdana', '14', 'bold'), anchor=W, text="Printer Serial Port")
        self.gui_printer_option_v = StringVar(self.top)
        self.gui_printer_option_list = ["Select serial port"]
        self.gui_printer_option_v.set(self.gui_printer_option_list[0])
        self.gui_printer_option = OptionMenu(self.top, self.gui_printer_option_v, *self.gui_printer_option_list)
        self.gui_check_for_updates_button = Button(self.top, text="Check for Updates", font=("Helvetica", 14, "bold"), height=4)
        self.gui_state_text_v = StringVar(self.top)
        self.gui_state_text = Label(self.top, font=("Helvetica", 14, "bold"), textvariable=self.gui_state_text_v, height=4)


        # GUI bindings
        self.gui_check_for_updates_button.config(command=self.check_for_updates)

        # GUI elements placement
        self.gui_title.pack(side=TOP, fill=X, pady=20)
        self.gui_title_line.pack(side=TOP, fill=X, padx=10)
        self.gui_printer_title.pack(side=TOP, fill=X, padx=10, pady=20)
        self.gui_printer_option.pack(side=TOP, fill=X, padx=10, pady=5)
        self.gui_check_for_updates_button.pack(side=BOTTOM, fill=X, padx=10, pady=10)


        self.gui_printer_option_list += ["COM1", "COM2", "COM3"]
        self._refresh_printer_option_list()
        

        # Start GUI
        try:
            self.top.mainloop()
        except KeyboardInterrupt:
            self._clean_exit()

    def _clean_exit(self):
        self.logger.info("Exiting.")
        try:
            exit(0)
        except:
            pass
        try:
            self.top.destroy()
        except:
            pass

    def _refresh_printer_option_list(self):
        self.gui_printer_option['menu'].delete(0, 'end')
        for option in self.gui_printer_option_list:
            self.gui_printer_option["menu"].add_command(label=option, command=_setit(self.gui_printer_option_v, option))
        return

    def check_for_updates(self):
        self.gui_check_for_updates_button.pack_forget()
        self.gui_state_text_v.set("Checking for updates...")
        self.gui_state_text.pack(side=BOTTOM, fill=X, padx=10, pady=10)
        if platform.system() == "Windows":
            self.top.config(cursor="wait")
        self.top.update()



if __name__ == '__main__':

    main = FirmwareUpdaterApp()
    main.start_gui()