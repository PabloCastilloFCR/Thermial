#include <Wire.h>                  // Librería para la comunicación I2C
#include "hardware/pwm.h"          // RP2040 PWM Library

#define I2C_ADDRESS 0x10           // Dirección I2C del dispositivo periferico
#define CMD_SET 0x01               // Comando para establecer un valor
#define CMD_GET 0x02               // Comando para solicitar un valor
#define RESP_FLOW 0x13             // Código de respuesta para el valor del flujo

#define PUMP_PWM_PIN 23            // Pin PWM para la bomba
const int sensorPin = 14;          // Pin del flujómetro

volatile int pulseCount = 0;
float flowRate = 0.0;
unsigned long lastMeasurement = 0;

uint8_t value = 0;
int pump_power = 0;

//Inicializar el  PWM solo una vez en setup() en vez de en cada función:
uint slice_num;

void countPulse() {
    pulseCount++;
}

void setPWM(int pin, int value) {
    gpio_set_function(pin, GPIO_FUNC_PWM);
    uint slice = pwm_gpio_to_slice_num(pin);
    pwm_set_wrap(slice, 255);
    pwm_set_gpio_level(pin, value);
    pwm_set_enabled(slice, true);
}

void setup() {
    Wire.begin(I2C_ADDRESS);
    Wire.onReceive(receiveEvent);
    Wire.onRequest(requestEvent);

    pinMode(sensorPin, INPUT_PULLUP);
    attachInterrupt(digitalPinToInterrupt(sensorPin), countPulse, FALLING);

    pinMode(PUMP_PWM_PIN, OUTPUT);
    setPWM(PUMP_PWM_PIN, 0); // bomba inicia en 0 %
}

void loop() {
    unsigned long currentMillis = millis();
    if (currentMillis - lastMeasurement >= 1000) {
        noInterrupts();
        int pulses = pulseCount;
        pulseCount = 0;
        interrupts();

        flowRate = (float)pulses / 7.5;
        lastMeasurement = currentMillis;
    }
}

void set_PumpPWM(int value){
    int pwmValue = map(value, 0, 100, 0, 255);
    setPWM(PUMP_PWM_PIN, pwmValue);
}

uint16_t get_flowData(){ 
    // Sicherstellen, dass der Rückgabewert nie negativ oder ungültig ist
    if(flowRate < 0) return 0;
    return (uint16_t)(flowRate * 100);
}

void receiveEvent(int bytes_msg) {
    if (bytes_msg < 4) return;

    uint8_t reg = Wire.read();
    uint8_t id  = Wire.read();
    uint8_t cmd = Wire.read();
    uint8_t len = Wire.read();

    if (cmd == CMD_SET && len == 1 && Wire.available()) {
        value = Wire.read();
        pump_power = constrain(value, 0, 100);
        set_PumpPWM(pump_power);
        // Kein direktes Aufrufen von requestEvent()
    }
    // CMD_GET: Master ruft automatisch requestEvent() auf
}

void requestEvent() {
    uint16_t flowData = get_flowData();

    uint8_t response[5] = {0};
    response[0] = 1;
    response[1] = RESP_FLOW;
    response[2] = 2;
    response[3] = static_cast<uint8_t>(flowData & 0xFF);
    response[4] = static_cast<uint8_t>(flowData >> 8);

    Wire.write(response, 5);       // Antwort senden
    // Minimales Delay nur, falls nötig, z.B. 50 µs
    delayMicroseconds(50);
}