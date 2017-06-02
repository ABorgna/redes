#!/usr/bin/python3

# parámetros: <destino> <iteraciones>

# Filtra el warning por IPv6 de scapy
import logging
logging.getLogger("scapy.runtime").setLevel(logging.ERROR)
import scapy.all as sc

import argparse
from numpy import mean, std, warnings
from scipy.stats import mode
import sys
from time import time

TIMEOUT = 1
MAX_TTL=30


def armar_rutas(dst, iteraciones, ans_unans):
    ans_unans[0], ans_unans[1] = 0, 0 # [answered, unanswered]

    for ttl_actual in range(1, MAX_TTL+1):
        ttl_times = []
        replied = False

        for i in range(iteraciones):
            packet = sc.IP(dst=dst,ttl=ttl_actual)/sc.ICMP()
            initial_t = time()
            ans,unans = sc.sr(packet, timeout=TIMEOUT, verbose=False)
            final_t = (time() - initial_t)*1000

            if ans:
                ans_unans[0] +=  1
                s, r = ans[0]

                if r.haslayer(sc.ICMP) and r.payload.type in [11, 0]: # time-exceeded o reply
                    ip = r.src
                    #print(ip)

                    ttl_times.append((ip, final_t))

                    if r.payload.type == 0: # ya llegó a destino
                        replied = True

            if unans:
                ans_unans[1] += 1

        yield ttl_actual, ttl_times

        if replied:
            break

def print_summary(times, ans_unans):
    print("ttl: ip                    min       avg       max      mdev  relativo ans/unans")
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

def print_detailed(times, ans_unans):
    print("TODO")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Correr un traceroute")

    parser.add_argument("host", default="www.msu.ru", help="(default: www.msu.ru)")
    parser.add_argument("iteraciones", default=3, type=int, help="(default: 3)")
    parser.add_argument("-v", "--verbose", action="store_true")

    args = parser.parse_args()

    ans_unans = []
    times = armar_rutas(args.host, args.iteraciones, ans_unans)

    if args.verbose:
        print_detailed(times, ans_unans)
    else:
        print_summary(times, ans_unans)

