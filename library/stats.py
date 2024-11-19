# turing-smart-screen-python - a Python system monitor and library for USB-C displays like Turing Smart Screen or XuanFang
# https://github.com/mathoudebine/turing-smart-screen-python/

# Copyright (C) 2021-2023  Matthieu Houdebine (mathoudebine)
# Copyright (C) 2022-2023  Rollbacke
# Copyright (C) 2022-2023  Ebag333
# Copyright (C) 2022-2023  w1ld3r
# Copyright (C) 2022-2023  Charles Ferguson (gerph)
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import datetime
import locale
import math
import os
import platform
import sys
from typing import List

import babel.dates
from psutil._common import bytes2human
from uptime import uptime

import library.config as config
from library.display import display
from library.log import logger

DEFAULT_HISTORY_SIZE = 10

ETH_CARD = config.CONFIG_DATA["config"].get("ETH", "")
WLO_CARD = config.CONFIG_DATA["config"].get("WLO", "")
HW_SENSORS = config.CONFIG_DATA["config"].get("HW_SENSORS", "AUTO")
CPU_FAN = config.CONFIG_DATA["config"].get("CPU_FAN", "AUTO")

if HW_SENSORS == "PYTHON":
    if platform.system() == 'Windows':
        logger.warning("It is recommended to use LibreHardwareMonitor integration for Windows instead of Python "
                       "libraries (require admin. rights)")
    import library.sensors.sensors_python as sensors
elif HW_SENSORS == "LHM":
    if platform.system() == 'Windows':
        import library.sensors.sensors_librehardwaremonitor as sensors
    else:
        logger.error("LibreHardwareMonitor integration is only available on Windows")
        try:
            sys.exit(0)
        except:
            os._exit(0)
elif HW_SENSORS == "STUB":
    logger.warning("Stub sensors, not real HW sensors")
    import library.sensors.sensors_stub_random as sensors
elif HW_SENSORS == "STATIC":
    logger.warning("Stub sensors, not real HW sensors")
    import library.sensors.sensors_stub_static as sensors
elif HW_SENSORS == "AUTO":
    if platform.system() == 'Windows':
        import library.sensors.sensors_librehardwaremonitor as sensors
    else:
        import library.sensors.sensors_python as sensors
else:
    logger.error("Unsupported HW_SENSORS value in config.yaml")
    try:
        sys.exit(0)
    except:
        os._exit(0)

import library.sensors.sensors_custom as sensors_custom


def get_theme_file_path(name):
    if name:
        return os.path.join(config.THEME_DATA['PATH'], name)
    else:
        return None


def display_themed_value(theme_data, value, min_size=0, unit=''):
    if not theme_data.get("SHOW", False):
        return None, 0, 0

    if value is None:
        return

    # overridable MIN_SIZE from theme with backward compatibility
    min_size = theme_data.get("MIN_SIZE", min_size)

    text = f"{{:>{min_size}}}".format(value)
    if theme_data.get("SHOW_UNIT", True) and unit:
        text += str(unit)

    return display.lcd.DisplayText(
        text=text,
        x=theme_data.get("X", 0),
        y=theme_data.get("Y", 0),
        width=theme_data.get("WIDTH", 0),
        height=theme_data.get("HEIGHT", 0),
        font=theme_data.get("FONT", "roboto-mono/RobotoMono-Regular.ttf"),
        font_size=theme_data.get("FONT_SIZE", 10),
        font_color=theme_data.get("FONT_COLOR", (0, 0, 0)),
        background_color=theme_data.get("BACKGROUND_COLOR", (255, 255, 255)),
        background_image=get_theme_file_path(theme_data.get("BACKGROUND_IMAGE", None)),
        align=theme_data.get("ALIGN", "left"),
        anchor=theme_data.get("ANCHOR", "lt"),
    )


def display_themed_percent_value(theme_data, value):
    return display_themed_value(
        theme_data=theme_data,
        value=int(value),
        min_size=3,
        unit="%"
    )


def display_themed_temperature_value(theme_data, value):
    return display_themed_value(
        theme_data=theme_data,
        value=int(value),
        min_size=3,
        unit="°C"
    )


def display_themed_progress_bar(theme_data, value):
    if not theme_data.get("SHOW", False):
        return None, 0, 0

    return display.lcd.DisplayProgressBar(
        x=theme_data.get("X", 0),
        y=theme_data.get("Y", 0),
        width=theme_data.get("WIDTH", 0),
        height=theme_data.get("HEIGHT", 0),
        value=int(value),
        min_value=theme_data.get("MIN_VALUE", 0),
        max_value=theme_data.get("MAX_VALUE", 100),
        bar_color=theme_data.get("BAR_COLOR", (0, 0, 0)),
        bar_outline=theme_data.get("BAR_OUTLINE", False),
        background_color=theme_data.get("BACKGROUND_COLOR", (255, 255, 255)),
        background_image=get_theme_file_path(theme_data.get("BACKGROUND_IMAGE", None))
    )


