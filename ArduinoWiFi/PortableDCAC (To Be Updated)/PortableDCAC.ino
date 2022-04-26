#include <WiFiNINA.h>
/************ Triangle Communication with vibration feature *********
 * Server: Arduino WiFI, Client connected to: 192.168.4.1
 * Author: Yitian Shao (ytshao@is.mpg.de)
 * Revived on 2022.04.26
********************************************/

/************Board Configuration************/
#define DAC A0 // Reserved analog output pin
/*Note: PWM pin 1 is reserved for relay!*/
#define PWM0 3 // The PWM pin used to control optocoupler 0
#define PWM1 4 // The PWM pin used to control optocoupler 1
#define PWM2 5 // The PWM pin used to control optocoupler 2

const int led =  LED_BUILTIN; // On-board LED pin
const int relay1 = 1; // HV Relay pin

/************WIFI Configuration Parameters************/
char ssid[] = "HVCtrl";        // your network SSID (name)
char pass[] = "1234";    // your network password (use for WPA, or use as key for WEP)
int status = WL_IDLE_STATUS;

/************High Voltage (HV) Variables************/
bool inTransition = false; // Flag: HV gain transition mode
bool isHV = false; // Flag: HV is turned on or off

bool openChann0 = false; // Open status of HV channel 0 (PWM0 pin)
bool openChann1 = false; // Open status of HV channel 1 (PWM1 pin)
bool openChann2 = false; // Open status of HV channel 2 (PWM2 pin)

uint HVGain = 0; // Target HV Gain (0 to 100)
uint currHVGain = 0; // Current HV Gain (0 to 100)
uint PWMGain = 0; // Computed PWM value to control the actual HV gain value  (0 to 10)

uint freq = 0; // Frequency of the square wave that is used to control the vibration
uint pulsewidth = 0; // Pulsewidth of the square wave (Uint: ms)
/************WIFI Configuration************/
WiFiServer server(80);

//void transitHV(uint curr_gain)
//{
//  PWMGain = 20*curr_gain/100;
//  if(PWMGain > 0)
//  {
//    if(openChann0) // HV Channel 0 enabled
//    {
//      digitalWrite(PWM0, HIGH);
//    }
//    if(openChann1) // HV Channel 1 enabled
//    {
//      digitalWrite(PWM1, HIGH);
//    }
//    if(openChann2) // HV Channel 2 enabled
//    {
//      digitalWrite(PWM2, HIGH);
//    }
//    delay(PWMGain);
//    //delayMicroseconds(PWMGain);
//  }
//  if(PWMGain < 20)
//  {
//    digitalWrite(PWM0, LOW);
//    digitalWrite(PWM1, LOW);
//    digitalWrite(PWM2, LOW);
//    delayMicroseconds(20 - PWMGain);
//  }
//}

void setup() {
  /************Initialize serial and wait for port to open************/
  //Serial.begin(9600);
  //delay(2000); //while (!Serial); // wait for serial port to connect. Needed for native USB port only
  //Serial.println("Access Point Web Server");

  /************Pin mode setup and Initialization************/
  pinMode(PWM0, OUTPUT); 
  digitalWrite(PWM0, LOW);// Must not use: analogWrite(PWM0,255); // Turn off the MOSFET 
  pinMode(PWM1, OUTPUT); 
  digitalWrite(PWM1, LOW);// Must not use: analogWrite(PWM1,255); // Turn off the MOSFET 
  pinMode(PWM2, OUTPUT); 
  digitalWrite(PWM2, LOW);// Must not use: analogWrite(PWM2,255); // Turn off the MOSFET 
  
  pinMode(led, OUTPUT);      
  digitalWrite(led, LOW);
  pinMode(relay1, OUTPUT);
  digitalWrite(relay1, LOW);

  // check for the WiFi module:
  if (WiFi.status() == WL_NO_MODULE) {
    //Serial.println("Communication with WiFi module failed!"); 
    while (true); // don't continue
  }

  String fv = WiFi.firmwareVersion();
  if (fv < WIFI_FIRMWARE_LATEST_VERSION) {
    //Serial.println("Please upgrade the firmware");
  }

  /************print the network name (SSID)************/
  //Serial.print("Creating access point named: "); Serial.println(ssid);

  /************Create open network. (Change this line to create an WEP network)************/
  status = WiFi.beginAP(ssid, pass);
  if (status != WL_AP_LISTENING) {
    while (true);
  }

  delay(1000); // wait 1 seconds for connection
  server.begin(); // start the web server on port 80

  // blink LED twice as a starting sign
  for(int i = 0; i < 2; i++)
  {
    digitalWrite(led, HIGH);
    delay(200);
    digitalWrite(led, LOW);
    delay(200);
  } 
  //printWiFiStatus(); // connected, print out the status
}


