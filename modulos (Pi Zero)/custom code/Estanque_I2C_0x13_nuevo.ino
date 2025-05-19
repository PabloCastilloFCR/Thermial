#include <Wire.h>
#include <Adafruit_MAX31865.h>

// I2C Konstante
#define I2C_ADDRESS 0x13  

//órdenes I2C
#define CMD_GET_TEMP 0x02
#define RESP_TEMP 0x12
#define RESP_LEVEL 0x14

// Definir SPI-Pins para sensopres MAX31865
#define CS_SENSOR1 17  
#define CS_SENSOR2 21  

// Definir Pins del sensor ultrasonido 
#define TRIG_PIN 9   // Trigger Pin (GPIO9)
#define ECHO_PIN 10  // Echo Pin (GPIO10)

// RTD-Parameter
#define RREF 430.0
#define RNOMINAL 100.0

// asignación del pin cs
Adafruit_MAX31865 sensor1 = Adafruit_MAX31865(CS_SENSOR1);
Adafruit_MAX31865 sensor2 = Adafruit_MAX31865(CS_SENSOR2);

// Variables
float temp1 = 0.0, temp2 = 0.0;
float measuredDistance = 0.0; // Declaración de measuredDistance
uint8_t last_cmd = 0x00;

uint16_t latest_temp1_scaled = 0;
uint16_t latest_temp2_scaled = 0;
uint16_t latest_level_scaled = 0;

// Altura del estanque
#define TANK_HEIGHT 38.0 

// Deklaración de los funciones
void receiveEvent(int bytes_msg);
void requestEvent();

void setup() {
    Wire.begin(I2C_ADDRESS);
    Wire.onReceive(receiveEvent); //Si el Controller (Raspberry Pi 4) manda datos
    Wire.onRequest(requestEvent); //Si el Controller (Raspberry Pi 4) solicite datos
    
    delay(1000);
    Serial.begin(115200);
    Serial.println("Test: Código 0x13 corre!");
    Serial.println("I2C periferico iniciado correctamente.");

    // inicialisar MAX31865
    sensor1.begin(MAX31865_4WIRE);
    sensor2.begin(MAX31865_4WIRE);

    // inicialisar Pin del sensor Ultrasonido
    pinMode(TRIG_PIN, OUTPUT);  // Trigger Pin salida
    pinMode(ECHO_PIN, INPUT);   // Echo Pin entrada
}

void loop() {
    temp1 = sensor1.temperature(RNOMINAL, RREF);
    delay(500);
    temp2 = sensor2.temperature(RNOMINAL, RREF);

    // Ultrasonido para nivel del agua
    digitalWrite(TRIG_PIN, LOW);  // Trigger Pin LOW 
    delayMicroseconds(2);
    digitalWrite(TRIG_PIN, HIGH); // activar Trigger 
    delayMicroseconds(10);
    digitalWrite(TRIG_PIN, LOW);  // terminar Trigger

    long duration = pulseIn(ECHO_PIN, HIGH);  // medir señal del echo

    // Debugging: Duración
    Serial.print("Duración del echo: ");
    Serial.println(duration); //Duración en micro segundos

    if (duration == 0) {
        measuredDistance = 0;  // no echo recibido, así 0 cm
    } else {
        measuredDistance = duration * 0.034 / 2;  // duración: tiempo de regreso de la señal ultrasónica (en microsegundos), 0,034: velocidad del sonido (cm/microsegundo).
    }

    // nivel del agua
    float waterLevel = TANK_HEIGHT - measuredDistance;
    if (waterLevel < 0) {
        waterLevel = 0; // no valores negativos
    }

    delay(1000); // esperar 1 segundo

    Serial.print("Temp1: ");
    Serial.print(temp1);
    Serial.print(" °C, Temp2: ");
    Serial.print(temp2);
    Serial.print(" °C, water level: ");
    Serial.print(waterLevel);
    Serial.println(" cm");

    delay(1000);  // 1 Sekunde warten
}


// I2C recibido (del Master)
void receiveEvent(int bytes_msg) {
    if (bytes_msg < 3) return;    // ahora acepta 3 bytes mínimo
    uint8_t id  = Wire.read();    // 1. Byte: ID
    uint8_t cmd = Wire.read();    // 2. Byte: comando
    uint8_t len = Wire.read();    // 3. Byte: longitud (0 si no hay datos)
    last_cmd    = cmd;            // guardamos el comando para la respuesta
    while (Wire.available())      // descartamos cualquier byte extra
        Wire.read();
}

// respuesta I2C (para el master)
void requestEvent() {
    if (last_cmd == CMD_GET_TEMP) {
        uint16_t temp1_scaled = static_cast<uint16_t>(temp1 * 100);
        uint16_t temp2_scaled = static_cast<uint16_t>(temp2 * 100);

        uint8_t response[8] = {
            0x00, RESP_TEMP, 4,
            (uint8_t)(temp1_scaled & 0xFF),
            (uint8_t)((temp1_scaled >> 8) & 0xFF),
            (uint8_t)(temp2_scaled & 0xFF),
            (uint8_t)((temp2_scaled >> 8) & 0xFF)
        };

        Serial.print("Response: [");
        for (int i = 0; i < 8; i++) {
            Serial.print(response[i]);
            if (i < 7) Serial.print(", ");
        }
        Serial.println("]");

        Wire.write(response, 8);

        Serial.print("temperatura enviada: ");
        Serial.print(temp1);
        Serial.print(" °C, ");
        Serial.print(temp2);
        Serial.println(" °C");
    }

    else if (last_cmd == 0x03) { // Nivel del estanque
        uint16_t level_scaled = static_cast<uint16_t>(TANK_HEIGHT - measuredDistance);
        if (level_scaled > 255) level_scaled = 255;  // Optional: Begrenzung auf 8 Bit, falls nötig

        uint8_t response[5] = {
            0x00, RESP_LEVEL, 2,
            (uint8_t)(level_scaled & 0xFF),
            (uint8_t)((level_scaled >> 8) & 0xFF)
        };

        Serial.print("Response: [");
        for (int i = 0; i < 5; i++) {
            Serial.print(response[i]);
            if (i < 4) Serial.print(", ");
        }
        Serial.println("]");

        Wire.write(response, 5);

        Serial.print("Nivel enviado: ");
        Serial.print(level_scaled);
        Serial.println(" cm");
    }
}
