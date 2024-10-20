import os
import math
import ipaddress
from scapy.all import rdpcap
import networkx as nx
import matplotlib.pyplot as plt
from collections import defaultdict
from matplotlib.lines import Line2D
import tkinter as tk
from tkinter import filedialog, messagebox
import sys
import threading

# ========================
# Funciones Auxiliares
# ========================

def es_ip_local(ip):
    try:
        ip_obj = ipaddress.IPv4Address(ip)
        return ip_obj.is_private
    except ipaddress.AddressValueError:
        return False

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

def generar_grafico_personalizado(ruta_archivo_pcapng, prefijo_subred, font_size, dpi, tamano_lienzo_ancho, tamano_lienzo_alto):
    try:
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

                src_local = es_ip_local(src_ip)
                dst_local = es_ip_local(dst_ip)

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

                if es_ip_local(client_ip):
                    G.add_node(dns_server_ip)
                    G.add_edge(client_ip, dns_server_ip)
                    dns_queries[(client_ip, dns_server_ip)] += 1
                    dns_servers.add(dns_server_ip)

                    subred_client = obtener_subred(client_ip, prefijo_subred)
                    subredes_locales[subred_client].add(client_ip)

        print(f'Número de paquetes con capa IP: {contador_paquetes_ip}')
        print(f'Número de nodos en el grafo: {G.number_of_nodes()}')
        print(f'Número de aristas en el grafo: {G.number_of_edges()}')

        if G.number_of_nodes() == 0 and not conexiones_internet and not dns_queries:
            print('El grafo está vacío. No se generará el gráfico.')
            messagebox.showwarning("Advertencia", "El grafo está vacío. No se generará el gráfico.")
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
        colores_vlan = ['red', 'blue', 'purple', 'orange', 'cyan', 'magenta', 'yellow', 'brown', 'pink']
        color_internet = 'grey'
        color_dns_server = 'green'

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
        messagebox.showinfo("Éxito", f'Gráfico guardado en:\n{ruta_grafico}')

# ========================
# Interfaz Gráfica (GUI)
# ========================

def iniciar_gui():
    # Crear la ventana principal
    root = tk.Tk()
    root.title("Generador de Gráficos de PCAP")
    root.geometry("500x400")
    root.resizable(False, False)

    # Variables para almacenar las entradas del usuario
    ruta_archivo_var = tk.StringVar()
    prefijo_subred_var = tk.IntVar(value=24)
    font_size_var = tk.IntVar(value=10)
    dpi_var = tk.IntVar(value=100)
    tamano_lienzo_ancho_var = tk.IntVar(value=20)
    tamano_lienzo_alto_var = tk.IntVar(value=20)

    # Función para seleccionar el archivo pcapng
    def seleccionar_archivo():
        archivo = filedialog.askopenfilename(
            title="Seleccione el archivo .pcapng",
            filetypes=[("Archivos pcapng", "*.pcapng"), ("Todos los archivos", "*.*")]
        )
        if archivo:
            ruta_archivo_var.set(archivo)

    # Función para iniciar el procesamiento en un hilo separado
    def iniciar_procesamiento():
        ruta_archivo = ruta_archivo_var.get()
        prefijo_subred = prefijo_subred_var.get()
        font_size = font_size_var.get()
        dpi = dpi_var.get()
        tamano_lienzo_ancho = tamano_lienzo_ancho_var.get()
        tamano_lienzo_alto = tamano_lienzo_alto_var.get()

        if not ruta_archivo:
            messagebox.showerror("Error", "Por favor, seleccione un archivo .pcapng.")
            return

        if not os.path.isfile(ruta_archivo):
            messagebox.showerror("Error", "La ruta especificada no es válida o el archivo no existe.")
            return

        # Ejecutar la función en un hilo separado para evitar que la GUI se congele
        threading.Thread(target=generar_grafico_personalizado, args=(
            ruta_archivo, prefijo_subred, font_size, dpi, tamano_lienzo_ancho, tamano_lienzo_alto
        )).start()

    # Etiqueta y botón para seleccionar archivo
    lbl_ruta_archivo = tk.Label(root, text="Archivo .pcapng:")
    lbl_ruta_archivo.pack(pady=(20, 5))

    frame_archivo = tk.Frame(root)
    frame_archivo.pack(pady=5)

    entry_ruta_archivo = tk.Entry(frame_archivo, textvariable=ruta_archivo_var, width=50)
    entry_ruta_archivo.pack(side=tk.LEFT, padx=5)

    btn_seleccionar = tk.Button(frame_archivo, text="Seleccionar", command=seleccionar_archivo)
    btn_seleccionar.pack(side=tk.LEFT)

    # Parámetros de visualización
    lbl_parametros = tk.Label(root, text="Parámetros de Visualización", font=("Arial", 12, "bold"))
    lbl_parametros.pack(pady=(20, 10))

    # Prefijo de subred
    frame_prefijo = tk.Frame(root)
    frame_prefijo.pack(pady=5)
    lbl_prefijo = tk.Label(frame_prefijo, text="Prefijo de Subred (/):")
    lbl_prefijo.pack(side=tk.LEFT, padx=5)
    entry_prefijo = tk.Entry(frame_prefijo, textvariable=prefijo_subred_var, width=5)
    entry_prefijo.pack(side=tk.LEFT)

    # Tamaño de fuente
    frame_font_size = tk.Frame(root)
    frame_font_size.pack(pady=5)
    lbl_font_size = tk.Label(frame_font_size, text="Tamaño de Fuente:")
    lbl_font_size.pack(side=tk.LEFT, padx=5)
    entry_font_size = tk.Entry(frame_font_size, textvariable=font_size_var, width=5)
    entry_font_size.pack(side=tk.LEFT)

    # DPI
    frame_dpi = tk.Frame(root)
    frame_dpi.pack(pady=5)
    lbl_dpi = tk.Label(frame_dpi, text="DPI:")
    lbl_dpi.pack(side=tk.LEFT, padx=5)
    entry_dpi = tk.Entry(frame_dpi, textvariable=dpi_var, width=5)
    entry_dpi.pack(side=tk.LEFT)

    # Tamaño del lienzo ancho
    frame_ancho = tk.Frame(root)
    frame_ancho.pack(pady=5)
    lbl_ancho = tk.Label(frame_ancho, text="Ancho del Lienzo (in):")
    lbl_ancho.pack(side=tk.LEFT, padx=5)
    entry_ancho = tk.Entry(frame_ancho, textvariable=tamano_lienzo_ancho_var, width=5)
    entry_ancho.pack(side=tk.LEFT)

    # Tamaño del lienzo alto
    frame_alto = tk.Frame(root)
    frame_alto.pack(pady=5)
    lbl_alto = tk.Label(frame_alto, text="Alto del Lienzo (in):")
    lbl_alto.pack(side=tk.LEFT, padx=5)
    entry_alto = tk.Entry(frame_alto, textvariable=tamano_lienzo_alto_var, width=5)
    entry_alto.pack(side=tk.LEFT)

    # Botón para iniciar el procesamiento
    btn_procesar = tk.Button(root, text="Generar Gráfico", command=iniciar_procesamiento, bg="green", fg="white", font=("Arial", 12, "bold"))
    btn_procesar.pack(pady=(30, 10))

    # Botón para salir
    btn_salir = tk.Button(root, text="Salir", command=root.destroy, bg="red", fg="white")
    btn_salir.pack()

    # Iniciar la GUI
    root.mainloop()

# ========================
# Ejecución del Script
# ========================

if __name__ == '__main__':
    # Ejecutar la GUI
    iniciar_gui()
