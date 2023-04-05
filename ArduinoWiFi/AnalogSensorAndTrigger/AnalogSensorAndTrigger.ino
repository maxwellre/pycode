#include <WiFiNINA.h>

/************Board Configuration************/
#define TriggerPin 0 // The PWM pin used to control optocoupler 0

void setup() 
{
    pinMode(TriggerPin, OUTPUT); // Trigger will be sent from PIN0
    digitalWrite(TriggerPin, LOW); 

    pinMode(LED_BUILTIN, OUTPUT); // For LED signals
    digitalWrite(LED_BUILTIN, LOW);

    Serial.begin(115200); 
     
    while (!Serial) { delay(10); }// wait for serial monitor to open.
}

void loop() 
{
  if(Serial.available() > 0)
  {
    char serialData = Serial.read();
    Serial.print(serialData);

    if(serialData == 't')
    {
      digitalWrite(TriggerPin, HIGH);
      digitalWrite(LED_BUILTIN, HIGH);
      delay(500);
      digitalWrite(TriggerPin, LOW);
      digitalWrite(LED_BUILTIN, LOW);
      Serial.print('f');
    }
  }
  else
  {
    Serial.println(analogRead(A0));
  }
}
