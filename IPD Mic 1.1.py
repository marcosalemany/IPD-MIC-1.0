import pyaudio
import audioop
import sounddevice as sd
import queue
import sys, os

from threading import Thread
import time
import tkinter as tk
from tkinter import ttk
from tkinter import *
from tkinter import messagebox
import ttkbootstrap as tb
from ttkbootstrap import Style
from ttkbootstrap.constants import *

import numpy as np
import math

import cv2
from PIL import Image, ImageTk

import cvzone
from cvzone.FaceMeshModule import FaceMeshDetector

# Variable para registrar eventos del Botón 1
registro_eventos_boton1 = []
registro_eventos_boton2 = []
registro_eventos_boton3 = []
# Mensajes iniciales de los botones 1 y 2
initial_message1 = "OFFSET DISTANCIA CALCULADO"
initial_message2 = "COORDENADAS DESCRITAS"

# Mensajes alternativos de los botones 1 y 2
alternate_message1 = "COLOCATE A 50 CM MIRANDO A LA LENTE"
alternate_message2 = "COLOCA EL MICRO EN LA IMAGEN, CUANDO TERMINES VUELVE A PULSAR EL BOTÓN"

# Estado de los interruptores (inicialmente apagados)
switch_state1 = False
switch_state2 = False
switch_state3 = False
# Coordenadas registradas por el boton 2 (boton micro)
clicked_coordinates = [0, 0]
# Cuadro de información
info_label = None
offsetmicro = 0
dBIn = -90
dBOut = -90
rmsOut=1
rmsIn=1
volume = 0
fuente_seleccionada = 0
distmicrocara = 0
# Detección de caras
detector = FaceMeshDetector(maxFaces=1)
Dist = 0  # La inicializo porque a veces da problemas
CorreccionDistancia = 0
Dreal = 50
faces = 0
# Función que se ejecuta cuando se hace clic en el botón de información del botón 1
def on_info_button_hover(event):
    global info_label
    destroy_info_label()
    show_info_label(
        "Botón cámara: una vez pulsado colócate a 50cm de la lente y vuelve a pulsar el botón para el ajuste")

def on_info_button1_hover(event, nombre):
    global info_label
    destroy_info_label()
    if nombre == 'boton1':
        show_info_label(
            "Botón cámara: una vez pulsado colócate a 50cm de la lente y vuelve a pulsar el botón para el ajuste")
    elif nombre == 'boton2':
        show_info_label("Coloca las coordenadas de la posición del micro en la pantalla")
    elif nombre == 'boton3':
        show_info_label("Selecciona el Offset del Micro.  (+10cm = Micro 10cm más próximo al usuario que la lente)")
    elif nombre == 'boton4':
        show_info_label("Corrige sutílmente el cambio indeseado de distancia por giro de la cara")
    elif nombre == 'boton5':
        show_info_label("Ajusta a cúantos dB debe actuar la puerta de ruido (Rango: [-90,0])")
    elif nombre == 'boton6':
        show_info_label("Selecciona tu entrada de Audio")
    elif nombre == 'boton7':
        show_info_label("Selecciona VB-Cable Input (Normalmente el C)")
    elif nombre=='boton9':
        show_info_label("Contribución del campo reverberado en el decaimiento por la distancia. 1 = Campo abierto --> 7 = Catedral")

# Función que se ejecuta cuando se hace clic en el botón 1
def on_button1_click():
    global switch_state1, switch_state2, registro_eventos_boton1, Dreal
    count = 0
    # Apagar el Botón 2 si está encendido
    if switch_state2:
        switch_state2 = False
        show_text_overlay(initial_message2)
        button2.config(bootstyle="primary, toolbutton")  # Cambiar el color del botón cuando está apagado

    switch_state1 = not switch_state1

    if switch_state1 or switch_state2:
        estado = activar_desactivar_bypass2(root)
        if estado == "ON":
            bypass_button2.invoke()
            #bypass_button.invoke()
        activar_desactivar_bypass2(root) == False
        bypass_button2.config(state='disabled')
        #bypass_button.config(state='disabled')
        button2.config(state='disabled')
        estado="OFF"
        Dreal = 50 - valorspinbox(offsetmicro)
        registro_eventos_boton1.append(f"Distancia a corregir: {Dreal}")
        show_text_overlay(alternate_message1)
        # Desvincular el evento de clic en la ventana de video
        video_label.unbind("<Button-1>")
        calibrar_dboton.config(bootstyle="warning-outline, toolbutton")  # Cambiar el color del botón a rojo cuando está apagado
        #

        #root.activar_desactivar_bypass2=True
    else:
        Dreal = round(Dist)
        registro_eventos_boton1.append(f"Distancia recalculada: {Dreal}")
        show_text_overlay(initial_message1)
        calibrar_dboton.config(bootstyle="info-outline, toolbutton")  # Cambiar el color del botón a rojo cuando está apagado
        # Volver a vincular el evento de clic en la ventana de video
        # video_label.bind("<Button-1>", on_video_click)
        # Actualizar la etiqueta con los eventos del Botón 1
        update_event_label()
        bypass_button2.config(state='enabled')
        #bypass_button.config(state='enabled')
        button2.config(state='enabled')
        estado = activar_desactivar_bypass2(root)
        bypass_button2.invoke()

        if estado == "OFF":
            activar_desactivar_bypass2(root)
            #bypass_button.invoke()

    return Dreal
