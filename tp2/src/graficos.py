#!/usr/bin/python3

from traceroute import armar_rutas
from intercon import ruta_promedio, tau
from geoip import Mapper
import sys
import math as m

from numpy import mean, std

import argparse
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# parámetros: <destino> <iteraciones> <nombre para los pdfs>

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Generar graficos")

    parser.add_argument("host", default="mu.ac.in", nargs="?",
            help="(default: www.msu.ru)")
    parser.add_argument("iteraciones", default=3, nargs="?", type=int,
            help="(default: 3)")
    parser.add_argument("output_name", default=None, nargs="?",
            help="(default: hostname)")

    args = parser.parse_args()

    dst = args.host
    iters = args.iteraciones
    target = args.output_name

    rtts = armar_rutas(dst, iters)
    ruta = ruta_promedio(rtts)
    print("RUTA : {}".format(ruta))

    # imprimir rtts de ruta
    df = pd.DataFrame(ruta, columns=['IP', 'RTT'])
    ax = sns.factorplot(x='IP', y='RTT', data=df, aspect=1.5)
    ax.set(xlabel='IPs con más apariciones por salto', ylabel='RTT medio (ms)')
    ax.set_xticklabels(rotation=90)
    ax.fig.suptitle('RTT medio para cada salto')

    plt.tight_layout()
    plt.show()
    if target:
        ax.savefig("../img/" + target + "-rtts.pdf")

    # imprimir incremento de rtts de ruta
    ruta_incremental = []
    for i in range(1, len(ruta)+1):
        suma_previa = sum([rtt for ip, rtt in ruta][:i])
        ip = ruta[i-1][0]
        ruta_incremental.append((ip, suma_previa))

    df = pd.DataFrame(ruta_incremental, columns=['IP', 'RTT incremental'])
    ax = sns.factorplot(x='IP', y='RTT incremental', data=df, aspect=1.5)
    ax.set(xlabel='IPs con más apariciones por salto', ylabel='Suma de RTTs (ms)')
    ax.set_xticklabels(rotation=90)
    ax.fig.suptitle('RTT incremental medio tras cada salto')

    plt.tight_layout()
    plt.show()
    if target:
        ax.savefig("../img/" + target + "-incrementales.pdf")

    # imprimir distribución ZRTT
    rtts = [rtt for ip, rtt in ruta]
    rtt_media = mean(rtts)
    rtt_sd = std(rtts)
    n = len(ruta)

    tuplas_zrtt = []
    for ip, rtt in ruta:
        zrtt = abs(rtt - rtt_media)/rtt_sd
        tuplas_zrtt.append((ip, zrtt))

    df = pd.DataFrame(tuplas_zrtt, columns=['IP', 'ZRTT'])
    ax = sns.barplot(x="ZRTT", y="IP", data=df, palette="Blues_d")
    ax.set(ylabel='IPs con más apariciones por salto', xlabel='ZRRTi')
    tau = ax.axvline(tau(n))
    one = ax.axvline(1, color='#B0E2FF')

    fig = ax.get_figure()
    fig.tight_layout()
    plt.show()

    if target:
        fig.savefig("../img/" + target + "-zrtt.pdf")

    # mapa
    ips = [ip for ip, rtt in ruta]
    tiempos = [rtt for ip, rtt in ruta]

    print("IPS : {}".format(ips))
    if target:
        Mapper.generate_route_map("../img/" + target + "-map", ips, tiempos)
