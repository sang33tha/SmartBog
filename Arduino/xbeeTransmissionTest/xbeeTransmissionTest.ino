#include <SoftwareSerial.h>

#include "DHT.h"
#include <stdlib.h>
#include <avr/wdt.h>            // library for default watchdog functions
#include <avr/interrupt.h>      // library for interrupts handling
#include <avr/sleep.h>          // library for sleep
#include <avr/power.h>

#define DHTPIN 7     
#define DHTTYPE DHT11 
#define RELAY_PIN 4     // Pin to switch on/off sensorss
#define SLEEP_PIN 5     // Connect to DTR on XBee adapter 


// RX: Arduino pin 2, XBee pin DOUT.  
// TX:  Arduino pin 3, XBee pin DIN
SoftwareSerial XBee(2, 3);

DHT dht(DHTPIN, DHTTYPE);
int count = 0;
int nbr_remaining; 

//pH sensor pin P0, Arduino Pin A0
//pH sensor pin G, Arduino Pin Gnd(Both G pins to Gnd)
//pH sensor pin V+, Arduino Pin 5V
const int analogInPin = A0; 
int sensorValue = 0; 
unsigned long int avgValue; 
float b;
float calibration=21.89;
int buf[10],temp;

// interrupt from watchdog
ISR(WDT_vect)
{
        wdt_reset();
}


void configure_wdt(void)
{
  cli(); // disable interrupts
  MCUSR = 0;                       
                                                                  
  WDTCSR |= 0b00011000;            
  WDTCSR = 0b01000000 | 0b100001; // delay interval 8 sec

  sei();  //enable interrupts
 
}

void sleep(int ncycles)
{  
  nbr_remaining = ncycles; // defines how many cycles should sleep
  set_sleep_mode(SLEEP_MODE_PWR_DOWN);
 
  power_adc_disable();
 
  while (nbr_remaining > 0){
    sleep_mode();
  
    // CPU is now asleep and program execution completely halts!
    // Once awake, execution will resume at this point if the
    // watchdog is configured for resume rather than restart
   
    // When awake, disable sleep mode
    sleep_disable();
    
    // we have slept one time more
    nbr_remaining = nbr_remaining - 1;
 
  }
 
  // put everything on again
  power_all_enable();
 
}


void setup() {
  pinMode(RELAY_PIN, OUTPUT);
  pinMode(SLEEP_PIN, OUTPUT);
  pinMode(3, OUTPUT);
  
  Serial.begin(9600);
  Serial.println("DHTxx test!");

  dht.begin();

  XBee.begin(9600);

  delay(1000);
  
  // configure the watchdog
  configure_wdt();

  Serial.println("Reset");
  
}

void loop() {
  Serial.println("Wake"); 
  digitalWrite(RELAY_PIN, HIGH);
  digitalWrite(SLEEP_PIN, LOW);
  
  delay(2000);

  char result[400]= ".";
  char tempBuffer[20];
  char humBuffer[20];
  char pHBuffer[20];
  char firstStr[20] = "Temp";
  
  int h = dht.readHumidity();
  double t = dht.readTemperature();
  
  if (isnan(h) || isnan(t)) {
    Serial.println("Failed to read from DHT sensor!");

    return;
  }

  dtostrf(t, 1+3, 1, tempBuffer);
  dtostrf(h, 1+3, 1, humBuffer);

  //Code for pH sensor
  for(int i=0;i<10;i++) 
  { 
   buf[i]=analogRead(analogInPin);
   delay(10);
  }
  for(int i=0;i<9;i++)
  {
   for(int j=i+1;j<10;j++)
   {
    if(buf[i]>buf[j])
    {
     temp=buf[i];
     buf[i]=buf[j];
     buf[j]=temp;
    }
   }
  }
  avgValue=0;
  for(int i=2;i<8;i++)
  avgValue+=buf[i];
  float pHVol=(float)avgValue*5.0/1024/6;
  float phValue = -5.70 * pHVol + calibration;
  Serial.print("sensor = ");
  Serial.println(phValue);
  dtostrf(phValue, 1+3, 1, pHBuffer);
  //delay(20);

  sprintf(result, "pH: %s, Temp: %s'C, Humidity: %s%%, Index:", pHBuffer, tempBuffer, humBuffer);
 
  sending(result);
  //Serial.write(h);
  XBee.write(t);
  delay(50);
  Serial.println("Sleeping");
  digitalWrite(SLEEP_PIN, HIGH);
  digitalWrite(3, LOW);
  digitalWrite(7, LOW);
  delay(1000);
  digitalWrite(RELAY_PIN, LOW);
  sleep(5);
 
}

uint16_t fletcher16(const uint8_t *data, size_t len)
{
    uint16_t sum1 = 0;
    uint16_t sum2 = 0;
    int index;
    
    for( index = 0; index < len; ++index )
    {
       sum1 = (sum1 + data[index]) % 255;
       sum2 = (sum2 + sum1) % 255;
    }
    
    return (sum2 << 8) | sum1;
}

char* concat(const char *s1, const char *s2)
{
    char *result = malloc(strlen(s1) + strlen(s2) + 1); // +1 for the null-terminator
    // in real code you will need to check for errors in malloc here
    strcpy(result, s1);
    strcat(result, s2);
    return result;
}

char* concatCheckSum(const char *s1, uint16_t sum)
{
    int len = strlen(s1) + 6;
    char *result = malloc(len); // +1 for the null-terminator
    sprintf(result, "%s%x%04x", s1, (count & 0xF), sum);
    return result;
}

void sending(uint8_t data[]) {
  boolean notSend = true; 
  while (notSend){
    digitalWrite(SLEEP_PIN, LOW);
    
    char test[10];
    sprintf(test, "%d", count);
    
    char* dataT = concat(&data[0], &test[0]);
  
    uint16_t sum16 = fletcher16(dataT, strlen(dataT));
    char* sendT = concatCheckSum(dataT, sum16);
    
    Serial.print("Sending\n");
    XBee.write(sendT);
    Serial.println(sendT);
    Serial.println(sum16);
  
    free(dataT);
  
    int waitTime = 0;
    String input = "";
    bool loading = true;
    delay(5000);  // Short waiting time for repsonse
    while (loading) {
      while (XBee.available()) {
        input += (char) XBee.read();
        if (input == "") {
          break;
        }
        if(input == "OK") {
          Serial.print(input+"\n");
          loading = false;
          notSend = false;
          break;
        }
      }
      if(loading && waitTime<30000) {
        waitTime++;
      }
      else {
        loading = false;
        Serial.print("Stop Reading\n");
      }
      
    }
  
    free(sendT);
    
    input="";
   
    if(notSend)
      delay(5000);
    else {
       count++;
      if (count > 99) {
        count = 0;
    }
    }
  }
  
}
