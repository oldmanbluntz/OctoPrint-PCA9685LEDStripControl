from __future__ import absolute_import
from __future__ import division
import time
import re
import octoprint.plugin
import board
from adafruit_pca9685 import PCA9685

i2c = board.I2C()
pca = PCA9685(i2c)
pca.frequency = 120


class PCA9685LED:
	def __init__(self, outpin):
		self.pca = pca
		self.outpin = outpin
		self.duty_cycle = 0

	def changedutycycle(self, duty_cycle):
		self.duty_cycle = int(duty_cycle * 65535)
		self.duty_cycle = max(0, min(self.duty_cycle, 65535))  # Clamp the duty_cycle value
		self.pca.channels[self.outpin].duty_cycle = self.duty_cycle

	def stop(self):
		self.changedutycycle(0)


class PCA9685LEDStripControlPlugin(
	octoprint.plugin.StartupPlugin,
	octoprint.plugin.TemplatePlugin,
	octoprint.plugin.SettingsPlugin,
	octoprint.plugin.RestartNeedingPlugin,
	octoprint.plugin.ShutdownPlugin
):

	def __init__(self):
		self._leds = dict(r=None, g=None, b=None, w=None)

	def _unregister_leds(self):
		self._logger.debug(u"_unregister_leds()")
		for i in ('r', 'g', 'b', 'w'):
			if self._leds[i]:
				self._leds[i].changedutycycle(0)
				self._leds[i].stop()
		self._leds = dict(r=None, g=None, b=None)

	def _register_leds(self):
		self._logger.debug(u"_register_leds()")
		for i in ('r', 'g', 'b', 'w'):
			outpin = self._settings.get_int([i])
			self._logger.debug(u"got pin(%s)" % (outpin,))
			self._leds[i] = PCA9685LED(outpin)

	def on_after_startup(self):
		self._logger.debug(u"PCA9685LEDStripControl Startup")

	def on_shutdown(self):
		self._logger.debug(u"PCA9685LEDStripControl Shutdown")
		self._unregister_leds()

	def handlem150(self, comm_instance, phase, cmd, cmd_type, gcode, *args, **kwargs):
		if gcode and cmd.startswith("M150"):
			self._logger.debug(u"M150 Detected: %s" % (cmd,))
			dutycycles = {'r': 0.0, 'g': 0.0, 'b': 0.0, 'w': 0.0}
			for match in re.finditer(r'([RGUBWrgubw]) *(\d*)', cmd):
				k = match.group(1).lower()
				# Marlin uses RUB instead of RGB
				if k == 'u':
					k = 'g'
				try:
					v = float(match.group(2))
				except ValueError:
					# more than likely match.group(2) was unspecified
					v = 255.0
				v = v / 255.0 * 65535.0  # convert RGB to RPi dutycycle
				v = max(min(v, 65535.0), 0.0)  # clamp the value
				dutycycles[k] = v
				self._logger.debug(u"match 1: %s 2: %s" % (k, v))

			for light in dutycycles.keys():
				if self._leds[light]:
					self._leds[light].changedutycycle(dutycycles[light])

			return None,

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
			if data.get(k):
				data[k] = max(0, int(data[k]))
		super().on_settings_save(data)
		self._register_leds()

	def on_settings_migrate(self, target, current=None):
		self._logger.debug(u"PCA9685LEDStripControl on_settings_migrate()")
		if current == 1:
			# add the 2 new values included
			self._settings.set(['w'], self.get_settings_defaults()["w"])
			self._settings.set(['on_startup'], self.get_settings_defaults()["on_startup"])

	def get_update_information(self):
		return {
			"PCA9685LEDStripControl": {
				"displayName": "PCA9685LEDStripControl Plugin",
				"displayVersion": self._plugin_version,

				"type": "github_release",
				"user": "OldMaNBlunTZ",
				"repo": "OctoPrint-Pca9685ledcontrol",
				"current": self._plugin_version,

				"pip": "https://github.com/OldMaNBlunTZ/OctoPrint-Pca9685ledcontrol/archive/{target_version}.zip",
			}
		}


__plugin_name__ = "Pca9685ledstripcontrol Plugin"

__plugin_pythoncompat__ = ">=3,<4"


def __plugin_load__():
	global __plugin_implementation__
	__plugin_implementation__ = PCA9685LEDStripControlPlugin()

	global __plugin_hooks__
	__plugin_hooks__ = {
		"octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information,
		"octoprint.comm.protocol.gcode.queuing": __plugin_implementation__.handlem150
	}
