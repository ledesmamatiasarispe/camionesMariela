# Distribucion autocontenida

## Requisito

La app debe poder ejecutarse en cada equipo usuario sin instalar manualmente dependencias tecnicas. El paquete final debe incluir todo lo necesario para abrir y usar el sistema.

## Que no debe exigir al usuario final

- Instalar Node.js.
- Instalar Python.
- Instalar Java.
- Instalar Git.
- Instalar gestores de paquetes.
- Ejecutar comandos por consola.
- Configurar variables de entorno.
- Descargar librerias adicionales.

## Que si puede requerir

- Ejecutar un instalador aprobado.
- Abrir una app portable desde una carpeta compartida o local.
- Aceptar permisos normales del sistema operativo.
- Configurar una ruta de datos una sola vez, si el flujo lo necesita.

## Criterios de tecnologia

La tecnologia elegida debe permitir:

- Build para Windows.
- Build para macOS.
- Inclusión de dependencias internas.
- Instalador o paquete portable.
- Actualizacion controlada.
- Configuracion separada del codigo.
- Logs accesibles para soporte.
- Publicacion de versiones en GitHub Releases.

## Preferencias iniciales

### App de escritorio Python

La direccion elegida es una app de escritorio en Python.

Usar PySide6 para la interfaz y PyInstaller para generar paquetes autocontenidos por sistema operativo.

El usuario final no debe instalar Python ni PySide6: ambas cosas deben quedar incluidas en el paquete generado.

## Datos compartidos

El requisito de app autocontenida no resuelve por si solo donde se guardan los datos. Hay que elegir una estrategia:

- Archivo local: simple, pero riesgoso si varias PCs editan al mismo tiempo.
- Carpeta compartida: posible, pero requiere control de bloqueos, backups y corrupcion de archivos.

Como la app sera cliente solamente, la recomendacion inicial es SQLite local y backups/exportaciones.

## Actualizaciones

El canal de actualizacion sera GitHub Releases.

La app debe consultar periodicamente si hay una version nueva y avisar al usuario. Para la primera etapa, la descarga/instalacion puede requerir confirmacion del usuario.

## Prueba obligatoria antes de entregar

Antes de considerar una version lista para uso, probar:

- Windows sin Node.js/Python/Git instalados.
- macOS sin herramientas de desarrollo instaladas.
- Ejecucion desde una carpeta con espacios en el nombre.
- Ejecucion con usuario sin permisos de administrador.
- Exportacion/importacion de archivos.
- Reinicio de la app conservando configuracion y datos.
