#include <Wire.h>
#include <Adafruit_MAX31865.h>
#include "hardware/pwm.h"

// constantes I2C 
#define I2C_ADDRESS     0x15  // dirección i2c
#define CMD_SET         0x01
#define CMD_GET_TEMP    0x02
#define RESP_TEMP       0x12
#define CMD_GET_PWM     0x03
#define RESP_PWM        0x15

// guardar último orden
uint8_t lastRequestCmd = 0;

// SPI-Pins para sensores MAX31865
#define CS_SENSOR5 17  // antes del ventilador
#define CS_SENSOR6 21  // después del ventilador

// PWM-Pin para el ventilador
#define FAN_PWM_PIN 15

// RTD-values para PT100
#define RREF 430.0
#define RNOMINAL 100.0

// Inicialización del los Adafruit sensores
Adafruit_MAX31865 sensor5 = Adafruit_MAX31865(CS_SENSOR5);
Adafruit_MAX31865 sensor6 = Adafruit_MAX31865(CS_SENSOR6);

// variables globales
uint8_t fan_speed = 0;
float temp_radiator1_in = 0.0, temp_radiator1_out = 0.0;

// set PWM
void setPWM(int pin, int value) {
    gpio_set_function(pin, GPIO_FUNC_PWM);
    uint slice_num = pwm_gpio_to_slice_num(pin);
    pwm_set_wrap(slice_num, 255);
    pwm_set_gpio_level(pin, value);
    pwm_set_enabled(slice_num, true);

    //Serial.print("PWM set a: ");
    //Serial.println(value);
}

void setup() {
    Wire.begin(I2C_ADDRESS);
    Wire.onReceive(receiveEvent);
    Wire.onRequest(requestEvent);

    //delay(1000);
    //Serial.begin(115200);
    //Serial.println("Test: Código 0x15 corre!");
    //Serial.println("I2C periferico iniciado correctamente.");

    // inicializar Sensores
    sensor5.begin(MAX31865_3WIRE);
    sensor6.begin(MAX31865_3WIRE);

    // inicializar PWM
    pinMode(FAN_PWM_PIN, OUTPUT);
    setPWM(FAN_PWM_PIN, 0);  // Ventilador apagado
}

void loop() {
    static unsigned long lastRead = 0;
    if (millis() - lastRead >= 1000) {
        lastRead = millis();
        temp_radiator1_in = sensor5.temperature(RNOMINAL, RREF);
        temp_radiator1_out = sensor6.temperature(RNOMINAL, RREF);
    }
}

// I2C recibido (del master)
void receiveEvent(int bytes_msg) {
    if (bytes_msg < 4) return;

    uint8_t reg = Wire.read();
    uint8_t id  = Wire.read();
    uint8_t cmd = Wire.read();
    uint8_t len = Wire.read();

    lastRequestCmd = cmd;  // Merken, um im nächsten requestEvent reagieren zu können

    if (cmd == CMD_SET && len == 1) {
        fan_speed = Wire.read();
        fan_speed = constrain(fan_speed, 0, 100);
        setPWM(FAN_PWM_PIN, map(fan_speed, 0, 100, 0, 255));
        //Serial.print("Ventilator velocidad [%]: ");
        //Serial.println(fan_speed);
    }
}


void requestEvent() {
    if (lastRequestCmd == CMD_GET_PWM) {
        uint8_t response_pwm[4] = {1, RESP_PWM, 1, fan_speed};
        Wire.write(response_pwm, 4);
        //Serial.print("PWM enviado: ");
        //Serial.println(fan_speed);
    } else if (lastRequestCmd == CMD_GET_TEMP) {
        uint16_t temp_radiator1_in_scaled = static_cast<uint16_t>(temp_radiator1_in * 100);
        uint16_t temp_radiator1_out_scaled = static_cast<uint16_t>(temp_radiator1_out * 100);

        uint8_t response[8] = {1, RESP_TEMP, 4,
                               (uint8_t)(temp_radiator1_in_scaled & 0xFF),
                               (uint8_t)((temp_radiator1_in_scaled >> 8) & 0xFF),
                               (uint8_t)(temp_radiator1_out_scaled & 0xFF),
                               (uint8_t)((temp_radiator1_out_scaled >> 8) & 0xFF)};

        //Serial.print("Response: [");
        //for (int i = 0; i < 8; i++) {
            //Serial.print(response[i]);
            //if (i < 7) Serial.print(", ");
        //}
        //Serial.println("]");

        Wire.write(response, 8);

        //Serial.print("temperaturas enviadas: ");
        //Serial.print(temp_radiator1_in);
        //Serial.print(" °C, ");
        //Serial.print(temp_radiator1_out);
        //Serial.println(" °C");
    }
}
