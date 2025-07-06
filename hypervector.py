import numpy as np
import hashlib


HD_DIM = 10000 # Hypervector

def vector(seed):
    seed = int.from_bytes(hashlib.sha256(seed.encode()).digest(), 'big')
    rng = np.random.default_rng(seed)
    vec = rng.choice([-1, 1], size=HD_DIM)
    return vec.astype(np.int8)

def bind(v1, v2):
    if v1.shape != v2.shape:
        raise ValueError("Vectors must have the same shape.")
    return v1 * v2

def rotate(v, n):
    return np.roll(v, n)

def bundle(vectors):
    sum_vec = np.sum(vectors, axis=0)
    return np.where(sum_vec >= 0, 1, -1).astype(np.int8)

def encode(sensor_data):
    sensor_vecs = []
    
    for sensor_type, data in sensor_data.items():
        sensor_vec = vector(sensor_type)
        
        if data.ndim == 1:
            data = data.reshape(1, -1)
        
        quantized_vals = np.round(data * 10).astype(int) # 10 = quantization scale
        
        for i, axis_data in enumerate(quantized_vals):
            axis_vec = rotate(sensor_vec, i + 1)
            for val in axis_data:
                level_vec = vector(str(val))
                bound_vec = bind(axis_vec, level_vec)
                sensor_vecs.append(bound_vec)

    return bundle(sensor_vecs)