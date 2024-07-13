import math
import psutil

def convert_size(size_bytes):
   if size_bytes == 0:
       return "0B"
   size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
   i = int(math.floor(math.log(size_bytes, 1024)))
   p = math.pow(1024, i)
   s = round(size_bytes / p, 2)
   return "%s %s" % (s, size_name[i])

async def net_usage():
    net_stat = psutil.net_io_counters()
    net_in = net_stat.bytes_recv
    net_out = net_stat.bytes_sent
    net_in_all = round((net_in) / 1024 / 1024, 3)
    net_out_all = round((net_out) / 1024 / 1024, 3)
    net_all = round((net_out + net_in) / 1024 / 1024, 3)
    return f"**Network Total :** {convert_size(net_all)}\n> **Network In :** {convert_size(net_in_all)}\n> **Network Out : **{convert_size(net_out_all)}"
