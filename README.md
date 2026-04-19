# Porch Light and Webcam Automation

# Introduction
This is a fun project to control a standard ceiling light and a webcam from a Raspberry PI Pico W, connected to two relays.

Web services running on the Pico can then be used to turn the light and the webcam on and off. 

Beyond this basic control, it opens the door to be able to do other automations in the future such as:
* Facial recognition
* Motion detection
* Parcel detection
* ...etc

# Setup

* Install Thonny e.g. ```apt install thonny```
* Install MicroPython firmware on the PI Pico W 
* Download [Microdot](https://github.com/miguelgrinberg/microdot/blob/main/src/microdot/microdot.py)
* Create a /lib directory on your Pico and move into it
* Right-click microdot.py and select 'Upload to /lib'
* Click 'Raspberry PI Pico' to return to the root directory 

# Configure WiFi
* Edit the file wifi-creds.json and provide your WiFi details
* Right-click wifi-creds.json and select 'Upload to /'
* Right-click Wify.py and select 'Upload to /'

# Upload main application
* Right-click main.py and select 'Upload to /'

# Using the application
* Either run the application within Thonny and note the IP address allocated to your device or find it from your router
* OPTIONAL: Configure your router to ALWAYS assign that IP address to the Pico
* On your phone or PC, open a browser and navigate to the IP address of the Pico
* Click the 'On' and 'Off' buttons against the light and the camera as desired
