# Laboratorio de Máquinas Virtuales para Probar TCPView

## Paso 1: Preparación del Entorno

### Instalación de Hyper-V

1. **Habilitar Hyper-V:**
   - En Windows, ve a 'Panel de Control' > 'Programas' > 'Activar o desactivar las características de Windows'.
   - Marca 'Hyper-V' y asegúrate de que las opciones de Hyper-V Management Tools y Hyper-V Platform estén seleccionadas. Haz clic en 'Aceptar' y reinicia tu sistema si es necesario.

## Paso 2: Creación de Máquinas Virtuales Base

### Crear una VM Base

1. **Abrir Hyper-V Manager.**
2. **Crear una nueva VM:**
   - Haz clic en 'New' > 'Virtual Machine'.
   - Configura la VM con las especificaciones necesarias (nombre, ubicación, generación de la máquina virtual).
   - Asigna memoria y configura la red virtual (usando una red interna o NAT).
   - Adjunta el ISO de Windows Server o Windows 10.
3. **Instalar el Sistema Operativo:**
   - Inicia la VM y sigue las instrucciones para instalar Windows Server o Windows 10.
4. **Configuración Inicial de la VM:**
   - Realiza todas las actualizaciones del sistema operativo.
   - Instala las herramientas de Hyper-V (Integration Services).
   - Descarga e instala Sysinternals Suite, incluyendo TCPView.

### Clonar la VM Base

1. **Apagar la VM Base.**
2. **Exportar la VM Base:**
   - En Hyper-V Manager, selecciona la VM base, haz clic en 'Export' y elige una ubicación para exportar los archivos.
3. **Importar la VM para Crear Clones:**
   - Haz clic en 'Import Virtual Machine' y selecciona la ubicación de exportación.
   - Configura la importación como una nueva VM para cada clon que necesites.

## Paso 3: Configuración de Roles de VM

### Configurar VMs para Diferentes Roles

1. **Servidores:**
   - Asigna roles de servidor (por ejemplo, servidor web con IIS, servidor de base de datos con SQL Server).
   - Configura las aplicaciones y servicios necesarios para que actúen como servidores en tu red de prueba.
2. **Clientes:**
   - Instala aplicaciones de cliente que generen tráfico de red (por ejemplo, navegadores web, clientes de base de datos).

## Paso 4: Configuración de la Red Virtual

1. **Crear Redes Virtuales:**
   - En Hyper-V Manager, ve a 'Virtual Switch Manager'.
   - Crea una red interna o NAT para permitir la comunicación entre las VMs.
   - Asigna las VMs a la red virtual creada.

## Paso 5: Realización de Pruebas con TCPView

### Pruebas Cliente-Servidor

1. **Monitorear Conexiones en el Servidor:**
   - Ejecuta TCPView en el servidor.
   - Desde un cliente, establece una conexión al servidor (por ejemplo, accede a una página web alojada en el servidor web o realiza consultas a la base de datos).
   - Observa las conexiones entrantes en TCPView. Verifica las direcciones IP y puertos de origen y destino.
2. **Monitorear Conexiones en el Cliente:**
   - Ejecuta TCPView en el cliente.
   - Realiza conexiones hacia el servidor.
   - Observa las conexiones salientes en TCPView y verifica que corresponden con las conexiones esperadas en el servidor.

### Pruebas Servidor-Servidor

1. **Configurar Comunicación Entre Servidores:**
   - Configura aplicaciones o servicios en los servidores que se comuniquen entre sí (por ejemplo, réplicas de bases de datos, servidores de aplicaciones distribuidas).
2. **Monitorear Conexiones:**
   - Ejecuta TCPView en ambos servidores.
   - Genera tráfico entre los servidores (por ejemplo, sincronización de bases de datos, transferencia de archivos).
   - Observa las conexiones en ambos servidores y verifica las direcciones IP y puertos.

### Análisis de Tráfico

1. **Identificar Conexiones Legítimas:**
   - Revisa las conexiones en TCPView para identificar procesos legítimos.
   - Verifica la firma digital de los procesos y la ubicación de los ejecutables.
2. **Detectar Actividad Sospechosa:**
   - Busca conexiones inesperadas o sospechosas.
   - Verifica si hay procesos sin firma digital o ubicados en directorios inusuales.

## Paso 6: Automatización y Reportes

### Automatizar Captura de Conexiones con Tcpvcon

1. Crea scripts de PowerShell para ejecutar `Tcpvcon` periódicamente y guardar la salida en archivos de texto para análisis posterior.
    ```powershell
    # Ruta al ejecutable Tcpvcon
    $tcpvconPath = "C:\ruta\a\tcpvcon.exe"
    
    # Ruta al archivo de salida
    $outputPath = "C:\ruta\a\salida_tcpvcon.txt"
    
    # Ejecutar Tcpvcon y redirigir la salida al archivo de texto
    & $tcpvconPath -a > $outputPath
    
    # Opción: Agregar una marca de tiempo a la salida
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Add-Content -Path $outputPath -Value "Reporte generado en: $timestamp"
    ```

### Programar Ejecuciones de Scripts

Usa el Programador de Tareas de Windows para ejecutar los scripts a intervalos regulares.

## Paso 7: Documentación y Análisis

1. **Documentar Observaciones:**
   - Toma notas detalladas de las observaciones durante cada prueba.
   - Documenta cualquier comportamiento inusual o conexión sospechosa.
2. **Analizar Datos Recogidos:**
   - Revisa los datos capturados y analiza patrones en el tráfico de red.
   - Genera reportes sobre el comportamiento de la red y el rendimiento de las aplicaciones probadas.