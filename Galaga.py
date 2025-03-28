from machine import Pin, I2C, PWM, ADC
import ssd1306
import neopixel
import time
import random

# ----------------------- CLASES DEL JUEGO -----------------------
puntaje = 0

class Nave:
    def __init__(self):
        self.x = 64
        self.y = 56
        self.vidas = 3

    def mover(self, valor_x):
        if valor_x > 3000 and self.x < 120:
            self.x -= 1
        elif valor_x < 600 and self.x > 0:
            self.x += 1

    def perder_vida(self):
        global puntaje
        self.vidas -= 1
        puntaje -= 10  # Restar 10 puntos si la nave pierde una vida
        sonido_perder_vida()

    def reset(self):
        self.vidas = 3
        self.x = 64

    def verificar_colision(self, objetos):
        return any(ox <= self.x <= ox + 8 and oy <= self.y <= oy + 8 for ox, oy in objetos)


class Enemigo:
    def __init__(self):
        self.x = random.randint(10, 110)
        self.y = random.randint(5, 30)
        self.velocidad = random.uniform(0.5, 1.2)
        self.direccion = random.choice([-1, 1])
        self.tiempo_disparo = random.randint(50, 100)

    def mover(self):
        self.x += self.direccion * self.velocidad
        if self.x <= 2 or self.x >= 118:
            self.direccion *= -1
            self.y += 3
        self.tiempo_disparo = max(0, self.tiempo_disparo - 1)

    def disparar(self):
        if self.tiempo_disparo == 0:
            self.tiempo_disparo = random.randint(50, 100)
            return True
        return False


class Pantalla:
    def __init__(self, oled):
        self.oled = oled

    def mostrar_texto(self, texto, x, y):
        self.oled.fill(0)
        self.oled.text(texto, x, y)
        self.oled.show()

    def dibujar_juego(self, nave, balas, enemigos, disparos_enemigos):
        self.oled.fill(0)  # Limpiar la pantalla
        self.oled.text(f"Puntos: {puntaje}", 5, 0)  # Mostrar puntaje en la esquina superior izquierda
        self.oled.text(f"Nivel: {nivel}", 5, 10)  # Mostrar nivel debajo del puntaje

        self.oled.rect(int(nave.x), int(nave.y), 6, 6, 1)  # Dibujar la nave

        for x, y in balas:
            self.oled.pixel(int(x), int(y), 1)  # Dibujar balas
        for enemigo in enemigos:
            self.oled.rect(int(enemigo.x), int(enemigo.y), 8, 8, 1)  # Dibujar enemigos
        for x, y in disparos_enemigos:
            self.oled.pixel(int(x), int(y), 1)  # Dibujar disparos enemigos

        self.oled.show()  # Actualizar la pantalla

# ----------------------- FUNCIONES DE SONIDO -----------------------

def reproducir_tono(frecuencia, duracion):
    buzzer.freq(frecuencia)
    buzzer.duty(512)  # 50% de duty cycle
    time.sleep(duracion)
    buzzer.duty(0)

def sonido_gameover():
    """ Reproduce un sonido de Game Over. """
    for _ in range(3):
        reproducir_tono(200, 0.3)
        time.sleep(0.1)

def sonido_perder_vida():
    """ Reproduce un sonido cuando la nave pierde una vida. """
    reproducir_tono(500, 0.1)
    reproducir_tono(300, 0.1)

def sonido_impacto_enemigo():
    """ Reproduce un sonido cuando un enemigo es impactado. """
    reproducir_tono(800, 0.1)
    reproducir_tono(600, 0.1)

def sonido_disparo():
    """ Reproduce un sonido de disparo. """
    reproducir_tono(1000, 0.05)

def melodía_juego():
    """ Reproduce una melodía de fondo durante el juego. """
    notas = [262, 294, 330, 349, 392, 440, 494, 523]  # Notas de la escala
    for nota in notas:
        reproducir_tono(nota, 0.1)
        time.sleep(0.05)

# ----------------------- CONFIGURACIÓN DE HARDWARE -----------------------

i2c = I2C(0, scl=Pin(33), sda=Pin(32))
oled = ssd1306.SSD1306_I2C(128, 64, i2c)
buzzer = PWM(Pin(2), freq=1000, duty=0)

joystick_x = ADC(Pin(34))
joystick_x.atten(ADC.ATTN_11DB)
button_fire = Pin(14, Pin.IN, Pin.PULL_UP)
button_pause = Pin(12, Pin.IN, Pin.PULL_UP)
button_reset = Pin(25, Pin.IN, Pin.PULL_UP)

NUM_PIXELS = 3
neopixels = neopixel.NeoPixel(Pin(15, Pin.OUT), NUM_PIXELS)

nave = Nave()
pantalla = Pantalla(oled)

enemigos = []
balas = []
disparos_enemigos = []

jugando = False
pausado = False
nivel = 1

# ----------------------- FUNCIONES DEL JUEGO -----------------------

