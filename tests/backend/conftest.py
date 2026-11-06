import bcrypt

# Tests only: make password hashing fast. Real passwords still use the normal, slow setting.
real_gensalt = bcrypt.gensalt
bcrypt.gensalt = lambda rounds=12, prefix=b"2b": real_gensalt(4, prefix)
