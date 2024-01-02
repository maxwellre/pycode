#include <Wire.h>
// Orange - 3V3, Yellow - SCL, Green - SDA, Blue - GND

#define DEBUG_MOD false // Debug mode will print sensor configuration details

#define WHO_AM_I 0x0F
#define CTRL1 0x20
#define CTRL2 0x21
#define FIFO_CTRL 0x2E
#define CTRL6 0x25
#define OUT_X_L 0x28

#define Sensor_ADDRESS 0x19
#define BUFFER_SIZE 126 // (6 bytes x 21)

int sampleNum = 1;

int totalByteNum = sampleNum*6;

void writeRegister(int regAddress, int value) 
{
  Wire.beginTransmission(Sensor_ADDRESS);
  Wire.write(regAddress);
  Wire.write(value);
  Wire.endTransmission();
}

byte readRegOneByte(int regAddress)
{
  Wire.beginTransmission(Sensor_ADDRESS);
  Wire.write(regAddress); 
  Wire.endTransmission();
  Wire.requestFrom(Sensor_ADDRESS, 1);
  return Wire.read();
}

void initializeByteStreaming(int regAddress, int bufferSize)
{
  Wire.beginTransmission(Sensor_ADDRESS);
  Wire.write(regAddress); 
  Wire.endTransmission();
  if(bufferSize > 0)
  {
    Wire.requestFrom(Sensor_ADDRESS, bufferSize);
  }
}

void setup(){
  Serial.begin(115200); delay(500); while(!Serial); // wait for serial port to connect

  Wire.begin(); 
  Wire.setClock(400000UL); // Set the clock of I2C bus to be 400 kHz

  /* Configure accelerometer */
  writeRegister(CTRL1, 0x97); // CTRL1 // 1600 Hz output data rate, High-Performance Mode
  writeRegister(CTRL2, 0x04); // CTRL2 // IF_ADD_INC:  Register address automatically incremented during multiple byte access with a serial interface
  writeRegister(FIFO_CTRL, 0xD0); // FIFO_CTRL [FMode2 FMode1 FMode0 FTH4 FTH3 FTH2 FTH1 FTH0], Continuous mode: If the FIFO is full, the new sample overwrites the older sample.
  writeRegister(CTRL6, 0x30); // CTRL6 

  delay(100);

  /* Check the configuration */
  if(DEBUG_MOD)
  {
    char messagebuffer[100];
    sprintf(messagebuffer, "WHO_AM_I: %02x , ", readRegOneByte(WHO_AM_I)); // WHO_AM_I = 44 for a functional accelerometer
    Serial.println(messagebuffer);
    sprintf(messagebuffer, "CTRL1: %02x , ", readRegOneByte(CTRL1));
    Serial.println(messagebuffer);
    sprintf(messagebuffer, "CTRL2: %02x , ", readRegOneByte(CTRL2));
    Serial.println(messagebuffer);
    sprintf(messagebuffer, "FIFO_CTRL: %02x , ", readRegOneByte(FIFO_CTRL));
    Serial.println(messagebuffer);
    sprintf(messagebuffer, "CTRL6: %02x , ", readRegOneByte(CTRL6));
    Serial.println(messagebuffer);
  }
}

void loop(){
  while(totalByteNum > 0)
  {
    initializeByteStreaming(OUT_X_L, BUFFER_SIZE); // Streaming starts from the X-axis LSB

    for(int i = 0; i < BUFFER_SIZE; ++i)
    {
      Serial.println(Wire.read());
    }

    totalByteNum -= BUFFER_SIZE;

    while(Wire.available()){ Wire.read(); } // Clear buffer
  }
}