def on_buttonreset_click():
    offsetmicro.set(0)
    puertaruido.set(-90)
    factorajuste.set(3)
    event_label.config(text="Distancia recalculada: ")
    event_label2.config(text="Coordenadas micrófono: ")
    global clicked_coordinates
    clicked_coordinates = (0, 0)
    if root.bypass:
        root.bypass == False
        switch_state1 = False
        bypass_button.invoke()

    if root.bypass3:
        root.bypass3 == False
        switch_state3 = False
        bypass_button3.invoke()

def update_event_label():
    if registro_eventos_boton1:
        last_event = registro_eventos_boton1[-1]
        event_label.config(text=last_event)
    else:
        event_label.config(text="")

# Función que se ejecuta cuando se hace clic en el botón posicion micro
def on_button2_click():
    global switch_state2, clicked_coordinates, switch_state1, registro_eventos_boton2
    # Apagar el Botón 1 si está encendido
    if switch_state1:
        switch_state1 = not switch_state1
        switch_state2 = False
        show_text_overlay(initial_message1)
        calibrar_dboton.config(bootstyle="primary, toolbutton")  # Cambiar el color del botón cuando está apagado

    switch_state2 = not switch_state2

    if switch_state2:
        show_text_overlay(alternate_message2)
        button2.config(bootstyle="warning-outline, toolbutton")  # Cambiar el color del botón  cuando está encendido
        video_label.bind("<Button-1>", on_video_click)
        bypass_button2.config(state='disabled')
        #bypass_button.config(state='disabled')
        calibrar_dboton.config(state='disabled')
    else:
        registro_eventos_boton2.append(f"Coordenadas micrófono: {clicked_coordinates}")
        show_text_overlay(initial_message2)
        button2.config(bootstyle="info-outline, toolbutton")  # Cambiar el color del botón a negro cuando está apagado
        bypass_button2.config(state='enabled')
        #bypass_button.config(state='enabled')
        calibrar_dboton.config(state='enabled')
        video_label.unbind("<Button-1>")
        update_event_label2()
        switch_state2 = False

def update_event_label2():
    if registro_eventos_boton2:
        last_event = registro_eventos_boton2[-1]
        event_label2.config(text=last_event)

def on_video_click(event):
    global clicked_coordinates
    # Obtener las coordenadas del clic en la ventana de video
    x, y = event.x, event.y
    clicked_coordinates = (x, y)
    show_text_overlay(f"Coordenadas registradas: {clicked_coordinates}")

# Función para mostrar una etiqueta de información en la posición del ratón
# BOTONES INFO
def show_info_label(message):
    global info_label
    x, y = root.winfo_pointerxy()
    x -= root.winfo_rootx()  # Ajustar según la posición de la ventana principal
    y -= root.winfo_rooty()  # Ajustar según la posición de la ventana principal
    info_label = tk.Label(root, text=message, font=("Helvetica", 8), background='white', relief='solid',
                          justify='right')
    ancho = len(message) * 5
    info_label.place(x=x - ancho, y=y)

def on_info_button1_leave(event):
    destroy_info_label()

# Función para destruir la etiqueta de información
def destroy_info_label():
    global info_label
    if info_label:
        info_label.destroy()
        info_label = None

# Función para mostrar un mensaje de texto sobre el video
def show_text_overlay(message):
    text_overlay.config(text=message)
    text_overlay.place(relx=0.5, rely=0.5, anchor='center')
    root.after(4000,
               lambda: text_overlay.place_forget())  # Ocultar el mensaje después de 4000 milisegundos (2 segundos)

