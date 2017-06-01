#!/usr/bin/python3
import scapy.all as sc
import sys
import math as m
from scipy import stats
from time import time
from traceroute import armar_rutas


def rtt_promedio(tanda):
    return sum([pair[1] for pair in tanda]) / len(tanda )

def ip_maximas_apariciones(tanda, ruta):
    # esto por el caso muy droga en que se agreguen nodos entre mediciones
    usadas = [ip for ip, rtt in ruta]
    ips = [ip for ip, rtt in tanda if ip not in usadas]
    sorted_sin_repetir = sorted(set(ips), key=ips.count, reverse=True)
    if sorted_sin_repetir:
        return sorted_sin_repetir[0]
    else:
        return ""

def ruta_promedio(times):
    ruta = []
    for ttl, tanda in times.items():
        proxima_ip = ip_maximas_apariciones(tanda, ruta)
        if tanda and proxima_ip:
            ruta.append((proxima_ip, rtt_promedio(tanda)))
    return ruta

def tau(n):
    t = stats.t.ppf(1-0.025, n-2)
    return t*(n - 1) / (m.sqrt(n)*m.sqrt(n-2 + t**2))

def sacar_outliers(ruta):
    outliers = []
    rtt_media = rtt_promedio(ruta)
    n = len(ruta)
    rtt_sd = m.sqrt( sum( [(pair[1]-rtt_media)**2 for pair in ruta]) / n)

    for ip, rtt in ruta:
        if abs(rtt - rtt_media)/rtt_sd < tau(n):
            outliers.append(ip)
    return outliers

if __name__ == '__main__':
    dst = sys.argv[1] if len(sys.argv) > 1 else "www.uwa.edu.au"
    iters = int(sys.argv[2]) if len(sys.argv) > 2 else 30

    rtts = armar_rutas(dst, iters)
    ruta = ruta_promedio(rtts)
    ruta_outliers = sacar_outliers(ruta)

    print(ruta_outliers)
