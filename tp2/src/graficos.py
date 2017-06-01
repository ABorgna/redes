from traceroute import armar_rutas
from intercon import ruta_promedio
import sys

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# parámetros: <destino> <iteraciones> <nombre para los pdfs>

if __name__ == '__main__':
    dst = sys.argv[1] if len(sys.argv) > 1 else "www.msu.ru"
    iters = int(sys.argv[2]) if len(sys.argv) > 2 else 30
    target = sys.argv[3] if len(sys.argv) > 3 else ""

    rtts = armar_rutas(dst, iters)
    ruta = ruta_promedio(rtts)
    print("RUTA : {}".format(ruta))

    # imprimir rtts de ruta
    df = pd.DataFrame(ruta, columns=['IP', 'RTT'])
    ax = sns.factorplot(x='IP', y='RTT', data=df, aspect=1.5)
    ax.set(xlabel='IPs con más apariciones por salto', ylabel='RTT medio')
    ax.set_xticklabels(rotation=40)
    ax.fig.suptitle('RTT medio para cada salto')

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
    ax.set(xlabel='IPs con más apariciones por salto', ylabel='Suma de RTTs')
    ax.set_xticklabels(rotation=40)
    ax.fig.suptitle('RTT incremental medio tras cada salto')

    plt.show()
    if target:
        ax.savefig("../img/" + target + "-incrementales.pdf")

    # TODO: imprimir distribución ZRTT
