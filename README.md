# Modelado y Diseño de un Sistema de Transcripción y Traducción en Tiempo Real Orientado a la Inclusión Educativa Universitaria

Trabajo Fin de Grado — Grado en Ingeniería Informática (Universidad de Alicante)
Autor: Rubén Calvo Mollón | Tutor: Rafael Rodrigo Guillén

## Requisitos previos

Antes de arrancar el sistema, se necesita tener lo siguiente:

- Una cuenta de Google, para poder ejecutar el notebook del servidor en Google Colab.
- Una cuenta gratuita en [ngrok](https://ngrok.com), necesaria para exponer el servidor a Internet.
- Python 3.10 o superior instalado en el ordenador donde se ejecutará el cliente.
- Un micrófono conectado y funcionando en ese mismo ordenador.

## Instalación

### 1. Instalar las dependencias del cliente

El cliente necesita las siguientes librerías de Python:

- `websockets`
- `sounddevice`
- `numpy`


### 3. Dependencias del servidor

No es necesario instalar nada en tu propio ordenador para el servidor, ya que se ejecuta completamente en Google Colab, que ya incluye la mayoría de librerías básicas necesarias (`torch`, `numpy`). Sin embargo, las siguientes dependencias si que necsitan ser intaladas al iniciar el cuaderno al cambiar de entorno de ejecución:

- `faster-whisper`
- `pyngrok`
- `websockets`

Para ello, antes de ejecutar la celda del código del servidor hay que ejecutar previamente la siguiente celda de instalación de dependencias.

```bash
!pip install -q faster-whisper pyngrok websockets
```

## Puesta en marcha

### Paso 1: Configurar y arrancar el servidor (Google Colab)

1. Subir o abrir `Servidor.ipynb` en [Google Colab](https://colab.research.google.com/).
2. Ir a **Entorno de ejecución > Cambiar tipo de entorno de ejecución** y selecciona **GPU** (El trabajo y sus pruebas se han ejecutado en T4).
3. Crear una cuenta gratuita en [ngrok.com](https://ngrok.com) si todavía no se tiene una.
4. Copiar el Authtoken personal desde el panel de ngrok:
   https://dashboard.ngrok.com/get-started/your-authtoken
5. En el cuaderno de Google Colab, donde se ecuentra el código del mópdulo servidor, localizar esta línea:

   ```python
   ngrok.set_auth_token("AUTHTOKEN_AQUI")
   ```

   Sustituye `"AUTHTOKEN_AQUI"` por el Authtoken que se copiado de la cuenta propia.
6. (Recomendado) Cambiar también el valor de la variable `SECRET` por una clave propia. Debe ser exactamente la misma en el servidor y en el cliente.
7. Ejecutar todas las celdas en orden: **Entorno de ejecución > Ejecutar todo**.
8. Esperar a que el modelo Whisper termine de cargarse (puede tardar 1-2 minutos la primera vez). Se verá en el log un mensaje similar a (si aparecen warnings no son relevantes mientras se haya cargado el modelo correctamente y se haya generado la URL correspondiente:

   ```
   [Servidor] Modelo cargado correctamente: large-v3
   ```

9. Al final de la ejecución aparecerá una URL pública generada por ngrok, con este formato:

   ```
   [Servidor] URL pública para el cliente:
   wss://xxxxxxxxxx.ngrok-free.app
   ```

   Copiar esta URL, será necesaria en el siguiente paso.

Las sesiones gratuitas de Google Colab se desconectan tras un periodo de inactividad o tras varias horas de uso continuado. Si esto ocurre, volver a ejecutar el cuaderno.

### Paso 2: Configurar y arrancar el cliente (equipo local)

1. Abrir el archivo `cliente.py` en un editor de texto y localizar estas variables al principio:

   ```python
   SERVER_URL = "wss://xxxxxxxxxx.ngrok-free.app"
   SECRET = ""
   ```

2. Sustituir `SERVER_URL` por la URL copiada del cuaderno del servidor.
3. Asegurarse de que `SECRET` coincide exactamente con el valor configurado en el servidor. Este se trata de la clave de autentiacación. (Se ha dejado los valores tanto de la URL como del SECRET los mismos que se han usado en las ejecuciones propias)
5. Ejecutar el cliente

6. Se abrirá una ventana con los subtítulos en tiempo real. Hablar cerca del micrófono. Después de unos segundos, el texto transcrito o traducido aparecerá en pantalla. La primera vez puede tardar mas de la cuenta en que aparezcan los subtítulos.
7. Usar los botones de la parte superior de la ventana para cambiar entre modo **Español** (transcripción) e **Inglés** (traducción).


