#!/bin/bash
set -x
espeak "$1" --stdout | mpv -vo=null --audio-device=pulse/alsa_output.usb-C-Media_Electronics_Inc._USB_PnP_Sound_Device-00.analog-stereo -
