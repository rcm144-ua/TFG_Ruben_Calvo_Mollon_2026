import asyncio
import json
import queue
import threading
import tkinter as tk
from tkinter import ttk
import time
import csv

import numpy as np
import sounddevice as sd
import websockets


SERVER_URL = "wss://spinster-outshine-late.ngrok-free.dev"
SECRET = "WS_TFG_Ruben_2026_k9P4xL2mQ7vN8s"

SAMPLERATE = 16000
BLOCK_DURATION = 0.5
CHANNELS = 1
DTYPE = "float32"

INITIAL_OUTPUT_MODE = "en"   # "es" o "en"

frames_per_block = int(SAMPLERATE * BLOCK_DURATION)


CHUNK_DURATION = 3.0
frames_per_chunk = int(SAMPLERATE * CHUNK_DURATION)
chunk_timestamps: "queue.Queue[float]" = queue.Queue()
latencias = []
full_text_global = ""  

audio_queue: "queue.Queue[np.ndarray]" = queue.Queue(maxsize=50)
ui_queue: "queue.Queue[tuple[str, str]]" = queue.Queue()
control_queue: "queue.Queue[dict]" = queue.Queue()
stop_event = threading.Event()


def clear_chunk_timestamps():
    while not chunk_timestamps.empty():
        try:
            chunk_timestamps.get_nowait()
        except queue.Empty:
            break


def merge_text(current: str, new: str) -> str:
    current = current.strip()
    new = new.strip()

    if not new:
        return current
    if not current:
        return new
    if current == new:
        return current
    if current.endswith(new):
        return current

    max_overlap = min(len(current), len(new))
    for i in range(max_overlap, 0, -1):
        if current[-i:] == new[:i]:
            return current + new[i:]

    return current + " " + new


def wrap_last_lines(text: str, line_width: int, max_lines: int) -> str:
    words = text.split()
    if not words:
        return ""

    lines = []
    current_line = ""

    for word in words:
        candidate = word if not current_line else current_line + " " + word
        if len(candidate) <= line_width:
            current_line = candidate
        else:
            if current_line:
                lines.append(current_line)
            current_line = word

    if current_line:
        lines.append(current_line)

    return "\n".join(lines[-max_lines:])


def audio_callback(indata, frames, time_info, status):
    if status:
        ui_queue.put(("status", f"Estado de audio: {status}"))

    block = indata.copy().reshape(-1).astype(np.float32)

    try:
        audio_queue.put_nowait(block)
    except queue.Full:
        ui_queue.put(("status", "Cola llena: se descarta un bloque de audio."))


def recorder():
    try:
        with sd.InputStream(
            samplerate=SAMPLERATE,
            channels=CHANNELS,
            dtype=DTYPE,
            blocksize=frames_per_block,
            callback=audio_callback,
        ):
            ui_queue.put(("status", "Micrófono activo. Escuchando..."))
            while not stop_event.is_set():
                sd.sleep(100)
    except Exception as e:
        ui_queue.put(("status", f"Error de micrófono: {e}"))


async def sender(ws):
    accumulated_frames = 0
    chunk_start_time = None

    while not stop_event.is_set():
        block = await asyncio.to_thread(audio_queue.get)

        if chunk_start_time is None:
            chunk_start_time = time.time()

        accumulated_frames += len(block)
        await ws.send(block.tobytes())

        if accumulated_frames >= frames_per_chunk:
            chunk_timestamps.put(chunk_start_time)
            accumulated_frames = 0
            chunk_start_time = None


async def control_sender(ws):
    while not stop_event.is_set():
        command = await asyncio.to_thread(control_queue.get)

        if command.get("type") == "set_mode":
            clear_chunk_timestamps()

        await ws.send(json.dumps(command, ensure_ascii=False))


async def receiver(ws):
    global full_text_global
    full_text = ""
    last_piece = ""

    async for message in ws:
        data = json.loads(message)

        if data.get("type") == "ack":
            mode = data.get("output_mode", INITIAL_OUTPUT_MODE)
            clear_chunk_timestamps() 
            ui_queue.put(("subtitle", ""))
            ui_queue.put(("status", f"Conectado. Modo actual: {mode}"))
            continue

        if data.get("type") == "mode_ack":
            mode = data.get("output_mode", INITIAL_OUTPUT_MODE)
            full_text = ""
            last_piece = ""
            clear_chunk_timestamps() 
            ui_queue.put(("subtitle", ""))
            ui_queue.put(("status", f"Modo cambiado a: {mode}"))
            continue

        if data.get("type") == "error":
            ui_queue.put(("status", f"ERROR servidor: {data.get('message', '')}"))
            continue

        if data.get("type") == "result":
            text = data.get("text", "").strip()

            if not text:
                translation = data.get("translation", "").strip()
                transcript = data.get("transcript", "").strip()
                text = translation if translation else transcript

            if text and text != last_piece:
                last_piece = text
                full_text = merge_text(full_text, text)
                full_text_global = full_text
                visible_text = wrap_last_lines(full_text, line_width=42, max_lines=2)
                ui_queue.put(("subtitle", visible_text))

                if not chunk_timestamps.empty():
                    t_envio = chunk_timestamps.get()
                    latencia = time.time() - t_envio
                    latencias.append(latencia)
                    ui_queue.put(("status", f"Latencia último chunk: {latencia:.2f}s"))


