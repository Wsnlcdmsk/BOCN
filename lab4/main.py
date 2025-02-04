import serial
import threading
import time
from tkinter import Tk, Label, Button, Entry, StringVar, Text, Scrollbar, END, messagebox, Frame, ttk
from packet_handler import string_by_packages, unpack_string_packages, corrupt_bit_with_probability
import random

packet_size = 26
channel_busy_probability = 0.5
collision_probability = 0.6
max_retries = 10
slot_time = 0.5
jam_signal = b"12345678900987654321=+98674"

def is_channel_busy():
    return random.random() < channel_busy_probability

def is_collision():
    return random.random() < collision_probability

def send_jam_signal(transmitter):
    global jam_signal
    transmitter.write(jam_signal)
    text_area.insert(END, "Передатчик: отправлен jam-сигнал\n")

def csma_cd_send(data, ser1):
    attempt = 0
    while attempt < max_retries:
        if is_channel_busy():
            R = random.randint(0, min(2 ** attempt - 1, 1023))
            delay = R * slot_time
            text_area.insert(END, f"Передатчик: ожидание {delay:.2f} секунд перед повторной попыткой...\n")
            time.sleep(delay)
            attempt += 1
            continue
        ser1.write(data)
        if is_collision():
            text_area.insert(END, "Передатчик: коллизия обнаружена!\n")
            send_jam_signal(ser1)
        break

    if attempt == max_retries:
        text_area.insert(END, "Передатчик: не удалось отправить данные после максимального количества попыток\n")

def send_data():
    message = string_by_packages(entry_message.get(), ser1.port[3])
    if message:
        try:
            sent_message = []
            for char in message:
                csma_cd_send(char, ser1)
                sent_message.append(char)
                time.sleep(0.1)
            update_state(len(sent_message))
            entry_message.set("")
        except serial.SerialException as e:
            messagebox.showerror("Ошибка отправки", f"Ошибка при отправке данных: {e}")

def highlight_debug_info():
    start = "1.0"
    while True:
        start = text_area.search(r'\\\\\#w', start, stopindex=END, regexp=True)
        if not start:
            break
        end = f"{start}+4c"
        text_area.tag_add("highlight", start, end)
        start = end

def read_data():
    global packet_size
    received_data = b''
    while True:
        try: 
            if ser2.in_waiting > 0:
                received_data += ser2.read_all()
            elif len(received_data) >= packet_size:
                print("vsfsag bfd")
                print(received_data[-27:0])
                if received_data[-27:] == jam_signal:
                    text_area.insert(END, "Пришел jam-signal\n")
                    received_data = b''
                    continue
                data_string = unpack_string_packages(received_data)
                received_data = corrupt_bit_with_probability(received_data)
                data_string = data_string.decode('utf-8')
                text_area.insert(END, f"Received (decoded): {received_data}\n")
                text_output.insert(END, f"{data_string}")
                received_data = b''
                text_output.see(END)
                text_area.see(END)
            time.sleep(0.01)
        except serial.SerialException as e:
            messagebox.showerror("Ошибка приёма", f"Ошибка при чтении данных: {e}")
            break

def update_state(bytes_sent):
    total_bytes = 0
    total_bytes += bytes_sent
    state_label.config(text=f"Скорость: {ser1.baudrate} бод, Передано байт: {total_bytes}")

def update_ports_direction(*args):
    selected_direction = direction_var.get()
    if selected_direction == "1 -> 2":
        send_var.set("COM1")
        receive_var.set("COM2")
    elif selected_direction == "5 <- 6":
        send_var.set("COM6")
        receive_var.set("COM5")


def start_program():
    global ser1, ser2
    send_port = send_var.get() if send_var.get() else "COM1"
    receive_port = receive_var.get() if receive_var.get() else "COM2"
    baudrate = int(baudrate_var.get())
    try:
        ser1 = serial.Serial(send_port, baudrate=baudrate, timeout=1)
        ser2 = serial.Serial(receive_port, baudrate=baudrate, timeout=1)

        threading.Thread(target=read_data, daemon=True).start()

        update_state(0)
    except serial.SerialException as e:
        messagebox.showerror("Ошибка порта", f"Не удалось открыть порт: {e}")

