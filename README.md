# carpi
Collect vehicle data from your car, in any configuration you wish! Each piece is a container with a standard socket protocol, so you can customize each piece for your car and what features you want to impliment or change.

In theory I would like custom plugins for this system where 

This is a redesign on the original rpi-dashcam project using a modular design with docker containers.

# Docker containers
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
