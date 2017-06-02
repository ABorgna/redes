#!/usr/bin/python3

# parámetros: <destino> <iteraciones>

import scapy.all as sc
import sys
import math as m
from scipy import stats
from time import time
from traceroute import armar_rutas

from numpy import mean, std


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
    for ttl, tanda in times:
        proxima_ip = ip_maximas_apariciones(tanda, ruta)
        chose_ones = [rtt for ip, rtt in tanda if ip == proxima_ip]
        if tanda and proxima_ip and chose_ones:
            ruta.append((proxima_ip, mean(chose_ones)))
    return ruta

def tau(n):
    t = stats.t.ppf(1-0.025, n-2)
    return t*(n - 1) / (m.sqrt(n)*m.sqrt(n-2 + t**2))

def sacar_outliers(ruta):
    outliers = []
    rtts = [rtt for ip, rtt in ruta]
    rtt_media = mean(rtts)
    rtt_sd = std(rtts)
    n = len(ruta)

    for ip, rtt in ruta:
        if abs(rtt - rtt_media)/rtt_sd > tau(n):
            outliers.append(ip)
    return outliers

if __name__ == '__main__':
    dst = sys.argv[1] if len(sys.argv) > 1 else "www.msu.ru"
    iters = int(sys.argv[2]) if len(sys.argv) > 2 else 30

    rtts = armar_rutas(dst, iters, [0,0])
    ruta = ruta_promedio(rtts)
    ruta_outliers = sacar_outliers(ruta)

    print(ruta_outliers)
