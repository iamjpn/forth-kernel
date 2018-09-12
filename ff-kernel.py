from ipykernel.kernelbase import Kernel

from pexpect import replwrap, EOF
import pexpect
import os
import sys
import argparse
import serial
import readline
import rlcompleter
import atexit
import logging
import signal
import string
from _thread import start_new_thread, allocate_lock
from time import *


class Config(object):
    def __init__(self):
        self.serial_port  = '/dev/ttyUSB0'
        self.port  = '/dev/ttyUSB0'
        self.rate = '38400'
        self.hw = False
        self.sw = True

class EchoKernel(Kernel):
    implementation = 'Forth'
    implementation_version = '1.0'
    language = 'no-op'
    language_version = '0.1'
    language_info = {
        'name': 'forth',
        'mimetype': 'text/plain',
        'file_extension': '.f',
    }
    banner = "Flash Forth kernel"
    words = [] 

    def __init__(self, **kwargs):
        Kernel.__init__(self, **kwargs)
        self._start_ff()

    def _start_ff(self):
        try:
            config.ser = serial.Serial(config.port, config.rate, timeout=1, writeTimeout=1.0, rtscts=config.hw, xonxoff=config.sw)
            config.ser.write(b'\017\n'); 
            config.ser.flush()       # Send the output buffer
            sleep(0.2)
            while config.ser.inWaiting() > 0:
                char = config.ser.read()
                #print(char)
            config.ser.write(b'words\n'); 
            config.ser.flush()       # Send the output buffer
            sleep(1)
            while config.ser.inWaiting() > 0:
                line = config.ser.readline().decode('ascii')
                #line = config.ser.readline()
                #print(line)
                self.words += line.split()


        except serial.SerialException as e:
            print("Could not open serial port '{}': {}".format(com_port, e))
            raise e
        
    def do_execute(self, code, silent, store_history=True, user_expressions=None,
                   allow_stdin=False):
        config.ser.write(code.encode() + b'\n'); 
        line_count = 0
        config.ser.flush()       # Send the output buffer
        sleep(0.1)
        response = ""
        while config.ser.inWaiting() > 0:
            response += config.ser.readline().decode('ascii')
            line_count += 1

        #stream_content = {'name': 'stderr', 'text': "hope this works"}
        #self.send_response(self.iopub_socket, 'stream', stream_content)

        if response.startswith(code):
            response = response[len(code):].strip()
        if not silent:
            stream_content = {'name': 'stdout', 'text': response}
            self.send_response(self.iopub_socket, 'stream', stream_content)

        response.strip()
        return {'status': 'ok',
                # The base class increments the execution count
                'execution_count': self.execution_count,
                'payload': [],
                'user_expressions': {},
               }

    def do_shutdown(self, restart):
        if restart:
            config.ser.write(b'\017\n'); 
            config.ser.flush()       # Send the output buffer
        else:
            config.ser.close()

    def do_complete(self, code, cursor_pos):
        code = code[:cursor_pos]
        code = code.split()[-1]
        matching = [] 
        for completion in self.words:
            if completion.startswith(code):
                matching.append(completion)

        return {
            'matches' : matching,
            'cursor_start' : cursor_pos - len(code),
            'cursor_end' : cursor_pos,
            'metadata' : {},
            'status' : 'ok'
            }
        

if __name__ == '__main__':
    config = Config() 
    from ipykernel.kernelapp import IPKernelApp
    IPKernelApp.launch_instance(kernel_class=EchoKernel)
