#!/usr/bin/python3
import scapy.all as sc
import sys
import math as m
from time import time
from traceroute import armar_rutas


def rtt_promedio(tanda):
    return sum([pair[1] for pair in tanda]) / len(tanda )

def ip_maximas_apariciones(tanda):
    ips = [par[0] for par in tanda]
    return max(set(ips), key=ips.count)

def ruta_promedio(times):
    ruta = []
    for ttl, tanda in times.items():
        if tanda:
            ruta.append((ip_maximas_apariciones(tanda), rtt_promedio(tanda)))
    return ruta

def tau(n):
    #TODO: t = sacar algo de la tabla student según n y un alfa como dice el paper
    t = 0.003
    return t*(n - 1) / (m.sqrt(n)*m.sqrt(n-2 + t**2))

def sacar_outliers(ruta):
    outliers = []
    rtt_media = rtt_promedio(ruta)
    n = len(ruta)
    rtt_sd = m.sqrt( sum( [(pair[1]-rtt_media)**2 for pair in ruta]) / n)

    for ip, rtt in ruta:
        if abs(rtt - rtt_media)*rtt_sd < tau(n):
            outliers.append(ip)
    return outliers

if __name__ == '__main__':
    dst = sys.argv[1] if len(sys.argv) > 1 else "www.google.com"
    iters = int(sys.argv[2]) if len(sys.argv) > 2 else 30

    rtts = armar_rutas(dst, iters)
    ruta = ruta_promedio(rtts)
    ruta_outliers = sacar_outliers(ruta)

    print(ruta_outliers)
