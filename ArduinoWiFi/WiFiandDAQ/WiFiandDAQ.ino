#include <WiFiNINA.h>
/************Triangle Communication *********
 * Server: Arduino WiFI, Client: PC with DAQ
 * Author: Yitian Shao (ytshao@is.mpg.de)
 * Created on 2022.02.28 based on "WiFiTriangleComm.ino"
 * 
 * Note: New protocol coding system
********************************************/

/************Board Configuration************/
#define DAC A0 // Reserved analog output pin
/*Note: PWM pin 1 is reserved for relay!*/
#define PWM0 3 // The PWM pin used to control optocoupler 0
#define PWM1 4 // The PWM pin used to control optocoupler 1
#define PWM2 5 // The PWM pin used to control optocoupler 2
#define PWM3 6 // The PWM pin used to control optocoupler 3

#define VOLT_LEVEL_NUM 4 // Number of voltage levels 

#define DEBUG_MOD false

#define MAX_CLIENT_NUM 10 // Must not change: Allow only one VR headset and one PC connected
//#define MAX_LINE_LEN * // ALlow maxium * bytes of data streamed per line

char ssid[] = "HVCtrl";        // your network SSID (name)
char pass[] = "1234";    // your network password (use for WPA, or use as key for WEP)

bool isVRReady = false; // Reserved
bool isPCReady = false;
int VRInd = -1; // Reserved
int PCInd = -1;

int status = WL_IDLE_STATUS;

float chargeDuration = 800; // Activation duration of positive voltage for zipping (Unit: ms)
float dischargeDuration = 250; // Activation duration of negative voltage for discharging (Unit: ms)

int voltageLevel = 0; // Range from 0 to 100 (Unit: %)
uint8_t PWMGain = 0; // Range from 0 to 255

// Setup of server
WiFiServer server(80); // web server on port 80
WiFiClient *clients[MAX_CLIENT_NUM] = { NULL };
int clientNum = 0;

void connectionCheck()
{
    if(isPCReady && !(clients[PCInd]->connected()))
    {
      isPCReady = false;
      clients[PCInd]->stop();
      clients[PCInd] = NULL;
      clientNum--;
      PCInd = -1;
      if(DEBUG_MOD){Serial.println("Connection to PC is lost: Reconnection Required!");}
    }
}

void setup() {
  if(DEBUG_MOD){Serial.begin(115200); delay(500); while (!Serial);} // wait for serial port to connect

  /************Pin mode setup and Initialization************/
  pinMode(PWM0, OUTPUT); 
  analogWrite(PWM0, 0);// Must not use: analogWrite(PWM0,255); // Turn off the optocoupler 
  pinMode(PWM1, OUTPUT); 
  analogWrite(PWM1, 0);// Must not use: analogWrite(PWM1,255); // Turn off the optocoupler 
  pinMode(PWM2, OUTPUT); 
  analogWrite(PWM2, 0);// Must not use: analogWrite(PWM2,255); // Turn off the optocoupler 
  pinMode(PWM3, OUTPUT); 
  analogWrite(PWM3, 0);// Must not use: analogWrite(PWM2,255); // Turn off the optocoupler 

  pinMode(LED_BUILTIN, OUTPUT);      
  digitalWrite(LED_BUILTIN, LOW);

  if (WiFi.status() == WL_NO_MODULE) {
    if(DEBUG_MOD){Serial.println("Communication with WiFi module failed!");}
    while (true); // don't continue
  }

  status = WiFi.beginAP(ssid, pass);
  if (status != WL_AP_LISTENING) {
    if(DEBUG_MOD){Serial.println("Creating access point failed");}
    while (true); // don't continue
  }
  
  if(DEBUG_MOD){Serial.println("Server Waiting Client");}
  delay(1000);   // wait 1 seconds for connection

  clientNum = 0;
  server.begin();

  // blink LED twice as a starting sign
  for(int i = 0; i < 2; i++) {
    digitalWrite(LED_BUILTIN, HIGH);
    delay(200);
    digitalWrite(LED_BUILTIN, LOW);
    delay(200);
  } 
}

