#include <Wire.h>
#include <Adafruit_NeoPixel.h>

#define I2C_ADDRESS 0x10
#define CMD_SET 0x01
#define CMD_GET 0x02
#define RESP_OK 0x10
#define RESP_ERROR 0x11
#define RESP_TEMPERATURE 0x12
#define rp2040_zero  true

#if rp2040_zero 
  int PIN = 16;
  int NUMPIXELS = 1;
  Adafruit_NeoPixel pixel(NUMPIXELS, PIN, NEO_GRB + NEO_KHZ800);
#endif

uint8_t value = 0;  // Set Value
int random_number;  // Get Value
int pwmPin = 8;  // Asignar un pin PWM adecuado

void setup() {
    Serial.begin(9600);
    Wire.begin(I2C_ADDRESS);
    Wire.onReceive(receiveEvent);
    Wire.onRequest(requestEvent);
    Serial.println("I2C esclavo iniciado correctamente.");
    // initialize digital pin LED_BUILTIN as an output.
    randomSeed(analogRead(A0));

    if (rp2040_zero){
      pixel.begin();
    }
}

void loop() {
    // No se necesita nada en el loop principal
}

void set_function(int value){
// Enviar pulso PWM usando el valor como duty cycle
    int pwmValue = map(value, 0, 100, 0, 127);  // Convertir valor (0-100) a rango de PWM (0-255)
    analogWrite(pwmPin, pwmValue);  // Enviar PWM al pin seleccionado

  if (rp2040_zero){
    pixel.clear();
    pixel.setPixelColor(0, pixel.Color(0, value, 0));
    pixel.show();
  }
}

int get_function(){
    return random(0,11);
}


void receiveEvent(int bytes_msg) {
    if (bytes_msg < 4) {  // Comando mínimo: REG (00) + ID (1) + CMD (1) + LEN (1)
        Serial.println("Comando incompleto recibido:");
        Serial.print("Cantidad de Bytes:");
        Serial.println(bytes_msg);
        uint8_t fail_byte = Wire.read();
        Serial.println(fail_byte);
        return;
    }
    uint8_t reg = Wire.read();
    uint8_t id = Wire.read();
    uint8_t cmd = Wire.read();
    uint8_t len = Wire.read();

    if (len > bytes_msg - 3) {  // Validar longitud de datos
        Serial.println("Longitud de datos no coincide con el paquete recibido.");
        return;
    }

    uint8_t data[len];
    for (int i = 0; i < len && Wire.available(); i++) {
        data[i] = Wire.read();
    }

    Serial.print("Comando recibido: REG=");
    Serial.print(reg);
    Serial.print(", ID=");
    Serial.print(id);
    Serial.print(", CMD=");
    Serial.print(cmd, HEX);
    Serial.print(", LEN=");
    Serial.println(len);

    if (cmd == CMD_SET && len == 1) {
        value = constrain(data[0], 0, 100);
        Serial.print("Parámetro actualizado a: ");
        Serial.println(value);
        set_function(value);

    } else if (cmd == CMD_GET && len == 0) {
        Serial.println("GET recibido.");
        random_number = get_function();
    } else {
        Serial.println("Comando no reconocido.");
    }
}



void requestEvent() {
    uint8_t response[4] = {0};  // Máximo de 16 bytes
    //response[0] = 
    response[0] = 1;                  // ID de respuesta
    response[1] = RESP_TEMPERATURE;   // Respuesta de temperatura
    response[2] = 1;                  // Longitud de datos
    response[3] = random_number;      // Ejemplo de temperatura 20°C

    Wire.write(response, 4);     // Enviar ID, CMD, LEN y DATA
    Serial.print("Respuesta enviada al maestro: ");
    for (int i = 0; i < 4; i++) {
        Serial.print(response[i], HEX);
        Serial.print(" ");
    }
    Serial.println();
}