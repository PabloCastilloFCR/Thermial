#include <Wire.h>                  // Librería para la comunicación I2C
#include "hardware/pwm.h"          // RP2040 PWM Library

// Definiciones de constantes y direcciones de comando
#define I2C_ADDRESS 0x14           // Dirección I2C del dispositivo periferico
#define CMD_SET 0x01               // Comando para establecer un valor
#define CMD_GET 0x02               // Comando para solicitar un valor
#define RESP_FLOW 0x13             // Código de respuesta para el valor del flujo

#define PUMP_PWM_PIN 23            // Pin PWM para la bomba
const int sensorPin = 14;          // Pin del flujómetro


// Flow-Sensor Setup
volatile int pulseCount = 0;
float flowRate = 0.0;
unsigned long lastMeasurement = 0;

uint8_t value = 0;                  // Variable para guardar el valor recibido a través del comando SET
int pump_power = 0;                // Variable de potencia de la bomba

//Inicializar el  PWM solo una vez en setup() en vez de en cada función:
uint slice_num;

// Interrupt-Service-Routine (ISR) - cuenta impulsos
void countPulse() {
    pulseCount++;
    
}

// PWM Steuerung für die Pumpe
void setPWM(int pin, int value) {
    gpio_set_function(pin, GPIO_FUNC_PWM);  // Configurar pin como PWM
    uint slice = pwm_gpio_to_slice_num(pin); // Obtener el canal PWM
    pwm_set_wrap(slice, 255); // PWM de 8 bits (0-255)
    pwm_set_gpio_level(pin, value); // Configurar valor PWM
    pwm_set_enabled(slice, true); // activar PWM
    //Serial.print("Valor PWM ajustado: ");
    //Serial.println(value); // Mensaje para confirmar el ajuste PWM
}

void setup() {
    // Inicialización de la comunicación serial (I2C)
    Wire.begin(I2C_ADDRESS); // Inicialización del periferico I2C con la dirección definida
    Wire.onReceive(receiveEvent); // Función que se llamará cuando lleguen datos desde el maestro
    Wire.onRequest(requestEvent); // Función que se llamará cuando el maestro solicite datos
    
    //delay(1000);
    //Serial.begin(115200);
    //Serial.println("Test: Código 0x14 corre!");    
    //Serial.println("I2C periferico iniciado correctamente.");

    // Configuración del sensor de flujo
    pinMode(sensorPin, INPUT_PULLUP);
    attachInterrupt(digitalPinToInterrupt(sensorPin), countPulse, FALLING); //wenn die Kurve fällt, wird ein Signal gesendet

    // Configuración PWM para la bomba, inicializa el control de la bomba
    pinMode(PUMP_PWM_PIN, OUTPUT);
    setPWM(PUMP_PWM_PIN, 0); // Bomba inicia con 0%//
}

void loop() {
    //Serial.println("Loop corre:...");
    unsigned long currentMillis = millis();
    if (currentMillis - lastMeasurement >= 1000) {
        noInterrupts();
        int pulses = pulseCount;
        pulseCount = 0;
        interrupts();

        // Conversión: 7.5 impulsos = 1 L/min
        flowRate = (float)pulses / 7.5;
        lastMeasurement = currentMillis;
    }
}

// Función para establecer (set) un valor y reflejarlo en el PWM, aquí la potencia de la bomba
void set_PumpPWM(int value){
    // Enviar pulso PWM usando el valor como duty cycle
    // Se convierte el rango (0-100) a (0-127) para configurar la salida PWM
    int pwmValue = map(value, 0, 100, 0, 255); // bomba se controla con PWM, rango de 0 a 255 para poder trabajar en potencia completa, la entrada de 0-100 se traduzca a rango completo de PWM de 8 bits 0 (apagado)-255(potencia completa)
    //analogWrite(pwmPin, pwmValue);  // analogWrite() no está disponible directamente en la Raspberry Pi Pico
    setPWM(PUMP_PWM_PIN, pwmValue); // Llamada a la función setPWM para aplicar el valor de PWM en el pin
    //Serial.print("PWM de la bomba ajustado a: ");
    //Serial.println(pwmValue);
}

// Función para obtener el valor del flujo
uint16_t get_flowData(){ 
    // Sicherstellen, dass der Rückgabewert nie negativ oder ungültig ist
    if(flowRate < 0) return 0;
    return (uint16_t)(flowRate * 100);
}

// Función de recepción de datos I2C, se llama cuando el maestro envía datos al periferico
void receiveEvent(int bytes_msg) {
    if (bytes_msg < 4) return;
    // Se leen los primeros 4 bytes (reg, id, cmd, len)
    uint8_t reg = Wire.read();
    uint8_t id  = Wire.read();
    uint8_t cmd = Wire.read();
    uint8_t len = Wire.read();
    
    if (cmd == CMD_SET && len == 1 && Wire.available()) {
        value = Wire.read();
        pump_power = constrain(value, 0, 100);
        set_PumpPWM(pump_power);
     //else if (cmd == CMD_GET && len == 0) {
        //requestEvent();
    }
}



// Función de respuesta a solicitudes I2C
void requestEvent() {
    uint16_t flowData = static_cast<uint16_t>(get_flowData());  // datos de flujo (flowRate * 100)

    uint8_t response[5] = {0};         // Máximo de 16 bytes (inicializar Array para respuesta)
    response[0] = 1;                  // ID de respuesta
    response[1] = RESP_FLOW;          // Respuesta del flow
    response[2] = 2;                  // Longitud de datos (bytes)
    response[3] = static_cast<uint8_t>(flowData & 0xFF);      // byte bajo
    response[4] = static_cast<uint8_t>(flowData >> 8);        // byte alto
 
    Wire.write(response, 5);          // Enviar respuesta (ID, CMD, LEN y DATA) sobre I2C
    delayMicroseconds(50);
    //Debugging para el serial monitor
    //Serial.print("Flujo enviado: ");
    //Serial.println(flowRate);

    //Debugging de la respuesta enviada
    //Serial.print("Respuesta enviada al maestro: ");
    //for (int i = 0; i < 5; i++) {
        //Serial.print(response[i], HEX);
        //Serial.print(" ");
    //}
    //Serial.println();
}