# ADroneViz

**Real-time Android IMU-Controlled 3D Futuristic Drone Simulator using ADB**

ADroneViz allows you to use your Android phone as a wireless IMU controller for 3D drone simulation via ADB. It reads live accelerometer and gyroscope data and can be used as a backend for real-time visualization and training scenarios.

## Features
- Clean ADB-based sensor reader for accelerometer & gyroscope
- Modular and reusable `sensor_reader.py`
- Designed for real-time 3D drone control and visualization
- Suitable for cybersecurity training and sensor data simulation

## Project Structure

```
ADroneViz/
├── sensor_reader.py     # Main ADB sensor module
├── README.md
├── requirements.txt
├── .gitignore
└── LICENSE
```

## Usage

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the sensor reader
```bash
python3 sensor_reader.py
```
### 3. Run drone vizualizer
```bash
python3 vizualize_drone.py
``` 

## How It Works
- Executes `adb shell dumpsys sensorservice`
- Parses accelerometer and gyroscope values using regex
- Returns clean structured data ready for visualization or processing

## Author
**Alan Jolly**  
Founder & CEO, Allegorix  
[allegorix.in](https://allegorix.in)

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