def actualizar_vidas():
    for i in range(NUM_PIXELS):
        neopixels[i] = (0, 255, 0) if i < nave.vidas else (255, 0, 0)
    neopixels.write()

def pantalla_inicio():
    pantalla.mostrar_texto("SPACE SHOOTER", 20, 20)
    while button_fire.value():  # Esperar a que se presione el botón de disparo
        time.sleep(0.1)

def juego():
    global jugando, pausado, enemigos, balas, disparos_enemigos, puntaje, nivel
    
    pantalla_inicio()
    jugando = True
    pausado = False
    nave.reset()
    puntaje = 0  # Reiniciar puntaje
    nivel = 1  # Reiniciar nivel
    actualizar_vidas()
    enemigos = [Enemigo() for _ in range(5)]
    balas.clear()
    disparos_enemigos.clear()
    puede_disparar = True
    
    melodía_juego()  # Iniciar melodía de fondo

    while jugando:
        if button_fire.value() == 0 and puede_disparar:
            balas.append([nave.x + 3, nave.y])
            sonido_disparo()
            puede_disparar = False
        if button_fire.value() == 1:
            puede_disparar = True

        if button_pause.value() == 0:
            pausado = not pausado
            time.sleep(0.3)
            if pausado:
                pantalla.mostrar_texto("PAUSA", 50, 30)
                while button_pause.value():
                    time.sleep(0.1)

        if button_reset.value() == 0:
            return  # Reiniciar el juego

        if not pausado:
            actualizar()
            pantalla.dibujar_juego(nave, balas, enemigos, disparos_enemigos)

        time.sleep(0.03)

def actualizar():
    global jugando, nivel, puntaje  # Asegúrate de incluir puntaje aquí

    nave.mover(joystick_x.read())

    # Mover balas y verificar colisión con enemigos
    nuevas_balas = []
    enemigos_a_eliminar = []  # Lista para almacenar enemigos a eliminar

    for x, y in balas:
        y -= 2  # Mover bala hacia arriba

        # Verificar colisión con enemigos
        impacto = False
        for enemigo in enemigos:
            if (enemigo.x <= x <= enemigo.x + 8) and (enemigo.y <= y <= enemigo.y + 8):
                enemigos_a_eliminar.append(enemigo)  # Marcar enemigo para eliminar
                sonido_impacto_enemigo()  # Reproducir sonido de impacto
                puntaje += 5  # Sumar 5 puntos por enemigo destruido
                print(f"Puntaje: {puntaje}")  # Imprimir el puntaje para depuración
                impacto = True
                break  # Salimos del bucle, ya que la bala impactó

        if not impacto and y > 0:  # Solo agregar la bala si no impactó y está en pantalla
            nuevas_balas.append((x, y))

    # Eliminar enemigos que fueron impactados
    for enemigo in enemigos_a_eliminar:
        if enemigo in enemigos:  # Verificar que el enemigo esté en la lista antes de eliminar
            enemigos.remove(enemigo)

    balas[:] = nuevas_balas

        # Mover enemigos y agregar disparos enemigos
    for enemigo in enemigos:
        enemigo.mover()
        if enemigo.disparar():
            disparos_enemigos.append([enemigo.x + 3, enemigo.y + 5])

    # Mover disparos enemigos
    nuevos_disparos = []
    for x, y in disparos_enemigos:
        y += 2  # Disparo se mueve hacia abajo
        if y < 64:
            nuevos_disparos.append([x, y])

    disparos_enemigos[:] = nuevos_disparos

    # Verificar colisión de disparos enemigos con la nave
    for disparo in disparos_enemigos[:]:  # Iterar sobre una copia de la lista
        x, y = disparo
        if (nave.x <= x <= nave.x + 6) and (nave.y <= y <= nave.y + 6):
            nave.perder_vida()
            sonido_perder_vida()  # Reproducir sonido de perder vida
            actualizar_vidas()
            disparos_enemigos.remove(disparo)  # Se elimina el disparo que impactó

        if nave.vidas <= 0:
            sonido_gameover()
            oled.fill(0)  
            oled.text("GAME OVER", 20, 10)  
            oled.text(f"Puntaje: {puntaje}", 20, 30)  
            oled.text(f"Nivel: {nivel}", 20, 50)
            oled.show()  
            time.sleep(4)
            pantalla_inicio()
            puntaje = 0
            nivel = 1
                
        if nivel == 10:
            sonido_gameover()
            oled.fill(0)  
            oled.text("Good Game", 20, 10)  
            oled.text(f"Puntaje: {puntaje}", 20, 30)  
            oled.text(f"Nivel: {nivel}", 20, 50)
            oled.show()  
            time.sleep(4)
            pantalla_inicio()
            nivel = 1

    # Si no hay más enemigos, subir de nivel
    if not enemigos:
        nivel += 1
        enemigos.extend([Enemigo() for _ in range(5)])
        for enemigo in enemigos:
            enemigo.velocidad += (nivel * 0.8)
            enemigo.tiempo_disparo = max(1, enemigo.tiempo_disparo - (nivel * 10))
            
    

# Iniciar el juego
juego()