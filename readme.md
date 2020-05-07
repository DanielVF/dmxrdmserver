# DMX RDM webserver for Enttec DMX PRO MK2

Gives you an HTTP API to send and receive DMX and RDM packets.

## Setup

Designed for python 3.x

To install dependencies:

    pip install flask serial

Then write a configuration file (config.ini) with the serial port your device is showing up as. For example on Mac OS:

    [device]
    serial_port = /dev/cu.usbserial-EN182471

Then start up the app:

    /Users/dvf/anaconda3/bin/flask run --without-threads

Visit http://127.0.0.1:5000/ in your browser for a sample of what you can do with the API.

## Todo

- Kill bugs
- Better read parser
- RDM Discovery packets
- RDM auto discovery
- Nice display of RDM responses

