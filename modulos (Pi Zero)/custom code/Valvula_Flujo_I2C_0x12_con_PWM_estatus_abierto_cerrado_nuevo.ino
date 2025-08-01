#include <Wire.h>

// dirección I2C
#define I2C_ADDRESS 0x12  
#define CMD_SET_VALVE 0x01  // orden para estatus de la válvula
#define CMD_GET_FLOW  0x02  // orden para recibir flujo
#define CMD_GET_VALVE_STATUS 0x03 // estatus de las valvulas
#define RESP_FLOW     0x13  // respuesta para flujo
#define RESP_VALVE_STATUS 0x14 // respuesta para valvulas

// Pins para las válvulas
#define RELAY_PIN_1 15
#define RELAY_PIN_2 14

// Pins para flujómetro
#define FLOW_SENSOR_1 2
#define FLOW_SENSOR_2 3

// variables globales para flujo
volatile uint16_t flowCount1 = 0;
volatile uint16_t flowCount2 = 0;
float flowRate1 = 0.0;
float flowRate2 = 0.0;

// Interrupt Service Routine para flujómetros
void flow1ISR() {
    flowCount1++;
}

void flow2ISR() {
    flowCount2++;
}

void setup() {
  // Inicialización de la comunicación serial (I2C)
    Wire.begin(I2C_ADDRESS);
    Wire.onReceive(receiveEvent);
    Wire.onRequest(requestEvent);

    delay(1000);
    Serial.begin(115200);
    Serial.println("Test: Código 0x12 corre!");
    Serial.println("I2C periferico iniciado correctamente.");

    // inicializar los Relais-Pins
    pinMode(RELAY_PIN_1, OUTPUT);
    pinMode(RELAY_PIN_2, OUTPUT);
    digitalWrite(RELAY_PIN_1, LOW);
    digitalWrite(RELAY_PIN_2, LOW);

    // Configuración de los sensores de flujo
    pinMode(FLOW_SENSOR_1, INPUT_PULLUP);
    pinMode(FLOW_SENSOR_2, INPUT_PULLUP);
    attachInterrupt(digitalPinToInterrupt(FLOW_SENSOR_1), flow1ISR, RISING);
    attachInterrupt(digitalPinToInterrupt(FLOW_SENSOR_2), flow2ISR, RISING);
}

void loop() {
    // Cálculo del caudal (fórmula supuesta: 7,5 impulsos por litro)
    flowRate1 = (flowCount1 / 7.5);
    flowRate2 = (flowCount2 / 7.5);

    Serial.print("Flow 1: ");
    Serial.print(flowRate1);
    Serial.print(" L/min, Flow 2: ");
    Serial.println(flowRate2);

    // Reiniciar contador
    flowCount1 = 0;
    flowCount2 = 0;

    delay(1000);
}

// Función de recepción de datos I2C, se llama cuando el maestro envía datos al periferico
void receiveEvent(int bytes_msg) {
    Serial.print("I2C mensaje recibido, Bytes: ");
    Serial.println(bytes_msg);

    if (bytes_msg < 4) return;

    uint8_t reg = Wire.read();
    uint8_t id  = Wire.read();
    uint8_t cmd = Wire.read();
    uint8_t len = Wire.read();

    uint8_t valve = 0;
    if (len > 0 && Wire.available()) {
        valve = Wire.read();  // Ventil-Daten lesen
    }
    
    //lastCommand = cmd;

    Serial.print("Orden: ");
    Serial.print(cmd);
    Serial.print(", Válvula: ");
    Serial.println(valve);

    if (cmd == CMD_SET_VALVE) {
        if (valve == 1) {
            digitalWrite(RELAY_PIN_1, HIGH);
            Serial.println("Válvula 1 abierta");
        } else if (valve == 2) {
            digitalWrite(RELAY_PIN_2, HIGH);
            Serial.println("Válvula 2 abierta");
        } else if (valve == 3) {
            digitalWrite(RELAY_PIN_1, LOW);
            Serial.println("Válvula 1 cerrada");
        } else if (valve == 4) {
            digitalWrite(RELAY_PIN_2, LOW);
            Serial.println("Válvula 2 cerrada");
        }
    }
}

// Función de respuesta a solicitudes I2C
void requestEvent() {
    uint16_t flow1_scaled = static_cast<uint16_t>(flowRate1 * 100);
    uint16_t flow2_scaled = static_cast<uint16_t>(flowRate2 * 100);

     // leer estatus de las válvulas
    uint8_t valve_status = 0;
    if (digitalRead(RELAY_PIN_1)) valve_status |= 0x01;  // Bit 0 = Ventil 1
    if (digitalRead(RELAY_PIN_2)) valve_status |= 0x02;  // Bit 1 = Ventil 2

    uint8_t response[7] = {RESP_FLOW, 5,
        (uint8_t)(flow1_scaled & 0xFF), (uint8_t)((flow1_scaled >> 8) & 0xFF),
        (uint8_t)(flow2_scaled & 0xFF), (uint8_t)((flow2_scaled >> 8) & 0xFF),
        valve_status
    };
    Wire.write(response, 7);
    Serial.print("Response: [");
    for (int i = 0; i < 7; i++) {
        Serial.print(response[i]);
        if (i < 6) Serial.print(", ");
    }
    Serial.println("]");
    Serial.println("Datos de flujo y estado de válvulas enviados");
}
