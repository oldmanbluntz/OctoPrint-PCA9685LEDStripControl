# OctoPrint-PCA9685LEDStripControl

OctoPrint plugin that intercepts M150 GCode commands and controls LEDs connected to PCA9685 over I2C. Forked to add support to connect 
to a desktop PC through I2C on an FT232H. Also updated the code to work with newer releases of Octoprint. This does not work in python 2 at all. Tested on Python 3.10 and higher.

![PCA9685 dev board](https://cdn-shop.adafruit.com/970x728/815-05.jpg)

https://www.adafruit.com/product/815

Implements the M150 command syntax from the latest Marlin.

        M150: Set Status LED Color - Use R-U-B for R-G-B Optional (W)
        M150 R255       ; Turn LED red
        M150 R255 U127  ; Turn LED orange (PWM only)
        M150            ; Turn LED off
        M150 R U B      ; Turn LED white
        M150 W          ; Turn LED white if using RGBW strips (optional)

## Setup

1. Connect PCA9685 (address 0x40) and enable I2C in configuration

    	sudo raspi-config

2. Install via the bundled [Plugin Manager](https://github.com/foosel/OctoPrint/wiki/Plugin:-Plugin-Manager)
or manually using this URL:

    	https://github.com/ozgunawesome/OctoPrint-PCA9685LEDStripControl/archive/master.zip

3. Restart OctoPrint

## Configuration

Configure the PCA9685 pins via the OctoPrint settings UI.

## Disclaimer

This is **not** an official Google product.
