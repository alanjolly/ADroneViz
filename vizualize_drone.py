import subprocess
import re
import math
import time
import threading
from ursina import *
from ursina.prefabs.editor_camera import EditorCamera

SENSITIVITY = 0.32
DEAD_ZONE = 0.02
SAMPLING_RATE = 0.08
SMOOTH_FACTOR = 0.25

sensor_data = {'pitch': 0.0, 'roll': 0.0, 'yaw': 0.0, 'throttle': 0.0}
data_lock = threading.Lock()

def get_sensor_data():
    try:
        result = subprocess.run(['adb', 'shell', 'dumpsys', 'sensorservice'],
                                capture_output=True, text=True, timeout=2)
        if result.returncode != 0 or not result.stdout: return None
        output = result.stdout

        accel = None
        for pat in [r'BMI160_ACCELEROMETER[^\n]*\n((?:.*\n)*?)(?=\n\S|\Z)',
                    r'Accelerometer[^\n]*\n((?:.*\n)*?)(?=\n\S|\Z)']:
            m = re.search(pat, output, re.MULTILINE)
            if m:
                for line in reversed(m.group(1).split('\n')):
                    nums = re.search(r'([\d.-]+),\s*([\d.-]+),\s*([\d.-]+)', line)
                    if nums: 
                        accel = tuple(map(float, nums.groups()))
                        break
                if accel: break

        gyro = None
        for pat in [r'BMI160_GYROSCOPE[^\n]*\n((?:.*\n)*?)(?=\n\S|\Z)',
                    r'Gyroscope[^\n]*\n((?:.*\n)*?)(?=\n\S|\Z)']:
            m = re.search(pat, output, re.MULTILINE)
            if m:
                for line in reversed(m.group(1).split('\n')):
                    nums = re.search(r'([\d.-]+),\s*([\d.-]+),\s*([\d.-]+)', line)
                    if nums: 
                        gyro = tuple(map(float, nums.groups()))
                        break
                if gyro: break

        if not accel and not gyro: return None
        data = {}
        if accel: data['accelerometer'] = {'x':accel[0],'y':accel[1],'z':accel[2]}
        if gyro:   data['gyroscope']     = {'x':gyro[0], 'y':gyro[1], 'z':gyro[2]}
        return data
    except: return None

def update_sensor_data():
    global sensor_data
    while True:
        raw = get_sensor_data()
        if raw:
            ax = raw.get('accelerometer',{}).get('x',0)
            ay = raw.get('accelerometer',{}).get('y',0)
            az = raw.get('accelerometer',{}).get('z',0)
            gx = raw.get('gyroscope',{}).get('x',0)
            gy = raw.get('gyroscope',{}).get('y',0)
            gz = raw.get('gyroscope',{}).get('z',0)

            if abs(gx)<DEAD_ZONE: gx=0
            if abs(gy)<DEAD_ZONE: gy=0
            if abs(gz)<DEAD_ZONE: gz=0

            if raw.get('gyroscope'):
                pitch = -gx * SENSITIVITY
                roll  =  gy * SENSITIVITY
                yaw   = -gz * SENSITIVITY
            else:
                pitch = math.atan2(ay, az) * 1.5
                roll  = math.atan2(ax, az) * 1.5
                yaw   = 0.0

            throttle = ((az-9.8)/9.8) * SENSITIVITY * 2.0
            pitch = max(-1.0, min(1.0, pitch))
            roll  = max(-1.0, min(1.0, roll))
            yaw   = max(-1.0, min(1.0, yaw))
            throttle = max(-1.0, min(1.0, throttle))

            with data_lock:
                sensor_data['pitch'] = pitch
                sensor_data['roll'] = roll
                sensor_data['yaw'] = yaw
                sensor_data['throttle'] = throttle
        time.sleep(SAMPLING_RATE)

