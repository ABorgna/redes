#!/usr/bin/python3

from traceroute import armar_rutas, print_summary
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

    parser.add_argument("host", help="host de destino")
    parser.add_argument("-i", "--iteraciones", default=3, type=int,
            help="cantidad de requests por ttl (default: 3)")
    parser.add_argument("-o", "--output", default=None,
            help="nombre de los archivos de salida (default: <hostname>)")
    parser.add_argument("-n", "--notarget", action="store_true",
            help="no generar archivo de salida, mostrar los gráficos solamente")

    args = parser.parse_args()

    dst = args.host
    iters = args.iteraciones
    target = args.output if args.output is not None else args.host
    if args.notarget:
        target = None

    rtts = []
    for item in armar_rutas(dst, iters):
        print(".", end="", flush=True)
        rtts.append(item)
    print()

    print_summary(rtts)
    ruta = list(ruta_promedio(rtts))

    print("RUTA : {}".format(ruta))

    # imprimir rtts relativos de ruta
    ultimo_rtt = 0
    ruta_final = []
    for ip, rtt in ruta:
        ruta_final.append((ip, rtt, rtt - ultimo_rtt))
        ultimo_rtt = rtt

    ruta_rtts_relativos = [(ip, rel_rtt) for (ip, rtt, rel_rtt) in ruta_final]

    print("ruta_rtts_relativos : {}".format(ruta_rtts_relativos))


    df = pd.DataFrame(ruta_rtts_relativos, columns=['IP', 'RTT'])
    sns.set(font_scale=1.5)
    ax = sns.factorplot(x='IP', y='RTT', data=df, aspect=1.5)
    ax.set(xlabel='IPs con más apariciones por salto', ylabel='RTT relativo medio (ms)')
    ax.set_xticklabels(rotation=90)
    ax.fig.suptitle('RTT medio para cada salto')

    #plt.tight_layout()
    if target:
        ax.fig.set_size_inches(12,8)
        ax.savefig("../img/" + target + "-rtts.pdf")
    else:
        plt.show()

    # imprimir incremento de rtts de ruta
    ruta_incremental = ruta
    df = pd.DataFrame(ruta_incremental, columns=['IP', 'RTT incremental'])
    ax = sns.factorplot(x='IP', y='RTT incremental', data=df, aspect=1.5)
    ax.set(xlabel='IPs con más apariciones por salto', ylabel='Suma de RTTs (ms)')
    ax.set_xticklabels(rotation=90)
    ax.fig.suptitle('RTT incremental medio tras cada salto')

    #plt.tight_layout()
    if target:
        ax.fig.set_size_inches(12,8)
        ax.savefig("../img/" + target + "-incrementales.pdf")
    else:
        plt.show()

    # imprimir distribución ZRTT
    rtts = [rtt for ip, rtt in ruta_rtts_relativos]
    rtt_media = mean(rtts)
    rtt_sd = std(rtts)
    n = len(rtts)

    tuplas_zrtt = []
    for ip, rtt in ruta_rtts_relativos:
        zrtt = abs(rtt - rtt_media)/rtt_sd
        tuplas_zrtt.append((ip, zrtt))

    df = pd.DataFrame(tuplas_zrtt, columns=['IP', 'ZRTT'])
    #sns.set(font_scale=1)
    ax = sns.barplot(x="ZRTT", y="IP", data=df, palette="Blues_d")
    ax.set(ylabel='IPs con más apariciones por salto', xlabel='ZRRTi')

    tau = ax.axvline(tau(n))
    one = ax.axvline(1, color='#B0E2FF')

    #plt.tight_layout()
    if target:
        fig = ax.get_figure()
        fig.set_size_inches(12,8)
        fig.savefig("../img/" + target + "-zrtt.pdf")
    else:
        plt.show()

    # mapa
    ips = [ip for ip, rtt in ruta]
    tiempos = [rtt for ip, rtt in ruta]

    print("IPS : {}".format(ips))
    if target:
        Mapper.generate_route_map("../img/" + target + "-map.png", ips, tiempos)