def display_themed_radial_bar(theme_data, value, min_size=0, unit='', custom_text=None):
    if not theme_data.get("SHOW", False):
        return None, 0, 0

    if theme_data.get("SHOW_TEXT", False):
        if custom_text:
            text = custom_text
        else:
            text = f"{{:>{min_size}}}".format(value)
            if theme_data.get("SHOW_UNIT", True) and unit:
                text += str(unit)
    else:
        text = ""

    return display.lcd.DisplayRadialProgressBar(
        xc=theme_data.get("X", 0),
        yc=theme_data.get("Y", 0),
        radius=theme_data.get("RADIUS", 1),
        bar_width=theme_data.get("WIDTH", 1),
        min_value=theme_data.get("MIN_VALUE", 0),
        max_value=theme_data.get("MAX_VALUE", 100),
        angle_start=theme_data.get("ANGLE_START", 0),
        angle_end=theme_data.get("ANGLE_END", 360),
        angle_steps=theme_data.get("ANGLE_STEPS", 1),
        angle_sep=theme_data.get("ANGLE_SEP", 0),
        clockwise=theme_data.get("CLOCKWISE", False),
        value=value,
        bar_color=theme_data.get("BAR_COLOR", (0, 0, 0)),
        text=text,
        font=theme_data.get("FONT", "roboto-mono/RobotoMono-Regular.ttf"),
        font_size=theme_data.get("FONT_SIZE", 10),
        font_color=theme_data.get("FONT_COLOR", (0, 0, 0)),
        background_color=theme_data.get("BACKGROUND_COLOR", (0, 0, 0)),
        background_image=get_theme_file_path(theme_data.get("BACKGROUND_IMAGE", None))
    )


def display_themed_percent_radial_bar(theme_data, value):
    return display_themed_radial_bar(
        theme_data=theme_data,
        value=int(value),
        unit="%",
        min_size=3
    )


def display_themed_temperature_radial_bar(theme_data, value):
    return display_themed_radial_bar(
        theme_data=theme_data,
        value=int(value),
        min_size=3,
        unit="°C"
    )


def display_themed_line_graph(theme_data, values):
    if not theme_data.get("SHOW", False):
        return None, 0, 0

    line_color = theme_data.get("LINE_COLOR", (0, 0, 0))

    return display.lcd.DisplayLineGraph(
        x=theme_data.get("X", 0),
        y=theme_data.get("Y", 0),
        width=theme_data.get("WIDTH", 1),
        height=theme_data.get("HEIGHT", 1),
        values=values,
        min_value=theme_data.get("MIN_VALUE", 0),
        max_value=theme_data.get("MAX_VALUE", 100),
        autoscale=theme_data.get("AUTOSCALE", False),
        line_color=line_color,
        line_width=theme_data.get("LINE_WIDTH", 2),
        graph_axis=theme_data.get("AXIS", False),
        axis_color=theme_data.get("AXIS_COLOR", line_color),  # If no color specified, use line color for axis
        background_color=theme_data.get("BACKGROUND_COLOR", (0, 0, 0)),
        background_image=get_theme_file_path(theme_data.get("BACKGROUND_IMAGE", None))
    )


def save_last_value(value: float, last_values: List[float], history_size: int):
    # Initialize last values list the first time with given size
    if len(last_values) != history_size:
        last_values[:] = last_values_list(size=history_size)
    # Store the value to the list that can then be used for line graph
    last_values.append(value)
    # Also remove the oldest value from list
    last_values.pop(0)


def last_values_list(size: int) -> List[float]:
    return [math.nan] * size


