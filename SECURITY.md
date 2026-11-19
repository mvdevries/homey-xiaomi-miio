# Security policy

## Supported versions

Only the latest released version of Xiaomi MiIO receives security fixes.

## Reporting a vulnerability

Please do not open a public issue for a security problem.

Report it privately through GitHub: open the **Security** tab of this repository and choose
**Report a vulnerability**. Include what you found, the version of the app, and the steps to reproduce it.

This is a hobby project maintained in spare time. You can expect an acknowledgement within a week and an
update on the fix as soon as there is one. Once a fix is released, the report can be made public together
with credit to you, if you want that.

## What is in scope

- The app code in this repository, including the pairing page and the miIO transport.
- The way the app handles the device token and the other stored device settings.

## What is out of scope

- Vulnerabilities in Homey, the devices, the `cryptography` library or other dependencies themselves; report those to their
  maintainers. Dependency updates are handled by Dependabot.
- Problems that need physical access to the Homey or a compromised local network.
