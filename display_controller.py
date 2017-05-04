#!/usr/bin/python
# coding=utf-8
# Python Version 2.7
# ------------------------------------------------------------

import signal
import sys
import time

# Library to control the 0,96" 128x64 OLED Display
import Adafruit_SSD1306
import psutil as psutil
from PIL import Image, ImageDraw, ImageFont


class DisplayController(object):
    """
    Main Display controller class for interfacing with the display
    """

    COLOR_MODE = '1'

    def __init__(self, rst_pin=24):
        """
        Creates a DisplayController object
        
        :param rst_pin: Raspberry Pi pin configuration:
        """

        # Display 128x64 display with hardware I2C:
        self._display = Adafruit_SSD1306.SSD1306_128_64(rst=rst_pin)

        # Initialize library.
        self._display.begin()

        self._image = self._get_clean_canvas()

        self.clear_canvas()

    def _get_clean_canvas(self):
        """
        :return: an empty canvas to draw on that fills the entire screen 
        """
        return Image.new(self.COLOR_MODE, (self.get_display_width(), self.get_display_height()))

    def clear_canvas(self, render=False):
        """
        Clears the current framebuffer
        
        :param render: if true renders a clear screen, otherwise only framebuffer 
        """

        # Create blank image for drawing.
        # Make sure to create image with mode '1' for 1-bit color.
        self._image = self._get_clean_canvas()

        # Clear display.
        self._display.clear()
        if render:
            self._display.display()

    def get_display_width(self):
        """
        :return: the display width in pixel 
        """
        return self._display.width

    def get_display_height(self):
        """
        :return: the display height in pixel 
        """
        return self._display.height

    def draw_rectangle(self, x, y, width, height, outline=True, fill=True):
        """
        Draws a reactangle
        
        :param x: X-Coordinate
        :param y: Y-Coordinate
        :param width: rectangle width 
        :param height: rectangle height
        :param outline: draw outline?
        :param fill: fill rectangle?
        """
        # Get drawing object to draw on image.
        draw = ImageDraw.Draw(self._image)

        # draw rectangle
        draw.rectangle((x, y, x + width, y + height), outline=outline, fill=fill)

    def draw_text(self, x, y, text, font=None, fill=True):
        """
        Draws the specified text on the screen
        
        :param x: X-Coordinate 
        :param y: Y-Coordinate
        :param text: Text
        :param font: Font (incl. size)
        :param fill: Fill amount?
        """
        if not font:
            font = self._get_default_font()

        # Get drawing object to draw on image.
        draw = ImageDraw.Draw(self._image)

        # Draw single line of text
        draw.text((x, y), text, font=font, fill=fill)

    def draw_time(self, x, y, font=None, fill=True):
        """
        Draws the current time to the specified coordinates
        
        :param x: X-Coordinate 
        :param y: Y-Coordinate
        :param font: Font (incl. size)
        :param fill: 
        """
        self.draw_text(x, y, self._get_current_time(), font=font, fill=fill)

    def draw_system_uptime(self, x, y, font=None, fill=True):
        """
        Draws the system uptime to the specified coordinates
        :param x: X-Coordinate 
        :param y: Y-Coordinate
        :param font: Font (incl. size)
        :param fill: 
        """

        def get_system_uptime():
            from datetime import timedelta

            with open('/proc/uptime', 'r') as f:
                uptime_seconds = float(f.readline().split()[0])
                return str(timedelta(seconds=uptime_seconds))[:-7]

        self.draw_text(x, y, get_system_uptime(), font=font, fill=fill)

    def draw_cpu_bars(self, x, y, bar_width=1, bar_height=10, padding=2, horizontal=False, percpu=False):
        """
        Draws a vertical bar for each CPU core.
        
        :param x: X-Coordinate to start drawing from 
        :param y: Y-Coordinate to start drawing from
        :param bar_width: width of a single core bar
        :param bar_height: hight of a single core bar
        :param padding: padding between bars in pixel
        :param horizontal: horizontal drawing?
        :param percpu: render one bar per core?
        """

        core_loads = psutil.cpu_percent(interval=1, percpu=percpu)

        for load in core_loads:
            if horizontal:
                self.draw_rectangle(x, y, load / 100 * bar_width, bar_height)
                y += bar_height + 1 + padding
            else:
                self.draw_rectangle(x, y, bar_width, load / 100 * bar_height)
                x += bar_width + 1 + padding

    def draw_service_status(self, x, y, services):
        """
        Draws a rectangle with a short name in it for each service.
        
        If the passed in service is NOT RUNNING 
        either because it is stopped or it has failed it will be drawn on screen.
        
        :param x: X-Coordinate to start drawing from 
        :param y: Y-Coordinate to start drawing from
        :param services: dictionary of {service_name: display_name} entries 
        """

        def get_service_status(service):
            from subprocess import call

            is_active = call(["systemctl", "-q", "is-active", str(service)]) == 0
            is_failed = call(["systemctl", "-q", "is-failed", str(service)]) == 0

            if is_failed:
                return "FAILED"

            if is_active:
                return "active"
            else:
                return "in-active"

        rect_width = 23
        rect_height = 13

        for service in services:
            status = get_service_status(service)
            name = services[service]

            if status == "FAILED":
                self.draw_rectangle(x, y, rect_width, rect_height, fill=False)
                self.draw_rectangle(x + 2, y + 2, rect_width - 4, rect_height - 4, fill=False)
                self.draw_text(x + 3, y + 1, name)
            elif status == "in-active":
                self.draw_rectangle(x, y, rect_width, rect_height, fill=False)
                self.draw_text(x + 3, y + 1, name)
            else:
                # dont draw it
                pass

            x += rect_width + 2

    def render_canvas(self):
        """
        Renders the current image stored in self._image
        """
        self._display.image(self._image)
        self._display.display()

    @staticmethod
    def _get_current_time():
        """
        :return: the current time 
        """
        t = time.localtime()
        hour, minute, second = t[3:6]
        return str(hour).zfill(2) + ":" + str(minute).zfill(2) + ":" + str(second).zfill(2)

    @staticmethod
    def _get_current_date():
        """
        :return: the current date 
        """
        t = time.localtime()
        year, month, day = t[0:3]
        return str(day).zfill(2) + "." + str(month).zfill(2) + "." + str(year)

    @staticmethod
    def _get_default_font():
        """
        :return: the default font 
        """
        return ImageFont.load_default()


