from nacl.signing import SigningKey, VerifyKey
from nacl.exceptions import BadSignatureError
from nacl.encoding import RawEncoder

# Using Ed25519 for the Schnorr-based ZKP.

class Prover:
    def __init__(self, k_scalar):
        if len(k_scalar) != 64: # SHA-512 output
             raise ValueError("Secret scalar k must be 64 bytes (from SHA-512).")
        self.signing_key = SigningKey(k_scalar[:32])

    def pkey(self):
        return self.signing_key.verify_key.encode()

    def proof(self, public_context, session_id):
        message = public_context + session_id
        signed_msg = self.signing_key.sign(message, encoder=RawEncoder)
        
        return signed_msg.signature[:32], signed_msg.signature[32:]

class Verifier:
    def __init__(self, P): # P = public key
        if len(P) != 32:
            raise ValueError("Public key P must be 32 bytes.")
        self.verify_key = VerifyKey(P)

    def verify(self, R, s, public_context, session_id):
        try:
            message = public_context + session_id
            signature = R + s
            self.verify_key.verify(message, signature, encoder=RawEncoder)
            return True
        except BadSignatureError:
            return False