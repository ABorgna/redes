import scapy.all as sc
from time import time

TIMEOUT = 5
MIN_TTL=1
MAX_TTL=30

RESULTS=0
UNANSWERED=1

times = []

DST = ["www.google.com"]

packet = sc.IP(dst=DST,ttl=(MIN_TTL,MAX_TTL))/sc.ICMP()


for p in packet:
    initial_t = time()
    ans,unans = sc.sr(p,timeout=TIMEOUT)
    final_t = time() - initial_t
    s, r = ans[0]

    if r.haslayer(sc.ICMP) and r.payload.type in [11, 0]: # time-exceeded o reply
        ip = r.src
        print(ip)
        times.append((ip, final_t))

        if r.payload.type == 0: # ya llegó a destino
            break


for ip, tiempo in times:
    print(" -------\n IP: {}\n Tiempo medido: {}".format(ip, tiempo))