def Distancia(slider, clicked_coordinates, root):
    global Dist, Dreal
    if faces:
        # la cara detectada es la cara 0
        face = faces[0]
        # puntos del ojo izquierdo,derecho y boca
        pointLeft = face[145]
        pointRight = face[374]
        mouth = face[0]
        # calculo aristas del triángulo
        # linea entre los ojos
        if root.bypass2:
            cv2.line(frame, pointLeft, pointRight, (150, 150, 150), 3)
            # los dibujo color=bgr
            cv2.circle(frame, pointLeft, 5, (182, 0, 124), cv2.FILLED)
            cv2.circle(frame, pointRight, 5, (182, 0, 124), cv2.FILLED)
            cv2.circle(frame, mouth, 5, (182, 0, 124), cv2.FILLED)
        # distancia entre ojos en píxeles
        w, _ = detector.findDistance(pointLeft, pointRight)
        bl, _ = detector.findDistance(pointLeft, mouth)
        br, _ = detector.findDistance(pointRight, mouth)
        correctorangulo = 1

        if root.bypass3:
            if bl == max(bl, br, w):
                direccion = 'derecha'
                correctorangulo = br * w / bl ** 2
            elif br == max(bl, br, w):
                direccion = 'izquierda'
                correctorangulo = bl * w / br ** 2
            else:
                direccion = 'centro'
            # distancia entre ojos cm
        W = 6.34
        # distancia al objetivo cm
        CorreccionDistancia = Dreal - 50
        d = 50 - CorreccionDistancia

        # foco calculado
        f = (w * d) / W
        # evaluo valores a 50cm para mi cámara
        # focal obtenida a 50cm (valor experimental)
        F = 420
        # distancia 'real
        Distog = (W * F) / w
        # correctorangulo=math.sqrt(math.sqrt(correctorangulo))
        correctorangulo = correctorangulo ** (1. / 3.)
        Dist1 = (Distog - CorreccionDistancia) * correctorangulo
        Dist = Dist1 - valorspinbox(offsetmicro)

        # escribo la distancia en centimetros en la posición de la frente
        if root.bypass2:
            cvzone.putTextRect(frame, f'Distancia: {int(Dist1)}cm', (face[10][0] - 125, face[10][1] - 50), scale=2,
                               colorR=(0, 300 - int(1.2 * Dist1), int(Dist1 * 2)))

        if clicked_coordinates[0] != 0 and clicked_coordinates[1] != 0 and Dist1 > 0:

            distx = clicked_coordinates[0] - mouth[0]
            disty = clicked_coordinates[1] - mouth[1]
            distmicrocara = int((distx ** 2 + disty ** 2) ** 0.5) * 0.01
            # distmicrocara = int(abs(modulocara-modulomicro)*0.02)
            distmicrocara = int(distmicrocara * 100 / (Dist))
            if root.bypass2:
                cv2.line(frame, mouth, clicked_coordinates, (150, 150, 150), 3)
                cv2.circle(frame, clicked_coordinates, 5, (182, 0, 124), cv2.FILLED)
        else:
            distmicrocara = 0
        valorajuste=valorspinbox(factorajuste)
        factorVolumen = (2*(int(Dist + distmicrocara-50)/valorajuste)+100)
        #print(factorVolumen)
        if root.bypass and Dist1 > 0:
            slider.set(factorVolumen)
    return Dist, faces

# Función principal para procesar el video en tiempo real
def show_video():
    global faces, frame
    sucess, frame = cap.read()
    if root.bypass2:
        frame, faces = detector.findFaceMesh(frame, draw=True)
    else:
        frame, faces = detector.findFaceMesh(frame, draw=False)
    Distancia(root.slider, clicked_coordinates, root)
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    photo = ImageTk.PhotoImage(image=Image.fromarray(frame))
    video_label.config(image=photo)
    video_label.image = photo
    video_label.after(10, show_video)  # Actualizar cada 10 milisegundos
    # lee la fuente de video
    # draw=false no mostramos los puntos de la detección

# código buga
def obtener_fuentes_disponibles():
    # Obtener el número total de dispositivos de captura disponibles
    num_dispositivos = 0
    fuentes_disponibles = []
    # Intentar abrir cada fuente de video hasta que no haya más disponible
    while True:
        cap = cv2.VideoCapture(num_dispositivos)
        if not cap.isOpened():
            break
        _, _ = cap.read()  # Intenta leer un frame
        fuentes_disponibles.append(f'Fuente {num_dispositivos}')
        cap.release()
        num_dispositivos += 1

    return fuentes_disponibles