"""
DEMO SCRIPT
"""


def signal_handler(signal, frame):
    """
    "CTRL+C" Handler.
    Clears the screen when exiting the program using the ctrl+c keyboard shortcut.
    """
    controller.clear_canvas(True)
    sys.exit(0)


# register a ctrl+c handler
signal.signal(signal.SIGINT, signal_handler)

# create a display controller
controller = DisplayController()

# draw to the screen indefinitely
while True:
    # create a new canvas
    controller.clear_canvas()

    x = 2
    y = 2

    # draw to the canvas

    # controller.draw_time(x, y)

    controller.draw_system_uptime(x, y)

    y = 20
    controller.draw_service_status(x, y, {
        "nginx.service": "NGX",
        "home-assistant.service": "HAS",
        "grafana-server.service": "GRA",
        "pyload.service": "PYL",
        "raspyrfm.service": "RPY"
    })

    # font = ImageFont.truetype("font/enhanced_dot_digital-7.ttf", 12)  # font, size

    # controller.draw_rectangle(0,
    #                           y,
    #                           controller.get_display_width() - 1,
    #                           controller.get_display_height() - 1 - y,
    #                           fill=False)

    y = 40
    controller.draw_cpu_bars(x,
                             y,
                             controller.get_display_width() - 1 - 2,
                             3,
                             padding=1,
                             horizontal=True,
                             percpu=True)

    # and finally render the canvas
    controller.render_canvas()

    # time.sleep(0.2)
