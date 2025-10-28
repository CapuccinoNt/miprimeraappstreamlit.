# PackSmith

PackSmith es un laboratorio de packs para Minecraft construido con Streamlit. Está pensado para importar paquetes existentes (CurseForge, Modrinth o ZIP genérico), inspeccionar su contenido y preparar cambios con seguridad desde un entorno web de escritorio.

## Características principales

- **Importación inteligente**: acepta `.zip` y `.mrpack`, crea un workspace temporal inmutable y detecta versión de Minecraft, loader y manifiestos (CurseForge, Modrinth, packwiz).
- **Panel de mods**: analiza la carpeta `/mods`, lee metadatos de Fabric/Quilt/Forge, calcula hashes SHA-1, permite activar o desactivar mods (moviendo archivos entre `mods/` y `mods_disabled/`) y resalta duplicados en la tabla editable (`st.experimental_data_editor`).
- **Validación de dependencias**: construye un grafo sencillo a partir de las dependencias declaradas y avisa cuando faltan requisitos obligatorios o se detectan duplicados.
- **Sugerencias automáticas**: ofrece recomendaciones para resolver faltantes, duplicados y conflictos básicos de loader directamente desde la pestaña Diagnostics.
- **Editor de configuraciones**: explora `/config`, `/defaultconfigs` y `/serverconfig`; permite editar archivos, compararlos con su versión original y revertir cambios rápidamente.
- **Scripts y datos**: navegación básica por scripts KubeJS, listado de datapacks, resourcepacks y shaderpacks.
- **Exportación rápida**: genera un ZIP con el estado actual del workspace y un changelog preliminar con mods detectados y archivos de configuración tocados.

## Uso

1. Instala dependencias:
   ```bash
   pip install -r requirements.txt
   ```
2. Ejecuta la aplicación:
   ```bash
   streamlit run app.py
   ```
3. Importa un paquete desde la barra lateral y recorre las pestañas para revisar mods, configuraciones y diagnósticos.

## Hoja de ruta sugerida

- **MVP**: importar/validar packs, tabla de mods, edición de configuraciones, exportación a ZIP.
- **v1**: visualizar grafo de dependencias enriquecido, sugerencias automáticas para resolver faltantes, editor KubeJS con búsqueda avanzada, analizador básico de logs de crash.
- **v2**: integración con Modrinth/CurseForge APIs, reglas de compatibilidad extensibles, transformaciones masivas de configs y exportación a formatos adicionales (Prism, packwiz).

PackSmith sienta las bases para un flujo de trabajo moderno en la gestión de modpacks y puede ampliarse con nuevas pestañas, análisis y automatizaciones según las necesidades del equipo.