def obtener_dispositivos_entrada():
    p = pyaudio.PyAudio()
    num_dispositivos = p.get_device_count()
    dispositivos = []
    for i in range(num_dispositivos):
        dispositivo = p.get_device_info_by_index(i)
        if dispositivo.get('maxInputChannels') > 0:
            dispositivos.append((i, dispositivo.get('name')))
    return dispositivos

def obtener_dispositivos_salida():
    p = pyaudio.PyAudio()
    num_dispositivos = p.get_device_count()
    dispositivos = []
    for i in range(num_dispositivos):
        dispositivo = p.get_device_info_by_index(i)
        if dispositivo.get('maxOutputChannels') > 0:
            dispositivos.append((i, dispositivo.get('name')))
    return dispositivos

def extraer_numero(input_string):
    patron = re.compile(r'^(\d+):')
    coincidencia = patron.match(input_string)
    return int(coincidencia.group(1)) if coincidencia else None

def procesar_rmsIn(rmsIn_queue, rmsOut_queue, contadorsilencio_queue):
    dBOut = -90

    while True:
        try:
            rmsIn = rmsIn_queue.get(timeout=1)  # Espera hasta que haya un elemento en la cola
            rmsOut = rmsOut_queue.get(timeout=1)
            contadorsilencio = contadorsilencio_queue.get(timeout=1)
            # Realiza aquí las operaciones con rmsIn
            # print(f"Procesando rmsIn: {rmsIn}")
            if rmsIn > 0:
                dBIn = (20 * math.log10(rmsIn)) - 90
                #print(dBIn)
                sound_barIn["value"] = int(100 + dBIn)
                sound_labelIn.config(text=f"Input: {int(dBIn)} dBFS")
                if sound_barIn["value"] < 80:
                    sound_barIn.config(bootstyle='success')
                elif sound_barIn["value"] >= 80 and sound_barOut["value"] <= 90:
                    sound_barIn.config(bootstyle='warning')
                elif sound_barIn["value"] > 90:
                    sound_barIn.config(bootstyle='danger')

            if rmsOut > 0:
                dBOut = (20 * math.log10(rmsOut)) - 90

            if contadorsilencio > 15:
                sound_barOut["value"] = 100 + valorspinbox(puertaruido)
                sound_barOut.config(bootstyle='dark')
                sound_labelOut.config(text=f" Output: -90 dBFS")
            else:
                sound_barOut["value"] = int(100 + dBOut)
                sound_labelOut.config(text=f" Output: {int(dBOut)} dBFS")
                if sound_barOut["value"] < 80:
                    sound_barOut.config(bootstyle='success')
                elif sound_barOut["value"] >= 80 and sound_barOut["value"] <= 90:
                    sound_barOut.config(bootstyle='warning')
                elif sound_barOut["value"] > 90:
                    sound_barOut.config(bootstyle='danger')


        except queue.Empty:
            # La cola está vacía; salir del bucle si se desea
            sound_barOut["value"] = 0
            sound_barIn["value"] = 0
            break

def iniciar_stream(root, dispositivo_entrada_var, dispositivo_salida_var, rmsIn_queue, rmsOut_queue,
                   contadorsilencio_queue):
    dBOutlog=-90
    start_time = time.time()
    contadorsilencio = 0
    global rmsIn, rmsOut, dBIn, dBOut
    p = pyaudio.PyAudio()
    indiceEntrada = dispositivo_entrada_var.get()
    indiceSalida = dispositivo_salida_var.get()
    if indiceEntrada != "Entrada de audio" and indiceSalida != "salida de audio":  # condicional para que no de error si no se ha seleccionado entrada o salida
        dispositivo_entrada = int(extraer_numero(indiceEntrada))
        dispositivo_salida = int(extraer_numero(indiceSalida))
        CHUNK = 1024
        frecuencia_muestreo = 44100
        formato_audio = pyaudio.paInt16
        canales = 1

        stream_entrada = p.open(format=formato_audio,
                                channels=canales,
                                rate=frecuencia_muestreo,
                                input=True,
                                frames_per_buffer=CHUNK,
                                input_device_index=dispositivo_entrada)

        stream_salida = p.open(format=formato_audio,
                               channels=canales,
                               rate=frecuencia_muestreo,
                               output=True,
                               frames_per_buffer=CHUNK,
                               output_device_index=dispositivo_salida)
        #print("Iniciando la transmisión de audio...")
        try:
            while root.streaming:
                # Captura el audio del micrófono
                datos_entrada = stream_entrada.read(CHUNK)
                array_entrada = np.frombuffer(datos_entrada, dtype=np.int16)
                array_salida = np.array(0, dtype=np.int16)
                dBthreshold = valorspinbox(puertaruido)  # Un valor típico de umbral
                rmsIn = audioop.rms(datos_entrada, 2)
                rmsIn_queue.put(rmsIn)

                if rmsIn > 0:
                    dBIn = (20 * math.log10(rmsIn)) - 90
                    array_salida = (array_entrada * root.factor_default).astype(np.int16)

                    if dBIn < dBthreshold:
                        contadorsilencio += 1
                    else:
                        contadorsilencio = 0
                    if contadorsilencio > 15:
                        array_salida = array_entrada * 0
                    else:
                        array_salida = (array_entrada * root.factor_default).astype(np.int16)
                contadorsilencio_queue.put(contadorsilencio)
                stream_salida.write(array_salida.tobytes())
                datos_salida = array_salida.tobytes()
                rmsOut = audioop.rms(datos_salida, 2)
                if rmsOut>0:
                    dBOutlog = (20 * math.log10(rmsOut)) - 90
                rmsOut_queue.put(rmsOut)
                elapsed_time = int((time.time() - start_time) * 1000)

                file.write(f"{elapsed_time},{round(Dist)}, {round(rmsIn,2)},{round(dBIn,2)},{round(rmsOut,2)}, {round(dBOutlog,2)}\n")
                file.flush()
        except KeyboardInterrupt:
            print("Deteniendo la transmisión de audio...")

        finally:
            # Cierra los flujos de audio
            stream_entrada.stop_stream()
            stream_entrada.close()
            stream_salida.stop_stream()
            stream_salida.close()
            p.terminate()
            file.close()
    else:

        pass