root = Tk()
root.title("COM-порты: Передача и приём данных")
root.geometry("600x750")
root.configure(bg="#1E1E1E")
root.resizable(False, False)

frame_top = Frame(root, bg="#3C3F41", relief="solid", bd=2)
frame_top.pack(pady=20, padx=10)

frame_middle = Frame(root, bg="#3C3F41", relief="solid", bd=2)
frame_middle.pack(pady=20, padx=10)

frame_bottom = Frame(root, bg="#3C3F41", relief="solid", bd=2)
frame_bottom.pack(pady=20, padx=10)

direction_var = StringVar(root)
direction_var.set("1 -> 2")
direction_var.trace("w", update_ports_direction)

Label(frame_top, text="Выберите направление передачи данных:", bg="#3C3F41", fg="white", font=("Arial", 12)).pack()
direction_menu = ttk.OptionMenu(frame_top, direction_var, "1 -> 2", "1 -> 2", "5 <- 6")
direction_menu.pack(pady=5)

send_var = StringVar(root, value="COM1")
receive_var = StringVar(root, value="COM2")

Label(frame_top, text="Порт для отправки данных:", bg="#3C3F41", fg="white", font=("Arial", 12)).pack()
send_label = Label(frame_top, textvariable=send_var, bg="#3C3F41", fg="white", font=("Arial", 10, "bold"))
send_label.pack()

Label(frame_top, text="Порт для получения данных:", bg="#3C3F41", fg="white", font=("Arial", 12)).pack()
receive_label = Label(frame_top, textvariable=receive_var, bg="#3C3F41", fg="white", font=("Arial", 10, "bold"))
receive_label.pack()

Label(frame_top, text="Выберите скорость передачи данных (бод):", bg="#3C3F41", fg="white", font=("Arial", 12)).pack(pady=5)
baudrate_var = StringVar(root)
baudrate_var.set("9600")
baudrate_menu = ttk.OptionMenu(frame_top, baudrate_var, "9600", "9600", "19200", "38400", "57600", "115200")
baudrate_menu.pack()

start_button = Button(frame_top, text="Запустить", command=start_program, bg="#76C7C0", fg="black", font=("Arial", 10, "bold"), padx=10, pady=5)
start_button.pack(pady=10)

Label(frame_middle, text="Введите сообщение для отправки:", bg="#3C3F41", fg="white", font=("Arial", 12)).pack()
entry_message = StringVar()
message_entry = Entry(frame_middle, textvariable=entry_message, width=50, font=("Arial", 10))
message_entry.pack(pady=5)

send_button = Button(frame_middle, text="Отправить", command=send_data, bg="#FFD700", fg="black", font=("Arial", 10, "bold"), padx=10, pady=5)
send_button.pack(pady=10)

Label(frame_bottom, text="Принятые данные:", bg="#3C3F41", fg="white", font=("Arial", 12)).pack()
text_output = Text(frame_bottom, height=5, width=60, bg="#282A36", fg="white", insertbackground='white', font=("Courier", 10))
text_output.pack(pady=5)

state_label = Label(frame_bottom, text="Скорость: неизвестно, Передано байт: 0", bg="#3C3F41", fg="white", font=("Arial", 10))
state_label.pack()

Label(frame_bottom, text="Отладочная информация:", bg="#3C3F41", fg="white", font=("Arial", 12)).pack(pady=5)
text_area = Text(frame_bottom, height=10, width=60, bg="#282A36", fg="white", insertbackground='white', font=("Courier", 10))
scrollbar = Scrollbar(frame_bottom)
scrollbar.pack(side="right", fill="y")
text_area.pack(side="left", fill="both")
text_area.config(yscrollcommand=scrollbar.set)
scrollbar.config(command=text_area.yview)

text_area.tag_config("highlight", background="yellow", foreground="red")

root.mainloop()

if 'ser1' in globals() and ser1.is_open:
    ser1.close()
if 'ser2' in globals() and ser2.is_open:
    ser2.close()
