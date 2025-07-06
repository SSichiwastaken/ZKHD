import numpy as np

# Prototype Sensor Data in HZ
KEYSTROKE = 2000
ACCELEROMETER = 100
HEARTRATE = 60
TIME = 3

def signals(hz, duration, base_val, noise_factor, periodic=False):
    num_points = int(hz * duration)
    time = np.linspace(0, duration, num_points, endpoint=False)
    if periodic:
        signal = base_val + np.sin(time * np.pi) * (base_val * 0.1)
    else:
        signal = np.full(num_points, base_val)
    
    noise = (np.random.randn(num_points)) * noise_factor
    return signal + noise

def keystroke(user_id, noise=0.01):
    base_latency = 120 - (hash(user_id) % 40) # Milliseconds
    return signals(KEYSTROKE, TIME, base_latency, noise)

def accelerometer(user_id, noise=0.1):
    base_g = 1.0 + (hash(user_id) % 10) / 100.0
    accel_x = signals(ACCELEROMETER, TIME, base_g * 0.1, noise, periodic=True)
    accel_y = signals(ACCELEROMETER, TIME, base_g * 0.2, noise, periodic=True)
    accel_z = signals(ACCELEROMETER, TIME, base_g * 0.9, noise, periodic=True)
    return np.vstack([accel_x, accel_y, accel_z])

def heartrate(user_id, noise=1.0):
    base_hr = 60 + (hash(user_id) % 20)
    return signals(HEARTRATE, TIME, base_hr, noise, periodic=True)

def simulate(user_id, noise_level=0.0):
    return {
        "keystroke": keystroke(user_id, noise_level * 0.1),
        "accelerometer": accelerometer(user_id, noise_level * 0.5),
        "heart_rate": heartrate(user_id, noise_level * 1.0),
    }