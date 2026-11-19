Xiaomi MiIO controls Xiaomi devices from Homey over the local miIO protocol. Everything runs on your Homey and your local network. Only the optional login with your Xiaomi account reads the token of your device once from the Xiaomi cloud; nothing is stored.

Supported devices
- Mi Bedside Lamp 2: on/off, brightness, colour, colour temperature and mode
- Mi Smart Standing Fan (zhimi.fan.za4): on/off, speed, natural wind, oscillation and angle, LED display, buzzer and child lock
- Mi Smart Humidifier (zhimi.humidifier.ca1 and cb1): on/off, mode, target humidity, dry mode, humidity and temperature, LED display, buzzer and child lock

Getting started
1. In Homey choose Add device, pick this app and the type of your device.
2. Search for your device on your network, or log in with your Xiaomi account by scanning a QR code with the Mi Home app. The name, the IP address and the token are filled in for you. You can also enter the IP address and the token (32 hexadecimal characters) yourself.
3. Check the details and choose Add device. The app checks that the device answers before it is added.

Good to know
- Give your device a fixed IP address in your router, so the app keeps finding it.
- The device is read every few seconds (at least every 5 seconds). A device that does not answer is shown as unavailable and comes back by itself.
- Problems and ideas are welcome on the GitHub page of the app (see the links of this app).

Xiaomi and Mi are trademarks of Xiaomi Corporation. Xiaomi MiIO is an independent app and is not affiliated with or endorsed by Xiaomi.
