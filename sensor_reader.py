import subprocess
import re
import time

def get_sensor_data():
    """Fetch latest accelerometer and gyroscope data from Android via ADB."""
    try:
        result = subprocess.run(
            ['adb', 'shell', 'dumpsys', 'sensorservice'],
            capture_output=True, text=True, timeout=2
        )
        if result.returncode != 0:
            return None

        output = result.stdout
        data = {}

        # Accelerometer
        accel_section = re.search(
            r'(?:BMI160_ACCELEROMETER|Accelerometer)[^\n]*\n((?:.*\n)*?)(?=\n\S|\Z)',
            output, re.MULTILINE | re.IGNORECASE
        )
        if accel_section:
            for line in reversed(accel_section.group(1).split('\n')):
                match = re.search(r'([\d.-]+),\s*([\d.-]+),\s*([\d.-]+)', line)
                if match:
                    data['accelerometer'] = {
                        'x': float(match.group(1)),
                        'y': float(match.group(2)),
                        'z': float(match.group(3))
                    }
                    break

        # Gyroscope
        gyro_section = re.search(
            r'(?:BMI160_GYROSCOPE|Gyroscope)[^\n]*\n((?:.*\n)*?)(?=\n\S|\Z)',
            output, re.MULTILINE | re.IGNORECASE
        )
        if gyro_section:
            for line in reversed(gyro_section.group(1).split('\n')):
                match = re.search(r'([\d.-]+),\s*([\d.-]+),\s*([\d.-]+)', line)
                if match:
                    data['gyroscope'] = {
                        'x': float(match.group(1)),
                        'y': float(match.group(2)),
                        'z': float(match.group(3))
                    }
                    break

        return data if data else None

    except Exception:
        return None


if __name__ == "__main__":
    print("Reading Android sensor data via ADB... (Ctrl+C to stop)")
    while True:
        data = get_sensor_data()
        if data:
            print(data)
        time.sleep(0.1)