def iniciar_parar_stream(root, dispositivo_entrada_var, dispositivo_salida_var):
    global file
    indiceEntrada = dispositivo_entrada_var.get()
    indiceSalida = dispositivo_salida_var.get()
    if indiceEntrada != "Entrada de audio" and indiceSalida != "Salida de audio":  # condicional para que no de error si no se ha seleccionado entrada o salida

        if not hasattr(root, 'stream_thread') or not root.stream_thread.is_alive():
            file = open("registro_variables.txt", "w")
            file.write("Tiempo, Distancia, rmsIn, dBIn, rmsOut, dBOut\n")
            root.streaming = True
            rmsIn_queue = queue.Queue()
            rmsOut_queue = queue.Queue()
            contadorsilencio_queue = queue.Queue()
            root.stream_thread = Thread(target=iniciar_stream, args=(
            root, dispositivo_entrada_var, dispositivo_salida_var, rmsIn_queue, rmsOut_queue, contadorsilencio_queue))
            root.stream_thread.start()
            root.procesar_thread = Thread(target=procesar_rmsIn,
                                          args=(rmsIn_queue, rmsOut_queue, contadorsilencio_queue))
            root.procesar_thread.start()
            root.start_button.config(text="Detener Stream")
            root.start_button.config(bootstyle='warning, toolbutton')

        else:
            root.streaming = False
            root.start_button.config(text="Iniciar Stream")
            root.start_button.config(bootstyle='primary, toolbutton')
            sound_barIn['value']=0
            sound_labelIn.config(text="Input:          dBFS")
            sound_barOut['value']=0
            sound_labelOut.config(text="Output:          dBFS")


    else:
        if indiceEntrada != "Entrada de audio" and indiceSalida != "Salida de audio":  # condicional para que no de error si no se ha seleccionado entrada o salida
            root.start_button.config(bootstyle='success, toolbutton')
        else:
            root.start_button.config(bootstyle='danger, toolbutton')

def actualizar_valor(valor, root):
    if root.slider.get() > 0:
        root.factor_default = int(float(valor)) / 100
        valor_log = 20 * math.log10(float(root.slider.get()) / 100.0)
        label_valor.config(text=f"Ganancia: {valor_log:.2f} dB ")

def habilitar_toolbutton(*args):
    if dispositivo_entrada_var.get() != "Entrada de audio" and dispositivo_salida_var.get() != "Salida de audio":
        root.start_button.config(state='enabled')

def activar_desactivar_bypass(root):
    root.bypass = not root.bypass

    if root.bypass:
        estado = "Manual"

        root.slider.config(bootstyle='success')
    else:
        estado = "Automático"
        root.slider.config(bootstyle='primary')
    root.slider.set(100)
    return estado

def activar_desactivar_bypass2(root):
    root.bypass2 = not root.bypass2
    estado2 = "OFF" if root.bypass2 else "ON"
    return estado2

def activar_desactivar_bypass3(root):
    root.bypass3 = not root.bypass3
    estado3 = "OFF" if root.bypass3 else "ON"
    return estado3

