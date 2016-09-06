#!/usr/bin/python
# -*- coding: utf-8 -*-

''' 
 ESC-POS Server Print - a web service for print using ESC-POS.

 You may use any  Server Print project under the terms
 of the GNU General Public License (GPL) Version 3.

 (c) 2016 Emilio Mariscal (emi420 [at] gmail.com)
 
 Module description:
 
    Server Print 
    
    Simple web server for print using ESC-POS.
 
'''

from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import os
from PIL import Image, ImageDraw, ImageFont
from urlparse import urlparse, parse_qs
import textwrap
import serial
import time
import image
import six

# Set to false if you want to test the image without printing
DEBUG = False

PORT = 8001

SERIAL = '/dev/ttyUSB0'
SPEED = 38400
DENSITY = 3

H1_FONT = ImageFont.truetype("OpenSans-Bold.ttf", 70)
H2_FONT = ImageFont.truetype("OpenSans-Regular.ttf", 30)
P_FONT = ImageFont.truetype("OpenSans-Regular.ttf", 23)
TMP_FILE = "page.png"
LOGO_FILE = "logo.png"
W = 300
GS = b'\x1d'


def _int_low_high(inp_number, out_bytes):
    """ 
    Generate multiple bytes for a number: In lower and higher parts, or more parts as needed.
    Function from python-escpos library (https://github.com/python-escpos/python-escpos)

    :param inp_number: Input number
    :param out_bytes: The number of bytes to output (1 - 4).
    """
    max_input = (256 << (out_bytes * 8) - 1)
    if not 1 <= out_bytes <= 4:
        raise ValueError("Can only output 1-4 bytes")
    if not 0 <= inp_number <= max_input:
        raise ValueError("Number too large. Can only output up to {0} in {1} bytes".format(max_input, out_bytes))
    outp = b''
    for _ in range(0, out_bytes):
        outp += six.int2byte(inp_number % 256)
        inp_number //= 256
    return outp


'''
APIServer create a simple web server to generate and print images
'''
class APIServer(BaseHTTPRequestHandler):

    def do_GET(self):
               
        mime = "text/html"

        self.send_response(200)
        self.send_header("Content-type", mime)
        self.send_header('Allow', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()

        height = 150

        imgtmp = Image.new("RGBA", (W,100), (255,255,255))
        drawtmp = ImageDraw.Draw(imgtmp)

        params = parse_qs(urlparse(self.path).query)

        if params:

            h1 = unicode(params.get("h1")[0],"utf8")
            h2 = unicode(params.get("h2")[0],"utf8")
            p = unicode(params.get("p")[0],"utf8")

            linesh2 = textwrap.wrap(h2, width=20)
            lines = textwrap.wrap(p, width=20)

            imglogo = Image.open(LOGO_FILE, 'r')
            img_w, img_h = imglogo.size

            wh1, hh1 = drawtmp.textsize(h1, font=H1_FONT)
            wh2, hh2 = drawtmp.textsize(h2, font=H2_FONT)

            height += img_h + hh1 + hh2 

            for line in lines:
                w, h = drawtmp.textsize(line, font=P_FONT)
                height += h

            for line in linesh2:
                w, h = drawtmp.textsize(line, font=H2_FONT)
                height += h

            del drawtmp

            img = Image.new("RGBA", (W,height), (255,255,255))

            img.paste(imglogo, (((W - img_w) / 2),30))
            draw = ImageDraw.Draw(img)

            draw.text(((W-wh1)/2, img_h + 50), h1, (0,0,0), font=H1_FONT)

            y_text = img_h  + hh1 + 80

            for line in linesh2:
                w, h = draw.textsize(line, font=H2_FONT)
                draw.text(((W-w)/2, y_text), line, (0,0,0), font=H2_FONT)
                y_text += h

            y_text += 25

            for line in lines:
                w, h = draw.textsize(line, font=P_FONT)
                draw.text(((W-w)/2, y_text), line, (0,0,0), font=P_FONT)
                y_text += h

            del draw

            img.save(TMP_FILE, "PNG")

            if not DEBUG:
                conn = serial.Serial(SERIAL, SPEED, timeout=10)
                im = image.EscposImage(TMP_FILE)
                out = im.to_raster_format()
                header = GS + b"v0" + six.int2byte(DENSITY) + _int_low_high(im.width_bytes, 2) + _int_low_high(im.height, 2)
                conn.write(header + out)
                conn.write("\x0a\x0a\x0a\x1d\x56\x00\x0a\x0a") 
                time.sleep(1)
                conn.close()
                printer_returns = 1
            else:
                printer_returns = 0

            self.wfile.write(printer_returns)

            return

def main():
  
   try:
        server = HTTPServer(('', PORT), APIServer)
        print 'Started httpserver on port ' + str(PORT)
        server.serve_forever()
    
   except KeyboardInterrupt:
        print '^C received, shutting down server'
        server.socket.close()

if __name__ == '__main__':
    main()





