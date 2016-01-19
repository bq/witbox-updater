# coding=utf-8

__author__ = "Nicanor Romero Venier <nicanor.romerovenier@bq.com>"


import os
from Tkinter import *
from Tkinter import _setit
import ttk
import tkFont
import logging
import logging.handlers
import platform
import serial
import serial.tools.list_ports
import urllib
import urllib2
import urlparse
import requests
import json
import tempfile
import threading
import sarge
import Image, ImageTk


class FirmwareUpdaterApp():

    def __init__(self, simulate_flashing):
        # Init Loggers
        self.logger = logging.getLogger("Logger")
        self._init_loggers()

        self.simulate_flashing = simulate_flashing

        self.ws_unformatted_url = "http://devices.bq.com/api/checkUpdate3D/{model}/{language}/{version}"

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
        w = 500
        h = 240
        screen_w = self.top.winfo_screenwidth()
        screen_h = self.top.winfo_screenheight()
        self.top.geometry("%dx%d+%d+%d" % (w, h, screen_w/2-w/2, screen_h/2-h/2))
        self.top.resizable(0,0)
        self.top.title("BQ - 3D Printers Firmware Updater")

        if platform.system() == "Linux":
            img = PhotoImage(file=os.path.join(self._get_resources_path(), "images", "64_border.png"))
            self.top.tk.call('wm','iconphoto', self.top._w, img)
        if platform.system() == "Windows":
            self.top.wm_iconbitmap(bitmap=os.path.join(self._get_resources_path(), "images", "64_border.png"))
        self.top.protocol("WM_DELETE_WINDOW", self._clean_exit)

        # Fonts
        self.f_title = tkFont.Font(family="Tahoma", size=-22, weight="bold")
        self.f_label = tkFont.Font(family="Tahoma", size=-16)
        self.f_combobox = tkFont.Font(family="Tahoma", size=-12)
        self.f_button = tkFont.Font(family="Tahoma", size=-12)
        self.f_middle_label_1 = tkFont.Font(family="Tahoma", size=-12)
        self.f_middle_label_2 = tkFont.Font(family="Tahoma", size=-12, weight="bold")
        self.f_label_bottom = tkFont.Font(family="Tahoma", size=-12)

        # Frames
        self.left_frame = Frame(width=140, height=240)
        self.right_frame = Frame(width=30, height=240)
        
        self.top_frame = Frame(width=330, height=78)
        self.middle_frame_1 = Frame(width=330, height=70)
        self.middle_frame_2 = Frame(width=330, height=34)
        self.bottom_frame = Frame(width=330, height=58)

        # Widgets

        # ** Left frame
        bq_logo_im = ImageTk.PhotoImage(Image.open(os.path.join(self._get_resources_path(), "images", "bq_logo.png")))
        self.g_bq_logo = Label(self.left_frame, image=bq_logo_im)

        # ** Top frame
        self.g_title = Label(self.top_frame, font=self.f_title, anchor=W, justify=LEFT, text="Firmware updater")
        self.g_title_separator = Frame(self.top_frame, height=2, bd=1, relief=SUNKEN)

        # ** Middle frame 1
        self.g_serial_port_label = Label(self.middle_frame_1, font=self.f_label, anchor=W, justify=LEFT, text="Printer serial port")
        self.serial_port_default_value = "Select a port"
        self.g_serial_port_combobox_v = StringVar(self.middle_frame_1)
        self.g_serial_port_combobox = ttk.Combobox(self.middle_frame_1, font=self.f_combobox, textvariable=self.g_serial_port_combobox_v, values=[self.serial_port_default_value], state="readonly")

        # ** Middle frame 2
        self.g_check_for_updates_button = Button(self.middle_frame_2, text="Connect to device", font=self.f_button, relief=GROOVE, bd=2)
        self.valid_icon = ImageTk.PhotoImage(Image.open(os.path.join(self._get_resources_path(), "images", "icon_valid.png")))
        self.warning_icon = ImageTk.PhotoImage(Image.open(os.path.join(self._get_resources_path(), "images", "icon_warning.png")))
        self.download_icon = ImageTk.PhotoImage(Image.open(os.path.join(self._get_resources_path(), "images", "icon_download.png")))
        self.g_status_icon = Label(self.middle_frame_2)
        self.g_middle_frame_2_label_1_v = StringVar(self.middle_frame_2)
        self.g_middle_frame_2_label_1 = Label(self.middle_frame_2, font=self.f_middle_label_1, textvariable=self.g_middle_frame_2_label_1_v)
        self.g_middle_frame_2_label_2_v = StringVar(self.middle_frame_2)
        self.g_middle_frame_2_label_2 = Label(self.middle_frame_2, font=self.f_middle_label_2, anchor=W, justify=LEFT, textvariable=self.g_middle_frame_2_label_2_v)
        self.printer_default_value = "Select printer"
        printers_list = [self.printer_default_value, "Witbox 2", "Hephestos 2"]
        self.g_printer_combobox_v = StringVar(self.middle_frame_2)
        self.g_printer_combobox = ttk.Combobox(self.middle_frame_2, font=self.f_combobox, textvariable=self.g_printer_combobox_v, values=printers_list, state="readonly")        

        # ** Bottom frame
        self.g_update_button = Button(self.bottom_frame, text="Update Firmware", font=self.f_button, relief=GROOVE, bd=2)
        self.g_manually_update_button = Button(self.bottom_frame, text="Update Firmware", font=self.f_button, relief=GROOVE, bd=2)
        self.g_bottom_frame_label_v = StringVar(self.bottom_frame)
        self.g_bottom_frame_label = Label(self.bottom_frame, font=self.f_label_bottom, textvariable=self.g_bottom_frame_label_v)
        s = ttk.Style()
        s.theme_use('clam')
        s.configure("custom.Horizontal.TProgressbar", foreground='#D5075E', background='#D5075E')
        self.g_progress_bar = ttk.Progressbar(self.bottom_frame, style="custom.Horizontal.TProgressbar", orient='horizontal', mode='indeterminate')
        if platform.system() == "Windows":
            self.progress_bar_speed = 2
        elif platform.system() == "Linux":
            self.progress_bar_speed = 7
        self.g_retry_check_button = Button(self.bottom_frame, text="Retry", font=self.f_button, relief=GROOVE, bd=2)
        self.g_exit_button = Button(self.bottom_frame, text="Exit", font=self.f_button, relief=GROOVE, bd=2)


        # GUI frames placement
        self.left_frame.pack(side=LEFT)
        self.left_frame.pack_propagate(False)
        self.right_frame.pack(side=RIGHT)
        self.right_frame.pack_propagate(False)
        self.top_frame.pack(side=TOP)
        self.top_frame.pack_propagate(False)
        self.middle_frame_1.pack(side=TOP)
        self.middle_frame_1.pack_propagate(False)
        self.middle_frame_2.pack(side=TOP)
        self.middle_frame_2.pack_propagate(False)
        self.bottom_frame.pack(side=TOP)
        self.bottom_frame.pack_propagate(False)
        

        # GUI elements placement

        # ** Left frame
        self.g_bq_logo.pack(side=TOP, padx=40, pady=38)

        # ** Top frame
        self.g_title_separator.pack(side=BOTTOM, fill=X)
        self.g_title.pack(side=BOTTOM, fill=X, pady=8)
        
        # ** Middle frame
        self.g_serial_port_label.pack(side=LEFT)
        self.g_serial_port_combobox.pack(side=RIGHT, fill=Y, pady=18)

        # ** Middle button frame
        self.g_check_for_updates_button.pack(side=BOTTOM, fill=BOTH, expand=1)

        # ** Bottom frame
        self.g_bottom_frame_label.pack(side=LEFT, fill=X, expand=1)

        # GUI bindings
        self.g_check_for_updates_button.config(command=self.check_for_updates)
        self.g_retry_check_button.config(command=self.check_for_updates)
        self.g_exit_button.config(command=self._clean_exit)
        self.g_update_button.config(command=self.update_firmware)
        self.g_manually_update_button.config(command=self.manually_update_firmware)
        self.g_serial_port_combobox.bind("<Button-1>", self._update_serial_port_combobox)
        self.top.bind("<<go_to_update_available>>", self._update_available)
        self.top.bind("<<go_to_update_firmware>>", self.update_firmware)
        self.top.bind("<<go_to_up_to_date>>", self._up_to_date)
        self.top.bind("<<go_to_connection_error>>", self._connection_error)
        self.top.bind("<<go_to_unknown_device>>", self._unknown_device)
        self.top.bind("<<go_to_flash_firmware>>", self._flash_firmware)
        self.top.bind("<<go_to_flashing_successful>>", self._flashing_successful)
        self.top.bind("<<go_to_flashing_error>>", self._flashing_error)
        self.top.bind("<<go_to_update_serial_port_combobox>>", self._update_serial_port_combobox)
        self.g_serial_port_combobox_v.trace("w", self._serial_port_combobox_changed)
        self.g_printer_combobox_v.trace("w", self._printer_combobox_changed)

        # Give value to the comboboxes and make the buttons refresh themselves
        self._update_serial_port_combobox()
        if len(self._get_serial_port_combobox_values()) == 2:
            self.g_serial_port_combobox_v.set(self._get_serial_port_combobox_values()[1])
        else:
            self.g_serial_port_combobox_v.set(self.serial_port_default_value)

        self.g_printer_combobox_v.set(self.printer_default_value)

        # Launch thread to listen to new serial port connections
        self._stop_checking_serial_port_connections = False
        check_serial_port_connections_thread = threading.Thread(target=self._check_serial_port_connections)
        check_serial_port_connections_thread.daemon = False
        check_serial_port_connections_thread.start()

        # Start GUI
        try:
            self.top.mainloop()
        except KeyboardInterrupt:
            self._clean_exit()
    
    def _check_serial_port_connections(self):
        while not self._stop_checking_serial_port_connections:
            try:
                serial_ports = [str(port)[str(port).find('(')+1:str(port).find(')')] for port in serial.tools.list_ports.comports()]
                if len(serial_ports) == 1 and self.g_serial_port_combobox_v.get() != serial_ports[0]:
                    self.g_serial_port_combobox_v.set(serial_ports[0])
                elif len(serial_ports) == 0 and self.g_serial_port_combobox_v.get() != self.serial_port_default_value:
                    self.g_serial_port_combobox_v.set(self.serial_port_default_value)
            except:
                self.logger.exception("Unable to check new serial port connections")
        return
  
    def check_for_updates(self):
        # Check if ready to check for updates
        if self.g_serial_port_combobox_v.get() not in self._get_serial_ports():
            self.logger.info("Invalid serial port")
            return
        self._stop_checking_serial_port_connections = True

        self._show_gui_as_busy()
        self.g_check_for_updates_button.pack_forget()
        self.g_bottom_frame_label.pack_forget()
        self.g_retry_check_button.pack_forget()
        self.g_status_icon.pack_forget()
        self.g_progress_bar.stop()

        self.g_serial_port_combobox.config(state="disabled")
        self.g_middle_frame_2_label_1_v.set("Connecting to printer...")
        self.g_middle_frame_2_label_1.pack(side=LEFT, fill=X, expand=1)
        self.g_progress_bar.pack(side=TOP, fill=X, expand=1)
        self.g_progress_bar.start(self.progress_bar_speed)

        check_update_thread = threading.Thread(target=self._check_for_updates)
        check_update_thread.daemon = False
        check_update_thread.start()

        return

    def _check_for_updates(self):
        try:
            # Connect to printer
            self.printer_serial_port = self.g_serial_port_combobox_v.get()
            
            self.ser = serial.Serial(port=self.printer_serial_port,\
                                     baudrate=115200,\
                                     parity=serial.PARITY_NONE,\
                                     stopbits=serial.STOPBITS_ONE,\
                                     bytesize=serial.EIGHTBITS,\
                                     timeout=1)

            self.logger.debug("Connected to printer.")

            # Wait for printer to start up
            response = self.ser.readline().strip()
            while "SD card ok" not in response and "SD init fail" not in response:
                self.logger.debug("Got: %s" % response)
                response = self.ser.readline().strip()

            self.logger.debug("Got: %s" % response)

            # Send M115 to get the printers info
            self.logger.debug("Sending M115...")
            self.ser.write("M115\n")
            self.logger.debug("M115 sent.")

            # Get response from printer
            self.logger.debug("Waiting for M115 response...")
            response = self.ser.readline().strip()
            while response == "" or response == "ok" or "SD" in response:
                self.logger.debug("Got: %s" % response)
                response = self.ser.readline().strip()
                
            self.logger.debug("Got response from printer: %s" % response)

            # Disconnect from printer
            self.ser.close()

        except:
            self.logger.exception("Error while communicating with printer")
            self.top.event_generate("<<go_to_unknown_device>>", when="tail")
            return

        # Parse response
        self.printer_info = dict()
        for pair in response.split(" "):
            try:
                self.printer_info[pair.split(":")[0]] = pair.split(":")[1]
            except:
                self.logger.error("Unable to parse pair from M115 response")

        if "FIRMWARE_VERSION" not in self.printer_info.keys() or "MACHINE_TYPE" not in self.printer_info.keys(): # TOERASE - for testing
            self.logger.debug("Insufficient data in M115 response to recognize device")
            self.update_info = None
            self.top.event_generate("<<go_to_unknown_device>>", when="tail")
            return

        # Construct request for Kiton server
        if self.printer_info["X-FIRMWARE_LANGUAGE"] == "":
            self.printer_info["X-FIRMWARE_LANGUAGE"] = "en"
        printer_model = urllib.quote(self.printer_info["MACHINE_TYPE"])
        fw_version = urllib.quote(self.printer_info["FIRMWARE_VERSION"])
        fw_version = "1.9.9" # TOERASE - for testing
        fw_language = urllib.quote(self.printer_info["X-FIRMWARE_LANGUAGE"])
        ws_url = self.ws_unformatted_url.format(model=printer_model, language=fw_language, version=fw_version)

        self.logger.debug(ws_url)

        # Send request to Kiton server
        self.logger.debug("Sending request to Kiton server...")
        try:
            ws_response = requests.get(ws_url)
        except:
            self.logger.exception("Unable to connect to update server.")
            self.top.event_generate("<<go_to_connection_error>>", when="tail")
            return

        if ws_response.status_code != 200:
            self.logger.error("Unable to connect to update server: Got status code %s" % ws_response.status_code)
            self.top.event_generate("<<go_to_connection_error>>", when="tail")
            return

        # Get response from Kiton server
        self.update_info = ws_response.json()
        if self.update_info["available"]:
            self.logger.info("Firmware update available (FW version: %s)" % self.update_info["ota"]["version"])
            self.logger.debug("Printer model: %s\nCurrent version: %s\nNew version: %s" % (self.printer_info["MACHINE_TYPE"].replace("_", " "), 
                                                                                           self.printer_info["FIRMWARE_VERSION"],
                                                                                           self.update_info["ota"]["version"]))
            self.top.event_generate("<<go_to_update_available>>", when="tail")
            return

        else:            
            self.logger.info("Firmware is up to date")
            self.top.event_generate("<<go_to_up_to_date>>", when="tail")
            return

    def _update_available(self, e=None):
        self.logger.debug("_update_available")
        
        self.g_status_icon.config(image=self.download_icon)
        self.g_middle_frame_2_label_1_v.set(self.printer_info["MACHINE_TYPE"].replace("_", " "))
        self.g_middle_frame_2_label_2_v.set("(%s version available)" % self.update_info["ota"]["version"])

        self.g_progress_bar.pack_forget()
        self.g_middle_frame_2_label_1.pack_forget()

        self.g_status_icon.pack(side=LEFT)
        self.g_middle_frame_2_label_1.pack(side=LEFT, fill=X, expand=1)
        self.g_middle_frame_2_label_2.pack(side=RIGHT)
        self.g_update_button.pack(side=LEFT, fill=X, expand=1)

        self._show_gui_as_normal()
        return

    def _up_to_date(self, e=None):
        self.logger.debug("_up_to_date")

        self.g_status_icon.config(image=self.valid_icon)
        self.g_middle_frame_2_label_1_v.set(self.printer_info["MACHINE_TYPE"].replace("_", " "))
        self.g_middle_frame_2_label_2_v.set("(Device is up to date)")

        self.g_progress_bar.pack_forget()
        self.g_middle_frame_2_label_1.pack_forget()

        self.g_status_icon.pack(side=LEFT)
        self.g_middle_frame_2_label_1.pack(side=LEFT)
        self.g_middle_frame_2_label_2.pack(side=LEFT)
        
        self._show_gui_as_normal()
        return

    def _connection_error(self, e=None):
        self.logger.debug("_connection_error")

        self.g_status_icon.config(image=self.warning_icon)
        self.g_middle_frame_2_label_1_v.set("Network connection error")

        self.g_progress_bar.pack_forget()
        self.g_middle_frame_2_label_1.pack_forget()
        self.g_printer_combobox.pack_forget()
        self.g_manually_update_button.pack_forget()

        self.g_status_icon.pack(side=LEFT)
        self.g_middle_frame_2_label_1.pack(side=LEFT, fill=X, expand=1)
        self.g_retry_check_button.pack(side=LEFT, fill=X, expand=1)

        self._show_gui_as_normal()
        return

    def _unknown_device(self, e=None):
        self.logger.debug("_unknown_device")
        
        self.g_status_icon.config(image=self.warning_icon)
        self.g_middle_frame_2_label_1_v.set("Unknown device")

        self.g_progress_bar.pack_forget()
        self.g_middle_frame_2_label_1.pack_forget()

        self.g_status_icon.pack(side=LEFT)
        self.g_middle_frame_2_label_1.pack(side=LEFT, fill=X, expand=1)
        self.g_printer_combobox.pack(side=RIGHT, fill=Y)
        self.g_manually_update_button.pack(side=LEFT, fill=X, expand=1)

        self._show_gui_as_normal()
        return

    def update_firmware(self, e=None):
        self._show_gui_as_busy()
        self.g_status_icon.pack_forget()
        self.g_middle_frame_2_label_1.pack_forget()
        self.g_middle_frame_2_label_2.pack_forget()
        self.g_update_button.pack_forget()
        self.g_progress_bar.stop()

        self.g_middle_frame_2_label_1.pack(side=LEFT, fill=X, expand=1)
        self.g_middle_frame_2_label_1_v.set("(1/3) Downloading new firmware...")
        self.g_progress_bar.pack(side=TOP, fill=X, expand=1)
        self.g_progress_bar.start(self.progress_bar_speed)

        # Flash firmware using avrdude
        download_firmware_thread = threading.Thread(target=self._download_firmware)
        download_firmware_thread.daemon = False
        download_firmware_thread.start()

        return

    def manually_update_firmware(self):
        self._show_gui_as_busy()
        self.g_manually_update_button.pack_forget()
        self.g_bottom_frame_label.pack_forget()
        self.g_retry_check_button.pack_forget()
        self.g_status_icon.pack_forget()
        self.g_printer_combobox.pack_forget()
        self.g_progress_bar.stop()

        self.g_serial_port_combobox.config(state="readonly")
        self.g_middle_frame_2_label_1_v.set("Updating firmware...")
        self.g_middle_frame_2_label_1.pack(side=LEFT, fill=X, expand=1)
        self.g_progress_bar.pack(side=TOP, fill=X, expand=1)
        self.g_progress_bar.start(self.progress_bar_speed)

        manually_update_thread = threading.Thread(target=self._manually_update_firmware)
        manually_update_thread.daemon = False
        manually_update_thread.start()

        return

    def _manually_update_firmware(self):
        # Build URL manually
        self.printer_info = dict()
        self.printer_info["MACHINE_TYPE"] = self.g_printer_combobox_v.get().replace(" ", "_")

        printer_model = self.printer_info["MACHINE_TYPE"]
        fw_language = "en"
        fw_version = "no_version"
        ws_url = self.ws_unformatted_url.format(model=printer_model, language=fw_language, version=fw_version)

        self.logger.debug(ws_url)

        # Send request to Kiton server
        self.logger.debug("Sending request to Kiton server...")
        try:
            ws_response = requests.get(ws_url)
        except:
            self.logger.exception("Unable to connect to update server.")
            self.top.event_generate("<<go_to_connection_error>>", when="tail")
            return

        if ws_response.status_code != 200:
            self.logger.error("Unable to connect to update server: Got status code %s" % ws_response.status_code)
            self.top.event_generate("<<go_to_connection_error>>", when="tail")
            return

        # Get response from Kiton server
        self.update_info = ws_response.json()
        if self.update_info["available"]:
            self.logger.info("Firmware update available (FW version: %s)" % self.update_info["ota"]["version"])
            self.logger.debug("Printer model: %s\nNew version: %s" % (self.printer_info["MACHINE_TYPE"].replace("_", " "),
                                                                      self.update_info["ota"]["version"]))
            self.top.event_generate("<<go_to_update_firmware>>", when="tail")
            return

        else:            
            self.logger.error("Unable to force firmware update")
            self.top.event_generate("<<go_to_connection_error>>", when="tail")
            return

    def _download_firmware(self):
        self.temp_hex_file_path = os.path.join(self._get_resources_path(), "firmware.hex")
        try:
            urllib.urlretrieve(self.update_info["ota"]["url"], self.temp_hex_file_path)
        except:
            self.logger.exception("Unable to retrieve hex file from url")
            self.top.event_generate("<<go_to_connection_error>>", when="tail")
            return
        
        self.logger.debug("Firmware downloaded successfully")
        self.top.event_generate("<<go_to_flash_firmware>>", when="tail")
        return

    def _flash_firmware(self, e=None):
        self.g_middle_frame_2_label_1_v.set("(2/3) Flashing new firmware...")
        self.g_progress_bar.stop()
        self.g_progress_bar.start(self.progress_bar_speed)

        # Flash firmware using avrdude
        flash_thread = threading.Thread(target=self._flash_worker)
        flash_thread.daemon = False
        flash_thread.start()

        return

    def _flash_worker(self):

        if platform.system() == "Windows":
            avrdude_filename = "avrdude.exe"
        elif platform.system() == "Linux":
            avrdude_filename = "avrdude"

        avrdude_path = os.path.join(self._get_resources_path(), "utils", avrdude_filename)
        working_dir = os.path.dirname(os.path.abspath(avrdude_path))
        hex_path = os.path.abspath(self.temp_hex_file_path)
        avrdude_command = [avrdude_path, "-v", "-p", "m2560", "-c", "wiring", "-P", self.printer_serial_port, "-U", "flash:w:" + hex_path + ":i", "-D"]

        self.logger.debug("Running %r in %s" % (' '.join(avrdude_command), working_dir))

        try:
            if not self.simulate_flashing:
                p = sarge.run(avrdude_command, cwd=working_dir, async=True, stdout=sarge.Capture(), stderr=sarge.Capture())
                p.wait_events()

                while p.returncode is None:
                    line = p.stderr.read(timeout=0.5)
                    if not line:
                        p.commands[0].poll()
                        continue
            
                    self.logger.debug(line)
            
                    if avrdude_filename + ": writing flash" in line:
                        self.logger.info("Writing memory...")
            
                    elif avrdude_filename + ": reading" in line:
                        self.logger.info("Reading memory...")
                        self.g_middle_frame_2_label_1_v.set("(3/3) Verifying new firmware...")
                        self.top.update()

                    elif avrdude_filename + ": verifying ..." in line:
                        self.logger.info("Verifying memory...")
            
                    elif "timeout communicating with programmer" in line:
                        e_msg = "Timeout communicating with programmer"
                        raise AvrdudeException
            
                    elif "avrdude: ERROR:" in line:
                        e_msg = "AVRDUDE error: " + line[line.find("avrdude: ERROR:")+len("avrdude: ERROR:"):].strip()
                        raise AvrdudeException

                if p.returncode == 0:
                    self.logger.info("Flashing successful.")
                    self.top.event_generate("<<go_to_flashing_successful>>", when="tail")
                else:
                    e_msg = "Avrdude returned code {returncode}".format(returncode=p.returncode)
                    raise AvrdudeException
            else:
                import time
                time.sleep(1)
                self.logger.warning("Flashing simulated.")
                self.top.event_generate("<<go_to_flashing_successful>>", when="tail")

        except AvrdudeException:
            self.logger.error("Flashing failed: %s." % e_msg)
            self.top.event_generate("<<go_to_flashing_error>>", when="tail")
        except:
            self.logger.exception("Flashing failed. Unexpected error.")
            self.top.event_generate("<<go_to_flashing_error>>", when="tail")

        finally:
            try:
                os.remove(hex_path)
            except:
                self.logger.exception("Unable to delete temp hex file")

        return

    def _flashing_successful(self, e=None):
        self.logger.debug("Flashing successful")

        self.g_status_icon.config(image=self.valid_icon)
        self.g_middle_frame_2_label_1_v.set(self.printer_info["MACHINE_TYPE"].replace("_", " "))
        self.g_middle_frame_2_label_2_v.set("(Device updated successfully)")

        self.g_progress_bar.pack_forget()
        self.g_middle_frame_2_label_1.pack_forget()

        self.g_status_icon.pack(side=LEFT)
        self.g_middle_frame_2_label_1.pack(side=LEFT, fill=X, expand=1)
        self.g_middle_frame_2_label_2.pack(side=RIGHT)
        self.g_exit_button.pack(side=LEFT, fill=X, expand=1)

        self._show_gui_as_normal()
        return

    def _flashing_error(self, e=None):
        self.logger.debug("Flashing error")
        self.g_bottom_frame_label_v.set("Flashing error")
        self._show_gui_as_normal()


    # Auxiliar methods

    def _get_resources_path(self):
        try:
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")
        return base_path

    def _show_gui_as_normal(self):
        if platform.system() == "Windows":
            self.top.config(cursor="")
        self.g_check_for_updates_button.config(state="normal")
        self.g_update_button.config(state="normal")
        self.g_printer_combobox.config(state="readonly")
        self.top.update()

    def _show_gui_as_busy(self):
        if platform.system() == "Windows":
            self.top.config(cursor="wait")
        self.g_check_for_updates_button.config(state="disabled")
        self.g_update_button.config(state="disabled")
        self.g_printer_combobox.config(state="disabled")
        self.top.update()

    def _update_serial_port_combobox(self, e=None):
        new_options = self._get_serial_ports()
        if new_options == self._get_serial_port_combobox_values():
            return
        else:
            self.g_serial_port_combobox.config(values=new_options)
        return

    def _get_serial_ports(self):
        if platform.system() == "Windows":
            return [self.serial_port_default_value] + [str(port)[str(port).find('(')+1:str(port).find(')')] for port in serial.tools.list_ports.comports()]
        elif platform.system() == "Linux":
            return [self.serial_port_default_value] + [ p[0] for p in serial.tools.list_ports.comports() if p[-1] != "n/a"]
        else:
            self.logger.error("OS not recognized")
            return

    def _serial_port_combobox_changed(self, *args):
        if self.g_serial_port_combobox_v.get() != self.serial_port_default_value:
            self.g_check_for_updates_button.config(state="normal")
        else:
            self.g_check_for_updates_button.config(state="disabled")

    def _printer_combobox_changed(self, *args):
        if self.g_printer_combobox_v.get() != self.printer_default_value:
            self.g_manually_update_button.config(state="normal")
        else:
            self.g_manually_update_button.config(state="disabled")

    def _get_serial_port_combobox_values(self):
        return list(self.g_serial_port_combobox.config("values")[-1])

    def _clean_exit(self):
        self.logger.info("Exiting.")
        self._stop_checking_serial_port_connections = True
        try:
            self.ser.close()
        except:
            pass
        try:
            exit(0)
        except:
            pass
        try:
            self.top.destroy()
        except:
            pass



class AvrdudeException(Exception):
    pass 

if __name__ == '__main__':

    if "simulate_flashing" in sys.argv:
        simulate_flashing = True
    else:
        simulate_flashing = False

    main = FirmwareUpdaterApp(simulate_flashing)
    main.start_gui()