# Xiaomi MiIO for Homey

Xiaomi MiIO controls Xiaomi devices from Homey over the local miIO protocol. Add a bedside lamp, a standing fan or
a humidifier, and control it from the Homey app, from flows and from your dashboard. The app finds the device on your
network and can read its token from your Xiaomi account.

Everything runs on your Homey and your local network. The only exception is the optional login with your Xiaomi
account, which reads the token of your device from the Xiaomi cloud once. Nothing is stored.

## What you get

- Control a lamp, a fan and a humidifier from Homey, including every capability in flows.
- The app searches your network for devices, so you do not have to type an IP address.
- Log in with your Xiaomi account by scanning a QR code with the Mi Home app, and the app fills in the name, the
  address and the token of your device.
- The app checks that the device answers before it is added, and tells you when the address or the token is wrong.
- The state of the device is read every few seconds. A change made on the device itself shows up in Homey on the
  next read.
- A device that stops answering is shown as unavailable and comes back by itself.
- The pairing page and the device settings are available in English and Dutch.

## Supported devices

| Device | What works in Homey |
|---|---|
| Mi Bedside Lamp 2 (`yeelink.light.bslamp2`) | On and off, brightness, colour, colour temperature and mode |
| Mi Smart Standing Fan (`zhimi.fan.za4`) | On and off, speed (also natural wind), oscillation and angle (30 to 120 degrees), LED display, buzzer and child lock |
| Mi Smart Humidifier (`zhimi.humidifier.ca1`, `cb1`) | On and off, mode, target humidity, dry mode, humidity and temperature, LED display, buzzer and child lock |

The humidifier is only tested against a fake device so far. Other Xiaomi devices are not supported yet; open an
issue with the model, its miIO properties and its commands.

## Requirements

- A Homey Pro running Homey version 13 or later.
- A supported Xiaomi device on the same network as your Homey, with the IP address and the token of the device.

## Getting started

1. Install Xiaomi MiIO on your Homey.
2. In Homey choose **Add device**, pick this app and the type of your device.
3. Choose how to add the device:
   - **Search for devices on my network**: pick your device in the list.
   - **Log in with my Xiaomi account**: scan the QR code with the Mi Home app and pick your device. The name, the IP
     address and the token are filled in. Your login goes straight to Xiaomi and is not stored.
   - **Enter the details myself**: type the IP address and the token. The token has 32 hexadecimal characters and
     can be read from your Xiaomi account, for example with
     [Xiaomi-cloud-tokens-extractor](https://github.com/PiotrMachowski/Xiaomi-cloud-tokens-extractor).
4. Check the name, the IP address, the token and how often the device is read, and choose **Add device**.

Give the device a fixed IP address in your router, otherwise Homey loses the device when the address changes.

## Settings

- **IP address**: the address of the device. Give the device a fixed address in your router.
- **Device token**: the token of the device. A new token reconnects the device.
- **Polling interval**: how often the state of the device is read, in seconds. The minimum is 5 seconds.

## Good to know

- The token changes when the device is reset or added again in the Mi Home app. Read the new token and enter it in
  the device settings.
- A command sent through UDP can get lost. The app tries again, so a command can occasionally take a second longer.
- The oscillation angle of the standing fan is limited to 120 degrees, because the fan refuses a larger angle.

## Troubleshooting

**The device cannot be added: "Cannot reach the device"**
- Check the IP address and the token. A wrong token looks the same as a device that does not answer.
- Check that the device is switched on and on the same network as your Homey.
- Make sure the router does not isolate wifi devices from each other, and that UDP port 54321 is not blocked.

**A device is shown as unavailable**
- Check that the device still has the same IP address. A fixed address in your router prevents this.
- Check that the token did not change, for example after the device was reset.

**A device reacts slowly**
- Check the wifi signal of the device. A weak signal loses packets and the app has to send them again.

Still stuck? Open an [issue](../../issues) with the version of the app and what you see. Please leave out personal
data such as device names, addresses and tokens.

## Contributing

Bug reports, ideas and pull requests are welcome. Read [CONTRIBUTING.md](CONTRIBUTING.md) first. Security
problems go through [SECURITY.md](SECURITY.md).

## How this was made

Xiaomi MiIO for Homey was built with the help of AI. Most of the code, the tests and the documentation were
written by [Claude](https://www.anthropic.com/claude), an AI assistant from Anthropic, working under the direction
of the maintainer. The maintainer decides what goes in, reviews the changes and is responsible for the result. The
tests and the pipelines in this repository are there to check the work, whoever wrote it.

## Trademarks

Xiaomi and Mi are trademarks of Xiaomi Corporation. Xiaomi MiIO for Homey is an independent project and is not
affiliated with or endorsed by Xiaomi.

## License

Xiaomi MiIO for Homey is released under the [MIT License](LICENSE).

## Credits

The store images are made from the photo
["Modern home living room with smart devices"](https://www.pexels.com/photo/modern-home-living-room-with-smart-devices-28549934/)
from Pexels, used under the [Pexels License](https://www.pexels.com/license/). The original is not included; the
image is cropped and scaled. Xiaomi MiIO for Homey is built on [cryptography](https://pypi.org/project/cryptography),
and the commands of the devices follow the documentation of
[python-miio](https://github.com/rytilahti/python-miio). The login with a QR code and the reading of the devices
from the Xiaomi account follow
[Xiaomi-cloud-tokens-extractor](https://github.com/PiotrMachowski/Xiaomi-cloud-tokens-extractor) by Piotr Machowski
(MIT License).
