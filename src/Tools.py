import time
import hashlib

def g_md5(value):
    m = hashlib.md5()
    m.update(value)
    return m.hexdigest()

def g_time():
    return int(time.time())

if __name__ == '__main__':
    print g_md5('123456')