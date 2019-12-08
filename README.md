# SmartCar ![Actions Status](https://github.com/jrcichra/smartcar/workflows/smartcar%20CI/CD/badge.svg)

## A microservice event-driven framework to enhance your car (Designed for the Raspberry Pi).

### Dashcam screenshot using smartcar:
![Imgur](https://i.imgur.com/k4FMbSt.png)

## Current Functionality
+ Starts recording and displays preview when you turn on the ignition
+ Stops recording and hides preview when you turn off the ignition
+ Sends dashcam footage to an SFTP server for offloading
+ Converts the .h264 file to .mp4 using MP4Box
+ Automatically powers itself using a latch relay

# Current Docker containers
+ Controller
  + Passes messages and manages state
+ Redis
  + Datastore for state
+ Dashcam
  + Interfaces with the Raspberry Pi Camera
+ GPIO
  + Interfaces with the GPIO pins on the Raspberry Pi
+ Transfer
  + Sets up keys with a backend NAS and transfers video footage

Feel free to make a pull request with a new container! 

# Centralized Pub/Sub
The controller is an implimentation of what I call "centralized pub/sub". The containers only provide "actions" and "events" (A&E)
## Actions
Actions describe what a container can "do" (ex. start recording, play music, transfer footage)
## Events
Events describe what things can "happen" (ex. car started, car stopped, reached 70mph)
## Configuration
### config.yml
This holds the mapping of events and actions (programming your car at a high level)
### settings.yml
Holds the settings for each container (camera fps, time after stopping car, etc)

You are in total control of how your car responds to events. This lets you connect any component to any component in a predetermined way. This was not possible with pub/sub, as the containers would have to determine what events they were interested in. Containers have no concept of events, they only take in actions when told to.

# TCP based
Currently, all communication between containers is through TCP (no HTTP). This may change depending on need from GUI applications.
