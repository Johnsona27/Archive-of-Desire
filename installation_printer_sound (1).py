from pathlib import Path
from PIL import Image, ImageOps, ImageWin
from pynput import keyboard
import ctypes
import win32ui
import win32con
import random
import threading
import time

# ARCHIVE OF DESIRE - installation printer and sound controller.
# Keep the POS-80C driver Cutter setting at NONE.
PRINTER_NAME = "POS-80C"
PRINT_WIDTH = 576
PRINT_INTERVAL = 0.2

AUDIO_FILE = (
    Path.home() / "Downloads" / "ArchiveOfDesireWebsite"
    / "sound" / "Sound design.mp3"
)

FOLDERS = [
    Path.home() / "Documents" / "ArchiveOfDesire" / "CONTACT_SHEET_IMAGES",
    Path(r"D:\Year 4\Final year project\PHASE 01 DESIRE\CONTACT_SHEET_IMAGES"),
]
SOURCE = next(
    (folder for folder in FOLDERS
     if folder.is_dir() and any(folder.glob("*.jpg"))),
    None,
)
if SOURCE is None:
    raise SystemExit("Could not find CONTACT_SHEET_IMAGES. Check FOLDERS.")
if not AUDIO_FILE.is_file():
    raise SystemExit(f"Audio file not found: {AUDIO_FILE}")

images = sorted(SOURCE.glob("*.jpg"))
printing_active = threading.Event()
state_lock = threading.RLock()
keys_held = set()
audio_open = False
printed_count = 0


def audio_command(text):
    error = ctypes.windll.winmm.mciSendStringW(text, None, 0, None)
    if error:
        message = ctypes.create_unicode_buffer(512)
        ctypes.windll.winmm.mciGetErrorStringW(error, message, 512)
        raise RuntimeError(message.value)


def stop_audio():
    global audio_open
    if audio_open:
        audio_command("close desire_audio")
        audio_open = False


def start_audio():
    global audio_open
    stop_audio()
    audio_command(f'open "{AUDIO_FILE}" type mpegvideo alias desire_audio')
    audio_open = True
    audio_command("play desire_audio from 0 repeat")


def disconnect():
    with state_lock:
        printing_active.clear()
        try:
            stop_audio()
        except Exception as error:
            print(f"Audio stop error: {error}")


def prepare_image(path):
    with Image.open(path) as original:
        image = ImageOps.exif_transpose(original)
        image = ImageOps.grayscale(image)
        new_height = max(1, round(image.height * PRINT_WIDTH / image.width))
        image = image.resize(
            (PRINT_WIDTH, new_height), Image.Resampling.LANCZOS
        )
        return image.convert("1").convert("RGB")


def print_image(image, title):
    printer = win32ui.CreateDC()
    started = False
    try:
        printer.CreatePrinterDC(PRINTER_NAME)
        width = printer.GetDeviceCaps(win32con.HORZRES)
        height = printer.GetDeviceCaps(win32con.VERTRES)
        scale = min(width / image.width, height / image.height)
        output_width = max(1, round(image.width * scale))
        output_height = max(1, round(image.height * scale))
        x = (width - output_width) // 2
        printer.StartDoc(title)
        started = True
        printer.StartPage()
        ImageWin.Dib(image).draw(
            printer.GetHandleOutput(),
            (x, 0, x + output_width, output_height),
        )
        printer.EndPage()
        printer.EndDoc()
        started = False
    finally:
        if started:
            try:
                printer.AbortDoc()
            except Exception:
                pass
        printer.DeleteDC()


def on_press(key):
    if key not in (keyboard.Key.f8, keyboard.Key.f10):
        return
    if key in keys_held:
        return
    keys_held.add(key)
    with state_lock:
        if key == keyboard.Key.f8:
            if printing_active.is_set():
                return
            try:
                start_audio()
                printing_active.set()
                print("\nCONNECTED - Printing and sound activated")
            except Exception as error:
                disconnect()
                print(f"Could not start: {error}")
        else:
            disconnect()
            print("\nDISCONNECTED - Sound stopped; new printing paused")


def on_release(key):
    keys_held.discard(key)


listener = keyboard.Listener(on_press=on_press, on_release=on_release)
listener.start()

print("\nARCHIVE OF DESIRE")
print(f"Loaded {len(images)} advertisements")
print(f"Source: {SOURCE}")
print(f"Sound: {AUDIO_FILE}")
print("\nF8  = CONNECT / START PRINTING AND SOUND")
print("F10 = DISCONNECT / STOP SOUND AND NEW PRINTING")
print("Ctrl+C = CLOSE PROGRAM (in this terminal)")
print("Submitted print jobs may finish after disconnecting.")
print("\nSystem ready. Currently DISCONNECTED.")

try:
    while True:
        if not printing_active.wait(timeout=0.2):
            continue
        image_path = random.choice(images)
        try:
            image = prepare_image(image_path)
            if not printing_active.is_set():
                continue
            print_image(image, f"Archive of Desire - {image_path.stem}")
            printed_count += 1
            print(f"Sent: {image_path.name} | Total: {printed_count}")
        except Exception as error:
            disconnect()
            print(f"Printer error: {error}")
            print("Printing and sound paused.")
            continue
        deadline = time.monotonic() + PRINT_INTERVAL
        while printing_active.is_set():
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                break
            time.sleep(min(0.05, remaining))
except KeyboardInterrupt:
    print("\nClosing installation controller.")
finally:
    listener.stop()
    listener.join()
    disconnect()
