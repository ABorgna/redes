#!/usr/bin/python3

# parámetros: <destino> <iteraciones>

# Filtra el warning por IPv6 de scapy
import logging
logging.getLogger("scapy.runtime").setLevel(logging.ERROR)
import scapy.all as sc

import argparse
from concurrent.futures import ThreadPoolExecutor
from numpy import mean, std, warnings
from scipy.stats import mode
import sys
from time import time

TIMEOUT = 1
MAX_TTL=30

def ip_maximas_apariciones(tanda, ips_usadas):
    # esto por el caso muy droga en que se agreguen nodos entre mediciones
    ips = [ip for ip, rtt in tanda if ip not in ips_usadas]
    sorted_sin_repetir = sorted(set(ips), key=ips.count, reverse=True)
    if sorted_sin_repetir:
        return sorted_sin_repetir[0]
    else:
        return ""

def armar_rutas(dst, iteraciones, parallel=True):
    for ttl_actual in range(1, MAX_TTL+1):
        # Usar ICMP o UDP (que nos permite mandar en paralelo, mas rápido)
        _send = _send_parallel if parallel else _send_serial

        ttl_times, replied = _send(dst, ttl_actual, iteraciones)
        yield ttl_actual, ttl_times

        if replied:
            break

def _send_serial(dst, ttl, count):
    ''' Manda [count] request y mide los tiempos de respuesta y la ip
    '''
    replied = False
    ip_times = []

    packet = sc.IP(dst=dst,ttl=ttl)/sc.ICMP()

    for i in range(count):
        ans,unans = sc.sr(packet, timeout=TIMEOUT, verbose=False)
        if ans:
            s, r = ans[0]
            final_t = (r.time - s.sent_time) * 1000

            if r.haslayer(sc.ICMP) and r.payload.type in [11, 0]: # time-exceeded o reply
                ip = r.src
                if r.payload.type == 0: # ya llegó a destino
                    replied = True

                ip_times.append((ip, final_t))

    return ip_times, replied


def _send_parallel(dst, ttl, count):
    ''' Manda [count] request en paralelo y mide los tiempos de respuesta y la ip

        Necesitamos usar UDP para distingir cual es nuestro mensaje segun el puerto
        Traceroute usa el rango de puertos de destino 33434-33534, así que lo copiamos
    '''
    replied = False
    ip_times = []

    def worker(id):
        packet = sc.IP(dst=dst,ttl=ttl, id=id)/sc.UDP(dport=33434+id)
        ans,unans = sc.sr(packet, timeout=TIMEOUT, verbose=False)

        ip_time = None
        replied = None
        if ans:
            s, r = ans[0]
            final_t = (r.time - s.sent_time) * 1000

            if r.haslayer(sc.ICMP) and r.payload.type in [11]: # time-exceeded o reply
                ip_time = r.src, final_t
                replied = False
            elif r.src == dst:
                ip_time = dst, final_t
                replied = True # ya llegó a destino

        return ip_time, replied

    with ThreadPoolExecutor(max_workers=8) as executor:
        for ip_time, rep in executor.map(worker, range(count)):
            if ip_time is not None:
                ip_times.append(ip_time)
                replied |= rep

    return ip_times, replied

def print_summary(times):
    print("ttl: ip                    min       avg       max      mdev  relativo")
    ans = 0
    total = 0
    last_t = 0
    ips_vistas = []
    for ttl, tanda in times:
        total += 1
        ip = ip_maximas_apariciones(tanda, ips_vistas)
        ips_vistas.append(ip)
        ts = [t for ip_tanda, t in tanda if ip_tanda == ip]
        if tanda and ip and ts:
            ans += 1
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

    print("-" * 70)
    print("Saltos que responden:", ans, "({:.2f}% del total)".format(100 * ans / total))

def print_detailed(times):
    ans = 0
    total = 0
    for ttl, tanda in times:
        total += 1
        if tanda:
            ans += 1
            print(" TTL: {} ----------".format(ttl))
            for ip, tiempo in tanda:
                print(" IP: {}\n Tiempo medido: {}".format(ip, tiempo))

    print("-" * 19)
    print("Saltos que responden:", ans, "({:.2f}% del total)".format(100 * ans / total))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Correr un traceroute")

    parser.add_argument("host", default="www.msu.ru", nargs="?",
            help="(default: www.msu.ru)")
    parser.add_argument("iteraciones", default=3, nargs="?", type=int,
            help="(default: 3)")
    parser.add_argument("-I", "--ICMP", action="store_true",
            help="usar versión ICMP (mas lenta)")
    parser.add_argument("-v", "--verbose", action="store_true")

    args = parser.parse_args()

    times = armar_rutas(args.host, args.iteraciones, not args.ICMP)

    if args.verbose:
        print_detailed(times)
    else:
        print_summary(times)

