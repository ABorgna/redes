#!/usr/bin/python3

# parámetros: <destino> <iteraciones>
import logging
logging.getLogger("scapy.runtime").setLevel(logging.ERROR)
import scapy.all as sc

from numpy import mean, std, warnings
from scipy.stats import mode
import sys
from time import time

TIMEOUT = 1
MAX_TTL=30

RESULTS=0
UNANSWERED=1


def armar_rutas(dst, iteraciones):
    for ttl_actual in range(1, MAX_TTL+1):
        ttl_times = []
        replied = False

        for i in range(iteraciones):
            packet = sc.IP(dst=dst,ttl=ttl_actual)/sc.ICMP()
            initial_t = time()
            ans,unans = sc.sr(packet, timeout=TIMEOUT, verbose=False)
            final_t = (time() - initial_t)*1000

            if ans:
                s, r = ans[0]

                if r.haslayer(sc.ICMP) and r.payload.type in [11, 0]: # time-exceeded o reply
                    ip = r.src
                    #print(ip)

                    ttl_times.append((ip, final_t))

                    if r.payload.type == 0: # ya llegó a destino
                        replied = True

        yield ttl_actual, ttl_times

        if replied:
            break

if __name__ == '__main__':
    dst = sys.argv[1] if len(sys.argv) > 1 else "www.msu.ru"
    iters = int(sys.argv[2]) if len(sys.argv) > 2 else 30
    times = armar_rutas(dst, iters)

    print("ttl: ip                    min       avg       max      mdev  relativo")
    last_t = 0
    for ttl, tanda in times:
        if tanda:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                ip = mode([ip for ip, t in tanda]).mode[0]
            ts = [t for ip_tanda, t in tanda if ip_tanda == ip]
            ts.sort()
            if len(ts) > 1:
                print("{:3}: {:15} {:7.2f}ms {:7.2f}ms {:7.2f}ms {:7.2f}ms {:7.2f}ms".format(
                    ttl, ip, min(ts), mean(ts), max(ts), std(ts), mean(ts)-last_t))
            else:
                # No variance
                print("{:3}: {:15} {:7.2f}ms {:7.2f}ms {:7.2f}ms         * {:7.2f}ms".format(
                    ttl, ip, ts[0], ts[0], ts[0], mean(ts)-last_t))
            last_t = mean(ts)
        else:
            print("{:3}: *                       *         *         *         *         *".format(ttl, ip))