class CPU:
    last_values_cpu_percentage = []
    last_values_cpu_temperature = []
    last_values_cpu_fan_speed = []
    last_values_cpu_frequency = []

    @classmethod
    def percentage(cls):
        theme_data = config.THEME_DATA['STATS']['CPU']['PERCENTAGE']
        cpu_percentage = sensors.Cpu.percentage(
            interval=theme_data.get("INTERVAL", None)
        )
        save_last_value(cpu_percentage, cls.last_values_cpu_percentage,
                        theme_data['LINE_GRAPH'].get("HISTORY_SIZE", DEFAULT_HISTORY_SIZE))
        # logger.debug(f"CPU Percentage: {cpu_percentage}")

        display_themed_progress_bar(theme_data['GRAPH'], cpu_percentage)
        display_themed_percent_radial_bar(theme_data['RADIAL'], cpu_percentage)
        display_themed_percent_value(theme_data['TEXT'], cpu_percentage)
        display_themed_line_graph(theme_data['LINE_GRAPH'], cls.last_values_cpu_percentage)

    @classmethod
    def frequency(cls):
        freq_ghz = sensors.Cpu.frequency() / 1000
        theme_data = config.THEME_DATA['STATS']['CPU']['FREQUENCY']

        save_last_value(freq_ghz, cls.last_values_cpu_frequency,
                        theme_data['LINE_GRAPH'].get("HISTORY_SIZE", DEFAULT_HISTORY_SIZE))

        display_themed_value(
            theme_data=theme_data['TEXT'],
            value=f'{freq_ghz:.2f}',
            unit=" GHz",
            min_size=4
        )
        display_themed_progress_bar(theme_data['GRAPH'], freq_ghz)
        display_themed_radial_bar(
            theme_data=theme_data['RADIAL'],
            value=f'{freq_ghz:.2f}',
            unit=" GHz",
            min_size=4
        )
        display_themed_line_graph(theme_data['LINE_GRAPH'], cls.last_values_cpu_frequency)

    @classmethod
    def load(cls):
        cpu_load = sensors.Cpu.load()
        # logger.debug(f"CPU Load: ({cpu_load[0]},{cpu_load[1]},{cpu_load[2]})")
        load_theme_data = config.THEME_DATA['STATS']['CPU']['LOAD']

        display_themed_percent_value(load_theme_data['ONE']['TEXT'], cpu_load[0])
        display_themed_percent_value(load_theme_data['FIVE']['TEXT'], cpu_load[1])
        display_themed_percent_value(load_theme_data['FIFTEEN']['TEXT'], cpu_load[2])

    @classmethod
    def temperature(cls):
        temperature = sensors.Cpu.temperature()
        save_last_value(temperature, cls.last_values_cpu_temperature,
                        config.THEME_DATA['STATS']['CPU']['TEMPERATURE']['LINE_GRAPH'].get("HISTORY_SIZE",
                                                                                           DEFAULT_HISTORY_SIZE))

        cpu_temp_text_data = config.THEME_DATA['STATS']['CPU']['TEMPERATURE']['TEXT']
        cpu_temp_radial_data = config.THEME_DATA['STATS']['CPU']['TEMPERATURE']['RADIAL']
        cpu_temp_graph_data = config.THEME_DATA['STATS']['CPU']['TEMPERATURE']['GRAPH']
        cpu_temp_line_graph_data = config.THEME_DATA['STATS']['CPU']['TEMPERATURE']['LINE_GRAPH']

        if math.isnan(temperature):
            temperature = 0
            if cpu_temp_text_data['SHOW'] or cpu_temp_radial_data['SHOW'] or cpu_temp_graph_data[
                'SHOW'] or cpu_temp_line_graph_data['SHOW']:
                logger.warning("Your CPU temperature is not supported yet")
                cpu_temp_text_data['SHOW'] = False
                cpu_temp_radial_data['SHOW'] = False
                cpu_temp_graph_data['SHOW'] = False
                cpu_temp_line_graph_data['SHOW'] = False

        display_themed_temperature_value(cpu_temp_text_data, temperature)
        display_themed_progress_bar(cpu_temp_graph_data, temperature)
        display_themed_temperature_radial_bar(cpu_temp_radial_data, temperature)
        display_themed_line_graph(cpu_temp_line_graph_data, cls.last_values_cpu_temperature)

    @classmethod
    def fan_speed(cls):
        if CPU_FAN != "AUTO":
            fan_percent = sensors.Cpu.fan_percent(CPU_FAN)
        else:
            fan_percent = sensors.Cpu.fan_percent()

        save_last_value(fan_percent, cls.last_values_cpu_fan_speed,
                        config.THEME_DATA['STATS']['CPU']['FAN_SPEED']['LINE_GRAPH'].get("HISTORY_SIZE",
                                                                                         DEFAULT_HISTORY_SIZE))

        cpu_fan_text_data = config.THEME_DATA['STATS']['CPU']['FAN_SPEED']['TEXT']
        cpu_fan_radial_data = config.THEME_DATA['STATS']['CPU']['FAN_SPEED']['RADIAL']
        cpu_fan_graph_data = config.THEME_DATA['STATS']['CPU']['FAN_SPEED']['GRAPH']
        cpu_fan_line_graph_data = config.THEME_DATA['STATS']['CPU']['FAN_SPEED']['LINE_GRAPH']

        if math.isnan(fan_percent):
            fan_percent = 0
            if cpu_fan_text_data['SHOW'] or cpu_fan_radial_data['SHOW'] or cpu_fan_graph_data[
                'SHOW'] or cpu_fan_line_graph_data['SHOW']:
                if sys.platform == "win32":
                    logger.warning("Your CPU Fan sensor could not be auto-detected")
                else:
                    logger.warning("Your CPU Fan sensor could not be auto-detected. Select it from Configuration UI.")
                cpu_fan_text_data['SHOW'] = False
                cpu_fan_radial_data['SHOW'] = False
                cpu_fan_graph_data['SHOW'] = False
                cpu_fan_line_graph_data['SHOW'] = False

        display_themed_percent_value(cpu_fan_text_data, fan_percent)
        display_themed_progress_bar(cpu_fan_graph_data, fan_percent)
        display_themed_percent_radial_bar(cpu_fan_radial_data, fan_percent)
        display_themed_line_graph(cpu_fan_line_graph_data, cls.last_values_cpu_fan_speed)


