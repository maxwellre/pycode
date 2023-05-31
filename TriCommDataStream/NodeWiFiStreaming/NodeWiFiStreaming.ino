#include <Wire.h>
#include <ESP8266WiFi.h>

#define DEBUG_MOD false // Debug mode will print to USB COM port

// WiFi parameters to be configured
const char* ssid = "ACCNET";
const char* password = "8266";

// TCP server at port 1234
WiFiServer server(80);

// Green - 3V3
// Blue - SCL
// Purple - SDA
// White - Ground

#define Sensor_ADDRESS 0x19
#define SCLPin 5    // D1 on ESP8266
#define SDAPin 4    // D2 on ESP8266

#define BUFFER_SIZE 126 // (6 bytes x 21)

int sampleNum = 0;

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

void setup() 
{
  if(DEBUG_MOD){Serial.begin(115200); delay(500); while (!Serial);} // wait for serial port to connect

  Wire.begin(SDAPin, SCLPin); 
  Wire.setClock(400000UL);


  writeRegister(0x20, 0x97); // CTRL1 // 1600 Hz output data rate, High-Performance Mode
  writeRegister(0x21, 0x04); // CTRL2 // IF_ADD_INC:  Register address automatically incremented during multiple byte access with a serial interface
  writeRegister(0x2E, 0xD0); // FIFO_CTRL // FMode2 FMode1 FMode0 FTH4 FTH3 FTH2 FTH1 FTH0
  writeRegister(0x25, 0x30); // CTRL6 

  delay(100);

  // Create WiFi network
  WiFi.softAP(ssid, password);

  // Start the server
  server.begin();

  delay(100);

  if(DEBUG_MOD)
  {
    IPAddress ip = WiFi.localIP();
    Serial.print("IP Address: "); Serial.println(ip);

    Serial.print("WHO_AM_I: "); Serial.printf("%02x , ", readRegOneByte(0x0F));
    Serial.print("CTRL1: "); Serial.printf("%02x , ", readRegOneByte(0x20));
    Serial.print("CTRL2: "); Serial.printf("%02x , ", readRegOneByte(0x21));
    Serial.print("FIFO_CTRL: "); Serial.printf("%02x , ", readRegOneByte(0x2E));
    Serial.print("CTRL6: "); Serial.printf("%02x , ", readRegOneByte(0x25));
    Serial.println();
  }
}

void loop() 
{
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
        client.printf("%02x", Wire.read());
      }

      totalByteNum -= BUFFER_SIZE;

      while(Wire.available()){ Wire.read(); } // Clear buffer
    }

    client.stop();
    toConnect = true;
  }
  delay(100);
}



// int16_t x = (Wire.read() | Wire.read() << 8);
// float x_g = (float)x / 32767.0 * 2.0;
// OUT_X_L_A | AUTOINCREMENT | 0x80
// Send the sensor readings to the client
// client.print(x_g, 4);
// client.print(",");
// client.print(y_g, 4);
// client.print(",");
// client.print(z_g, 4);
// client.println();


    // while (client.connected() && (sampleNum-- > 0)) 
    // {
    //   Wire.requestFrom(Sensor_ADDRESS, 6);
    //   for(int i = 0; i < 6; ++i)
    //   {
    //     byte datain = Wire.read();
    //     client.printf("%02x", datain);
    //     // if(DEBUG_MOD){Serial.print(datain,HEX); Serial.print(" ");}
    //   }
    // }

  // Wire.beginTransmission(Sensor_ADDRESS);
  //   Wire.write(0x28); // OUT_X_L_A | AUTOINCREMENT | 0x80
  //   Wire.endTransmission();

  //   sampleNum *= 3; // X, Y, Z forms one complete data sample

  //   int totalByteNum = sampleNum*2;
  //   Wire.requestFrom(Sensor_ADDRESS, totalByteNum);

  //   while (client.connected() && (sampleNum-- > 0)) 
  //   {
  //     byte dataL = Wire.read();
  //     byte dataH = Wire.read();

  //     client.printf("%02x%02x", dataL, dataH);

  //     int16_t x = (dataL | dataH << 8);
  //     float x_g = (float)x / 32767.0 * 2.0;

  //     if(DEBUG_MOD){//Serial.printf("%02x%02x", dataH, dataL); Serial.print("->"); 
  //     Serial.print(x); Serial.print("->");Serial.print(x_g); Serial.println();}
  //   }


    // while (client.connected() && (totalByteNum > 0)) 
    // {
    //   if(Wire.available() > 0)
    //   {
    //     byte datain = Wire.read();
    //     client.printf("%02x", datain);
    //     totalByteNum--;
    //     if(DEBUG_MOD){Serial.print(datain,HEX); Serial.print(" ");}
    //   }
    //   else
    //   {
    //     if(DEBUG_MOD){Serial.println();}
    //     // delay(1);
    //     Wire.requestFrom(Sensor_ADDRESS, totalByteNum, true);
    //   }
    // }