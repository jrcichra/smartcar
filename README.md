# SmartCar ![Actions Status](https://github.com/jrcichra/smartcar/workflows/smartcar%20CI/CD/badge.svg) [![Docker Hub](https://img.shields.io/badge/docker-hub-blue.svg)](https://hub.docker.com/r/jrcichra/)

## A collection of [karmen](https://github.com/jrcichra/karmen) containers to build a distributed car container network

### Smartcar footage:
![smartcar gif](./smartcar.gif)

## Current Functionality
+ Starts and stops recording with ignition
+ 

# Current containers
+ [Karmen](https://github.com/jrcichra/karmen) 
  + Controller for managing all other containers
+ [Dashcam](./containers/dashcam)
  + Interfaces with the Raspberry Pi Camera
+ [GPIO](./containers/gpio)
  + Interfaces with the GPIO pins (for ignition)
+ [Transfer](./containers/transfer)
  + Transfers footage to NAS when you get home

More containers on the way (OBDII) - make new containers and make a pull request!


## Getting started
You need some hardware and handywork to get this started in your car.
1. Look at your car's wiring diagram. Find out where you can tap into 5V (preferable but harder) or 12V (w/ a buck converter and probably a fuse)
2. Also see what wire corelates to your ignition
3. (I used wires going to my car radio (12V & ignition on/off))
4. You'll need a latch relay that is triggered with ignition on. This powers the Pi
5. Once the Pi is on, smartcar will emit "key_on" by default, starting the recording process
6. You'll need another relay system to determine when the ignition went off, but on a different pin, that does not turn off the Pi (remember, your Pi is on because of the former latch relay)

NOTE: as of writing the pin numbers are hardcoded in [gpio.py](./containers/gpio/gpio.py)

## Configuration
### config.yml
See [my example RPi config](./test_config_rpi.yml). TLDR; [karmen](https://github.com/jrcichra/karmen) takes a declarative mapping of container events to container actions

### docker-compose.yml
See [my example RPi compose](./docker-compose-test-rpi.yml). 