void loop() {
  /*compare the previous status to the current status*/
  if (status != WiFi.status()) {
    status = WiFi.status(); // it has changed update the variable
  }

  /*Create Webpage Interface*/
  WiFiClient client = server.available();   // listen for incoming clients
  if (client) {                             // if you get a client,
    //Serial.println("new client");           // print a message out the serial port
    String currentLine = "";                // make a String to hold incoming data from the client
    while (client.connected()) {            // loop while the client's connected
      if (client.available()) {             // if there's bytes to read from the client,
        char c = client.read();             // read a byte, then
        //Serial.write(c);                    // print it out the serial monitor
        if (c == '\n') {                    // if the byte is a newline character

          // if the current line is blank, you got two newline characters in a row.
          // that's the end of the client HTTP request, so send a response:
          if (currentLine.length() == 0) {
            // HTTP headers always start with a response code (e.g. HTTP/1.1 200 OK)
            // and a content-type so the client knows what's coming, then a blank line:
            client.println("HTTP/1.1 200 OK");
            client.println("Content-type:text/html");
            client.println();

            // Main content of html
            String html_main = createWebpage();
            client.print(html_main);
            client.println(); // The HTTP response ends with another blank line:
            
            // break out of the while loop:
            break;
          }
          else {      // if you got a newline, then clear currentLine:
            currentLine = "";
          }
        }
        else if (c != '\r') {    // if you got anything else but a carriage return character,
          currentLine += c;      // add it to the end of the currentLine
        }

        /*Square Wave Tuning Table*/
        /*PulseWidth (ms)| 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10| 20|*/
        /*ActualFreq (Hz)|370|212|149|115| 91| 78| 68| 59| 53| 48| 25|*/

        // Check the client request for relay control:
        if (currentLine.endsWith("GET /?relay1=lowVolt")) {
          digitalWrite(led, LOW); 
          digitalWrite(relay1,LOW);
          HVGain = 0;
          //inTransition = true;
          isHV = false;
        }
        else if (currentLine.endsWith("GET /?relay1=highVolt")) {
          digitalWrite(led, HIGH); 
          digitalWrite(relay1,HIGH);
          HVGain = 100;
          //inTransition = true;
          isHV = true;
        }
        else if (currentLine.endsWith("GET /?button=b01")) {
          freq = 0;
          pulsewidth = 0;
        }
        else if (currentLine.endsWith("GET /?button=b02")) {
          freq = 20;
          pulsewidth = 24000; // (us)
        }
        else if (currentLine.endsWith("GET /?button=b03")) {
          freq = 100;
          pulsewidth = 4600; // (us)
        }
        else if (currentLine.endsWith("GET /?button=b04")) {
          freq = 300;
          pulsewidth = 1300; // (us)
        }
        else if (currentLine.endsWith("GET /?button=bCh0")) {
          openChann0 = !openChann0;
        }
        else if (currentLine.endsWith("GET /?button=bCh1")) {
          openChann1 = !openChann1;
        }
        else if (currentLine.endsWith("GET /?button=bCh2")) {
          openChann2 = !openChann2;
        }
      }
    } 
    client.stop(); // close the connection // Serial.println("client disconnected");
  }

  /*Implement Control Based on User Input*/
//  if(inTransition) // HV gain in transition mode
//  {
//    freq = 0;
//    pulsewidth = 0;
//    if(currHVGain < HVGain) // Increase current voltage gain to target gain
//    {
//      currHVGain++;
//    }
//    else if(currHVGain > HVGain) // Decrease current voltage gain to target gain
//    {
//      currHVGain--;
//    }
//    else
//    {
//      inTransition = false;
//    }
//    transitHV(currHVGain);
//  }
//  else 
  if(isHV) // HV output enabled
  {
    if(openChann0) // HV Channel 0 enabled
    {
      digitalWrite(PWM0, HIGH);
    }
    else
    {
      digitalWrite(PWM0, LOW);
    }
    
    if(openChann1) // HV Channel 1 enabled
    {
      digitalWrite(PWM1, HIGH);
    }
    else
    {
      digitalWrite(PWM1, LOW);
    }
    
    if(openChann2) // HV Channel 2 enabled
    {
      digitalWrite(PWM2, HIGH);
    }
    else
    {
      digitalWrite(PWM2, LOW);
    }
    
    if(pulsewidth > 0) // Vibration enabled: Add an AC (squarewave) in addition to DC HV output
    {
      delayMicroseconds(pulsewidth);
      digitalWrite(PWM0, LOW);
      digitalWrite(PWM1, LOW);
      digitalWrite(PWM2, LOW);
      delayMicroseconds(pulsewidth);
    }
  }
  else // Redundant code ensuring safety
  {
    digitalWrite(PWM0, LOW);
    digitalWrite(PWM1, LOW);
    digitalWrite(PWM2, LOW);
  }
}

