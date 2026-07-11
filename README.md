# Sistema de Transcripción y Traducción en Tiempo Real Orientado a la Inclusión Educativa Universitaria

Trabajo Fin de Grado — Grado en Ingeniería Informática (Universidad de Alicante)
Autor: Rubén Calvo Mollón | Tutor: Rafael Rodrigo Guillén

## Descripción del sistema

El sistema está compuesto por dos módulos independientes que se comunican mediante WebSocket:

- **Servidor** (`Servidor.ipynb`): se ejecuta en Google Colab. Carga un modelo Whisper (mediante `faster-whisper`) y expone un servidor WebSocket accesible desde Internet a través de un túnel creado con ngrok. Recibe audio en streaming, lo transcribe y, opcionalmente, lo traduce al inglés.
- **Cliente** (`cliente.py`): se ejecuta en el ordenador del usuario. Captura el audio del micrófono, lo envía al servidor en tiempo real y muestra los subtítulos generados en una ventana gráfica (Tkinter).

El flujo completo es: micrófono → cliente local → servidor en la nube (Colab + GPU) → subtítulos en pantalla.

## Requisitos previos

Antes de arrancar el sistema, necesitas tener preparado lo siguiente:

- Una cuenta de Google, para poder ejecutar el notebook del servidor en Google Colab.
- Una cuenta gratuita en [ngrok](https://ngrok.com), necesaria para exponer el servidor a Internet.
- Python 3.10 o superior instalado en el ordenador donde se ejecutará el cliente.
- Un micrófono conectado y funcionando en ese mismo ordenador.
- Git instalado (opcional, solo si vas a clonar el repositorio en lugar de descargarlo como ZIP).

## Instalación

### 1. Descargar el repositorio

Clona el repositorio o descárgalo como ZIP desde GitHub:

```bash
git clone https://github.com/rcm144-ua/TFG_Ruben_Calvo_Mollon_2026.git
cd TFG_Ruben_Calvo_Mollon_2026
```

### 2. Instalar las dependencias del cliente

El cliente necesita las siguientes librerías de Python:

- `websockets`
- `sounddevice`
- `numpy`

Instálalas con:

```bash
pip install websockets sounddevice numpy
```

O, si el repositorio incluye un archivo `requirements.txt`:

```bash
pip install -r requirements.txt
```

`tkinter` no necesita instalación aparte en la mayoría de sistemas, ya que viene incluido con Python. En algunas distribuciones de Linux puede requerir instalarlo por separado (`sudo apt install python3-tk`).

### 3. Dependencias del servidor

No es necesario instalar nada en tu propio ordenador para el servidor, ya que se ejecuta íntegramente en Google Colab, que ya incluye la mayoría de librerías necesarias (`torch`, `numpy`). Las únicas que instala el propio notebook al ejecutarse son:

- `faster-whisper`
- `pyngrok`
- `websockets`

Estas se instalan automáticamente si el notebook incluye una celda con:

```bash
!pip install faster-whisper pyngrok websockets
```

Si tu copia del notebook no la tiene, añádela como primera celda antes de ejecutar el resto.

## Puesta en marcha

### Paso 1: Configurar y arrancar el servidor (Google Colab)

1. Sube o abre `Servidor.ipynb` en [Google Colab](https://colab.research.google.com/).
2. Ve a **Entorno de ejecución > Cambiar tipo de entorno de ejecución** y selecciona **GPU** (recomendado: T4). Es importante para que la transcripción funcione con una latencia razonable.
3. Crea una cuenta gratuita en [ngrok.com](https://ngrok.com) si todavía no tienes una.
4. Copia tu Authtoken personal desde el panel de ngrok:
   👉 https://dashboard.ngrok.com/get-started/your-authtoken
5. En el notebook, busca la sección `NGROK` (cerca del final del script) y localiza esta línea:

   ```python
   ngrok.set_auth_token("TU_AUTHTOKEN_AQUI")
   ```

   Sustituye `"TU_AUTHTOKEN_AQUI"` por el Authtoken que has copiado de tu cuenta.
6. (Recomendado) Cambia también el valor de la variable `SECRET` por una clave propia. Debe ser exactamente la misma en el servidor y en el cliente:

   ```python
   SECRET = "TU_CLAVE_SECRETA_AQUI"
   ```

7. Ejecuta todas las celdas en orden: **Entorno de ejecución > Ejecutar todo**.
8. Espera a que el modelo Whisper termine de cargarse (puede tardar 1-2 minutos la primera vez). Verás en el log un mensaje similar a:

   ```
   [Servidor] Modelo cargado correctamente: large-v3
   ```

9. Al final de la ejecución aparecerá una URL pública generada por ngrok, con este formato:

   ```
   [Servidor] URL pública para el cliente:
   wss://xxxxxxxxxx.ngrok-free.app
   ```

   Copia esta URL, la necesitarás en el siguiente paso.

⚠️ Las sesiones gratuitas de Google Colab se desconectan tras un periodo de inactividad o tras varias horas de uso continuado. Si esto ocurre, vuelve a ejecutar el notebook: obtendrás una nueva URL de ngrok que deberás actualizar en el cliente.

### Paso 2: Configurar y arrancar el cliente (equipo local)

1. Abre el archivo `cliente.py` en un editor de texto y localiza estas variables al principio del script:

   ```python
   SERVER_URL = "wss://xxxxxxxxxx.ngrok-free.app"
   SECRET = "TU_CLAVE_SECRETA_AQUI"
   ```

2. Sustituye `SERVER_URL` por la URL copiada del notebook del servidor.
3. Asegúrate de que `SECRET` coincide exactamente con el valor configurado en el servidor.
4. Ejecuta el cliente desde una terminal:

   ```bash
   python cliente.py
   ```

5. Se abrirá una ventana con los subtítulos en tiempo real. Habla cerca del micrófono; tras unos segundos, el texto transcrito o traducido aparecerá en pantalla.
6. Usa los botones de la parte superior de la ventana para alternar entre modo **Español** (transcripción) e **Inglés** (traducción).
7. Al cerrar la ventana (botón "Salir" o el aspa), se generan automáticamente dos archivos en la carpeta del proyecto:
   - `transcripcion_completa.txt`: texto completo transcrito/traducido durante la sesión.
   - `latencias.csv`: latencias medidas (en segundos) por cada fragmento de audio procesado.

## Solución de problemas comunes

| Problema | Posible causa | Solución |
|---|---|---|
| El cliente no conecta al servidor | La URL de ngrok ha cambiado o expirado | Vuelve a ejecutar el notebook y actualiza `SERVER_URL` en `cliente.py` |
| "ERROR servidor: Auth incorrecta" | El valor de `SECRET` no coincide entre cliente y servidor | Verifica que ambos archivos tengan exactamente la misma clave |
| No se detecta el micrófono | Dispositivo no configurado o sin permisos | Revisa los permisos de micrófono del sistema operativo |
| El servidor tarda mucho en responder | Sesión de Colab sin GPU asignada | Comprueba que el entorno de ejecución esté en modo GPU |
| Error al pegar el Authtoken de ngrok | Cuenta de ngrok no verificada o token incorrecto | Verifica tu correo y copia el token de nuevo desde el panel de ngrok |

## Estructura del repositorio

```
TFG_Ruben_Calvo_Mollon_2026/
├── Servidor.ipynb          # Notebook del servidor (ejecutar en Google Colab)
├── cliente.py              # Script del cliente (ejecutar en local)
├── requirements.txt        # Dependencias del cliente
└── README.md               # Este archivo
```

## Notas de seguridad

- El Authtoken de ngrok y la clave `SECRET` son credenciales personales. No las compartas públicamente ni las subas a un repositorio con visibilidad pública si mantienes tu servidor activo, ya que cualquiera con el `SECRET` podría autenticarse contra tu servidor mientras esté en ejecución.
- Cada usuario que quiera ejecutar este sistema debe generar su propio Authtoken de ngrok con su propia cuenta gratuita; el incluido originalmente en el desarrollo del proyecto ha sido eliminado del código fuente.
