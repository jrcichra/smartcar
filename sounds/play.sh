#!/bin/bash
set -x
mpv --vo=null --audio-device='pulse/alsa_output.usb-C-Media_Electronics_Inc._USB_PnP_Sound_Device-00.analog-stereo' $1
