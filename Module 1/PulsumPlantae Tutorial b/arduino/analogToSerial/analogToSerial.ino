/*  Analog to Serial Transmitter 
 *  Get analog data measures, send it by serial port.
 *  
 *  
 *  Material for the Pulsum Plantae Seminar
 *  by .interspecifics.
 */


// variables for incoming lectures
int dataA0;
int dataA1;
int dataA2;
unsigned long timer;

void setup() {
  // begin serial communications
  Serial.begin(115200);
  //Serial.println(F("Sending Analog Readings: "));
  //Serial.println("Done!\n");
}


void loop() {
  // make new readings
  dataA0 = analogRead(A0);
  dataA1 = analogRead(A1);
  dataA2 = analogRead(A2);
  // send data every 10ms, (Fsampling = 100Hz) 
  if((millis()-timer)>10){
    Serial.print(dataA0);
    Serial.print(",");
    Serial.print(dataA1);
    Serial.print(",");
    Serial.println(dataA2);
    timer = millis();  
  }
} 
