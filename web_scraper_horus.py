from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException
import dotenv
import os
import time
import telebot
from datetime import datetime

#Obtener datos de archivo .env
dotenv.load_dotenv(dotenv.find_dotenv())
URL = os.environ.get("URL")
BINARY_LOCATION = os.environ.get("BINARY_LOCATION")
USER = os.environ.get("USER")
PASSWORD = os.environ.get("PASSWORD")
BOT_TOKEN = os.environ.get('BOT_TOKEN')
KIA_USER_ID = os.environ.get('KIA_USER_ID')
ART_USER_ID = os.environ.get('ART_USER_ID')

#Bot de Telegram para enviar mensajes
bot = telebot.TeleBot(BOT_TOKEN)

#Chrome Options configuraciones
chrome_options = Options()
chrome_options.binary_location = BINARY_LOCATION
chrome_options.add_experimental_option("detach", True)
driver = webdriver.Chrome(options = chrome_options)
driver.get(URL)

#Encontrar elementos input
input_user = WebDriverWait(driver, 30).until(
    EC.presence_of_element_located((By.XPATH, '//input[@name="user"]'))
)
input_pass = driver.find_element(By.XPATH, '//input[@name="password"]')

#Ingresar usuario y contraseña
input_user.send_keys(USER)
input_pass.send_keys(PASSWORD)

#Clickear en Log in
boton_login = driver.find_element(By.XPATH, '//button[@class="css-1wkrg9j-button"]')
boton_login.click()

#Clickear en "Temperatura pasillos"
boton_pasillos = WebDriverWait(driver, 30).until(
    EC.presence_of_element_located((By.PARTIAL_LINK_TEXT, "Temperatura pasillos"))
)
boton_pasillos.click()

#Obtener temperatura de forma periódica cada 15 seg.
start_time = time.time()
wait_duration = 5
loop_duration = 15
acum_NAs = 0
acum_altas_temps = 0
alta_temp_limite = 28
message = ""
limite_intentos = 20

while True:

    #Obtener temperatura Pasillo 1
    try:
        elemento_temp_pasillo_uno = WebDriverWait(driver, wait_duration).until(
            EC.presence_of_element_located((
                By.XPATH, '//div[@data-panelid="2"]//section[@class="panel-container"]//div[@class="panel-content panel-content--no-padding"]//div//div//div//div//div//div//span'
            ))
        )
        temp_pasillo_uno = elemento_temp_pasillo_uno.text
    except TimeoutException as ex:
        print("Error al obtener elemento de Temp. Pasillo 1")
        temp_pasillo_uno = "N/A"

    #Obtener temperatura Pasillo 2
    try:
        elemento_temp_pasillo_dos = WebDriverWait(driver, wait_duration).until(
            EC.presence_of_element_located((
                By.XPATH, '//div[@data-panelid="18"]//section[@class="panel-container"]//div[@class="panel-content panel-content--no-padding"]//div//div//div//div//div//div//span'
            ))
        )
        temp_pasillo_dos = elemento_temp_pasillo_dos.text
    except TimeoutException as ex:
        print("Error al obtener elemento de Temp. Pasillo 2")
        temp_pasillo_dos = "N/A"

    #Comprobar valor N/A
    if temp_pasillo_uno == "N/A" and temp_pasillo_dos == "N/A":
        acum_NAs += 1
    else:
        acum_NAs = 0
    
    #Comprobar altas temps.
    try:
        if float(temp_pasillo_uno) >= alta_temp_limite or float(temp_pasillo_dos) >= alta_temp_limite:
            acum_altas_temps += 1
        else:
            acum_altas_temps = 0
    except ValueError:
        pass

    if acum_NAs >= limite_intentos or acum_altas_temps >= limite_intentos:
        #En caso de que acum_NAs llegue a 20
        if acum_NAs >= limite_intentos:
            message = "Han pasado 5 minutos sin recibir la temperatura, REVISAR ESTADO DE LA SALA!"
        
        #En caso de que acum_altas_temps llegue a 20
        if acum_altas_temps >= limite_intentos:
            message = f"La temperatura del pasillo 2 de la sala acaba de llegar a los {temp_pasillo_dos} grados celcius, REVISAR VENTILADORES!"

        print(message)
        bot.send_message(KIA_USER_ID, message)
        bot.send_message(ART_USER_ID, message)
        break

    #Imprimir resultados cada 15 segundos
    current_time = datetime.now().strftime("%H:%M:%S")
    print(f"[{current_time}] - Temp. Pasillo 1: {temp_pasillo_uno}")
    print(f"[{current_time}] - Temp. Pasillo 2: {temp_pasillo_dos}")
    time.sleep(loop_duration - ((time.time() - start_time) % loop_duration))
