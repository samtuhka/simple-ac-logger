import struct
import matplotlib.pyplot as plt
import numpy as np
from logger import parse_message

from base64 import b64decode


f = open("raw.csv")
locs = []

for line in f:
    msg = line.split(",")
    msg = b64decode(msg[1].encode('utf-8'))
    val, msg = parse_message(msg)
    if val: #e:
        t = msg.split(",")
        locs.append([float(t[-1]), float(t[-3])])
       
locs = np.array(locs)
plt.plot(locs[:,0], locs[:,1], 'og', alpha = 0.5)


f = open("parsed.csv")
locs = []

for line in f:
    t = line.split(",")
    locs.append([float(t[-1]), float(t[-3])])

locs = np.array(locs)
plt.plot(locs[:,0], locs[:,1], '.r', alpha = 0.5)
plt.show()