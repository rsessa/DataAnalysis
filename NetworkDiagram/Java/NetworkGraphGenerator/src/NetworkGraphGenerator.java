import java.awt.Color;
import java.awt.image.BufferedImage;
import java.io.File;
import java.io.FilenameFilter;
import java.io.IOException;
import java.net.InetAddress;
import java.net.UnknownHostException;
import java.util.*;
import javax.imageio.ImageIO;
import javax.swing.JFileChooser;
import javax.swing.JOptionPane;
import javax.swing.UIManager;

import org.jgrapht.Graph;
import org.jgrapht.graph.DefaultEdge;
import org.jgrapht.graph.SimpleGraph;
import org.pcap4j.core.*;
import org.pcap4j.packet.*;

import com.mxgraph.layout.mxOrganicLayout;
import com.mxgraph.layout.mxIGraphLayout;
import com.mxgraph.util.mxCellRenderer;
import com.mxgraph.view.mxGraph;

public class NetworkGraphGenerator {

    // ========================
    // Funciones Auxiliares
    // ========================

    public static boolean esIpLocal(String ipStr) {
        try {
            InetAddress ip = InetAddress.getByName(ipStr);
            byte[] address = ip.getAddress();
            int firstOctet = Byte.toUnsignedInt(address[0]);
            int secondOctet = Byte.toUnsignedInt(address[1]);

            // Rango 10.0.0.0/8
            if (firstOctet == 10) {
                return true;
            }
            // Rango 172.16.0.0/12
            if (firstOctet == 172 && (secondOctet >= 16 && secondOctet <= 31)) {
                return true;
            }
            // Rango 192.168.0.0/16
            if (firstOctet == 192 && secondOctet == 168) {
                return true;
            }
            return false;
        } catch (UnknownHostException e) {
            return false;
        }
    }

    public static String obtenerSubred(String ipStr, int prefijo) {
        try {
            InetAddress ip = InetAddress.getByName(ipStr);
            byte[] address = ip.getAddress();
            int ipInt = ((address[0] & 0xFF) << 24) | ((address[1] & 0xFF) << 16)
                    | ((address[2] & 0xFF) << 8) | (address[3] & 0xFF);

            int mask = -1 << (32 - prefijo);

            int network = ipInt & mask;

            int[] bytes = new int[4];
            bytes[0] = (network >> 24) & 0xFF;
            bytes[1] = (network >> 16) & 0xFF;
            bytes[2] = (network >> 8) & 0xFF;
            bytes[3] = network & 0xFF;

            return String.format("%d.%d.%d.%d/%d", bytes[0], bytes[1], bytes[2], bytes[3], prefijo);
        } catch (UnknownHostException e) {
            return null;
        }
    }

    public static double calcularTamanoNodo(String label, int fontSize, int dpi) {
        double textWidth = label.length() * fontSize * 0.6;
        double textWidthInch = textWidth / 72;
        double nodeAreaInch = Math.PI * Math.pow(textWidthInch / 2, 2);
        double nodeSize = nodeAreaInch * Math.pow(dpi, 2);
        return nodeSize;
    }

    // ========================
    // Función Principal
    // ========================

