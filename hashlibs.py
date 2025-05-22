import hashlib

def hash_sha256(input_string: str) -> str:
    """
    Hashes the given input string using SHA-256 and returns the hexadecimal digest.
    """
    sha256_hash = hashlib.sha256()
    sha256_hash.update(input_string.encode('utf-8'))
    return sha256_hash.hexdigest()

if __name__ == "__main__":
    input_string = input("Enter a string to hash: ")
    hashed_value = hash_sha256(input_string)
    print(f"SHA-256 Hash: {hashed_value}")
 # type: ignore
 