async def websocket_client():
    config_msg = {
        "type": "config",
        "secret": SECRET,
        "samplerate": SAMPLERATE,
        "channels": CHANNELS,
        "block_duration": BLOCK_DURATION,
        "dtype": DTYPE,
        "output_mode": INITIAL_OUTPUT_MODE,
    }

    while not stop_event.is_set():
        try:
            ui_queue.put(("status", f"Conectando a {SERVER_URL} ..."))

            async with websockets.connect(
                SERVER_URL,
                max_size=None,
                ping_interval=30,
                ping_timeout=30,
                compression=None,
            ) as ws:
                ui_queue.put(("status", "Conexión WebSocket establecida"))

                await ws.send(json.dumps(config_msg, ensure_ascii=False))
                ui_queue.put(("status", "Autenticación/configuración enviada"))

                send_task = asyncio.create_task(sender(ws))
                recv_task = asyncio.create_task(receiver(ws))
                control_task = asyncio.create_task(control_sender(ws))

                done, pending = await asyncio.wait(
                    [send_task, recv_task, control_task],
                    return_when=asyncio.FIRST_EXCEPTION,
                )

                for task in pending:
                    task.cancel()

                for task in done:
                    exc = task.exception()
                    if exc:
                        raise exc

        except Exception as e:
            if not stop_event.is_set():
                ui_queue.put(("status", f"Conexión perdida o error: {e}"))
                ui_queue.put(("status", "Reintentando en 3 segundos..."))
                await asyncio.sleep(3)


def run_async_client():
    asyncio.run(websocket_client())


class SubtitleWindow:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Subtítulos en tiempo real")
        self.root.geometry("1100x320")
        self.root.configure(bg="black")

        self.subtitle_var = tk.StringVar(value="")
        self.status_var = tk.StringVar(value="Inicializando...")
        self.mode_var = tk.StringVar(value=INITIAL_OUTPUT_MODE)

        top_frame = tk.Frame(root, bg="black")
        top_frame.pack(fill="x", pady=(10, 0))

        mode_label = tk.Label(
            top_frame,
            text="Modo:",
            font=("Segoe UI", 11, "bold"),
            fg="white",
            bg="black",
        )
        mode_label.pack(side="left", padx=(12, 6))

        rb_es = tk.Radiobutton(
            top_frame,
            text="Español",
            variable=self.mode_var,
            value="es",
            command=self.on_mode_change,
            fg="white",
            bg="black",
            selectcolor="#222222",
            activebackground="black",
            activeforeground="white",
        )
        rb_es.pack(side="left", padx=4)

        rb_en = tk.Radiobutton(
            top_frame,
            text="English",
            variable=self.mode_var,
            value="en",
            command=self.on_mode_change,
            fg="white",
            bg="black",
            selectcolor="#222222",
            activebackground="black",
            activeforeground="white",
        )
        rb_en.pack(side="left", padx=4)

        self.subtitle_label = tk.Label(
            root,
            textvariable=self.subtitle_var,
            font=("Segoe UI", 24, "bold"),
            fg="white",
            bg="black",
            justify="center",
            wraplength=1000,
            anchor="center",
            padx=20,
            pady=20,
        )
        self.subtitle_label.pack(fill="both", expand=True)

        self.status_label = tk.Label(
            root,
            textvariable=self.status_var,
            font=("Segoe UI", 10),
            fg="#bbbbbb",
            bg="black",
            anchor="w",
            padx=10,
            pady=4,
        )
        self.status_label.pack(fill="x")

        button_frame = tk.Frame(root, bg="black")
        button_frame.pack(fill="x", pady=(0, 8))

        clear_btn = ttk.Button(
            button_frame,
            text="Limpiar",
            command=self.clear_subtitle,
        )
        clear_btn.pack(side="left", padx=10)

        close_btn = ttk.Button(
            button_frame,
            text="Salir",
            command=self.on_close,
        )
        close_btn.pack(side="right", padx=10)

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.poll_ui_queue()

    def clear_subtitle(self):
        self.subtitle_var.set("")
        self.status_var.set("Texto limpiado.")

    def on_mode_change(self):
        selected_mode = self.mode_var.get()
        self.subtitle_var.set("")

        control_queue.put({
            "type": "set_mode",
            "output_mode": selected_mode,
        })

        if selected_mode == "es":
            self.status_var.set("Cambiando a transcripción en español...")
        else:
            self.status_var.set("Cambiando a traducción en inglés...")

    def poll_ui_queue(self):
        try:
            while True:
                msg_type, payload = ui_queue.get_nowait()

                if msg_type == "status":
                    self.status_var.set(payload)
                elif msg_type == "subtitle":
                    self.subtitle_var.set(payload)
        except queue.Empty:
            pass

        if not stop_event.is_set():
            self.root.after(120, self.poll_ui_queue)

    def on_close(self):
        stop_event.set()

        try:
            with open("latencias.csv", "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["chunk", "latencia_segundos"])
                for i, lat in enumerate(latencias):
                    writer.writerow([i, round(lat, 3)])
            print(f"Guardadas {len(latencias)} latencias en latencias.csv")
        except Exception as e:
            print(f"Error al guardar latencias.csv: {e}")

        try:
            with open("transcripcion_completa.txt", "w", encoding="utf-8") as f:
                f.write(full_text_global)
            print("Transcripción completa guardada en transcripcion_completa.txt")
        except Exception as e:
            print(f"Error al guardar transcripcion_completa.txt: {e}")

        self.root.destroy()


def main():
    rec_thread = threading.Thread(target=recorder, daemon=True)
    rec_thread.start()

    client_thread = threading.Thread(target=run_async_client, daemon=True)
    client_thread.start()

    root = tk.Tk()
    SubtitleWindow(root)
    root.mainloop()


if __name__ == "__main__":
    main()