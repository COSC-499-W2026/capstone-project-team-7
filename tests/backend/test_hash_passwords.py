from utils.passwords import hash_password, verify_password

def test_hash_is_not_plaintext():
    hashed = hash_password("MysecretPassword123")
    assert hashed != "MysecretPassword123"

def test_same_password_hashes_differ():
    hashed1 = hash_password("MysecretPassword123")
    hashed2 = hash_password("MysecretPassword123")
    assert hashed1 != hashed2

def test_verify_password_correct():
    hashed = hash_password("MysecretPassword123")
    assert verify_password("MysecretPassword123", hashed) == True

def test_verify_password_incorrect():
    hashed = hash_password("MysecretPassword123")
    assert verify_password("WrongPassword456", hashed) == False