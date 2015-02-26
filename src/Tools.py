import hashlib

def md5(value):
    m = hashlib.md5()
    m.update(value)
    return m.hexdigest()


if __name__ == '__main__':
    print md5('123456')