void loop() {
  if (status != WiFi.status()) { // compare the previous status to the current status and update the variable
    status = WiFi.status(); 
  }
  
  while ( (!isPCReady) && clientNum < MAX_CLIENT_NUM ) // Wait until both the VR client and PC client connected
  {
    WiFiClient newClient = server.available();   // listen for incoming new client

    if (newClient != NULL && newClient.connected()) // When get a new client connected
    {                             
      String msgValue = newClient.readStringUntil('\r');
      newClient.flush();
      if(DEBUG_MOD){Serial.print("New client: "); Serial.println(msgValue);}
      
      /* ---------------- Handshake with PC headset ---------------- */
      if (!isPCReady && (msgValue == "pcprogram"))
      {  
          while(clients[clientNum] != NULL && clientNum < MAX_CLIENT_NUM){ clientNum++;}
          
          if (clientNum < MAX_CLIENT_NUM) 
          {
            PCInd = clientNum; 
            clients[PCInd] = new WiFiClient(newClient); // Add the new PC client to the list of clients   
            clientNum++;
            clients[PCInd]->println("high-voltage-controller-is-ready");
            isPCReady = true;
          }          
      }
      if(DEBUG_MOD){Serial.print("Client Number = "); Serial.print(clientNum); Serial.print(" , VR [Reserved] "); Serial.print(isVRReady); Serial.print(" , PC Ready = "); Serial.println(isPCReady);}
    }
     
    connectionCheck(); /* Reconnect if any connection is lost */
  }  /* ------ Wait until both the VR client and PC client connected ------ */

  if(isPCReady)
  {
    if(DEBUG_MOD){
      Serial.println("All Clients are Ready");
      if(!clients[PCInd]->connected()){Serial.println("PC cannot connect");}
    }
    
    while(clients[PCInd]->connected() ) // While all clients are connected 
    {
      if(clients[PCInd]->available()) // Connection with PC established and data available
      {
        /* ---------------- Receive a message ---------------- */
        char msg2 = clients[PCInd]->read(); // Fast communication by a single char  
        if(DEBUG_MOD){Serial.print("PC: "); Serial.println(msg2);}
        

        if (msg2 == 'l') { // ---------------- Button 2
          if(DEBUG_MOD){Serial.print("PC: Pressed button2 Left PWM = "); Serial.println(PWMGain);}
  
          analogWrite(PWM0, PWMGain);
          delay(chargeDuration);
          analogWrite(PWM0, 0);
          delay(1);
          
          analogWrite(PWM1, PWMGain);
          delay(dischargeDuration);
          analogWrite(PWM1, 0);
          delay(1); 
  
          clients[PCInd]->println("command-received"); // Acknowledgement
        } /* ---------------- Botton 2 ---------------- */

        else if (msg2 == 's') { // ---------------- Button 4
          clients[PCInd]->println("command-received"); // Acknowledgement for PC is different!!!
          delay(100);
          
          String msgValue = clients[PCInd]->readStringUntil('\r');
          clients[PCInd]->flush();
          
          if(DEBUG_MOD){Serial.print("PC: "); Serial.println(msgValue);}
          
          if(msgValue.substring(0,9) == "voooooooo") {
            voltageLevel = msgValue.substring(10,13).toInt();
      
            PWMGain = 255*voltageLevel/100;
          }
      
          if(msgValue.substring(14,21) == "chhhhhT") {
            chargeDuration = msgValue.substring(22,26).toInt();
          }
      
          if(msgValue.substring(27,37) == "diiiiiiiiT") {
            dischargeDuration = msgValue.substring(38,42).toInt();
          }
      
          /* Safety check */
          if ((chargeDuration > 4000) || (chargeDuration < 0)) {
              chargeDuration = 0;
          }
          if ((dischargeDuration > 4000) || (dischargeDuration < 0)) {
              dischargeDuration = 0;
          }
          clients[PCInd]->println("command-received"); // Acknowledgement for second-level command for PC is different!!!
          if(DEBUG_MOD){Serial.print("PC: "); Serial.println(PWMGain); Serial.println(chargeDuration); Serial.println(dischargeDuration);}           
        } /* ---------------- Botton 4 ---------------- */
              
      } /* ---------------- PC client ready and available ---------------- */      
    } 
  }/* ---------------- Both clients connected ---------------- */

  /* When any connection is lost, stop all connection and reset all status */
  analogWrite(PWM1, 0); // Ensure all PWM port is closed 
  analogWrite(PWM0, 0);

  for (int cl_i = 0 ; cl_i < MAX_CLIENT_NUM ; ++cl_i)
  {
    if (clients[cl_i] != NULL) 
    {
        clients[cl_i]->stop();
        clients[cl_i] = NULL;
    }
  }
  clientNum = 0;
  isVRReady = false;
  isPCReady = false;
  VRInd = -1;
  PCInd = -1;

  if(DEBUG_MOD){Serial.println("All clients disconnected");}
}
