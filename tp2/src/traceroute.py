import scapy.all as sc
from time import time

TIMEOUT = 5
MIN_TTL=10
MAX_TTL=10

RESULTS=0
UNANSWERED=1

times = {}

DST = ["www.google.com"]

packet = sc.IP(dst=DST,ttl=(MIN_TTL,MAX_TTL))/sc.ICMP()


for p in packet:
    initial_t = time()*1000 # Milisegundos
    ans,unans = sc.sr(p,timeout=TIMEOUT)
    final_t = time()*1000 - initial_t

    print(ans.summary( lambda t,r : r.sprintf("%ICMP.type%") ))

    if (ans.summary( lambda t,r : r.sprintf("%ICMP.type%") )) == "echo-reply":
        ip = ans.summary( lambda t,r : r.sprintf("%IP.dst%"))
        times[ip] = final_t 

    