class Gpu:
    last_values_gpu_percentage = []
    last_values_gpu_mem_percentage = []
    last_values_gpu_temperature = []
    last_values_gpu_fps = []
    last_values_gpu_fan_speed = []
    last_values_gpu_frequency = []

    @classmethod
    def stats(cls):
        load, memory_percentage, memory_used_mb, total_memory_mb, temperature = sensors.Gpu.stats()
        fps = sensors.Gpu.fps()
        fan_percent = sensors.Gpu.fan_percent()
        freq_ghz = sensors.Gpu.frequency() / 1000

        theme_gpu_data = config.THEME_DATA['STATS']['GPU']

        save_last_value(load, cls.last_values_gpu_percentage,
                        theme_gpu_data['PERCENTAGE']['LINE_GRAPH'].get("HISTORY_SIZE", DEFAULT_HISTORY_SIZE))
        save_last_value(memory_percentage, cls.last_values_gpu_mem_percentage,
                        theme_gpu_data['MEMORY_PERCENT']['LINE_GRAPH'].get("HISTORY_SIZE", DEFAULT_HISTORY_SIZE))
        save_last_value(temperature, cls.last_values_gpu_temperature,
                        theme_gpu_data['TEMPERATURE']['LINE_GRAPH'].get("HISTORY_SIZE", DEFAULT_HISTORY_SIZE))
        save_last_value(fps, cls.last_values_gpu_fps,
                        theme_gpu_data['FPS']['LINE_GRAPH'].get("HISTORY_SIZE", DEFAULT_HISTORY_SIZE))
        save_last_value(fan_percent, cls.last_values_gpu_fan_speed,
                        theme_gpu_data['FAN_SPEED']['LINE_GRAPH'].get("HISTORY_SIZE", DEFAULT_HISTORY_SIZE))
        save_last_value(freq_ghz, cls.last_values_gpu_frequency,
                        theme_gpu_data['FREQUENCY']['LINE_GRAPH'].get("HISTORY_SIZE", DEFAULT_HISTORY_SIZE))

        ################################ for backward compatibility only
        gpu_mem_graph_data = theme_gpu_data['MEMORY']['GRAPH']
        gpu_mem_radial_data = theme_gpu_data['MEMORY']['RADIAL']
        if math.isnan(memory_percentage):
            memory_percentage = 0
            if gpu_mem_graph_data['SHOW'] or gpu_mem_radial_data['SHOW']:
                logger.warning("Your GPU memory relative usage (%) is not supported yet")
                gpu_mem_graph_data['SHOW'] = False
                gpu_mem_radial_data['SHOW'] = False

        gpu_mem_text_data = theme_gpu_data['MEMORY']['TEXT']
        if math.isnan(memory_used_mb):
            memory_used_mb = 0
            if gpu_mem_text_data['SHOW']:
                logger.warning("Your GPU memory absolute usage (M) is not supported yet")
                gpu_mem_text_data['SHOW'] = False

        display_themed_progress_bar(gpu_mem_graph_data, memory_percentage)
        display_themed_percent_radial_bar(gpu_mem_radial_data, memory_percentage)
        display_themed_value(
            theme_data=gpu_mem_text_data,
            value=int(memory_used_mb),
            min_size=5,
            unit=" M"
        )
        ################################ end of backward compatibility only

        # GPU usage (%)
        gpu_percent_graph_data = theme_gpu_data['PERCENTAGE']['GRAPH']
        gpu_percent_radial_data = theme_gpu_data['PERCENTAGE']['RADIAL']
        gpu_percent_text_data = theme_gpu_data['PERCENTAGE']['TEXT']
        gpu_percent_line_graph_data = theme_gpu_data['PERCENTAGE']['LINE_GRAPH']

        if math.isnan(load):
            load = 0
            if gpu_percent_graph_data['SHOW'] or gpu_percent_text_data['SHOW'] or gpu_percent_radial_data['SHOW'] or \
                    gpu_percent_line_graph_data['SHOW']:
                logger.warning("Your GPU load is not supported yet")
                gpu_percent_graph_data['SHOW'] = False
                gpu_percent_text_data['SHOW'] = False
                gpu_percent_radial_data['SHOW'] = False
                gpu_percent_line_graph_data['SHOW'] = False

        display_themed_progress_bar(gpu_percent_graph_data, load)
        display_themed_percent_radial_bar(gpu_percent_radial_data, load)
        display_themed_percent_value(gpu_percent_text_data, load)
        display_themed_line_graph(gpu_percent_line_graph_data, cls.last_values_gpu_percentage)

        # GPU mem. usage (%)
        gpu_mem_percent_graph_data = theme_gpu_data['MEMORY_PERCENT']['GRAPH']
        gpu_mem_percent_radial_data = theme_gpu_data['MEMORY_PERCENT']['RADIAL']
        gpu_mem_percent_text_data = theme_gpu_data['MEMORY_PERCENT']['TEXT']
        gpu_mem_percent_line_graph_data = theme_gpu_data['MEMORY_PERCENT']['LINE_GRAPH']

        if math.isnan(memory_percentage):
            memory_percentage = 0
            if gpu_mem_percent_graph_data['SHOW'] or gpu_mem_percent_radial_data['SHOW'] or gpu_mem_percent_text_data[
                'SHOW'] or gpu_mem_percent_line_graph_data['SHOW']:
                logger.warning("Your GPU memory relative usage (%) is not supported yet")
                gpu_mem_percent_graph_data['SHOW'] = False
                gpu_mem_percent_radial_data['SHOW'] = False
                gpu_mem_percent_text_data['SHOW'] = False

        display_themed_progress_bar(gpu_mem_percent_graph_data, memory_percentage)
        display_themed_percent_radial_bar(gpu_mem_percent_radial_data, memory_percentage)
        display_themed_percent_value(gpu_mem_percent_text_data, memory_percentage)
        display_themed_line_graph(gpu_mem_percent_line_graph_data, cls.last_values_gpu_mem_percentage)

        # GPU mem. absolute usage (M)
        gpu_mem_used_text_data = theme_gpu_data['MEMORY_USED']['TEXT']
        if math.isnan(memory_used_mb):
            memory_used_mb = 0
            if gpu_mem_used_text_data['SHOW']:
                logger.warning("Your GPU memory absolute usage (M) is not supported yet")
                gpu_mem_used_text_data['SHOW'] = False

        display_themed_value(
            theme_data=gpu_mem_used_text_data,
            value=int(memory_used_mb),
            min_size=5,
            unit=" M"
        )

        # GPU mem. total memory (M)
        gpu_mem_total_text_data = theme_gpu_data['MEMORY_TOTAL']['TEXT']
        if math.isnan(memory_used_mb):
            memory_used_mb = 0
            if gpu_mem_total_text_data['SHOW']:
                logger.warning("Your GPU total memory capacity (M) is not supported yet")
                gpu_mem_total_text_data['SHOW'] = False

        display_themed_value(
            theme_data=gpu_mem_total_text_data,
            value=int(total_memory_mb),
            min_size=5,  # Adjust min_size as necessary for your display
            unit=" M"  # Assuming the unit is in Megabytes
        )

        # GPU temperature (°C)
        gpu_temp_text_data = theme_gpu_data['TEMPERATURE']['TEXT']
        gpu_temp_radial_data = theme_gpu_data['TEMPERATURE']['RADIAL']
        gpu_temp_graph_data = theme_gpu_data['TEMPERATURE']['GRAPH']
        gpu_temp_line_graph_data = theme_gpu_data['TEMPERATURE']['LINE_GRAPH']

        if math.isnan(temperature):
            temperature = 0
            if gpu_temp_text_data['SHOW'] or gpu_temp_radial_data['SHOW'] or gpu_temp_graph_data[
                'SHOW'] or gpu_temp_line_graph_data['SHOW']:
                logger.warning("Your GPU temperature is not supported yet")
                gpu_temp_text_data['SHOW'] = False
                gpu_temp_radial_data['SHOW'] = False
                gpu_temp_graph_data['SHOW'] = False
                gpu_temp_line_graph_data['SHOW'] = False

        display_themed_temperature_value(gpu_temp_text_data, temperature)
        display_themed_progress_bar(gpu_temp_graph_data, temperature)
        display_themed_temperature_radial_bar(gpu_temp_radial_data, temperature)
        display_themed_line_graph(gpu_temp_line_graph_data, cls.last_values_gpu_temperature)

        # GPU FPS
        gpu_fps_text_data = theme_gpu_data['FPS']['TEXT']
        gpu_fps_radial_data = theme_gpu_data['FPS']['RADIAL']
        gpu_fps_graph_data = theme_gpu_data['FPS']['GRAPH']
        gpu_fps_line_graph_data = theme_gpu_data['FPS']['LINE_GRAPH']

        if fps < 0:
            fps = 0
            if gpu_fps_text_data['SHOW'] or gpu_fps_radial_data['SHOW'] or gpu_fps_graph_data[
                'SHOW'] or gpu_fps_line_graph_data['SHOW']:
                logger.warning("Your GPU FPS is not supported yet")
                gpu_fps_text_data['SHOW'] = False
                gpu_fps_radial_data['SHOW'] = False
                gpu_fps_graph_data['SHOW'] = False
                gpu_fps_line_graph_data['SHOW'] = False

        display_themed_progress_bar(gpu_fps_graph_data, fps)
        display_themed_value(
            theme_data=gpu_fps_text_data,
            value=int(fps),
            min_size=4,
            unit=" FPS"
        )
        display_themed_radial_bar(
            theme_data=gpu_fps_radial_data,
            value=int(fps),
            min_size=4,
            unit=" FPS"
        )
        display_themed_line_graph(gpu_fps_line_graph_data, cls.last_values_gpu_fps)

        # GPU Fan Speed (%)
        gpu_fan_text_data = theme_gpu_data['FAN_SPEED']['TEXT']
        gpu_fan_radial_data = theme_gpu_data['FAN_SPEED']['RADIAL']
        gpu_fan_graph_data = theme_gpu_data['FAN_SPEED']['GRAPH']
        gpu_fan_line_graph_data = theme_gpu_data['FAN_SPEED']['LINE_GRAPH']

        if math.isnan(fan_percent):
            fan_percent = 0
            if gpu_fan_text_data['SHOW'] or gpu_fan_radial_data['SHOW'] or gpu_fan_graph_data[
                'SHOW'] or gpu_fan_line_graph_data['SHOW']:
                logger.warning("Your GPU Fan Speed is not supported yet")
                gpu_fan_text_data['SHOW'] = False
                gpu_fan_radial_data['SHOW'] = False
                gpu_fan_graph_data['SHOW'] = False
                gpu_fan_line_graph_data['SHOW'] = False

        display_themed_percent_value(gpu_fan_text_data, fan_percent)
        display_themed_progress_bar(gpu_fan_graph_data, fan_percent)
        display_themed_percent_radial_bar(gpu_fan_radial_data, fan_percent)
        display_themed_line_graph(gpu_fan_line_graph_data, cls.last_values_gpu_fan_speed)

        # GPU Frequency (Ghz)
        gpu_freq_text_data = theme_gpu_data['FREQUENCY']['TEXT']
        gpu_freq_radial_data = theme_gpu_data['FREQUENCY']['RADIAL']
        gpu_freq_graph_data = theme_gpu_data['FREQUENCY']['GRAPH']
        gpu_freq_line_graph_data = theme_gpu_data['FREQUENCY']['LINE_GRAPH']
        display_themed_value(
            theme_data=gpu_freq_text_data,
            value=f'{freq_ghz:.2f}',
            unit=" GHz",
            min_size=4
        )
        display_themed_progress_bar(gpu_freq_graph_data, freq_ghz)
        display_themed_radial_bar(
            theme_data=gpu_freq_radial_data,
            value=f'{freq_ghz:.2f}',
            unit=" GHz",
            min_size=4
        )
        display_themed_line_graph(gpu_freq_line_graph_data, cls.last_values_gpu_frequency)

    @staticmethod
    def is_available():
        return sensors.Gpu.is_available()


