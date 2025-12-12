import psutil
import os
import socket
import platform
from datetime import datetime
from jinja2 import Template
from collections import defaultdict
import heapq
import time

# Fonction pour obtenir la couleur en fonction du taux d'utilisation
def get_usage_color(usage):
    if usage <= 50:
        return "green"
    elif usage <= 80:
        return "orange"
    else:
        return "red"

# Récupérer les informations CPU
def get_cpu_info():
    cpu_cores = psutil.cpu_count(logical=False)  # Nombre de cœurs physiques
    cpu_threads = psutil.cpu_count(logical=True)  # Nombre de threads
    cpu_freq = psutil.cpu_freq().current  # Fréquence actuelle du CPU
    cpu_usage = psutil.cpu_percent(interval=1)  # Utilisation globale du CPU
    cpu_per_core_usage = psutil.cpu_percent(interval=1, percpu=True)  # Utilisation par cœur
    return cpu_cores, cpu_threads, cpu_freq, cpu_usage, cpu_per_core_usage

# Récupérer les informations sur la mémoire RAM
def get_memory_info():
    mem = psutil.virtual_memory()
    ram_used = mem.used / (1024 ** 3)  # Convertir en Go
    ram_total = mem.total / (1024 ** 3)  # Convertir en Go
    ram_usage = mem.percent  # Pourcentage utilisé
    return ram_used, ram_total, ram_usage

# Récupérer les informations sur le système (OS, hôte, IP, uptime)
def get_system_info():
    hostname = socket.gethostname()  # Nom de la machine
    os_info = platform.platform()  # Informations sur l'OS
    boot_time = psutil.boot_time()  # Temps de démarrage du système
    uptime = datetime.now() - datetime.fromtimestamp(boot_time)  # Calcul de l'uptime
    users = psutil.users()  # Utilisateurs connectés
    load = psutil.getloadavg()  # Charge moyenne du système

    # Récupérer l'adresse IP dynamique
    ip_address = None
    for interface, addrs in psutil.net_if_addrs().items():
        for addr in addrs:
            if addr.family == socket.AF_INET and addr.address != '127.0.0.1':  # Ignorer loopback (127.0.0.1)
                ip_address = addr.address
                break
        if ip_address:
            break
    return hostname, os_info, uptime, len(users), ip_address, load

# Récupérer les informations sur les processus
def get_process_info():
    processes_cpu = []
    processes_ram = []
    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
        try:
            processes_cpu.append((proc.info['name'], proc.info['cpu_percent']))
            processes_ram.append((proc.info['name'], proc.info['memory_percent']))
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    top_cpu = sorted(processes_cpu, key=lambda x: x[1], reverse=True)[:3]  # Top 3 processus CPU
    top_ram = sorted(processes_ram, key=lambda x: x[1], reverse=True)[:3]  # Top 3 processus RAM
    return top_cpu, top_ram

# Analyser les fichiers dans un répertoire
def analyze_files(directory):
    file_count = defaultdict(int)
    file_sizes = defaultdict(int)
    largest_files = []
    file_extensions = ['.txt', '.py', '.pdf', '.jpg', '.png', '.docx', '.xlsx', '.csv', '.log', '.zip', '.tar.gz']

    for root, dirs, files in os.walk(directory):
        for file in files:
            ext = os.path.splitext(file)[1]
            if ext in file_extensions:
                file_count[ext] += 1
                file_size = os.path.getsize(os.path.join(root, file))
                file_sizes[ext] += file_size
                heapq.heappush(largest_files, (file_size, os.path.join(root, file)))
                if len(largest_files) > 10:
                    heapq.heappop(largest_files)

    total_files = sum(file_count.values())
    file_percentages = {ext: (count / total_files * 100) for ext, count in file_count.items()}
    file_space = {ext: (size / (1024 ** 3)) for ext, size in file_sizes.items()}  # Convertir en Go
    return file_count, total_files, file_percentages, file_space, largest_files

# Générer le rapport HTML avec les données
def generate_html_report(data):
    # Déterminer la couleur pour l'utilisation du CPU et de la RAM
    data["cpu_usage_color"] = get_usage_color(data["cpu_usage"])
    data["ram_usage_color"] = get_usage_color(data["ram_usage"])
    with open('template.html', 'r') as file:
        template = Template(file.read())
    html_output = template.render(data)

    # Sauvegarder dans le répertoire actuel
    file_path = 'checkpoint.html'  # Le fichier sera généré dans le répertoire courant
    with open(file_path, 'w') as file:
        file.write(html_output)

def main():
    while True:
        # Collecter les données
        cpu_cores, cpu_threads, cpu_freq, cpu_usage, cpu_per_core_usage = get_cpu_info()
        ram_used, ram_total, ram_usage = get_memory_info()
        hostname, os_info, uptime, num_users, ip_address, load = get_system_info()
        top_cpu, top_ram = get_process_info()
        directory = 'C:\Users\horus\OneDrive\Desktop'  # Remplacez ceci par le répertoire à analyser
        file_count, total_files, file_percentages, file_space, largest_files = analyze_files(directory)

        # Créer un dictionnaire de données à passer au modèle HTML
        data = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "hostname": hostname,
            "os_info": os_info,
            "uptime": str(uptime),
            "num_users": num_users,
            "ip_address": ip_address,
            "load": load,
            "cpu_cores": cpu_cores,
            "cpu_threads": cpu_threads,
            "cpu_freq": cpu_freq,  # Ajout de la fréquence CPU
            "cpu_usage": cpu_usage,
            "ram_used": ram_used,
            "ram_total": ram_total,
            "ram_usage": ram_usage,
            "top_cpu": [{"name": name, "cpu_usage": cpu} for name, cpu in top_cpu],
            "top_ram": [{"name": name, "ram_usage": ram} for name, ram in top_ram],
            "file_percentages": file_percentages,
            "file_space": file_space,
            "largest_files": largest_files,
            "generator_name": "Your Python Script"
        }

        # Générer le rapport HTML
        generate_html_report(data)
        
        # Attendre 30 secondes avant de refaire une mise à jour
        time.sleep(30)

if __name__ == "__main__":
    main()
