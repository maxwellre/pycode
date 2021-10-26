#include <WiFiNINA.h>

char ssid[] = "HVCtrl";        // your network SSID (name)
char pass[] = "1234";    // your network password (use for WPA, or use as key for WEP)

bool isConnected = false;

int status = WL_IDLE_STATUS;
WiFiServer server(80); // web server on port 80

void setup() {
  Serial.begin(115200);
  delay(500); while (!Serial); // wait for serial port to connect. Needed for native USB port only

  Serial.println("Access Point Web Server");

  if (WiFi.status() == WL_NO_MODULE) {
    Serial.println("Communication with WiFi module failed!"); 
    while (true); // don't continue
  }

  status = WiFi.beginAP(ssid, pass);
  if (status != WL_AP_LISTENING) {
    Serial.println("Creating access point failed");
    while (true); // don't continue
  }
  // wait 1 seconds for connection:
  delay(1000);

  server.begin();
}

void loop() {
  // compare the previous status to the current status
  if (status != WiFi.status()) {
    // it has changed update the variable
    status = WiFi.status();
  }

  WiFiClient client = server.available();   // listen for incoming clients

  if (client) {                             // if you get a client,
    Serial.println("New client"); 

    String currentLine = "";                // make a String to hold incoming data from the client
    while (client.connected()) {            // loop while the client's connected
      if (client.available()) { 
        /* ---------------- Receive a message ---------------- */
        String msg = client.readStringUntil('\r');
        Serial.println(msg);
        client.flush();

        /* ---------------- GUI Unconnected ---------------- */
        if ((msg == "request-to-connect-high-voltage-controller") && !isConnected) {    
          client.println("high-voltage-controller-is-ready");
          isConnected = true;
        }

        /* ---------------- GUI Connected ---------------- */
        if (isConnected) { // Connection established, program starts
          if (msg == "button1-both") {
            Serial.println("Pressed button1");
            client.println("command-received"); // Acknowledgement
          }
          else if (msg == "button2-left") {
            Serial.println("Pressed button2");
            client.println("command-received"); // Acknowledgement
          }
          else if (msg == "button3-right") {
            Serial.println("Pressed button3");
            client.println("command-received"); // Acknowledgement
          }
        }
        
      } /* ---------------- client available ---------------- */
    } /* ---------------- client connected ---------------- */

    client.stop();
    isConnected = false;
    Serial.println("client disconnected");
  }
}