class Memory:
    last_values_memory_swap = []
    last_values_memory_virtual = []

    @classmethod
    def stats(cls):
        memory_stats_theme_data = config.THEME_DATA['STATS']['MEMORY']

        swap_percent = sensors.Memory.swap_percent()
        save_last_value(swap_percent, cls.last_values_memory_swap,
                        memory_stats_theme_data['SWAP']['LINE_GRAPH'].get("HISTORY_SIZE", DEFAULT_HISTORY_SIZE))
        display_themed_progress_bar(memory_stats_theme_data['SWAP']['GRAPH'], swap_percent)
        display_themed_percent_radial_bar(memory_stats_theme_data['SWAP']['RADIAL'], swap_percent)
        display_themed_line_graph(memory_stats_theme_data['SWAP']['LINE_GRAPH'], cls.last_values_memory_swap)

        virtual_percent = sensors.Memory.virtual_percent()
        save_last_value(virtual_percent, cls.last_values_memory_virtual,
                        memory_stats_theme_data['VIRTUAL']['LINE_GRAPH'].get("HISTORY_SIZE", DEFAULT_HISTORY_SIZE))
        display_themed_progress_bar(memory_stats_theme_data['VIRTUAL']['GRAPH'], virtual_percent)
        display_themed_percent_radial_bar(memory_stats_theme_data['VIRTUAL']['RADIAL'], virtual_percent)
        display_themed_percent_value(memory_stats_theme_data['VIRTUAL']['PERCENT_TEXT'], virtual_percent)
        display_themed_line_graph(memory_stats_theme_data['VIRTUAL']['LINE_GRAPH'], cls.last_values_memory_virtual)

        display_themed_value(
            theme_data=memory_stats_theme_data['VIRTUAL']['USED'],
            value=int(sensors.Memory.virtual_used() / 1024 ** 2),
            min_size=5,
            unit=" M"
        )
        display_themed_value(
            theme_data=memory_stats_theme_data['VIRTUAL']['FREE'],
            value=int(sensors.Memory.virtual_free() / 1024 ** 2),
            min_size=5,
            unit=" M"
        )
        display_themed_value(
            theme_data=memory_stats_theme_data['VIRTUAL']['TOTAL'],
            value=int((sensors.Memory.virtual_free() + sensors.Memory.virtual_used()) / 1024 ** 2),
            min_size=5,
            unit=" M"
        )


