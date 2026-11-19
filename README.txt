Xiaomi MiIO controls Xiaomi devices from Homey over the local miIO protocol. Everything runs on your Homey and your local network. Nothing is sent to the cloud.

Supported devices
- Mi Bedside Lamp 2: on/off, brightness, colour, colour temperature and mode
- Mi Smart Standing Fan (zhimi.fan.za4): on/off, speed, natural wind, oscillation and angle, LED display, buzzer and child lock
- Mi Smart Humidifier (zhimi.humidifier.ca1 and cb1): on/off, mode, target humidity, dry mode, humidity and temperature, LED display, buzzer and child lock

Getting started
1. Find the IP address and the device token (32 hexadecimal characters) of your device. The token can be read from your Xiaomi account with a token extractor tool.
2. In Homey choose Add device, pick this app and the type of your device.
3. Enter a name, the IP address, the token and how often the device is read. The app checks that the device answers before it is added.

Good to know
- Give your device a fixed IP address in your router, so the app keeps finding it.
- The device is read every few seconds (at least every 5 seconds). A device that does not answer is shown as unavailable and comes back by itself.
- Problems and ideas are welcome on the GitHub page of the app (see the links of this app).

Xiaomi and Mi are trademarks of Xiaomi Corporation. Xiaomi MiIO is an independent app and is not affiliated with or endorsed by Xiaomi.
