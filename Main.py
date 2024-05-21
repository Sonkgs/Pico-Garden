#TODO:
#1 Tornar o contador de ativações uma variável persistente
#2 Refatorar as funções de bibliotecas
#3 Padronizar os nomes das variáveis

from machine import Pin
from machine import I2C
from machine import ADC
import ssd1306
import utime
from utime import sleep

#====== INICIALIZAÇÃO DE VARIÁVEIS =======#
sleep_dia_seco = 86400-24 #86400 é um dia em segundos
sleep_dia_molhado = 86400-1
#====== CONFIGURAÇÃO DO MOTOR ====#
stepper_pins = [Pin(10, Pin.OUT), Pin(11, Pin.OUT), Pin(12, Pin.OUT), Pin(13, Pin.OUT)] #IN1 GPIO10, IN2 GPIO11, IN3 GPIO12, IN4 GPIO13

step_sequence = [
    [1, 0, 0, 1], # full steps tem dois 1s e dois 0s
#    [1, 0, 0, 0], # half steps tem um 1 e três 0s
    [1, 1, 0, 0],
#    [0, 1, 0, 0],
    [0, 1, 1, 0],
#    [0, 0, 1, 0],
    [0, 0, 1, 1],
#    [0, 0, 0, 1],
]
def girar(direction, steps, delay):
    global step_index
    for i in range(steps): #roda esse looping uma vez para cada "steps"
        step_index = (step_index + direction) % len(step_sequence) #fórmula interessante para fazer um looping dentro de um array sem usar for/while:
        #o step_index é sempre o resto da divisão pelo tamanho do array (tamanho = 4), então o resto da divisão sempre vai ser 0, 1, 2 ou 3
        #fazendo com que o step_index percorra os itens do array e, quando acabar, retorne ao primeiro e faça tudo de novo quantas vezes for preciso
        
        for pin_index in range(len(stepper_pins)): #roda 4 vezes sem delay, uma setando cada pino com 1 ou 0, e volta ao for anterior para avançar um passo
            pin_value = step_sequence[step_index][pin_index]
            stepper_pins[pin_index].value(pin_value)
        utime.sleep(delay)
#=== ZERAR OS PINOS DO MOTOR PARA POUPAR ENERGIA APÓS GIRAR ===#
    stepper_pins[0].value(0)
    stepper_pins[1].value(0)
    stepper_pins[2].value(0)
    stepper_pins[3].value(0)

#=== CONFIGURANDO OS PINOS DE COMUNICAÇÃO DO DISPLAY ===#
i2c = I2C(0, scl=Pin(1), sda=Pin(0))
oled = ssd1306.SSD1306_I2C(128, 64, i2c)

#======= CONFIGURANDO PINOS DO SENSOR DE UMIDADE =======#
digital_pin = Pin(15, Pin.IN) 
analog_pin = ADC(26)

#=========== RESETANDO/LIMPANDO O DISPLAY ==============#
oled.fill(0)
oled.show()
ativado = 0

#===== LENDO OS DADOS DO SENSOR
def read_soil():
    max_analog = 55535#
    inverted_analog = (max_analog - analog_pin.read_u16())/300 #
    return digital_pin.value(), inverted_analog

#==== ESCREVENDO E LENDO NO LOG AO DAR BOOT =====#
with open("log.txt", "r+") as log_file:
    try:
        contador = int(log_file.read())
    except: #se o contador estiver vazio, vai começar do zero
        contador = 0
    contador += 1
    log_file.seek(0)
    log_file.write(str(contador))
    log_file.flush() #O log não persiste sem esta função
    log_file.close()

#================ LOOPING PRINCIPAL =================#
while True:
    digital_value, analog_value = read_soil()
    if digital_value == 0:
        digital_str = 'Sim'
    else:
        digital_str = 'Nao'
    
    oled.text('Irrigado? {}'.format(digital_str), 0, 0) #o primeiro numero é a posição no eixo X(esquerda/direita), o segundo no Y(cima/baixo)
    oled.text('Nivel: {} %'.format(int(analog_value)), 0, 12)
    oled.text('Reboots: {}'.format(contador), 0, 24)
    oled.text('Vezes ativado: {}'.format(ativado), 0, 36)
    oled.show()
    
    if analog_value < 20:
        step_index = 0
        girar(1, 4096, 0.002) #0.002 é a valocidade máxima que esse motor de passo aguenta, acima disso ele não move
        utime.sleep(1) #precisa ser revisto para garantir que vai água o suficiente
        girar(-1, 4096, 0.002)
        utime.sleep(sleep_dia_seco)
        ativado += 1
        
    else:
        utime.sleep(sleep_dia_molhado)
    utime.sleep(1)
    oled.fill(0)