class Disk:
    last_values_disk_usage = []

    @classmethod
    def stats(cls):
        used = sensors.Disk.disk_used()
        free = sensors.Disk.disk_free()

        disk_theme_data = config.THEME_DATA['STATS']['DISK']

        disk_usage_percent = sensors.Disk.disk_usage_percent()
        save_last_value(disk_usage_percent, cls.last_values_disk_usage,
                        disk_theme_data['USED']['LINE_GRAPH'].get("HISTORY_SIZE", DEFAULT_HISTORY_SIZE))
        display_themed_progress_bar(disk_theme_data['USED']['GRAPH'], disk_usage_percent)
        display_themed_percent_radial_bar(disk_theme_data['USED']['RADIAL'], disk_usage_percent)
        display_themed_percent_value(disk_theme_data['USED']['PERCENT_TEXT'], disk_usage_percent)
        display_themed_line_graph(disk_theme_data['USED']['LINE_GRAPH'], cls.last_values_disk_usage)

        display_themed_value(
            theme_data=disk_theme_data['USED']['TEXT'],
            value=int(used / 1000000000),
            min_size=5,
            unit=" G"
        )
        display_themed_value(
            theme_data=disk_theme_data['TOTAL']['TEXT'],
            value=int((free + used) / 1000000000),
            min_size=5,
            unit=" G"
        )
        display_themed_value(
            theme_data=disk_theme_data['FREE']['TEXT'],
            value=int(free / 1000000000),
            min_size=5,
            unit=" G"
        )


class Net:
    last_values_wlo_upload = []
    last_values_wlo_download = []
    last_values_eth_upload = []
    last_values_eth_download = []

    @classmethod
    def stats(cls):
        net_theme_data = config.THEME_DATA['STATS']['NET']
        interval = net_theme_data.get("INTERVAL", None)
        upload_wlo, uploaded_wlo, download_wlo, downloaded_wlo = sensors.Net.stats(WLO_CARD, interval)

        save_last_value(upload_wlo, cls.last_values_wlo_upload,
                        net_theme_data['WLO']['UPLOAD']['LINE_GRAPH'].get("HISTORY_SIZE", DEFAULT_HISTORY_SIZE))
        Net._show_themed_tax_rate(net_theme_data['WLO']['UPLOAD']['TEXT'], upload_wlo)
        Net._show_themed_total_data(net_theme_data['WLO']['UPLOADED']['TEXT'], uploaded_wlo)
        display_themed_line_graph(net_theme_data['WLO']['UPLOAD']['LINE_GRAPH'], cls.last_values_wlo_upload)

        save_last_value(download_wlo, cls.last_values_wlo_download,
                        net_theme_data['WLO']['DOWNLOAD']['LINE_GRAPH'].get("HISTORY_SIZE", DEFAULT_HISTORY_SIZE))
        Net._show_themed_tax_rate(net_theme_data['WLO']['DOWNLOAD']['TEXT'], download_wlo)
        Net._show_themed_total_data(net_theme_data['WLO']['DOWNLOADED']['TEXT'], downloaded_wlo)
        display_themed_line_graph(net_theme_data['WLO']['DOWNLOAD']['LINE_GRAPH'], cls.last_values_wlo_download)

        upload_eth, uploaded_eth, download_eth, downloaded_eth = sensors.Net.stats(ETH_CARD, interval)

        save_last_value(upload_eth, cls.last_values_eth_upload,
                        net_theme_data['ETH']['UPLOAD']['LINE_GRAPH'].get("HISTORY_SIZE", DEFAULT_HISTORY_SIZE))
        Net._show_themed_tax_rate(net_theme_data['ETH']['UPLOAD']['TEXT'], upload_eth)
        Net._show_themed_total_data(net_theme_data['ETH']['UPLOADED']['TEXT'], uploaded_eth)
        display_themed_line_graph(net_theme_data['ETH']['UPLOAD']['LINE_GRAPH'], cls.last_values_eth_upload)

        save_last_value(download_eth, cls.last_values_eth_download,
                        net_theme_data['ETH']['DOWNLOAD']['LINE_GRAPH'].get("HISTORY_SIZE", DEFAULT_HISTORY_SIZE))
        Net._show_themed_tax_rate(net_theme_data['ETH']['DOWNLOAD']['TEXT'], download_eth)
        Net._show_themed_total_data(net_theme_data['ETH']['DOWNLOADED']['TEXT'], downloaded_eth)
        display_themed_line_graph(net_theme_data['ETH']['DOWNLOAD']['LINE_GRAPH'], cls.last_values_eth_download)

    @staticmethod
    def _show_themed_total_data(theme_data, amount):
        display_themed_value(
            theme_data=theme_data,
            value=f"{bytes2human(amount)}",
            min_size=6
        )

    @staticmethod
    def _show_themed_tax_rate(theme_data, rate):
        display_themed_value(
            theme_data=theme_data,
            value=f"{bytes2human(rate, '%(value).1f %(symbol)s/s')}",
            min_size=10
        )


