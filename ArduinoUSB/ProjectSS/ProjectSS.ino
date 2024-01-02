#include <Wire.h>
#include <WiFiS3.h>
// Hardware connection: Orange - 3V3, Yellow - SCL, Green - SDA, Blue - GND

#define DEBUG_MOD true // Debug mode will print sensor configuration details

#define WHO_AM_I 0x0F
#define CTRL1 0x20
#define CTRL2 0x21
#define FIFO_CTRL 0x2E
#define CTRL6 0x25
#define OUT_X_L 0x28

#define Sensor_ADDRESS 0x19
#define BUFFER_SIZE 126 // (6 bytes x 21)

int sampleNum = 1;

/* WiFi configuration */
const char* ssid = "ACCNET";
WiFiServer server(80);

int status = WL_IDLE_STATUS;

char msgBuffer[100];

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
  writeRegister(CTRL1, 0x97); // CTRL1 - 1600 Hz output data rate, High-Performance Mode
  writeRegister(CTRL2, 0x04); // CTRL2 - IF_ADD_INC:  Register address automatically incremented during multiple byte access with a serial interface
  writeRegister(FIFO_CTRL, 0xD0); // FIFO_CTRL [FMode2 FMode1 FMode0 FTH4 FTH3 FTH2 FTH1 FTH0], Continuous mode: If the FIFO is full, the new sample overwrites the older sample.
  writeRegister(CTRL6, 0x30); // CTRL6 - Full-scale selection: ±16 g

  delay(100);

  /* Check the configuration */
  if(DEBUG_MOD)
  {
    sprintf(msgBuffer, "WHO_AM_I: %02x", readRegOneByte(WHO_AM_I)); // WHO_AM_I = 44 for a functional accelerometer
    Serial.println(msgBuffer);
    sprintf(msgBuffer, "CTRL1: %02x", readRegOneByte(CTRL1));
    Serial.println(msgBuffer);
    sprintf(msgBuffer, "CTRL2: %02x", readRegOneByte(CTRL2));
    Serial.println(msgBuffer);
    sprintf(msgBuffer, "FIFO_CTRL: %02x", readRegOneByte(FIFO_CTRL));
    Serial.println(msgBuffer);
    sprintf(msgBuffer, "CTRL6: %02x", readRegOneByte(CTRL6));
    Serial.println(msgBuffer);
  }

  /* Initialize WiFi connection */
  if (WiFi.status() == WL_NO_MODULE) 
  {
    Serial.println("Communication with WiFi module failed!");
    while(true);
  }

  if (WiFi.firmwareVersion() < WIFI_FIRMWARE_LATEST_VERSION) 
  {
    Serial.println("Firmware update required");
  }

  do
  {
    status = WiFi.beginAP(ssid); // Create WiFi network
    delay(500);
    Serial.println("Creating access point ...");
  }
  while(status != WL_AP_LISTENING);

  server.begin(); // Start the server

  delay(100);

  if(DEBUG_MOD)
  {
    IPAddress ip = WiFi.localIP();
    Serial.print("IP Address: "); Serial.println(ip);
  }

  // char dataBuffer[BUFFER_SIZE];

  // for(int i = 0; i < BUFFER_SIZE; ++i)
  // {
  //   sprintf(dataBuffer, "%02x", i); //Wire.read()
  // }

  // for(int i = 0; i < BUFFER_SIZE; ++i)
  // {
  //   Serial.println(dataBuffer[i], HEX);
  // }
}

void loop(){
  bool toConnect = true;
  WiFiClient client = server.available();

  if (client && client.connected()) 
  {
    while (toConnect)
    {
      if(client.available())
      {
        String msg = client.readStringUntil('\r');
        client.flush();

        if (msg.substring(0,6) == "sample") 
        {
          sampleNum = msg.substring(6).toInt();
          client.println("accnet-ready");
          toConnect = false;
          if(DEBUG_MOD){Serial.print("Sample Number = "); Serial.println(sampleNum);}
        }
      }
      delay(100);
    }

    int totalByteNum = sampleNum*6; // Six bytes [X_L, X_H, Y_L, Y_H, Z_L, Z_H] form one complete data sample

    while (client.connected() && (totalByteNum > 0)) 
    {
      initializeByteStreaming(0x28, BUFFER_SIZE);

      for(int i = 0; i < BUFFER_SIZE; ++i)
      {
        char dataBuffer[2];
        sprintf(dataBuffer, "%02x", Wire.read());
        client.print(dataBuffer);
      }

      totalByteNum -= BUFFER_SIZE;

      while(Wire.available()){ Wire.read(); } // Clear buffer
    }

    client.stop();
    toConnect = true;
    if(DEBUG_MOD){Serial.println("Data transmission completed");}
  }
  delay(100);
}

    //   while (client.connected() && (totalByteNum > 0)) 
    // {
    //   initializeByteStreaming(0x28, BUFFER_SIZE);

    //   for(int i = 0; i < BUFFER_SIZE; ++i)
    //   {
    //     char dataBuffer[2];
    //     sprintf(dataBuffer, "%02x", Wire.read());
    //     client.print(dataBuffer);

    //     // client.print(i, HEX); //Wire.read()
    //     // Serial.println(Wire.read(), HEX);
    //     // dataBuffer[i] = printf(Wire.read(), HEX);
    //   }

    //   totalByteNum -= BUFFER_SIZE;

    //   //while(Wire.available()){ Wire.read(); } // Clear buffer
    // }