# SELECCIÓN DE FUENTE DE VIDEO
def actualizar_variable(event):
    global cap
    # Obtén el valor seleccionado en el ComboBox y actualiza la variable
    #print(combo.get())
    seleccion = re.findall(r'\d+', combo.get())
    seleccion = int(seleccion[0])
    #print(seleccion)
    # Actualiza la variable que se utiliza en la línea de código
    cap.release()
    cap = cv2.VideoCapture(seleccion)
    #print(type(seleccion))
def valorspinbox(input):
    valor = input.get()
    # offset = offsetmicro.get()
    if valor.lstrip('-').isdigit() == False:
        # if offset=='' or offset=='-':
        valor = 0
    else:
        valor = int(input.get())

    return valor
def on_closing():

    if root.streaming == True:
        # messagebox.askokcancel("Ok", "Detén la salida de audio primero","Aceptar")
        messagebox.showinfo("Ok", "Detén la salida de audio primero")
    else:
        if messagebox.askokcancel("IPD Mic Exit", "¿Estás seguro de que quieres salir?"):
            root.quit()
            # root.destroy()

    # root.destroy()
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

if __name__ == "__main__":

    root = tb.Window()
    root.title("IPD Mic")

    icon = Image.open(resource_path("icono\icon-1.png"))
    photo = ImageTk.PhotoImage(icon)
    root.iconphoto(True, photo)
    root.photo = photo

    cap = cv2.VideoCapture(0)
    style = Style(theme='custommm')
    dispositivo_entrada_var = tk.StringVar(value="Entrada de audio")
    dispositivo_salida_var = tk.StringVar(value="Salida de audio")
    CHUNK = 1024
    dispositivos_entrada = obtener_dispositivos_entrada()
    dispositivos_salida = obtener_dispositivos_salida()
    root.streaming = False
    root.factor_default = 1
    root.stream_thread = Thread()  # Inicializamos el hilo vacío
    root.bypass = False  # Inicialmente, el bypass está desactivado
    root.bypass2 = False
    root.bypass3 = False
    message = ""
    my_style = tb.Style()
    my_style.configure('primary.TButton, toolbutton.TButton', font=('Helvetica', 12))

    # FRAME GENERAL
    frame = tk.Frame(root)
    frame.pack(padx=10, pady=10, side="top", anchor="nw")

    # VIDEO
    video_label = tb.Label(frame)
    video_label.grid(row=0, column=0, sticky='NW')

    # FUENTE DE VIDEO
    # Crear un desplegable para las fuentes de video
    # Lista de opciones para el ComboBox
    opciones = obtener_fuentes_disponibles()
    # Crear el ComboBox de ttk
    combo = tb.Combobox(frame, text="Fuente de video:", values=opciones, textvariable=actualizar_variable,
                        state="readonly", width=30)
    combo.grid(row=0, column=0, sticky='NW')
    combo.bind("<<ComboboxSelected>>", actualizar_variable)
    combo.set('Video Input')

    # Caja Combobox
    combo_frame = tb.Frame(frame)
    combo_frame.grid(row=0, column=0, padx=(645, 0), pady=(420, 0), sticky='NW')
    # DESPLEGABLE BOTÓN DE ENTRADA
    combo_entrada = tb.Combobox(combo_frame, textvariable=dispositivo_entrada_var, bootstyle='warning',
                                state="readonly", width=48)
    combo_entrada['values'] = [f"{idx}: {nombre}" for idx, nombre in dispositivos_entrada]
    combo_entrada.grid(row=0, column=0, padx=2, sticky='ne')
    combo_entrada.bind('<Button-1>', lambda event: combo_entrada.config(bootstyle='success'))
    combo_entrada.bind("<Enter>", lambda event: on_info_button1_hover(event,
                                                                      "boton6"))  # Mostrar información al pasar el ratón sobre el botón
    combo_entrada.bind("<Leave>", on_info_button1_leave)

    # DESPLEGABLE BOTÓN DE SALIDA
    combo_salida = tb.Combobox(combo_frame, textvariable=dispositivo_salida_var, bootstyle='warning', state="readonly",
                               width=48)
    combo_salida['values'] = [f"{idx}: {nombre}" for idx, nombre in dispositivos_salida]
    combo_salida.grid(row=1, column=0, padx=2, sticky='ne')
    combo_salida.bind('<Button-1>', lambda event: combo_salida.config(bootstyle='success'))
    combo_salida.bind("<Enter>", lambda event: on_info_button1_hover(event,
                                                                     "boton7"))  # Mostrar información al pasar el ratón sobre el botón
    combo_salida.bind("<Leave>", on_info_button1_leave)

    # TEXT OVERLAY VIDEO
    # Configurar una etiqueta para mostrar el texto sobre el video
    text_overlay = tk.Label(video_label, text="1", font=("Helvetica", 16))
    text_overlay.grid(row=0, column=0, columnspan=2)
    show_text_overlay("Que pasa tronco!\nSelecciona las fuentes de entrada y salida de audio")
    # Configurar una etiqueta para mostrar los eventos del Botón 1 sobre el video
    event_label = tb.Label(frame, text="Distancia recalculada:", font=("Helvetica", 12), justify="right")
    # event_label.grid(row=8, sticky='nw',pady=(50,0))
    event_label.place(y=585)
    event_label2 = tb.Label(frame, text="Coordenadas micrófono:", font=("Helvetica", 12), justify="right")
    # event_label2.grid(row=9, sticky='sw',pady=(0,0))
    event_label2.place(y=605)

    # CAJA BOTONES
    buttons_frame = tb.Frame(frame)
    buttons_frame.grid(row=0, column=0, padx=(650, 0), sticky='NW')
    # BOTONES CONFIGURACIÓN
    # BOTON CALIBRAR DISTANCIA
    calibrar_dboton = tb.Button(buttons_frame, bootstyle="primary, toolbutton", text="CALIBRAR DISTANCIA", width=30,
                                command=on_button1_click)  # Inicialmente gris (apagado)
    calibrar_dboton.grid(row=0, column=0, padx=10, pady=10)
    calibrar_dboton.bind("<Enter>", lambda event: on_info_button1_hover(event,
                                                                "boton1"))  # Mostrar información al pasar el ratón sobre el botón
    calibrar_dboton.bind("<Leave>", on_info_button1_leave)

    # BOTON POSICION MICRO
    button2 = tb.Button(buttons_frame, bootstyle="primary, toolbutton", width=30, text="POSICIÓN MICROFONO",
                        command=on_button2_click)  # Inicialmente rojo (apagado)
    button2.grid(row=1, column=0, padx=10, pady=10)
    button2.bind("<Enter>", lambda event: on_info_button1_hover(event,
                                                                "boton2"))  # Mostrar información al pasar el ratón sobre el botón
    button2.bind("<Leave>", on_info_button1_leave)
    # Input Offset Micro
    tb.Label(buttons_frame, text="OFFSET MICRO (cm)").grid(row=0, column=1, sticky='W', padx=(0, 80))
    offsetmicro = tb.Spinbox(buttons_frame, bootstyle='success', text="", from_=-50, to=50, width=5)
    offsetmicro.grid(row=0, column=1, sticky='NE', padx=10, pady=10)
    offsetmicro.set(0)
    offsetmicro.bind("<Enter>", lambda event: on_info_button1_hover(event,
                                                                    "boton3"))  # Mostrar información al pasar el ratón sobre el botón
    offsetmicro.bind("<Leave>", on_info_button1_leave)

    # Input Noise gate
    tb.Label(buttons_frame, text="PUERTA DE RUIDO (dB)").grid(row=1, column=1, sticky='W', padx=(0, 80))
    puertaruido = tb.Spinbox(buttons_frame, bootstyle='success', text="", from_=-90, to=0, width=5)
    puertaruido.grid(row=1, column=1, sticky='NE', padx=10, pady=10)
    puertaruido.set(-90)
    puertaruido.bind("<Enter>", lambda event: on_info_button1_hover(event,
                                                                    "boton5"))  # Mostrar información al pasar el ratón sobre el botón
    puertaruido.bind("<Leave>", on_info_button1_leave)

    tb.Label(buttons_frame, text="Factor de Ajuste").grid(row=2, column=1, sticky='W', padx=(0, 80))
    factorajuste = tb.Spinbox(buttons_frame, bootstyle='success', text="", from_=1, to=7, width=5)
    factorajuste.grid(row=2, column=1, sticky='NE', padx=10, pady=10)
    factorajuste.set(3)
    factorajuste.bind("<Enter>", lambda event: on_info_button1_hover(event,
                                                                    "boton9"))  # Mostrar información al pasar el ratón sobre el botón
    factorajuste.bind("<Leave>", on_info_button1_leave)

    # Caja Switches
    switches_frame = tb.Frame(frame)
    switches_frame.grid(row=0, column=0, padx=(750, 0), pady=(200, 0), sticky='Ne')

    # Botón para activar/desactivar Interfaz IA
    tb.Label(buttons_frame, text="INTERFAZ IA").grid(row=3, column=0, sticky='ne', padx=(10, 40), pady=(10, 0))
    bypass_button2 = tb.Checkbutton(buttons_frame, bootstyle='success, round-toggle', text="",
                                    command=lambda: activar_desactivar_bypass2(root))
    bypass_button2.grid(row=3, column=0, sticky='NE', padx=10, pady=(10, 0))

    # Botón para activar/desactivar Corrección Ángulo
    #tb.Label(buttons_frame, text="CORRECCIÓN ÁNGULO").grid(row=3, column=1, sticky='ne', padx=(0, 40), pady=(10, 0))
    labelcorreccion = tk.Label(buttons_frame, text="corrección angulo", bg="yellow", fg="blue")
    labelcorreccion.grid(row=3, column=1, sticky='ne', padx=(0, 40), pady=(10, 0))
    bypass_button3 = tb.Checkbutton(buttons_frame, bootstyle='success, round-toggle', text="",
                                    command=lambda: activar_desactivar_bypass3(root))
    bypass_button3.grid(row=3, column=1, sticky='NE', padx=10, pady=(10, 0))
    bypass_button3.bind("<Enter>", lambda event: on_info_button1_hover(event,
                                                                       "boton4"))  # Mostrar información al pasar el ratón sobre el botón
    bypass_button3.bind("<Leave>", on_info_button1_leave)

    # Caja Automático
    auto_frame = tb.Frame(frame)
    auto_frame.grid(row=9, column=0, padx=(732, 0), pady=(0, 0), sticky='NW')
    # Botón para activar/desactivar el modo automático
    tb.Label(auto_frame, text="Ganancia Manual/Automática").grid(row=0, column=0, sticky='NE', padx=40, pady=0)
    bypass_button = tb.Checkbutton(auto_frame, bootstyle='success, round-toggle',
                                   command=lambda: activar_desactivar_bypass(root))
    bypass_button.grid(row=0, column=0, sticky='NE', padx=10, pady=0)

    # Barras de audio
    # INPUT
    style.configure("TProgressbar.Horizontal.TProgressbar", thickness=20)
    sound_barIn = tb.Progressbar(frame, orient="horizontal", length=960, mode="determinate")
    sound_barIn.grid(row=4, column=0, sticky='SW', pady=2)
    sound_labelIn = tb.Label(frame, text="Input          dBFS")
    sound_labelIn.grid(row=4, column=0, sticky='Se', padx=(660, 10))
    # OUTPUT
    sound_barOut = tb.Progressbar(frame, bootstyle='info', orient="horizontal", length=960, mode="determinate")
    sound_barOut.grid(row=6, column=0, sticky='NW', pady=2)
    sound_labelOut = tb.Label(frame, text="Output:          dBFS")
    sound_labelOut.grid(row=6, column=0, sticky='Se', padx=(660, 10))

    # SLIDER
    label_valor = tb.Label(frame, text="")
    label_valor.grid(row=9, column=0)
    root.slider = tb.Scale(frame, from_=0, to=400, orient='horizontal', bootstyle='primary',
                           command=lambda val: actualizar_valor(val, root), length=700)
    root.slider.grid(row=8, column=0, pady=10, sticky='sw', padx=(260, 0))
    root.slider.set(100)

    # BOTON RESET
    botonreset = tb.Button(frame, bootstyle="warning, toolbutton", text="RESET", width=30, command=on_buttonreset_click)
    botonreset.grid(row=8, column=0, padx=(0, 0), sticky='w')
    botonreset.bind("<Enter>", lambda event: on_info_button1_hover(event,
                                                                   "boton8"))  # Mostrar información al pasar el ratón sobre el botón
    botonreset.bind("<Leave>", on_info_button1_leave)

    # BOTÓN INICIAR STREAM
    root.start_button = tb.Button(frame, text="Iniciar Stream", bootstyle='primary, toolbutton', width=40,
                                  state='disabled', command=lambda: iniciar_parar_stream(root, dispositivo_entrada_var,
                                                                                         dispositivo_salida_var))
    root.start_button.grid(row=10, column=0, pady=(20, 0), sticky='n')
    # Asocia la función habilitar_toolbutton al cambio en los Combobox
    dispositivo_entrada_var.trace_add("write", habilitar_toolbutton)
    dispositivo_salida_var.trace_add("write", habilitar_toolbutton)
    show_video()
    root.geometry("1100x650")
    root.resizable(False, False)
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.iconbitmap(resource_path("icono\icono.ico"))
    root.mainloop()