class Date:
    @staticmethod
    def stats():
        if HW_SENSORS == "STATIC":
            # For static sensors, use predefined date/time
            date_now = datetime.datetime.fromtimestamp(1694014609)
        else:
            date_now = datetime.datetime.now()

        if platform.system() == "Windows":
            # Windows does not have LC_TIME environment variable, use deprecated getdefaultlocale() that returns language code following RFC 1766
            lc_time = locale.getdefaultlocale()[0]
        else:
            lc_time = babel.dates.LC_TIME

        date_theme_data = config.THEME_DATA['STATS']['DATE']
        day_theme_data = date_theme_data['DAY']['TEXT']
        date_format = day_theme_data.get("FORMAT", 'medium')
        display_themed_value(
            theme_data=day_theme_data,
            value=f"{babel.dates.format_date(date_now, format=date_format, locale=lc_time)}"
        )

        hour_theme_data = date_theme_data['HOUR']['TEXT']
        time_format = hour_theme_data.get("FORMAT", 'medium')
        display_themed_value(
            theme_data=hour_theme_data,
            value=f"{babel.dates.format_time(date_now, format=time_format, locale=lc_time)}"
        )


class SystemUptime:
    @staticmethod
    def stats():
        if HW_SENSORS == "STATIC":
            # For static sensors, use predefined uptime
            uptimesec = 4294036
        else:
            uptimesec = int(uptime())

        uptimeformatted = str(datetime.timedelta(seconds=uptimesec))

        systemuptime_theme_data = config.THEME_DATA['STATS']['UPTIME']

        systemuptime_sec_theme_data = systemuptime_theme_data['SECONDS']['TEXT']
        display_themed_value(
            theme_data=systemuptime_sec_theme_data,
            value=uptimesec
        )

        systemuptime_formatted_theme_data = systemuptime_theme_data['FORMATTED']['TEXT']
        display_themed_value(
            theme_data=systemuptime_formatted_theme_data,
            value=uptimeformatted
        )


class Custom:
    @staticmethod
    def stats():
        for custom_stat in config.THEME_DATA['STATS']['CUSTOM']:
            if custom_stat != "INTERVAL":

                # Load the custom sensor class from sensors_custom.py based on the class name
                try:
                    custom_stat_class = getattr(sensors_custom, str(custom_stat))()
                    numeric_value = custom_stat_class.as_numeric()
                    string_value = custom_stat_class.as_string()
                    last_values = custom_stat_class.last_values()
                except Exception as e:
                    logger.error(
                        "Error loading custom sensor class " + str(custom_stat) + " from sensors_custom.py : " + str(e))
                    return

                if string_value is None:
                    string_value = str(numeric_value)

                # Display text
                theme_data = config.THEME_DATA['STATS']['CUSTOM'][custom_stat].get("TEXT", None)
                if theme_data is not None and string_value is not None:
                    display_themed_value(theme_data=theme_data, value=string_value)

                # Display graph from numeric value
                theme_data = config.THEME_DATA['STATS']['CUSTOM'][custom_stat].get("GRAPH", None)
                if theme_data is not None and numeric_value is not None and not math.isnan(numeric_value):
                    display_themed_progress_bar(theme_data=theme_data, value=numeric_value)

                # Display radial from numeric and text value
                theme_data = config.THEME_DATA['STATS']['CUSTOM'][custom_stat].get("RADIAL", None)
                if theme_data is not None and numeric_value is not None and not math.isnan(
                        numeric_value) and string_value is not None:
                    display_themed_radial_bar(
                        theme_data=theme_data,
                        value=numeric_value,
                        custom_text=string_value
                    )

                # Display plot graph from histo values
                theme_data = config.THEME_DATA['STATS']['CUSTOM'][custom_stat].get("LINE_GRAPH", None)
                if theme_data is not None and last_values is not None:
                    display_themed_line_graph(theme_data=theme_data, values=last_values)


import time
from typing import Any
from PIL import Image, ImageFont
import library.sensors.sensors_weather as sensors_weather


