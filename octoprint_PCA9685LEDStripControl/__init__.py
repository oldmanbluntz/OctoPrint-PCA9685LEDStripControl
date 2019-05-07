#
# Copyright 2017 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# coding=utf-8

from __future__ import absolute_import
from __future__ import division
import time
import re

import octoprint.plugin
import Adafruit_PCA9685

pwm = Adafruit_PCA9685.PCA9685()
pwm.set_pwm_freq(120)

class PCA9685LED:
	pwm = None
	pin = None
	def __init__(self, pwm, pin):
		self.pwm = pwm
		self.pin = pin

	def ChangeDutyCycle(self, duty_cycle):
		self.pwm.set_pwm(self.pin, 0, int(duty_cycle))

	def stop(self):
		self.ChangeDutyCycle(0)


class PCA9685LEDStripControlPlugin(octoprint.plugin.AssetPlugin,
							octoprint.plugin.SettingsPlugin,
							octoprint.plugin.ShutdownPlugin,
							octoprint.plugin.StartupPlugin,
							octoprint.plugin.TemplatePlugin):

	def __init__(self):
		self._leds = dict(r=None, g=None, b=None, w=None)

	def _unregister_leds(self):
		self._logger.debug(u"_unregister_leds()")
		for i in ('r', 'g', 'b', 'w'):
			if self._leds[i]:
				self._leds[i].ChangeDutyCycle(0)
				self._leds[i].stop()
		self._leds = dict(r=None, g=None, b=None)

	def _register_leds(self):
		self._logger.debug(u"_register_leds()")
		for i in ('r', 'g', 'b', 'w'):
			pin = self._settings.get_int([i])
			self._logger.debug(u"got pin(%s)" % (pin,))
			self._leds[i] = PCA9685LED(pwm, pin)

	def on_after_startup(self):
		self._logger.debug(u"PCA9685LEDStripControl Startup")

	def on_shutdown(self):
		self._logger.debug(u"PCA9685LEDStripControl Shutdown")
		self._unregister_leds()

	def HandleM150(self, comm_instance, phase, cmd, cmd_type, gcode, *args, **kwargs):
		if gcode and cmd.startswith("M150"):
			self._logger.debug(u"M150 Detected: %s" % (cmd,))
			# Emulating Marlin 1.1.0's syntax
			# https://github.com/MarlinFirmware/Marlin/blob/RC/Marlin/Marlin_main.cpp#L6133
			dutycycles = {'r':0.0, 'g':0.0, 'b':0.0, 'w':0.0}
			for match in re.finditer(r'([RGUBWrgubw]) *(\d*)', cmd):
				k = match.group(1).lower()
				# Marlin uses RUB instead of RGB
				if k == 'u': k = 'g'
				try:
					v = float(match.group(2))
				except ValueError:
					# more than likely match.group(2) was unspecified
					v = 255.0
				v = v/255.0 * 4095.0 # convert RGB to RPi dutycycle
				v = max(min(v, 4095.0), 0.0) # clamp the value
				dutycycles[k] = v
				self._logger.debug(u"match 1: %s 2: %s" % (k, v))

			for l in dutycycles.keys():
				if self._leds[l]:
					self._leds[l].ChangeDutyCycle(dutycycles[l])

			return None,

	##~~ SettingsPlugin mixin

	def get_settings_version(self):
		return 2

	def get_template_configs(self):
		return [
			dict(type="settings", name="PCA9685 LED Strip Control", custom_bindings=False)
		]

	def get_settings_defaults(self):
		return dict(r=0, g=0, b=0, w=0, on_startup=True)

	def on_settings_initialized(self):
		self._logger.debug(u"PCA9685LEDStripControl on_settings_load()")

		self._register_leds()

	def on_settings_save(self, data):
		self._logger.debug(u"PCA9685LEDStripControl on_settings_save()")
		self._unregister_leds()
		# cast to proper types before saving
		for k in ('r', 'g', 'b', 'w'):
			if data.get(k): data[k] = max(0, int(data[k]))
		octoprint.plugin.SettingsPlugin.on_settings_save(self, data)
		self._register_leds()

	def on_settings_migrate(self, target, current=None):
		self._logger.debug(u"PCA9685LEDStripControl on_settings_migrate()")
		if current == 1:
			# add the 2 new values included
			self._settings.set(['w'], self.get_settings_defaults()["w"])
			self._settings.set(['on_startup'], self.get_settings_defaults()["on_startup"])

	##~~ Softwareupdate hook

	def get_update_information(self):
		return dict(
			ledstripcontrol=dict(
				displayName="PCA9685 PCA9685 LED Strip Control Plugin",
				displayVersion=self._plugin_version,

				# version check: github repository
				type="github_release",
				user="ozgunawesome",
				repo="OctoPrint-PCA9685LEDStripControl",
				current=self._plugin_version,

				# update method: pip
				pip="https://github.com/ozgunawesome/OctoPrint-PCA9685LEDStripControl/archive/{target_version}.zip"
			)
		)

__plugin_name__ = "PCA9685 LED Strip Control"

def __plugin_load__():
	global __plugin_implementation__
	__plugin_implementation__ = PCA9685LEDStripControlPlugin()

	global __plugin_hooks__
	__plugin_hooks__ = {
		"octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information,
		"octoprint.comm.protocol.gcode.queuing": __plugin_implementation__.HandleM150
	}

