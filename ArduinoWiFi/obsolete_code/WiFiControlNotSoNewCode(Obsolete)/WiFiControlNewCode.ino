#include <WiFiNINA.h>
/************Board Configuration************/
#define DAC A0 // Reserved analog output pin
/*Note: PWM pin 1 is reserved for relay!*/
#define PWM0 3 // The PWM pin used to control optocoupler 0
#define PWM1 4 // The PWM pin used to control optocoupler 1
#define PWM2 5 // The PWM pin used to control optocoupler 2
#define PWM3 6 // The PWM pin used to control optocoupler 3

#define VOLT_LEVEL_NUM 4 // Number of voltage levels 

#define DEBUG_MOD true // Debug mode will print to USB COM port

char ssid[] = "HVCtrl";        // your network SSID (name)
char pass[] = "1234";    // your network password (use for WPA, or use as key for WEP)

bool isConnected = false;

int status = WL_IDLE_STATUS;

float chargeDuration = 800; // Activation duration of positive voltage for zipping (Unit: ms)
float dischargeDuration = 250; // Activation duration of negative voltage for discharging (Unit: ms)

int voltageLevel = 0; // Range from 0 to 100 (Unit: %)
uint8_t PWMGain = 0; // Range from 0 to 255

WiFiServer server(80); // web server on port 80

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
  //if(DEBUG_MOD){Serial.println("Access Point Web Server");}

  if (WiFi.status() == WL_NO_MODULE) {
    //if(DEBUG_MOD){Serial.println("Communication with WiFi module failed!");}
    while (true); // don't continue
  }

  status = WiFi.beginAP(ssid, pass);
  if (status != WL_AP_LISTENING) {
    //if(DEBUG_MOD){Serial.println("Creating access point failed");}
    while (true); // don't continue
  }
  // wait 1 seconds for connection:
  delay(1000);

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
  // compare the previous status to the current status
  if (status != WiFi.status()) {
    // it has changed update the variable
    status = WiFi.status();
  }

  WiFiClient client = server.available();   // listen for incoming clients

  if (client) {                             // if you get a client,
    if(DEBUG_MOD){Serial.println("New client");}

    String currentLine = "";                // make a String to hold incoming data from the client
    while (client.connected()) {            // loop while the client's connected
      if (client.available()) { 
        /* ---------------- Receive a message ---------------- */
        char msg = client.read(); // Faster way to communicate
        if(DEBUG_MOD){Serial.println(msg);}
        /* ---------------- GUI Unconnected ---------------- */
        if ((msg == 'q') && !isConnected) {    
          client.println("high-voltage-controller-is-ready");
          isConnected = true;
        }

        /* ---------------- GUI Connected ---------------- */
        if (isConnected) { // Connection established, program starts
          if (msg == 'b') { // ---------------- Button 1
            if(DEBUG_MOD){Serial.print("Pressed button1 Both PWM = "); Serial.println(PWMGain);}   

            float indiDuration = chargeDuration*0.2;

            for(int indi_i = 0; indi_i < 5; indi_i++) {
              analogWrite(PWM2, 0);
              analogWrite(PWM0, PWMGain);
              delay(indiDuration);
              
              analogWrite(PWM0, 0);
              analogWrite(PWM2, PWMGain);
              delay(indiDuration);
            }
            analogWrite(PWM0, 0);
            analogWrite(PWM2, 0);
            delay(1);

            indiDuration = dischargeDuration*0.2;
            for(int indi_i = 0; indi_i < 5; indi_i++) {
              analogWrite(PWM3, 0);
              analogWrite(PWM1, PWMGain);
              delay(indiDuration);
              
              analogWrite(PWM1, 0);
              analogWrite(PWM3, PWMGain);
              delay(indiDuration);
            }
            analogWrite(PWM1, 0);
            analogWrite(PWM3, 0);
            delay(1);

            client.println("command-received"); // Acknowledgement
          } /* ---------------- Botton 1 ---------------- */
          
          else if (msg == 'l') { // ---------------- Button 2
            if(DEBUG_MOD){Serial.print("Pressed button2 Left PWM = "); Serial.println(PWMGain);}

            analogWrite(PWM0, PWMGain);
            delay(chargeDuration);
            analogWrite(PWM0, 0);
            delay(1);
            
            analogWrite(PWM1, PWMGain);
            delay(dischargeDuration);
            analogWrite(PWM1, 0);
            delay(1); 

            client.println("command-received"); // Acknowledgement
          } /* ---------------- Botton 2 ---------------- */
          
          else if (msg == 'r') { // ---------------- Button 3
            if(DEBUG_MOD){Serial.print("Pressed button3 Right PWM = "); Serial.println(PWMGain);}

            analogWrite(PWM2, PWMGain);
            delay(chargeDuration);
            analogWrite(PWM2, 0);
            delay(1);
            
            analogWrite(PWM3, PWMGain);
            delay(dischargeDuration);
            analogWrite(PWM3, 0);
            delay(1); 

            client.println("command-received"); // Acknowledgement
          } /* ---------------- Botton 3 ---------------- */
          
          else if (msg == 's') { // ---------------- Button 4
            //client.println("ready-to-change"); // Acknowledgement
            client.println("command-received"); // Acknowledgement for second-level command

            delay(100);
            
            String msgValue = client.readStringUntil('\r');
            client.flush();
            if(DEBUG_MOD){Serial.println(msgValue);}
            
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
            //client.println("setting-changed"); // Acknowledgement for second-level command
            client.println("command-received"); // Acknowledgement for second-level command
            if(DEBUG_MOD){Serial.println(PWMGain); Serial.println(chargeDuration); Serial.println(dischargeDuration);}           
          } /* ---------------- Botton 4 ---------------- */


          else if (msg == 'n') { // ---------------- Button 5
            if(DEBUG_MOD){Serial.print("Pressed button5 charge PWM = "); Serial.println(PWMGain);}

            analogWrite(PWM1, 0);
            delay(1);
            analogWrite(PWM0, PWMGain);
            delay(chargeDuration);
            analogWrite(PWM0, 0);
            delay(1);  
                     
            client.println("command-received"); // Acknowledgement
          } /* ---------------- Botton 5 ---------------- */

          else if (msg == 'f') { // ---------------- Button 6
            if(DEBUG_MOD){Serial.print("Pressed button6 discharge PWM = "); Serial.println(PWMGain);}
            
            analogWrite(PWM1, PWMGain);

            client.println("command-received"); // Acknowledgement
          } /* ---------------- Botton 6 ---------------- */
          
        } /* ---------------- GUI available ---------------- */
      } /* ---------------- client available ---------------- */
    } /* ---------------- client connected ---------------- */

    analogWrite(PWM1, 0); // Ensure all PWM port is closed 
    analogWrite(PWM0, 0);
    
    client.stop();
    isConnected = false;
    if(DEBUG_MOD){Serial.println("client disconnected");}
  }
}
