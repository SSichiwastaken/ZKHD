import json
import time
import hashlib
import numpy as np
import os

from sensor_sim import simulate
from hypervector import encode
from fuzzy_extractor import FuzzyExtractor
from zk_protocol import Prover, Verifier


SERVER_STORAGE = {}

def noise(v, noise_level):
    if noise_level == 0.0:
        return v
    
    # Each bit has a noise_level probability of being selected.
    flip_mask = np.random.rand(v.shape[0]) < noise_level
    
    v_noisy = v.copy()
    v_noisy[flip_mask] *= -1
    
    return v_noisy

def register(username):
    print(f"\n#--------- Registering User: {username} ---------#")
    enroll_data = simulate(username)
    v_ref = encode(enroll_data)
    
    extractor = FuzzyExtractor()
    S = extractor.bipolar2binary(v_ref)
    
    k = hashlib.sha512(S.tobytes()).digest()
    prover = Prover(k)
    P = prover.pkey()

    SERVER_STORAGE[username] = {
        "S": S.tolist(),
        "P": P.hex()
    }
    print(f"    User: '{username}' registered successfully.")
    print(f"    Stored Public Key P: {P.hex()[:12]}...")
    print("#-----------------------------------------------#")
    with open(f"{username}_enrollment.json", "w") as f:
        json.dump({ "username": username, "storage": { "S_shape": np.array(SERVER_STORAGE[username]['S']).shape, "P": SERVER_STORAGE[username]['P'] } }, f, indent=2)

def login(username, noise_level=0.0, verbose=True):
    if verbose:
        print(f"\nAuthenticating User: {username} (Noise: {noise_level:.2f})")
    start_time = time.time()
    
    if username not in SERVER_STORAGE:
        if verbose: print("Authentication Failed: User not found.")
        return False, 0.0

    # Client-side
    login_data = simulate(username)
    v_prime_ideal = encode(login_data)
    v_prime_noisy = noise(v_prime_ideal, noise_level)
    
    S = np.array(SERVER_STORAGE[username]['S'], dtype=np.uint8)
    extractor = FuzzyExtractor()
    v_reconstructed = extractor.reproduce(v_prime_noisy, S)

    # If reconstruction fails, authentication stops.
    if v_reconstructed is None:
        latency = time.time() - start_time
        if verbose:
            print(f" - FAIL - Authentication Failed. (Latency: {latency:.4f}s)")
            print(" - Reason: Key could not be reproduced from noisy vector.")
        return False, latency

    k_reproduced = hashlib.sha512(v_reconstructed.tobytes()).digest()
    prover = Prover(k_reproduced)

    # ZKP
    session_id = os.urandom(16)
    R, s = prover.proof(public_context=b"ZKHD_AUTH_V1", session_id=session_id)
    if verbose: 
        print(f"    1. Prover -> Verifier: Proof (R, s)")
        print(f"       - R (Commitment): {R.hex()[:12]}...")
        print(f"       - s (Response):   {s.hex()[:12]}...")

    # Server-side
    P_stored = bytes.fromhex(SERVER_STORAGE[username]['P'])
    verifier = Verifier(P_stored)
    
    is_valid_proof = verifier.verify(R, s, public_context=b"ZKHD_AUTH_V1", session_id=session_id)
    latency = time.time() - start_time
    
    # Result
    log_data = { "username": username, "noise_level": noise_level, "success": is_valid_proof, "latency_ms": latency * 1000, "transcript": { "R": R.hex(), "s": s.hex() } }
    with open(f"{username}_login_attempt_{time.time()}.json", "w") as f:
        json.dump(log_data, f, indent=2)

    if is_valid_proof:
        if verbose: print(f" - SUCCESS - Authentication Successful! (Latency: {latency:.4f}s)")
        return True, latency
    else:
        if verbose:
            print(f" - FAIL - Authentication Failed. (Latency: {latency:.4f}s)")
            print("  - Reason: Zero-Knowledge Proof verification failed.")
        return False, latency

def frr(username, test_noise_level, n_runs=30):
    print(f"\n--- Simulating FRR at {test_noise_level*100:.1f}% Noise ---")
    failures = 0
    for i in range(n_runs):
        print(f"  Running test {i+1}/{n_runs}...", end='\r')
        success, _ = login(username, noise_level=test_noise_level, verbose=False)
        if not success:
            failures += 1
    frr = (failures / n_runs) * 100
    print(f"\nSimulation Complete.                                  ")
    print(f"False Rejection Rate: {frr:.1f}% ({failures}/{n_runs} failures)")
    
def test():
    username = "ZKHD_USER"
    
    register(username)
    
    login(username, noise_level=0.0, verbose=True)      
    login(username, noise_level=0.03, verbose=True)     
    login(username, noise_level=0.04, verbose=True)     
    
    frr(username, test_noise_level=0.034)

    frr(username, test_noise_level=0.04)

if __name__ == "__main__":
    test()