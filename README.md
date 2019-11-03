# SmartCar [![Actions Status](https://github.com/jrcichra/smartcar/workflows/smartcar%20CI/CD/badge.svg)]

## An event-driven car framework to intellegently control your car.

### Example configurations:
+ Have your dashcam record video when your ignition is on, but only when you're going under the speed limit :)
+ At a certain speed, have your sound system play a different track.
+ Send a warning to your phone when your ignition has been on for 5 minutes but the car hasn't moved
+ When the key goes off, transfer your dashcam footage to a NFS mount in your house over Wifi

These are all possible configurations, but this isn't a "one-size fits all" solution. Some people might not have a GPS module, or an OBDII reader. They might not have a touchscreen, or a dashcam! How do we provide an intelligent car framework that can work with any configuration? This project aims to answer that question.

Each service is a container with a standard socket protocol, so you can customize each piece for your car and what features you want to impliment or change.

This is a redesign on the original rpi-dashcam project, but uses a modular design with docker containers. I have open sourced this project since this surely has no market other than for extreme hobbists.

# Example Docker containers
+ Controller
  + The main container who's managing the entire application, managing the state of what's there and not
+ Dashcam
  + Records footage from the Dashcam when told by the controller
+ OBDII
  + Collects data from the OBDII port when told by the controller
+ GUI
  + Handles the GUI shown to the user by their touchscreen display
+ Voice
  + Processes microphone input from the car and passes information to the controller
+ Audio
  + Handles audio output, talking to the speaker system with the specific chip you bought for audio output
+ Backup Cam
  + Handles input from the backup cam, with the ability to take over the main display
+ NAS 
  + Sends data to a network attached storage device
  
# Centralized Pub/Sub (A&E)
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
Currently, all communication between containers is through TCP (no HTTP). This may change depending on need from GUI applications
