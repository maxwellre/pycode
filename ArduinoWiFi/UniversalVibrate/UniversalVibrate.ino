#include <WiFiNINA.h>
/************Universal WiFi Communication for Vibration Output *********
 * Server: Arduino WiFI, Client 0: VR headset/PC
 * Author: Yitian Shao (yitian.shao@tu-dresden.de)
 * Created on 2023.02.08 based on "UniversalCtrl.ino"
 * 
 * Note: New setting protocol for frequency control
********************************************/

/************Board Configuration************/
#define DAC A0 // Reserved analog output pin
/*Note: PWM pin 1 is reserved for relay!*/
#define PWM0 3 // The PWM pin used to control optocoupler 0
#define PWM1 4 // The PWM pin used to control optocoupler 1
// #define PWM2 5 // The PWM pin used to control optocoupler 2
// #define PWM3 6 // The PWM pin used to control optocoupler 3

#define VOLT_LEVEL_NUM 4 // Number of voltage levels 

#define DEBUG_MOD false // Debug mode will print to USB COM port

#define MAX_CLIENT_NUM 2 // Must not change: Allow only one VR headset and one PC connected
//#define MAX_LINE_LEN * // ALlow maxium * bytes of data streamed per line

char ssid[] = "HVCtrl";        // your network SSID (name)
char pass[] = "1234";    // your network password (use for WPA, or use as key for WEP)

bool isVRReady = false;
int VRInd = -1;

int status = WL_IDLE_STATUS;

float chargeDuration = 800; // Activation duration of positive voltage for zipping (Unit: ms)
float dischargeDuration = 250; // Activation duration of negative voltage for discharging (Unit: ms)

float vibTime = 1000; // Total time of vibration per command (Unit: ms)
float freq = 10; // Time interval of vibration mode, one cycle contains four intervals: charge-hold-discharge-hold (Unit: ms)

int voltageLevel = 0; // Range from 0 to 100 (Unit: %)
uint8_t PWMGain = 0; // Range from 0 to 255

// Setup of server
WiFiServer server(80); // web server on port 80
WiFiClient *clients[MAX_CLIENT_NUM] = { NULL };
int clientNum = 0;

void connectionCheck()
{
    if(isVRReady && !(clients[VRInd]->connected()))
    {
      isVRReady = false;
      clients[VRInd]->stop();
      clients[VRInd] = NULL;
      clientNum--;
      VRInd = -1;
      if(DEBUG_MOD){Serial.println("Connection to VR is lost: Reconnection Required!");}
    }
}

void vibrationOut(float vibTime, float freq) // Vibration without discharging [Mode 1] 'vibTime' (Unit: ms), 'freq' (Unit: Hz)
{
  if(freq <= 0) return;
  freq = min(freq, 1000); // Frequency must stay in the range of (0, 1000]

  int halfCycleTime = (int) (500000/freq - 2); // Time duration of half a cycle (Unit: us)
  int cycleNum = (int) (vibTime * freq / 1000);
  
  digitalWrite(PWM1, 0); // Ensure discharging channel is off
  delay(1);

  for (int i = 0; i < cycleNum; i++)
  {
    digitalWrite(PWM0, HIGH);
    delayMicroseconds(halfCycleTime);
    digitalWrite(PWM0, LOW);
    delayMicroseconds(halfCycleTime);
  }

  digitalWrite(PWM1, HIGH); // Ensure enough discharging time after each actuation (0.5 secs)
  delay(500);
  digitalWrite(PWM1, LOW);
}

void vibrationOutD(float vibTime, float freq) // Vibration with discharging [Mode 2] 'vibTime' (Unit: ms), 'freq' (Unit: Hz)
{
  if(freq <= 0) return;
  freq = min(freq, 1000); // Frequency must stay in the range of (0, 1000]

  int halfIntvTime = (int) (500000/freq - 3); // (us) time interval of helf cycle of the vibration with 3 us reserved for HV switching
  int cycleNum = (int) (vibTime * freq / 1000);
    
  digitalWrite(PWM1, 0); // Ensure discharging channel is off
  delay(1);

  for (int i = 0; i < cycleNum; i++)
  {
    digitalWrite(PWM0, HIGH);
    delayMicroseconds(halfIntvTime);
    digitalWrite(PWM0, LOW);
    delayMicroseconds(2);
    
    digitalWrite(PWM1, HIGH);
    delayMicroseconds(halfIntvTime);
    digitalWrite(PWM1, LOW);
    delayMicroseconds(2);
  }

  digitalWrite(PWM1, HIGH); // Ensure enough discharging time after each actuation (0.1 secs)
  delay(100);
  digitalWrite(PWM1, LOW);
}