    public static void generarGraficoPersonalizado(String rutaCarpeta) {
        // Establecer el aspecto de la interfaz
        try {
            UIManager.setLookAndFeel(UIManager.getSystemLookAndFeelClassName());
        } catch (Exception e) {
            e.printStackTrace();
        }

        // Buscar archivos .pcapng en la carpeta seleccionada
        File folder = new File(rutaCarpeta);
        File[] archivosPcapng = folder.listFiles(new FilenameFilter() {
            public boolean accept(File dir, String name) {
                return name.toLowerCase().endsWith(".pcapng");
            }
        });

        if (archivosPcapng == null || archivosPcapng.length == 0) {
            JOptionPane.showMessageDialog(null, "No se encontró ningún archivo .pcapng en la carpeta seleccionada.",
                    "Error", JOptionPane.ERROR_MESSAGE);
            System.exit(1);
        }

        File rutaArchivoPcapng = null;
        if (archivosPcapng.length == 1) {
            rutaArchivoPcapng = archivosPcapng[0]; // Tomar el único archivo encontrado
        } else {
            // Si hay múltiples archivos, permitir al usuario seleccionar uno
            JOptionPane.showMessageDialog(null,
                    "Se encontraron múltiples archivos .pcapng. Seleccione uno.", "Seleccionar Archivo",
                    JOptionPane.INFORMATION_MESSAGE);
            JFileChooser chooser = new JFileChooser(rutaCarpeta);
            chooser.setFileFilter(new javax.swing.filechooser.FileNameExtensionFilter("Archivos pcapng", "pcapng"));
            int returnVal = chooser.showOpenDialog(null);
            if (returnVal == JFileChooser.APPROVE_OPTION) {
                rutaArchivoPcapng = chooser.getSelectedFile();
            } else {
                JOptionPane.showMessageDialog(null, "No se seleccionó ningún archivo.", "Error",
                        JOptionPane.ERROR_MESSAGE);
                System.exit(1);
            }
        }

        // Solicitar los valores de las variables en ventanas de diálogo
        String prefijoSubredStr = JOptionPane.showInputDialog(null,
                "Ingrese el prefijo de subred para agrupar IPs (por defecto 24):", "Prefijo de Subred",
                JOptionPane.QUESTION_MESSAGE);
        int prefijoSubred = 24;
        if (prefijoSubredStr != null && !prefijoSubredStr.isEmpty()) {
            prefijoSubred = Integer.parseInt(prefijoSubredStr);
        }

        String fontSizeStr = JOptionPane.showInputDialog(null,
                "Ingrese el tamaño de fuente para las etiquetas:", "Tamaño de Fuente",
                JOptionPane.QUESTION_MESSAGE);
        int fontSize = 10;
        if (fontSizeStr != null && !fontSizeStr.isEmpty()) {
            fontSize = Integer.parseInt(fontSizeStr);
        }

        String dpiStr = JOptionPane.showInputDialog(null, "Ingrese la resolución de la figura en DPI:", "DPI",
                JOptionPane.QUESTION_MESSAGE);
        int dpi = 100;
        if (dpiStr != null && !dpiStr.isEmpty()) {
            dpi = Integer.parseInt(dpiStr);
        }

        String anchoLienzoStr = JOptionPane.showInputDialog(null, "Ingrese el ancho del lienzo en pulgadas:",
                "Ancho del Lienzo", JOptionPane.QUESTION_MESSAGE);
        int anchoLienzo = 20;
        if (anchoLienzoStr != null && !anchoLienzoStr.isEmpty()) {
            anchoLienzo = Integer.parseInt(anchoLienzoStr);
        }

        String altoLienzoStr = JOptionPane.showInputDialog(null, "Ingrese el alto del lienzo en pulgadas:",
                "Alto del Lienzo", JOptionPane.QUESTION_MESSAGE);
        int altoLienzo = 20;
        if (altoLienzoStr != null && !altoLienzoStr.isEmpty()) {
            altoLienzo = Integer.parseInt(altoLienzoStr);
        }

        // Verificar si se ingresaron valores
        if (prefijoSubred <= 0 || fontSize <= 0 || dpi <= 0 || anchoLienzo <= 0 || altoLienzo <= 0) {
            JOptionPane.showMessageDialog(null, "No se ingresaron todos los valores necesarios.", "Error",
                    JOptionPane.ERROR_MESSAGE);
            System.exit(1);
        }

        // Parámetros de visualización y otros
        String[] coloresVlan = { "red", "blue", "purple", "orange", "cyan", "magenta", "yellow", "brown", "pink" };
        String colorInternet = "grey";
        String colorDnsServer = "green";

        // ========================
        // Aquí comienza el procesamiento del archivo
        // ========================

        System.out.println("Procesando archivo: " + rutaArchivoPcapng.getAbsolutePath());

        Graph<String, DefaultEdge> G = new SimpleGraph<>(DefaultEdge.class);
        Map<String, Set<String>> subredesLocales = new HashMap<>();
        int contadorPaquetesIp = 0;
        Map<String, Integer> conexionesInternet = new HashMap<>();
        Map<String, Integer> dnsQueries = new HashMap<>();
        Set<String> dnsServers = new HashSet<>();

        PcapHandle handle = null;
        try {
            handle = Pcaps.openOffline(rutaArchivoPcapng.getAbsolutePath());

            Packet packet = null;
            while ((packet = handle.getNextPacket()) != null) {
                // Verificar si el paquete tiene capa IP
                if (packet.contains(IpV4Packet.class)) {
                    contadorPaquetesIp++;
                    IpV4Packet ipPacket = packet.get(IpV4Packet.class);
                    String srcIp = ipPacket.getHeader().getSrcAddr().getHostAddress();
                    String dstIp = ipPacket.getHeader().getDstAddr().getHostAddress();

                    // Ignorar la IP de broadcast 255.255.255.255
                    if (srcIp.equals("255.255.255.255") || dstIp.equals("255.255.255.255")) {
                        continue;
                    }

                    boolean srcLocal = esIpLocal(srcIp);
                    boolean dstLocal = esIpLocal(dstIp);

                    if (srcLocal && dstLocal) {
                        String subredSrc = obtenerSubred(srcIp, prefijoSubred);
                        String subredDst = obtenerSubred(dstIp, prefijoSubred);
                        subredesLocales.putIfAbsent(subredSrc, new HashSet<>());
                        subredesLocales.putIfAbsent(subredDst, new HashSet<>());
                        subredesLocales.get(subredSrc).add(srcIp);
                        subredesLocales.get(subredDst).add(dstIp);
                        G.addVertex(srcIp);
                        G.addVertex(dstIp);
                        G.addEdge(srcIp, dstIp);
                    } else if (srcLocal && !dstLocal) {
                        conexionesInternet.put(srcIp, conexionesInternet.getOrDefault(srcIp, 0) + 1);
                        String subredSrc = obtenerSubred(srcIp, prefijoSubred);
                        subredesLocales.putIfAbsent(subredSrc, new HashSet<>());
                        subredesLocales.get(subredSrc).add(srcIp);
                    } else if (!srcLocal && dstLocal) {
                        conexionesInternet.put(dstIp, conexionesInternet.getOrDefault(dstIp, 0) + 1);
                        String subredDst = obtenerSubred(dstIp, prefijoSubred);
                        subredesLocales.putIfAbsent(subredDst, new HashSet<>());
                        subredesLocales.get(subredDst).add(dstIp);
                    }
                }

                // Procesar tráfico DNS
                if (packet.contains(DnsPacket.class) && packet.contains(UdpPacket.class)
                        && packet.contains(IpV4Packet.class)) {
                    DnsPacket dnsPacket = packet.get(DnsPacket.class);
                    if (!dnsPacket.getHeader().isResponse()) {
                        IpV4Packet ipPacket = packet.get(IpV4Packet.class);
                        String clientIp = ipPacket.getHeader().getSrcAddr().getHostAddress();
                        String dnsServerIp = ipPacket.getHeader().getDstAddr().getHostAddress();

                        if (clientIp.equals("255.255.255.255") || dnsServerIp.equals("255.255.255.255")) {
                            continue;
                        }

                        if (esIpLocal(clientIp)) {
                            G.addVertex(dnsServerIp);
                            G.addEdge(clientIp, dnsServerIp);
                            String key = clientIp + "-" + dnsServerIp;
                            dnsQueries.put(key, dnsQueries.getOrDefault(key, 0) + 1);
                            dnsServers.add(dnsServerIp);

                            String subredClient = obtenerSubred(clientIp, prefijoSubred);
                            subredesLocales.putIfAbsent(subredClient, new HashSet<>());
                            subredesLocales.get(subredClient).add(clientIp);
                        }
                    }
                }
            }

            System.out.println("Número de paquetes con capa IP: " + contadorPaquetesIp);
            System.out.println("Número de nodos en el grafo: " + G.vertexSet().size());
            System.out.println("Número de aristas en el grafo: " + G.edgeSet().size());

            if (G.vertexSet().isEmpty() && conexionesInternet.isEmpty() && dnsQueries.isEmpty()) {
                System.out.println("El grafo está vacío. No se generará el gráfico.");
                return;
            }

            // ========================
            // Preparación de Datos
            // ========================

            // Añadir el nodo de Internet si hay conexiones externas
            if (!conexionesInternet.isEmpty()) {
                G.addVertex("Internet");
            }

            // Calcular tamaños de nodos
            Map<String, Double> nodeSizes = new HashMap<>();
            for (String node : G.vertexSet()) {
                String nodeLabel = node.equals("Internet") ? "Internet" : node;
                double nodeSize = calcularTamanoNodo(nodeLabel, fontSize, dpi);
                nodeSizes.put(node, nodeSize);
            }

            // Asignar colores a los nodos según la VLAN (subred)
            Map<String, String> subredColorMap = new HashMap<>();
            Map<String, String> nodeColorMap = new HashMap<>();
            int idxColor = 0;
            for (String subred : subredesLocales.keySet()) {
                String color = coloresVlan[idxColor % coloresVlan.length];
                subredColorMap.put(subred, color);
                idxColor++;
                for (String ip : subredesLocales.get(subred)) {
                    nodeColorMap.put(ip, color);
                }
            }

            // Asignar color al nodo de Internet
            if (G.containsVertex("Internet")) {
                nodeColorMap.put("Internet", colorInternet);
            }

            // Asignar color a los servidores DNS
            for (String dnsIp : dnsServers) {
                nodeColorMap.put(dnsIp, colorDnsServer);
            }

            // ========================
            // Visualización
            // ========================

            mxGraph mxGraph = new mxGraph();
            Object parentObj = mxGraph.getDefaultParent();

            Map<String, Object> vertexMapObj = new HashMap<>();

            mxGraph.getModel().beginUpdate();
            try {
                // Crear nodos
                for (String node : G.vertexSet()) {
                    String label = node.equals("Internet") ? "Internet" : node;
                    double nodeSize = nodeSizes.get(node) / dpi; // Ajustar el tamaño para el gráfico
                    Object v = mxGraph.insertVertex(parentObj, null, label, 0, 0, nodeSize, nodeSize,
                            "fillColor=" + nodeColorMap.getOrDefault(node, "grey") + ";fontSize=" + fontSize);
                    vertexMapObj.put(node, v);
                }

                // Crear aristas
                for (DefaultEdge e : G.edgeSet()) {
                    String source = G.getEdgeSource(e);
                    String target = G.getEdgeTarget(e);
                    Object v1 = vertexMapObj.get(source);
                    Object v2 = vertexMapObj.get(target);
                    mxGraph.insertEdge(parentObj, null, "", v1, v2);
                }

                // Añadir aristas hacia Internet
                if (!conexionesInternet.isEmpty()) {
                    Object internetVertex = vertexMapObj.get("Internet");
                    for (String node : conexionesInternet.keySet()) {
                        Object v1 = vertexMapObj.get(node);
                        if (v1 != null) {
                            mxGraph.insertEdge(parentObj, null, "", v1, internetVertex,
                                    "dashed=1;strokeColor=black;");
                        }
                    }
                }

                // Añadir aristas DNS
                for (String key : dnsQueries.keySet()) {
                    String[] parts = key.split("-");
                    if (parts.length == 2) {
                        String clientIp = parts[0];
                        String dnsServerIp = parts[1];
                        Object v1 = vertexMapObj.get(clientIp);
                        Object v2 = vertexMapObj.get(dnsServerIp);
                        if (v1 != null && v2 != null) {
                            mxGraph.insertEdge(parentObj, null, dnsQueries.get(key).toString(), v1, v2,
                                    "dashed=1;strokeColor=green;");
                        }
                    }
                }

            } finally {
                mxGraph.getModel().endUpdate();
            }

            // Layout del grafo
            mxIGraphLayout layout = new mxOrganicLayout(mxGraph);
            layout.execute(parentObj);

            // Exportar el grafo como imagen
            String nombreBase = rutaArchivoPcapng.getName().substring(0,
                    rutaArchivoPcapng.getName().lastIndexOf('.'));
            String nombreGrafico = nombreBase + ".png";
            String rutaGrafico = rutaArchivoPcapng.getParent() + File.separator + nombreGrafico;

            BufferedImage image = mxCellRenderer.createBufferedImage(mxGraph, null, 1, Color.WHITE, true, null);
            ImageIO.write(image, "PNG", new File(rutaGrafico));
            System.out.println("Gráfico guardado en: " + rutaGrafico);
        } catch (PcapNativeException | NotOpenException e) { // Captura de NotOpenException aquí
            e.printStackTrace();
        } catch (IOException e) {
            e.printStackTrace();
        } finally {
            if (handle != null && handle.isOpen()) {
                try {
                    handle.close();
                } catch (NotOpenException e) { // Captura de NotOpenException al cerrar
                    e.printStackTrace();
                }
            }
        }
    }

    // ========================
    // Ejecución del Programa
    // ========================

    public static void main(String[] args) {
        if (args.length > 0) {
            String rutaCarpeta = args[0];
            generarGraficoPersonalizado(rutaCarpeta);
        } else {
            // Crear ventana para seleccionar carpeta si no se proporcionó ruta
            JFileChooser chooser = new JFileChooser();
            chooser.setFileSelectionMode(JFileChooser.DIRECTORIES_ONLY);
            int returnVal = chooser.showOpenDialog(null);
            if (returnVal == JFileChooser.APPROVE_OPTION) {
                String rutaCarpeta = chooser.getSelectedFile().getAbsolutePath();
                generarGraficoPersonalizado(rutaCarpeta);
            } else {
                JOptionPane.showMessageDialog(null, "No se proporcionó la ruta de la carpeta.", "Error",
                        JOptionPane.ERROR_MESSAGE);
                System.exit(1);
            }
        }
    }
}
