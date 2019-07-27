[![Build Status](https://travis-ci.org/jrcichra/smartcar.svg?branch=master)](https://travis-ci.org/jrcichra/smartcar)
# SmartCar

## An event-driven car network platform to intellegently control your car.

### Example configurations:
+ Have your dashcam record video when your ignition is on, but only when you're going under the speed limit :)
+ At a certain speed, have your sound system play a different track.
+ Send a warning to your phone when your ignition has been on for 5 minutes but the car hasn't moved
+ When the key goes off, transfer your dashcam footage to a NFS mount in your house over Wifi

These are all possible configurations, but this isn't a "one-size fits all" solution. Some people might not have a GPS module, or an OBDII reader. They might not have a touchscreen, or a dashcam! How do we provide an intelligent car framework that can work with any configuration? This project aims to answer that question.

Each service is a container with a standard socket protocol (to be defined), so you can customize each piece for your car and what features you want to impliment or change.

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
  
# TCP based
I am currently designing a TCP JSON protocol to handle the inter-container communication. I am looking at in-memory databases to manage the state of the containers, like redis.