class DroneVisualizer(Entity):
    def __init__(self):
        super().__init__()
        self.prop_assemblies = []
        self.last_time = time.time()
        self.current_pitch = self.current_roll = self.current_yaw = 0.0
        self.current_y = 0.65

        self.build_drone()
        self.setup_hud()
        threading.Thread(target=update_sensor_data, daemon=True).start()

    def build_drone(self):
        # === BLACK FUTURISTIC DRONE BODY ===
        # Main chassis (black)
        Entity(parent=self, model='cube', color=color.black,
               scale=(0.52, 0.13, 0.56), position=(0, 0.60, 0))
        # Top cover (slightly lighter black)
        Entity(parent=self, model='cube', color=color.rgba(15,15,18,255),
               scale=(0.40, 0.07, 0.44), position=(0, 0.71, 0))

        # Bright glowing cyan core
        self.core = Entity(parent=self, model='sphere', color=color.cyan,
                           scale=0.17, position=(0, 0.80, 0))

        # Holographic energy field (subtle cyan glow)
        self.glow = Entity(parent=self, model='sphere',
                           color=color.rgba(0, 200, 255, 28),
                           scale=2.0, position=(0, 0.62, 0))

        arm_len = 0.98
        motor_positions = [
            Vec3(-arm_len, 0.62,  arm_len),
            Vec3( arm_len, 0.62,  arm_len),
            Vec3( arm_len, 0.62, -arm_len),
            Vec3(-arm_len, 0.62, -arm_len),
        ]

        for i, mpos in enumerate(motor_positions):
            mid = (Vec3(0, 0.60, 0) + mpos) / 2
            dist = (mpos - Vec3(0, 0.60, 0)).length()
            yaw = math.degrees(math.atan2(mpos.x, mpos.z))

            # Black arms
            Entity(parent=self, model='cube', color=color.black,
                   scale=(0.052, 0.032, dist * 0.96), position=mid, rotation=(0, yaw, 0))

            # Black motor housing
            Entity(parent=self, model='cube', color=color.rgba(10,10,12,255),
                   scale=(0.15, 0.085, 0.15), position=mpos)

            # Bright neon LED ring (cyan or magenta)
            led_color = color.cyan if i % 2 == 0 else color.rgba(255, 40, 180, 255)
            Entity(parent=self, model='cube', color=led_color,
                   scale=(0.19, 0.007, 0.19),
                   position=(mpos.x, mpos.y + 0.062, mpos.z))

            # Prop hub (dark)
            hub = Entity(parent=self, model='cube', color=color.rgba(20,20,25,255),
                         scale=(0.055, 0.06, 0.055),
                         position=(mpos.x, mpos.y + 0.125, mpos.z))

            # Bright spinning propeller blades
            blades = Entity(parent=hub)
            blade_color = color.rgba(80, 220, 255, 255) if i % 2 == 0 else color.rgba(255, 100, 210, 255)
            for b in range(3):
                Entity(parent=blades, model='cube', color=blade_color,
                       scale=(0.013, 0.008, 0.30),
                       position=(0, 0.01, 0),
                       rotation=(0, b * 120, 0))

            self.prop_assemblies.append((blades, 1 if i % 2 == 0 else -1))

        # Black landing skids
        for sign in [-1, 1]:
            Entity(parent=self, model='cube', color=color.rgba(20,20,22,255),
                   scale=(1.25, 0.022, 0.038), position=(0, 0.33, sign * 0.40))
            for mx in [-0.46, 0.46]:
                Entity(parent=self, model='cube', color=color.rgba(25,25,28,255),
                       scale=(0.028, 0.24, 0.028), position=(mx, 0.45, sign * 0.40))

        # Front black sensor detail
        Entity(parent=self, model='cube', color=color.rgba(8,8,10,255),
               scale=(0.09, 0.065, 0.13), position=(0, 0.63, 0.40))

    def setup_hud(self):
        self.angle_text = Text('Pitch: 0.0°   Roll: 0.0°   Yaw: 0.0°',
                               position=(-0.82, 0.46), scale=1.85, color=color.cyan)
        self.throttle_text = Text('Throttle: 0.00',
                                  position=(-0.82, 0.40), scale=1.85, color=color.rgba(255, 80, 200, 255))
        Text('Mouse Drag = Orbit  |  Scroll = Zoom  |  Tilt phone to fly  |  ESC = Exit',
             position=(0, -0.48), scale=1.1, color=color.rgba(100, 200, 255, 200), origin=(0, 0))

    def update(self):
        with data_lock:
            p = sensor_data['pitch']
            r = sensor_data['roll']
            y = sensor_data['yaw']
            t = sensor_data['throttle']

        self.current_pitch = lerp(self.current_pitch, -p * 46, SMOOTH_FACTOR)
        self.current_roll  = lerp(self.current_roll,  r * 46, SMOOTH_FACTOR)
        self.current_yaw   = lerp(self.current_yaw,   y * 46, SMOOTH_FACTOR * 0.55)
        self.rotation = (self.current_pitch, self.current_yaw, self.current_roll)

        self.current_y = lerp(self.current_y, 0.65 + t * 0.48, 0.18)
        self.y = self.current_y

        # Fast spinning props
        dt = time.time() - self.last_time
        self.last_time = time.time()
        spin_speed = 350 + ((t + 1) / 2) ** 1.65 * 1550

        for blades, direction in self.prop_assemblies:
            blades.rotation_y += spin_speed * direction * dt

        # Subtle pulsing glow
        pulse = 1.85 + math.sin(time.time()*3.5)*0.07 + t*0.2
        self.glow.scale = (pulse, pulse*0.72, pulse)

        self.angle_text.text = f'Pitch: {self.current_pitch:+.1f}°   Roll: {self.current_roll:+.1f}°   Yaw: {self.current_yaw:+.1f}°'
        self.throttle_text.text = f'Throttle: {t:+.2f}'

def main():
    print("🚁 BLACK DRONE + BLUE/WHITE TILE VISUALIZER")
    print("Tilt your phone to control the black drone with bright cyan props")
    
    if "device" not in subprocess.getoutput("adb devices"):
        print("❌ Please connect your phone via ADB first.")
        return

    app = Ursina(title="Drone Visualizer - Black + Tiled Floor", vsync=True)
    window.color = color.rgba(245, 248, 255, 255)   # Light background

    # === BLUE + WHITE CHECKERED TILE FLOOR ===
    tile_size = 0.95
    tiles = 13
    offset = (tiles * tile_size) / 2

    dark_blue  = color.rgba(25, 55, 115, 255)
    light_tile = color.rgba(195, 210, 235, 255)

    for x in range(tiles):
        for z in range(tiles):
            col = dark_blue if (x + z) % 2 == 0 else light_tile
            Entity(model='cube',
                   scale=(tile_size, 0.06, tile_size),
                   color=col,
                   position=(x * tile_size - offset + tile_size/2, 0, 
                             z * tile_size - offset + tile_size/2))

    # Glowing central landing pad (cyan neon)
    Entity(model='cube', scale=(2.8, 0.08, 2.8), color=color.rgba(15, 25, 45, 255), position=(0, 0.04, 0))
    Entity(model='cube', scale=(3.1, 0.05, 3.1), color=color.cyan, position=(0, 0.09, 0))

    # Lighting
    AmbientLight(color=color.rgba(90, 95, 110, 255))
    DirectionalLight(color=color.rgba(255, 255, 255, 255), direction=(0.3, 0.9, 0.25))

    DroneVisualizer()
    EditorCamera(distance=6.5, rotation=(18, 42, 0), target=Vec3(0, 0.9, 0))

    app.run()

if __name__ == "__main__":
    main()
