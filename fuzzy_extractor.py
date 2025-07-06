import numpy as np


class FuzzyExtractor:
    def __init__(self, hd_dim=10000):
        self.hd_dim = hd_dim
        self.max_noise = int(hd_dim * 0.038) # 3.8% noise tolerance (~380 bit-flips)

    def bipolar2binary(self, v):
        return ((v + 1) // 2).astype(np.uint8)

    def reproduce(self, v_prime, S):
        v_prime = self.bipolar2binary(v_prime)
        hamming_distance = np.sum(np.bitwise_xor(v_prime, S))
        
        if hamming_distance <= self.max_noise:
            return S
        else:
            return None