void PWMVoltageOut(int pinMarco, float vibTime, int voltageLevel) // 'vibTime' (Unit: ms), 'voltageLevel' ranged from 0 to 100 (Unit: %)
{
  int pulseWidth = 10 * voltageLevel;

  if(pulseWidth <= 0) 
  {
    return;
  } 
  else if(pulseWidth >= 1000) // Constant output without PWM
  {
    digitalWrite(pinMarco, HIGH);
    delay(vibTime);
    digitalWrite(pinMarco, LOW);
  }
  else // PWM enabled if pulseWidth ranged in (0,1000) ms
  {
    int intervalWidth = 1000 - pulseWidth;  // Approximately 1ms duty cycle (1kHz)

    int cycleNum = (int)(vibTime);

    for (int i = 0; i < cycleNum; i++)
    {
      digitalWrite(pinMarco, HIGH);
      delayMicroseconds(pulseWidth);
      digitalWrite(pinMarco, LOW);
      delayMicroseconds(intervalWidth);
    }
  }
}

void setup() {
  if(DEBUG_MOD){Serial.begin(115200); delay(500); while (!Serial);} // wait for serial port to connect

  /************Pin mode setup and Initialization************/
  pinMode(PWM0, OUTPUT); 
  digitalWrite(PWM0, LOW); // Turn off the optocoupler 
  pinMode(PWM1, OUTPUT); 
  digitalWrite(PWM1, LOW); // Turn off the optocoupler 
  // pinMode(PWM2, OUTPUT);   pinMode(PWM3, OUTPUT); // Reserved for future extension

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
  
  if(DEBUG_MOD){
    IPAddress ip = WiFi.localIP();
    Serial.print("IP Address: ");
    Serial.println(ip);
    Serial.println("Server Waiting Client");
  }
  // wait 1 seconds for connection:
  delay(1000);

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
  
  while (!isVRReady) // && clientNum < MAX_CLIENT_NUM ) // Wait until the VR client is connected
  {
    WiFiClient newClient = server.available();   // listen for incoming new client

    if (newClient != NULL && newClient.connected()) // When get a new client connected
    {                             
      String msgValue = newClient.readStringUntil('\r');
      newClient.flush();
      if(DEBUG_MOD){Serial.print("New client: "); Serial.println(msgValue);}

      /* ---------------- Handshake with VR headset (or a faked VR client by a PC) ---------------- */
      if (!isVRReady && (msgValue == "vrheadset")) 
      {                          
          while(clients[clientNum] != NULL && clientNum < MAX_CLIENT_NUM){ clientNum++;}

          if (clientNum < MAX_CLIENT_NUM)
          {
            VRInd = clientNum;
            clients[VRInd] = new WiFiClient(newClient); // Add the new VR client to the list of clients  
            clientNum++;
            clients[VRInd]->println("high-voltage-controller-is-ready");
            isVRReady = true;
          }        
      }
    
      if(DEBUG_MOD){Serial.print("Client Number = "); Serial.print(clientNum); Serial.print(" , VR Ready = "); Serial.println(isVRReady);}
    }
     
    connectionCheck(); /* Reconnect if any connection is lost */
  }  /* ------ Wait until both the VR client and PC client connected ------ */

  if(isVRReady)
  {
    if(DEBUG_MOD){
      Serial.println("VR/PC Client: Ready");
      if(!clients[VRInd]->connected()){Serial.println("VR cannot connect");}
    }
    
    while( clients[VRInd]->connected() ) // Only check the connection with VR headset
    {
      if (clients[VRInd]->available()) // Connection with VR established and data available
      { 
        /* ---------------- Receive a message ---------------- */
        char msg = clients[VRInd]->read(); // Fast communication by a single char
        if(DEBUG_MOD){Serial.print("VR: "); Serial.println(msg);}

        if (msg == 'l') { // ---------------- Button 2
          if(DEBUG_MOD){Serial.print("VR: Pressed button2 Left PWM = "); Serial.println(PWMGain);}

          PWMVoltageOut(PWM0, chargeDuration, voltageLevel);
          delay(1);
          PWMVoltageOut(PWM1, dischargeDuration, 100);
  
          clients[VRInd]->println("command-received"); // Acknowledgement
        } /* ---------------- Botton 2 ---------------- */
       
        else if (msg == 's') { // ---------------- Button 4 (Button 1 to 3 are reserved for legacy version)
          clients[VRInd]->println("ready-to-change"); // Acknowledgement
          delay(200);
          
          String msgValue = clients[VRInd]->readStringUntil('\r');
          clients[VRInd]->flush();
          
          if(DEBUG_MOD){Serial.println(msgValue);}
          
          if(msgValue.substring(0,2) == "Vo") {
            voltageLevel = msgValue.substring(3,6).toInt();
      
            PWMGain = 255*voltageLevel/100;
          }
      
          if(msgValue.substring(7,9) == "Fr") {
            freq = msgValue.substring(10,13).toInt();
          }
      
          if(msgValue.substring(14,16) == "Ti") {
            vibTime = msgValue.substring(17,21).toInt();
          }
      
          /* Safety check */
          if ((chargeDuration > 4000) || (chargeDuration < 0)) {
              chargeDuration = 0;
          }
          if ((dischargeDuration > 4000) || (dischargeDuration < 0)) {
              dischargeDuration = 0;
          }
          if ((freq > 1000) || (freq < 0)) {
              freq = 0;
          }
          if ((vibTime > 4000) || (vibTime < 0)) {
              vibTime = 0;
          }
          clients[VRInd]->println("setting-changed"); // Acknowledgement for second-level command
          if(DEBUG_MOD){Serial.print("PC: "); Serial.println(PWMGain); Serial.println(freq); Serial.println(vibTime);}
          // Serial.println(chargeDuration); Serial.println(dischargeDuration);}           
        } /* ---------------- Botton 4 ---------------- */
      
        else if (msg == 'n') { // ---------------- Button 5
            if(DEBUG_MOD){Serial.print("VR: Pressed button5 charge PWM = "); Serial.println(PWMGain);}
      
            digitalWrite(PWM1, LOW);
            delay(1);
            PWMVoltageOut(PWM0, chargeDuration, voltageLevel);
            digitalWrite(PWM0, LOW);
            delay(1);  
                     
            clients[VRInd]->println("command-received"); // Acknowledgement
          } /* ---------------- Botton 5 ---------------- */
      
          else if (msg == 'f') { // ---------------- Button 6
            if(DEBUG_MOD){Serial.println("VR: Pressed button6 discharge");}

            digitalWrite(PWM0, LOW);
            delay(1);
            digitalWrite(PWM1, HIGH); // Note the potential risk when using bipolar actuation
      
            clients[VRInd]->println("command-received"); // Acknowledgement
          } /* ---------------- Botton 6 ---------------- */

          else if (msg == 'w') { // ---------------- Button 7 (Start vibration with discharging)
            if(DEBUG_MOD){Serial.print("VR: Pressed button7 Vibration (Discharge) "); Serial.print(" , Freq="); Serial.print(freq); Serial.print(" , Vib.Time="); Serial.println(vibTime);}      
            
            vibrationOutD(vibTime, freq);

            clients[VRInd]->println("command-received"); // Acknowledgement       
          } /* ---------------- Botton 7 ---------------- */

          else if (msg == 'x') { // ---------------- Button 8 (Start vibration without discharging)
            if(DEBUG_MOD){Serial.print("VR: Pressed button8 Vibration "); Serial.print(" , Freq="); Serial.print(freq); Serial.print(" , Vib.Time="); Serial.println(vibTime);}

            // vibrationOut(vibTime, freq);
            
            clients[VRInd]->println("command-received"); // Acknowledgement sent to VR headset     
          } /* ---------------- Botton 8 ---------------- */

          else if (msg == 'd') { // ------------- Data streaming         
            delay(100);
            if(DEBUG_MOD){Serial.println("Data Saved");}  
            delay(400);
            clients[VRInd]->println("data-received"); // Acknowledgement sent to VR headset (Only for compatibility with legacy build)                              
          } /* ---------------- Stream data ---------------- */         
      } /* ---------------- VR client ready and available ---------------- */      
    } /* ---------------- VR client is connected ---------------- */  
  }/* ---------------- All clients ready ---------------- */

  /* When any connection is lost, stop all connection and reset all status */
  digitalWrite(PWM0, LOW);
  digitalWrite(PWM1, LOW); // Ensure all PWM port is closed 
  
  for (int cl_i = 0 ; cl_i < MAX_CLIENT_NUM ; ++cl_i) // Stop all client if one lost its connection
  {
    if (clients[cl_i] != NULL) 
    {
        clients[cl_i]->stop();
        clients[cl_i] = NULL;
    }
  }
  clientNum = 0;
  isVRReady = false;
  VRInd = -1;

  if(DEBUG_MOD){Serial.println("All clients disconnected");}
}