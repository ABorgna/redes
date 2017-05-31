import scapy.all as sc
import sys
from time import time

TIMEOUT = 1
MAX_TTL=30

RESULTS=0
UNANSWERED=1


def armar_rutas(dst, iteraciones):
    times = {}

    for ttl_actual in range(1, MAX_TTL+1):
        times[ttl_actual] = []

        for i in range(iteraciones):
            packet = sc.IP(dst=dst,ttl=ttl_actual)/sc.ICMP()
            initial_t = time()
            ans,unans = sc.sr(packet,timeout=TIMEOUT)
            final_t = time() - initial_t

            if ans:
                s, r = ans[0]

                if r.haslayer(sc.ICMP) and r.payload.type in [11, 0]: # time-exceeded o reply
                    ip = r.src
                    #print(ip)

                    times[ttl_actual].append((ip, final_t))

                    if r.payload.type == 0: # ya llegó a destino
                        break
    return times



if __name__ == '__main__':
    dst = sys.argv[1] if len(sys.argv) > 1 else "www.google.com"
    iters = int(sys.argv[2]) if len(sys.argv) > 2 else 30
    times = armar_rutas(dst, iters)

    for ttl, tanda in times.items():
        if tanda:
            print(" TTL: {} ----------".format(ttl))
            for ip, tiempo in tanda:
                print(" IP: {}\n Tiempo medido: {}".format(ip, tiempo))
