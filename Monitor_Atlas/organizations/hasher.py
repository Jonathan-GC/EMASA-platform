import os
import time
import hashlib


def generate_id():
    """
    output example: 'a9f2c1e7bd3a1wqz', 16 characters long to avoid collisions;
    collision rate: 1 in 56 billion for 1 million ids
    """
    random_data = os.urandom(16)
    timestamp = str(time.time()).encode("utf-8")
    hash_input = random_data + timestamp
    hash_output = hashlib.sha256(hash_input).hexdigest()
    unique_id = hash_output[:16]
    return unique_id
