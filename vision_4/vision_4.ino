#include <Arduino.h>
#include <AFMotor.h>

// Motors 
AF_DCMotor FL(1, MOTOR12_1KHZ); // create motor #3, 1KHz pwm
AF_DCMotor FR(2, MOTOR12_1KHZ); // create motor #4, 1KHz pwm
 
AF_DCMotor RL(4, MOTOR34_1KHZ); // create motor #1, 2KHz pwm
AF_DCMotor RR(3, MOTOR34_1KHZ); // create motor #2, 2KHz pwm

int initialSpeed = 100;

// Create an array of 3
int incomingByte[3]; 


long lastCommandMillis = 0;
int timeout = 1000;
void setup()
{
  Serial3.begin(19200);          // Rpi port
  Serial.begin(19200);           // Arduino port
   
  FL.setSpeed(initialSpeed);     
  FR.setSpeed(initialSpeed);     
  RL.setSpeed(initialSpeed);     
  RR.setSpeed(initialSpeed);     
}

void loop()
{
  while(1)
  {
    if (Serial3.available() >= 3)
    {
      for(int i=0; i<3; i++)
      {
        incomingByte[i] = Serial3.read();
        
        if(incomingByte[i] == '\n')
        {
          lastCommandMillis = millis(); 
          break;
        }
      }
    }
    if (millis() - lastCommandMillis > timeout) 
    {
      runCar(0,0);
      Serial.println("no signal from Rpi! \n");
     }
     else
     {
       runCar(incomingByte[1], incomingByte[0]);
     }
  }
    
    //Serial.println(incomingByte[0]);
    //Serial.println(incomingByte[1]);
    
    
}



void runCar(short leftWheels, short rightWheels)
{
  FL.setSpeed(abs(leftWheels));
  RL.setSpeed(abs(leftWheels));
  FR.setSpeed(abs(rightWheels)); 
  RR.setSpeed(abs(rightWheels));
  
  FL.run(FORWARD);
  RL.run(FORWARD);
  FR.run(FORWARD);
  RR.run(FORWARD);
 
}
  

