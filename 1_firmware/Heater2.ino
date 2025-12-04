#include <Wire.h>
#include <Adafruit_MAX31865.h>
#include "hardware/pwm.h"

// I2C Konstante
#define I2C_ADDRESS 0x16  
#define CMD_SET 0x01     
#define CMD_GET_TEMP 0x02 // Neuer Befehl für Temperaturabfrage
#define RESP_TEMP 0x12  
// Neue I2C-Befehle für PWM
#define CMD_GET_PWM 0x03  // Befehl zum Abrufen des PWM-Werts
#define RESP_PWM 0x15     // ID de respuesta para PWM
// Variable global de la última orden recibida
uint8_t lastRequestCmd = 0;

// Definiere SPI-Pins für den MAX31865-Sensor
#define CS_SENSOR1 17  

// PWM für Heizstab
#define HEATER_PWM_PIN 14

// RTD-Parameter
#define RREF 430.0
#define RNOMINAL 100.0

// Initialisierung der Sensoren
Adafruit_MAX31865 sensor1 = Adafruit_MAX31865(CS_SENSOR1);


// Variablen
uint8_t heater_power = 0;
float temp_heater2_out = 0.0;

// PWM Steuerung für den Heizstab
void setPWM(int pin, int value) {
    gpio_set_function(pin, GPIO_FUNC_PWM);
    uint slice_num = pwm_gpio_to_slice_num(pin);
    pwm_set_wrap(slice_num, 225);
    pwm_set_gpio_level(pin, value);
    pwm_set_enabled(slice_num, true);
}

void setup() {
  // Inicialización de la comunicación serial (I2C)
    Wire.begin(I2C_ADDRESS);
    Wire.onReceive(receiveEvent);
    Wire.onRequest(requestEvent);

    //delay(1000);
    //Serial.begin(115200);
    //Serial.println("Test: Código 0x11 corre!"); 
    //Serial.println("I2C periferico iniciado correctamente");

    // inicialiszar MAX31865 
    sensor1.begin(MAX31865_3WIRE);
        
    // inicializar PWM para calentador
    pinMode(HEATER_PWM_PIN, OUTPUT);
    setPWM(HEATER_PWM_PIN, 0);
}

void loop() {
    static unsigned long lastRead = 0;
    if (millis() - lastRead >= 1000) {
        lastRead = millis();
        temp_heater2_out = sensor1.temperature(RNOMINAL, RREF);    

        // Debug-Ausgabe SPÄTER LÖSCHEN
        //Serial.print("Temp_heater2_out: ");
        //Serial.print(temp_heater2_out);
        //Serial.println(" °C");
    }
}


// I2C recibido (del master)
void receiveEvent(int bytes_msg) {
    if (bytes_msg < 4) return;
    
    uint8_t reg = Wire.read();
    uint8_t id  = Wire.read();
    uint8_t cmd = Wire.read();
    uint8_t len = Wire.read();

    lastRequestCmd = cmd;  // Speichert den letzten empfangenen Befehl

    if (cmd == CMD_SET && len == 1) {
        heater_power = Wire.read();
        heater_power = constrain(heater_power, 0, 100);
        setPWM(HEATER_PWM_PIN, map(heater_power, 0, 100, 0, 255));
        //Serial.print("Heizung PWM: ");
        //Serial.println(heater_power);
    }
}

void requestEvent() {
    if (lastRequestCmd == CMD_GET_PWM) {
        uint8_t response_pwm[4] = {1, RESP_PWM, 1, heater_power};  // respuesta con valor PWM
        Wire.write(response_pwm, 4);
        //Serial.print("PWM enviado: ");
        //Serial.println(heater_power);
    } else if (lastRequestCmd == CMD_GET_TEMP) {
    uint16_t temp_heater2_out_scaled = static_cast<uint16_t>(temp_heater2_out * 100);

    uint8_t response[5] = {1, RESP_TEMP, 2, 
                        (uint8_t)(temp_heater2_out_scaled & 0xFF), 
                        (uint8_t)((temp_heater2_out_scaled >> 8) & 0xFF)};

  
                        
    //Serial.print("Response: [");
    //for (int i = 0; i < 5; i++) {
        //Serial.print(response[i]);
        //if (i < 4) Serial.print(", ");
    //}
    //Serial.println("]");
                    
    Wire.write(response, 5);

    //Serial.print("temperatura enviada: ");
    //Serial.print(temp_heater2_out);
    //Serial.print(" °C, ");
    //Serial.println(temp_heater2_out);
    //Serial.print(" °C, ");
    
    }
}
