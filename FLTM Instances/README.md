
# Documentación
## AddContextMenu.reg
### Objetivo
El objetivo de estos scripts es agregar opciones personalizadas al menú contextual de Windows para facilitar tareas específicas de análisis de datos.
### Estructura
Los scripts modifican el registro de Windows para incluir un nuevo menú contextual llamado 'Data Analysis', con varias opciones y submenús para realizar diferentes tareas relacionadas con el análisis de datos.
### Árbol de directorio que crea
Los scripts asumen la existencia de un directorio `C:\DataAnalysis` donde se deben ubicar los siguientes archivos:
- `ProcessAltitudes.ps1`: Script de PowerShell para la opción 'Check_FLTMC'.
- `UninstallContextMenu.reg`: Script de registro para eliminar las opciones del menú contextual.
- `documentación.pdf`: Documentación relacionada con las herramientas de análisis de datos.
### Cómo usarlo
Para utilizar las opciones del menú contextual proporcionadas por estos scripts:
1. Ejecute el script `.reg` para agregar las opciones al menú contextual.
2. Haga clic derecho en un archivo o carpeta y seleccione 'Data Analysis' para acceder a las herramientas.
3. Elija 'Check_FLTMC' para ejecutar el script de análisis correspondiente.
4. Seleccione 'Documentación' para abrir el archivo PDF con la documentación.
5. Para desinstalar las opciones del menú contextual, elija 'Uninstall ContextMenus'.
**Nota:** Es importante tener permisos de administrador antes de realizar cambios en el registro de Windows y entender que la modificación incorrecta del registro puede causar problemas en el sistema.
---------------------------------------------------------------------------------------
## Procesaltitudes.ps1
### Objetivo
Este script automatiza la recopilación y análisis de datos de altitudes asignadas a compañías, facilitando la gestión y visualización de esta información.
### Estructura
El script realiza las siguientes funciones:
- Verifica la existencia de un archivo CSV con datos recientes.
- Si los datos no están actualizados o no existen, realiza una solicitud web para obtener datos nuevos.
- Procesa el contenido HTML de la página web para extraer datos relevantes.
- Exporta los datos a un archivo CSV.
- Lee un archivo de texto específico y procesa su contenido.
- Compara los datos obtenidos con los datos locales.
- Exporta los resultados finales a archivos CSV y TXT.
### Árbol de directorio que crea
El script utiliza y, si es necesario, crea la siguiente estructura de directorio:
- `C:\DataAnalysis`: Carpeta principal para los scripts y bibliotecas.
- `C:\DataAnalysis\db`: Carpeta donde se almacenan los archivos CSV con los datos de altitudes.
### Cómo usarlo
Para ejecutar este script, siga estos pasos:
1. Guarde el script en una ubicación accesible en su sistema.
2. Abra PowerShell como administrador.
3. Ejecute el script proporcionando una ruta válida como argumento.
4. Revise los resultados en las carpetas y archivos generados.
**Nota:** Asegúrese de tener los permisos necesarios y de entender que la modificación de archivos y directorios puede afectar su sistema.
---------------------------------------------------------------------------------------------
## Uninstallcontextmenu.reg
### Objetivo
Este script se utiliza para desinstalar automáticamente las opciones personalizadas del menú contextual de Windows que fueron agregadas previamente.
### Estructura
El script ejecuta un archivo `.reg` que contiene las instrucciones necesarias para eliminar las entradas del registro de Windows asociadas con las opciones del menú contextual.
### Cómo usarlo
Para ejecutar este script, siga estos pasos:
1. Asegúrese de tener derechos de administrador en su sistema.
2. Guarde el script en una ubicación accesible en su sistema.
3. Haga clic derecho en el script y seleccione 'Ejecutar como administrador'.
4. El script ejecutará el archivo `.reg` y confirmará la desinstalación con un mensaje.
5. Presione Enter para cerrar la ventana de PowerShell cuando haya terminado.
**Nota:** Ejecutar scripts que modifican el registro puede afectar la configuración de su sistema. Asegúrese de entender las acciones que realiza el script antes de ejecutarlo.
---------------------------------------------------------------------------------------------
