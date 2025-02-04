import serial
import threading
import time
from tkinter import Tk, Label, Button, Entry, StringVar, Text, Scrollbar, END, OptionMenu, messagebox, Frame

# Функция для выбора направления
def update_ports_direction(*args):
    selected_direction = direction_var.get()
    if selected_direction == "1 -> 2":
        send_var.set("COM1")
        receive_var.set("COM2")
    elif selected_direction == "5 <- 6":
        send_var.set("COM6")
        receive_var.set("COM5")

# Функция для посимвольной отправки данных
def send_data():
    message = entry_message.get()
    if message:
        try:
            sent_message = ""  # Создаем строку для отправленных данных
            for char in message:  # Посимвольная передача
                ser1.write(char.encode('utf-8'))  # Преобразование символа в байты
                sent_message += char  # Добавляем символ в строку
                time.sleep(0.1)  # Задержка между символами
            update_state(len(sent_message))  # Обновляем количество переданных байт
            ser1.write('\n'.encode('utf-8'))  # Отправляем символ новой строки
            entry_message.set("")  # Очищаем поле ввода
        except serial.SerialException as e:
            messagebox.showerror("Ошибка отправки", f"Ошибка при отправке данных: {e}")

# Функция для чтения данных
def read_data():
    while True:
        try:
            if ser2.in_waiting > 0:
                received_data = ser2.read(1)  # Чтение по одному символу
                try:
                    decoded_char = received_data.decode('utf-8')
                    text_output.insert(END, decoded_char)  # Добавляем символ к строке
                except UnicodeDecodeError:
                    hex_data = received_data.hex()
                    text_output.insert(END, f"[не декодировано: 0x{hex_data}]")  # Обработка недекодируемых данных
                text_output.see(END)  # Прокрутка вниз
            time.sleep(0.1)
        except serial.SerialException as e:
            messagebox.showerror("Ошибка приёма", f"Ошибка при чтении данных: {e}")
            break

# Функция для обновления состояния (количество переданных байт и скорость порта)
def update_state(bytes_sent):
    global total_bytes
    total_bytes += bytes_sent
    state_label.config(text=f"Скорость: {ser1.baudrate} бод, Передано байт: {total_bytes}")

# Функция для запуска программы
def start_program():
    global ser1, ser2, total_bytes
    total_bytes = 0

    send_port = send_var.get()
    receive_port = receive_var.get()
    baudrate = int(baudrate_var.get())  # Получаем выбранную скорость из переменной

    try:
        ser1 = serial.Serial(send_port, baudrate=baudrate, timeout=1)
        ser2 = serial.Serial(receive_port, baudrate=baudrate, timeout=1)

        # Запуск потока для чтения данных
        threading.Thread(target=read_data, daemon=True).start()

        # Обновление окна состояния
        update_state(0)
    except serial.SerialException as e:
        messagebox.showerror("Ошибка порта", f"Не удалось открыть порт: {e}")

# Создаем главное окно
root = Tk()
root.title("COM-порты: Передача и приём данных")
root.geometry("600x700")  # Увеличим размер окна для размещения дополнительных элементов
root.configure(bg="#2E2E2E")  # Цвет фона
root.resizable(False, False)  # Отключим возможность изменения размера

# Создаем рамки для разделения интерфейса
frame_top = Frame(root, bg="#2E2E2E")
frame_top.pack(pady=10)

frame_middle = Frame(root, bg="#2E2E2E")
frame_middle.pack(pady=10)

frame_bottom = Frame(root, bg="#2E2E2E")
frame_bottom.pack(pady=10)

# Направление передачи данных
direction_var = StringVar(root)
direction_var.set("1 -> 2")  # Значение по умолчанию
direction_var.trace("w", update_ports_direction)  # Обновляем порты при изменении направления

Label(frame_top, text="Выберите направление передачи данных:", bg="#2E2E2E", fg="white").pack()
direction_menu = OptionMenu(frame_top, direction_var, "1 -> 2", "5 <- 6")
direction_menu.pack()

# Выпадающие списки для отображения выбранных портов
send_var = StringVar(root)
receive_var = StringVar(root)
Label(frame_top, text="Порт для отправки данных:", bg="#2E2E2E", fg="white").pack()
send_label = Label(frame_top, textvariable=send_var, bg="#2E2E2E", fg="white")
send_label.pack()

Label(frame_top, text="Порт для получения данных:", bg="#2E2E2E", fg="white").pack()
receive_label = Label(frame_top, textvariable=receive_var, bg="#2E2E2E", fg="white")
receive_label.pack()

# Добавляем выбор скорости (baud rate)
Label(frame_top, text="Выберите скорость передачи данных (бод):", bg="#2E2E2E", fg="white").pack(pady=5)
baudrate_var = StringVar(root)
baudrate_var.set("9600")  # Значение по умолчанию
baudrate_menu = OptionMenu(frame_top, baudrate_var, "9600", "19200", "38400", "57600", "115200")
baudrate_menu.pack()

# Кнопка для запуска программы
start_button = Button(frame_top, text="Запустить", command=start_program, bg="#4CAF50", fg="white", padx=10, pady=5)
start_button.pack(pady=10)

# Окно ввода для передачи данных
Label(frame_middle, text="Введите сообщение для отправки:", bg="#2E2E2E", fg="white").pack()
entry_message = StringVar()
message_entry = Entry(frame_middle, textvariable=entry_message, width=50)
message_entry.pack(pady=5)

send_button = Button(frame_middle, text="Отправить", command=send_data, bg="#2196F3", fg="white", padx=10, pady=5)
send_button.pack(pady=10)

# Окно вывода для отображения принятых данных
Label(frame_bottom, text="Принятые данные:", bg="#2E2E2E", fg="white").pack()
text_output = Text(frame_bottom, height=10, width=60, bg="#424242", fg="white", insertbackground='white')
text_output.pack(pady=5)  # Добавим отступ для улучшения видимости

# Окно состояния
state_label = Label(frame_bottom, text="Скорость: неизвестно, Передано байт: 0", bg="#2E2E2E", fg="white")
state_label.pack()

# Окно для вывода отладочной информации
Label(frame_bottom, text="Отладочная информация:", bg="#2E2E2E", fg="white").pack()
text_area = Text(frame_bottom, height=5, width=60, bg="#424242", fg="white", insertbackground='white')
scrollbar = Scrollbar(frame_bottom)
scrollbar.pack(side="right", fill="y")
text_area.pack(side="left", fill="both")
text_area.config(yscrollcommand=scrollbar.set)
scrollbar.config(command=text_area.yview)

# Запуск главного цикла программы
root.mainloop()

# Закрытие портов при выходе
if 'ser1' in globals() and ser1.is_open:
    ser1.close()
if 'ser2' in globals() and ser2.is_open:
    ser2.close()