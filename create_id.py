import time
import re
import random


def create_id():
    time_stamp = time.time()
    time_stamp = re.sub(r'\.', '', str(time_stamp))
    time_stamp = ''.join([t for t in time_stamp][-14:])
    random_int = str(random.randint(100, 999))
    random_id = random_int + time_stamp
    return random_id

