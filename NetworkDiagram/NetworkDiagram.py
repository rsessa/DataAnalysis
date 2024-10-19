import os
import math
import ipaddress
from scapy.all import rdpcap
import networkx as nx
import matplotlib.pyplot as plt
from collections import defaultdict
from matplotlib.lines import Line2D
import tkinter as tk
from tkinter import simpledialog, messagebox, filedialog
import sys
import glob

# ========================
# Funciones Auxiliares
# ========================

def es_ip_local(ip):
    ip_obj = ipaddress.IPv4Address(ip)
    return ip_obj.is_private

def obtener_subred(ip, prefijo):
    ip_obj = ipaddress.IPv4Address(ip)
    red = ipaddress.ip_network(f"{ip}/{prefijo}", strict=False)
    return str(red)

def calcular_tamano_nodo(label, font_size, dpi):
    text_width = len(label) * font_size * 0.6
    text_width_inch = text_width / 72
    node_area_inch = ((text_width_inch / 2) ** 2) * math.pi
    node_size = node_area_inch * (dpi ** 2)
    return node_size

# ========================
# Función Principal
# ========================

def generar_grafico_personalizado(ruta_carpeta):
    # Crear ventana oculta de Tkinter
    root = tk.Tk()
    root.withdraw()

    # Buscar archivos .pcapng en la carpeta seleccionada
    archivos_pcapng = glob.glob(os.path.join(ruta_carpeta, "*.pcapng"))
    if not archivos_pcapng:
        messagebox.showerror("Error", "No se encontró ningún archivo .pcapng en la carpeta seleccionada.")
        sys.exit(1)
    elif len(archivos_pcapng) == 1:
        ruta_archivo_pcapng = archivos_pcapng[0]  # Tomar el único archivo encontrado
    else:
        # Si hay múltiples archivos, permitir al usuario seleccionar uno
        messagebox.showinfo("Seleccionar Archivo", "Se encontraron múltiples archivos .pcapng. Seleccione uno.")
        ruta_archivo_pcapng = filedialog.askopenfilename(
            title="Seleccione el archivo .pcapng a analizar",
            initialdir=ruta_carpeta,
            filetypes=[("Archivos pcapng", "*.pcapng")]
        )
        if not ruta_archivo_pcapng:
            messagebox.showerror("Error", "No se seleccionó ningún archivo.")
            sys.exit(1)

    # Solicitar los valores de las variables en una ventana modal
    prefijo_subred = simpledialog.askinteger("Prefijo de Subred", "Ingrese el prefijo de subred para agrupar IPs (por defecto 24):", initialvalue=24, minvalue=1, maxvalue=32)
    font_size = simpledialog.askinteger("Tamaño de Fuente", "Ingrese el tamaño de fuente para las etiquetas:", initialvalue=10, minvalue=1)
    dpi = simpledialog.askinteger("DPI", "Ingrese la resolución de la figura en DPI:", initialvalue=100, minvalue=1)
    tamano_lienzo_ancho = simpledialog.askinteger("Ancho del Lienzo", "Ingrese el ancho del lienzo en pulgadas:", initialvalue=20, minvalue=1)
    tamano_lienzo_alto = simpledialog.askinteger("Alto del Lienzo", "Ingrese el alto del lienzo en pulgadas:", initialvalue=20, minvalue=1)

    # Verificar si se ingresaron valores
    if None in [prefijo_subred, font_size, dpi, tamano_lienzo_ancho, tamano_lienzo_alto]:
        messagebox.showerror("Error", "No se ingresaron todos los valores necesarios.")
        sys.exit(1)

    # Parámetros de visualización y otros
    colores_vlan = ['red', 'blue', 'purple', 'orange', 'cyan', 'magenta', 'yellow', 'brown', 'pink']
    color_internet = 'grey'
    color_dns_server = 'green'

    # Restablecer la ventana de Tkinter
    root.destroy()

    # ========================
    # Aquí comienza el procesamiento del archivo
    # ========================

    print(f'Procesando archivo: {ruta_archivo_pcapng}')
    packets = rdpcap(ruta_archivo_pcapng)
    print(f'Número total de paquetes leídos: {len(packets)}')

    G = nx.Graph()
    subredes_locales = defaultdict(set)
    contador_paquetes_ip = 0
    conexiones_internet = defaultdict(int)
    dns_queries = defaultdict(int)
    dns_servers = set()

    for pkt in packets:
        # Verificar si el paquete tiene capa IP
        if pkt.haslayer('IP'):
            contador_paquetes_ip += 1
            src_ip = pkt['IP'].src
            dst_ip = pkt['IP'].dst

            # Ignorar la IP de broadcast 255.255.255.255
            if src_ip == '255.255.255.255' or dst_ip == '255.255.255.255':
                continue

            try:
                src_local = es_ip_local(src_ip)
                dst_local = es_ip_local(dst_ip)
            except ValueError:
                continue

            if src_local and dst_local:
                subred_src = obtener_subred(src_ip, prefijo_subred)
                subred_dst = obtener_subred(dst_ip, prefijo_subred)
                subredes_locales[subred_src].add(src_ip)
                subredes_locales[subred_dst].add(dst_ip)
                G.add_edge(src_ip, dst_ip)

            elif src_local and not dst_local:
                conexiones_internet[src_ip] += 1
                subred_src = obtener_subred(src_ip, prefijo_subred)
                subredes_locales[subred_src].add(src_ip)

            elif not src_local and dst_local:
                conexiones_internet[dst_ip] += 1
                subred_dst = obtener_subred(dst_ip, prefijo_subred)
                subredes_locales[subred_dst].add(dst_ip)

        # Procesar tráfico DNS
        if pkt.haslayer('DNS') and pkt['DNS'].qr == 0 and pkt.haslayer('IP'):
            client_ip = pkt['IP'].src
            dns_server_ip = pkt['IP'].dst

            if client_ip == '255.255.255.255' or dns_server_ip == '255.255.255.255':
                continue

            try:
                if es_ip_local(client_ip):
                    G.add_node(dns_server_ip)
                    G.add_edge(client_ip, dns_server_ip)
                    dns_queries[(client_ip, dns_server_ip)] += 1
                    dns_servers.add(dns_server_ip)

                    subred_client = obtener_subred(client_ip, prefijo_subred)
                    subredes_locales[subred_client].add(client_ip)
            except ValueError:
                continue

    print(f'Número de paquetes con capa IP: {contador_paquetes_ip}')
    print(f'Número de nodos en el grafo: {G.number_of_nodes()}')
    print(f'Número de aristas en el grafo: {G.number_of_edges()}')

    if G.number_of_nodes() == 0 and not conexiones_internet and not dns_queries:
        print('El grafo está vacío. No se generará el gráfico.')
        return

    # ========================
    # Preparación de Datos
    # ========================

    # Añadir el nodo de Internet si hay conexiones externas
    if conexiones_internet:
        G.add_node('Internet')

    # Calcular tamaños de nodos
    node_sizes = {}
    for node in G.nodes():
        if node == 'Internet':
            node_label = 'Internet'
        else:
            node_label = str(node)
        node_size = calcular_tamano_nodo(node_label, font_size, dpi)
        node_sizes[node] = node_size

    # Asignar colores a los nodos según la VLAN (subred)
    subred_color_map = {}
    node_color_map = {}
    for idx, (subred, ips) in enumerate(subredes_locales.items()):
        color = colores_vlan[idx % len(colores_vlan)]
        subred_color_map[subred] = color
        for ip in ips:
            node_color_map[ip] = color

    # Asignar color al nodo de Internet
    if 'Internet' in G.nodes():
        node_color_map['Internet'] = color_internet

    # Asignar color a los servidores DNS
    for dns_ip in dns_servers:
        node_color_map[dns_ip] = color_dns_server

    # ========================
    # Configuración de la Figura
    # ========================

    # Crear la figura con el tamaño especificado
    plt.figure(figsize=(tamano_lienzo_ancho, tamano_lienzo_alto), dpi=dpi)

    # ========================
    # Visualización
    # ========================

    # Utilizar el algoritmo de Spring Layout para posicionar los nodos
    pos = nx.spring_layout(G, k=1.5, iterations=100)

    # Dibujar aristas normales
    aristas_normales = [(u, v) for u, v in G.edges() if ('Internet' not in [u, v]) and (v not in dns_servers) and (u not in dns_servers)]
    nx.draw_networkx_edges(G, pos, edgelist=aristas_normales, alpha=0.5)

    # Dibujar aristas hacia Internet
    aristas_internet = []
    for node, count in conexiones_internet.items():
        if node in G.nodes():
            G.add_edge(node, 'Internet')
            aristas_internet.append((node, 'Internet'))

    nx.draw_networkx_edges(G, pos, edgelist=aristas_internet, style='dashed', edge_color='black')

    # Añadir etiquetas a las aristas hacia Internet con el número de conexiones
    for (node, internet_node) in aristas_internet:
        x_text = (pos[node][0] + pos[internet_node][0]) / 2
        y_text = (pos[node][1] + pos[internet_node][1]) / 2
        plt.text(x_text, y_text, str(conexiones_internet[node]), fontsize=font_size - 2, fontweight='bold', color='black')

    # Dibujar aristas DNS
    aristas_dns = list(dns_queries.keys())
    nx.draw_networkx_edges(G, pos, edgelist=aristas_dns, style='dotted', edge_color='green')

    # Añadir etiquetas a las aristas DNS con el número de consultas
    edge_labels_dns = {(u, v): str(dns_queries[(u, v)]) for u, v in aristas_dns}
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels_dns, font_size=font_size - 2, font_color='green')

    # Dibujar nodos coloreados
    node_colors = [node_color_map.get(node, 'grey') for node in G.nodes()]
    node_sizes_list = [node_sizes[node] for node in G.nodes()]

    nx.draw_networkx_nodes(G, pos, node_color=node_colors, node_size=node_sizes_list)

    # Etiquetas
    etiquetas = {node: node if node != 'Internet' else 'Internet' for node in G.nodes()}
    nx.draw_networkx_labels(G, pos, labels=etiquetas, font_size=font_size)

    plt.title(f'Conexiones de {os.path.basename(ruta_archivo_pcapng)}')
    plt.axis('off')

    # Crear leyenda
    legend_elements = []
    for subred, color in subred_color_map.items():
        legend_elements.append(Line2D([0], [0], marker='o', color='w', label=f'Subred {subred}',
                                      markerfacecolor=color, markersize=10))
    # Añadir entrada para Internet
    if 'Internet' in G.nodes():
        legend_elements.append(Line2D([0], [0], marker='o', color='w', label='Internet',
                                      markerfacecolor=color_internet, markersize=10))
    # Añadir entrada para Servidores DNS
    if dns_servers:
        legend_elements.append(Line2D([0], [0], marker='o', color='w', label='Servidor DNS',
                                      markerfacecolor=color_dns_server, markersize=10))

    plt.legend(handles=legend_elements, loc='upper right')

    # ========================
    # Guardar el Gráfico
    # ========================

    directorio_archivo = os.path.dirname(ruta_archivo_pcapng)
    nombre_base = os.path.splitext(os.path.basename(ruta_archivo_pcapng))[0]
    nombre_grafico = f"{nombre_base}.png"
    ruta_grafico = os.path.join(directorio_archivo, nombre_grafico)

    plt.savefig(ruta_grafico, bbox_inches='tight')
    plt.close()
    print(f'Gráfico guardado en: {ruta_grafico}')

# ========================
# Ejecución del Script
# ========================

if __name__ == '__main__':
    if len(sys.argv) > 1:
        ruta_carpeta = sys.argv[1]
        generar_grafico_personalizado(ruta_carpeta)
    else:
        # Crear ventana de Tkinter para seleccionar carpeta si no se proporcionó ruta
        root = tk.Tk()
        root.withdraw()
        ruta_carpeta = filedialog.askdirectory(title="Seleccione la carpeta que contiene el archivo .pcapng")
        if ruta_carpeta:
            generar_grafico_personalizado(ruta_carpeta)
        else:
            messagebox.showerror("Error", "No se proporcionó la ruta de la carpeta.")
            sys.exit(1)
