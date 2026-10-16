import bcrypt

def hash_password(password: str) -> str:
    """ Turn a plain password into a scrambled hash to safely store in our database. """
    
    password_bytes = password.encode('utf-8')
    hashed = bcrypt.hashpw(password_bytes, bcrypt.gensalt())
    return hashed.decode('utf-8')

def verify_password(password: str, hashed_password: str) -> bool:
    """ Check if a plain password matches the hashed password. """

    return bcrypt.checkpw(
        password.encode('utf-8'),
        hashed_password.encode('utf-8')
    )