/* Generate a website of interface for remote control */
String createWebpage(){
  String relay1_status, Chann0_status, Chann1_status, Chann2_status, Panel_info;
  Panel_info = "<p>Vibration - - - - - - Channel</p>";
  //Panel_info = "<p>0:" + String(openChann0) + ", 1:"+ String(openChann1) + ", 2:"+ String(openChann2) + ", PW:"+ String(pulsewidth) + ", HV:"+ String(isHV) + ", G:"+ String(currHVGain) + "</p>";
  
  if(digitalRead(relay1))
  {
    relay1_status = "<a style = \"color:red\">On";
  }
  else
  {
    relay1_status = "<a style = \"color:white\">Off";
  }

  if(openChann0)
  {
    Chann0_status = "<button name= \"button\" type=\"submit\" value=\"bCh0\" class=\"smallbutton\" style = \"background-color:#ffe6b3\">Ch0 on</button>";
  }
  else
  {
    Chann0_status = "<button name= \"button\" type=\"submit\" value=\"bCh0\" class=\"smallbutton\" style = \"background-color:#cce6ff\">Ch0 off</button>";
  }

  if(openChann1)
  {
    Chann1_status = "<button name= \"button\" type=\"submit\" value=\"bCh1\" class=\"smallbutton\" style = \"background-color:#ffe6b3\">Ch1 on</button>";
  }
  else
  {
    Chann1_status = "<button name= \"button\" type=\"submit\" value=\"bCh1\" class=\"smallbutton\" style = \"background-color:#cce6ff\">Ch1 off</button>";
  }

  if(openChann2)
  {
    Chann2_status = "<button name= \"button\" type=\"submit\" value=\"bCh2\" class=\"smallbutton\" style = \"background-color:#ffe6b3\">Ch2 on</button>";
  }
  else
  {
    Chann2_status = "<button name= \"button\" type=\"submit\" value=\"bCh2\" class=\"smallbutton\" style = \"background-color:#cce6ff\">Ch2 off</button>";
  }

  String html = "<!DOCTYPE html>";
  html += "<html><head><meta charset=\"UTF-8\"><style>";
  html += "body {background-color:black;}"; 
  html += "h1 {font-family:Arial; color: white; font-size:80px; margin-top:80px;}";
  html += "p {font-family:Arial; color: white; font-size:60px;}";
  html += ".buttonform{position:relative;  top:80%;  left:30%;}";
  html += ".largebutton{font-size:120px; margin-bottom:140px; margin-left:200px; padding: 30px 50px; border: none; border-radius: 10%; font-family:Arial;}";
  html += ".smallbutton{font-size:100px; margin-bottom:100px; margin-right:100px; padding: 10px 20px; border: none; border-radius: 2%; font-family:Arial;}";
  html += "</style></head><body>";
  html += "<h1 align=\"center\">High Voltage Controller</h1>";
  html += "<p align=\"center\">Current status : " + relay1_status + "</p><p><form action=\"/\" method=\"get\" class=\"buttonform\"><br>";
  html += "<button name= \"relay1\" type=\"submit\" value=\"highVolt\" class=\"largebutton\" style = \"background-color:#ff8080\">ON</button><br>";
  html += "<button name= \"relay1\" type=\"submit\" value=\"lowVolt\" class=\"largebutton\" style = \"background-color:#f2f2f2\">OFF</button><br>";
  html += "<button name= \"button\" type=\"submit\" value=\"b01\" class=\"largebutton\" style = \"background-color:#209920\">DC</button>";
  html += Panel_info + "<br>";
  html += "<button name= \"button\" type=\"submit\" value=\"b02\" class=\"smallbutton\" style = \"background-color:#40bb40\">020 Hz</button>";
  html += Chann0_status + "<br>";
  html += "<button name= \"button\" type=\"submit\" value=\"b03\" class=\"smallbutton\" style = \"background-color:#60dd60\">100 Hz</button>";
  html += Chann1_status + "<br>";
  html += "<button name= \"button\" type=\"submit\" value=\"b04\" class=\"smallbutton\" style = \"background-color:#80ff80\">300 Hz</button>";
  html += Chann2_status;
  html += "</form></p></body></html>";
  return html;
}