class Weather:
    IMAGES_LIST = [
        {
            "key": "current_weather",
            "api": "get_current_weather",
            "draw": "get_current_weather",
            "cache_seconds": 600,
        },
        {
            "key": "hourly_forecast",
            "api": "get_hourly_forecast",
            "draw": "get_hourly_forecast",
        },
        {
            "key": "daily_forecast",
            "api": "get_daily_forecast",
            "draw": "get_daily_forecast",
            "cache_seconds": 21600,
        },
        {
            "key": "warning",
            "api": "get_warning",
            "draw": "get_warning",
        },
        {
            "key": "air_quality",
            "api": "get_air_quality",
            "draw": "get_air_quality",
        },
        {
            "key": "precipitation",
            "api": "get_precipitation",
            "draw": "get_precipitation",
            "cache_seconds": 600,
        },
    ]
    cache: dict[str, Any] = {}

    @classmethod
    def stats(self):
        if not self.cache:
            draw_config = config.THEME_DATA["STATS"]["WEATHER"]["GRAPH"]
            weather_config = config.CONFIG_DATA.get("custom", {}).get("WEATHER", {})
            if not draw_config.get("SHOW", False) or not (weather_config.get("KEY") and weather_config.get("PUBLICID")):
                self.cache.update({
                    "show": False,
                })
                return

            ratio: int = draw_config.get("RATIO", 1)
            font: str = draw_config.get("FONT", "roboto-mono/RobotoMono-Regular.ttf")
            font_cache = display.lcd.font_cache
            for size in (12, 18):
                true_size = int(size * ratio)
                if (font, true_size) not in font_cache:
                    font_cache[(font, true_size)] = ImageFont.truetype("./res/fonts/" + font, true_size)

            if draw_config.get("BACKGROUND_IMAGE"):
                x = draw_config.get("X", 0)
                y = draw_config.get("Y", 0)
                basic_image = display.lcd.open_image(get_theme_file_path(draw_config.get("BACKGROUND_IMAGE"))).crop(
                    (x, y, x + int(200 * ratio), y + int(80 * ratio)))
            else:
                background_color = draw_config.get("BACKGROUND_COLOR", (0, 0, 0))
                if isinstance(background_color, str):
                    background_color = tuple(map(int, background_color.split(",")))
                basic_image = Image.new("RGB", (int(200 * ratio), int(80 * ratio)), background_color)

            draw = sensors_weather.WeatherDraw(
                font_cache[(font, int(12 * ratio))],
                font_cache[(font, int(18 * ratio))],
                draw_config.get("FONT_COLOR", (255, 255, 255)),
                basic_image,
                ratio,
            )

            api = sensors_weather.WeatherApi(
                weather_config.get("KEY", ""),
                weather_config.get("PUBLICID", ""),
                weather_config.get("LOCATIONID", ""),
                weather_config.get("COORDINATES", ""),
            )

            self.cache.update({
                "show": True,
                "api": api,
                "draw": draw,
                "draw_config": draw_config,
                "images": {},
                "last_index": -1,
                "last_image": None,
            })

        if not self.cache.get("show", False):
            return

        draw_config = self.cache.get("draw_config", {})
        duration = max(2, draw_config.get("DURATION", 10))
        now = time.time()
        index = int(now) // duration % len(self.IMAGES_LIST)
        image_data = self.IMAGES_LIST[index]
        key = image_data["key"]
        cache_seconds = image_data.get("cache_seconds", 1800)
        if key not in self.cache["images"] or now - self.cache["images"][key]["time"] > cache_seconds:
            try:
                data = getattr(self.cache["api"], image_data["api"])()
                image = getattr(self.cache["draw"], image_data["draw"])(data)
                self.cache["images"][key] = {
                    "image": image,
                    "time": now // cache_seconds * cache_seconds,
                }
                logger.debug(
                    f"Updated weather image: {key} ({datetime.datetime.fromtimestamp(now // cache_seconds * cache_seconds).strftime('%Y-%m-%d %H:%M:%S')})"
                )
            except Exception as e:
                logger.error(f"Failed to update weather image: {key} ({e})")

        if index != self.cache["last_index"]:
            x = draw_config.get("X", 0)
            y = draw_config.get("Y", 0)
            image = self.cache["images"][key]["image"]
            if draw_config.get("ANIMATION", False) and int(now) % duration == 0 and self.cache["last_image"] != None:
                new_image = image.copy()
                new_image.putalpha(int(now % 1 * 256))
                last_image = self.cache["last_image"].copy()
                last_image.paste(new_image, (0, 0), new_image)
                display.lcd.DisplayPILImage(last_image, x, y)
            else:
                display.lcd.DisplayPILImage(image, x, y)
                self.cache["last_index"] = index
                self.cache["last_image"] = image


import library.sensors.sensors_rss as sensors_rss


class Rss:
    cache: dict[str, Any] = {}

    @classmethod
    def stats(self):
        if not self.cache:
            draw_config = config.THEME_DATA["STATS"]["RSS"]["TEXT"]
            rss_config = config.CONFIG_DATA.get("custom", {}).get("RSS", [])
            if not draw_config.get("SHOW", False) or not rss_config:
                self.cache.update({
                    "show": False,
                })
                return

            display_themed_value(draw_config, "新闻正在载入……")
            feed_list = []
            for feed in rss_config:
                feed_list.append(sensors_rss.Feed(
                    feed["URL"],
                    feed.get("TITLE", ""),
                    feed.get("LIMIT", 10),
                ))

            self.cache.update({
                "show": True,
                "feed_list": feed_list,
                "draw_config": draw_config,
                "item_list": [],
                "last_index": -1,
                "last_image": None,
                "offset": 0,
            })

        if not self.cache.get("show", False):
            return

        draw_config = self.cache.get("draw_config", {})
        duration = max(2, int(draw_config.get("DURATION", 10)))
        now = time.time()
        item_list = self.cache["item_list"]

        index = 0 if not item_list else (int(now) // duration - self.cache["offset"]) % len(item_list)
        if index == 0:
            item_list = []
            for feed in self.cache["feed_list"]:
                items = feed.get_items()
                if not items:
                    continue
                item_list.append(feed.title)
                for item in items:
                    item_list.append(item["title"])
            self.cache["item_list"] = item_list
            self.cache["offset"] = int(now) // duration

        if not item_list:
            return

        text = item_list[index]
        if index != self.cache["last_index"]:
            image, x, y = display_themed_value(draw_config, text)
            if draw_config.get("ANIMATION", False) and int(now) % duration == 0 and self.cache["last_image"] != None:
                new_image = image.copy()
                new_image.putalpha(int(now % 1 * 256))
                last_image = self.cache["last_image"].copy()
                last_image.paste(new_image, (0, 0), new_image)
                display.lcd.DisplayPILImage(last_image, x, y)
            else:
                self.cache["last_index"] = index
                self.cache["last_image"] = image
