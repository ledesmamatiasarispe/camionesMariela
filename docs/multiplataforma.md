# Multiplataforma

## Requisito

La aplicacion debe funcionar en Windows y macOS. El diseno tecnico debe evitar dependencias exclusivas de un sistema operativo salvo que exista una alternativa equivalente para el otro.

La aplicacion debe distribuirse con sus dependencias internas, evitando pasos de instalacion tecnica en cada equipo usuario.

La aplicacion sera cliente solamente, sin servidor.

## Opciones tecnicas candidatas

### App de escritorio con Python

Una app instalable o portable desarrollada en Python.

Ventajas:

- Permite construir logica de negocio clara y mantenible.
- Funciona en Windows y macOS si se eligen librerias compatibles.
- Puede empaquetarse con Python incluido para que el usuario final no instale nada.
- Es buena opcion si el equipo prefiere evitar una arquitectura web.

Riesgos:

- Hay que generar un build por sistema operativo.
- Algunas librerias graficas o de sistema pueden comportarse distinto entre Windows y macOS.
- El empaquetado debe probarse en maquinas limpias.

### Web app

Una aplicacion web accesible desde navegador.

Ventajas:

- Funciona en Windows y macOS sin instalador.
- Facil de actualizar.
- Menos problemas con permisos locales.
- Buena opcion si varios usuarios comparten datos.

Riesgos:

- Requiere servidor local, red interna o hosting.
- Si necesita funcionar sin red, hay que diseñar modo offline.
- Si se instala un servidor local por PC, ese servidor tambien debe venir empaquetado.

### App de escritorio con Electron

Una app instalable basada en tecnologias web.

Ventajas:

- Misma base de codigo para Windows y macOS.
- Permite acceso mas controlado a archivos locales.
- Ecosistema maduro para instaladores.
- Incluye Chromium y Node dentro del paquete final.

Riesgos:

- App mas pesada.
- Hay que mantener builds separados para Windows y macOS.

### App de escritorio con Tauri

Una app instalable liviana basada en frontend web y backend Rust.

Ventajas:

- Menor peso que Electron.
- Buena integracion con escritorio.
- Builds para Windows y macOS.
- Puede generar binarios autocontenidos con instaladores por sistema.

Riesgos:

- Requiere mas cuidado tecnico.
- Rust agrega complejidad si el equipo no lo usa.

## Recomendacion inicial

La direccion elegida es una app de escritorio en Python. Conviene mantener la maqueta visual web solo como referencia de diseno, mientras la implementacion real avanza en `src/gestion_camiones`.

Si el sistema va a ser usado por varias computadoras, asumir inicialmente que cada equipo gestiona datos locales. Compartir un mismo archivo de datos en red debe considerarse una excepcion y probarse con cuidado.

## Reglas practicas

- No guardar rutas absolutas del estilo `C:\...` o `/Users/...` en la logica de negocio.
- Usar selectores de archivos cuando el usuario deba elegir documentos.
- Normalizar nombres de archivos y extensiones.
- Evitar comandos del sistema operativo en procesos centrales.
- Diseñar exportaciones en formatos comunes: CSV, XLSX o PDF.
- Probar teclado, scroll, tablas y formularios en ambos sistemas.
- Mantener fuentes del sistema para que la interfaz se vea nativa.
- No requerir instalacion manual de Node.js, Python, Java, .NET SDK, Rust, Git u otras herramientas en equipos usuarios.
- Diferenciar dependencias de desarrollo y dependencias incluidas en el paquete final.

## Datos y archivos

Definir temprano donde viven los datos:

- Archivo local por equipo.
- Carpeta compartida de red, solo si se acepta el riesgo y se valida.
- Exportaciones y backups manuales.

Esta decision afecta permisos, copias de seguridad, concurrencia y riesgo de perdida de datos.

## Empaquetado futuro

Si se convierte en app de escritorio, preparar:

- Instalador para Windows.
- Paquete o imagen para macOS.
- Firma de la aplicacion si se distribuye fuera del equipo de desarrollo.
- Estrategia de actualizacion.
- Ubicacion clara para configuracion, logs y datos locales.
- Verificacion de que la app abre en una maquina limpia sin herramientas de desarrollo instaladas.
