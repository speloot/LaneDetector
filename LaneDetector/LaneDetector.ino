#include <Arduino.h>
#include <AFMotor.h>

class CarRunner {
  /*
  Stateful controller for the cars speed.

  The car has a serious issue with dead zone and hysteresis on the motors,
  and so this class gives the motors small bursts of speed if the desired speed
  is lower than the minimum continuous motor speed.
  */
  int counter = 0;
  const int counterPeriod = 1;  // period for updating counter. milliseconds. prefer power of 2, since it's used in division
  long lastCounterUpdate = 0;
  int threshold = 100;

  boolean run = true;  // flag for toggling operation
  boolean timeout = false;  // flag for timeout detection
  long timeout_time = 1000;  // milliseconds
  long lastCommand = 0;  // contains time for last received message

  int leftSpeed = 0;
  int rightSpeed = 0;

  AF_DCMotor* FR; // create motor #4, 1KHz pwm
  AF_DCMotor* FL; // create motor #3, 1KHz pwm
  AF_DCMotor* RR; // create motor #1, 2KHz pwm
  AF_DCMotor* RL; // create motor #2, 2KHz pwm

  public: CarRunner(){
    FR = new AF_DCMotor(1, MOTOR12_1KHZ); // create motor #4, 1KHz pwm
    FL = new AF_DCMotor(2, MOTOR12_1KHZ); // create motor #3, 1KHz pwm
    RR = new AF_DCMotor(4, MOTOR34_1KHZ); // create motor #1, 2KHz pwm
    RL = new AF_DCMotor(3, MOTOR34_1KHZ); // create motor #2, 2KHz pwm
    lastCommand = millis();
  }


  public: void runCar(){
    /*
    Main function for running the car.

    Increases a counter loop. If the counter is
    below the speed value, the actual output speed is set to the minimum
    functioning speed. The time the counter spends below the speed
    value is linear with the speed value, and so the speed actually achieved
    is still a linear function of the speed input.
    */
    int leftWheelOut = leftSpeed;
    int rightWheelOut = rightSpeed;
    
    counter++;
    if (counter > threshold){
      counter = 0;
    }
    
    if(leftSpeed < threshold){
      if(counter < leftSpeed)  {
        leftWheelOut = threshold;  // set speed to minimum functioning
      } else {
        leftWheelOut = 0;
      } 
    } else leftWheelOut = leftSpeed;
    
    if(rightSpeed < threshold) {
      if(counter < rightSpeed)  {
        rightWheelOut = threshold;  // set speed to minimum functioning
      } else {
        rightWheelOut = 0;
      } 
    } else {
      rightWheelOut = rightSpeed;
    }

    if(millis() > lastCommand + timeout_time){
      timeout = true;
    } else {
      timeout = false;
    }
    if (run and not timeout){
      FL->setSpeed(abs(leftWheelOut));
      RL->setSpeed(abs(leftWheelOut));
      FR->setSpeed(abs(rightWheelOut));
      RR->setSpeed(abs(rightWheelOut));
      
      if(leftWheels > 0) {
        FL->run(FORWARD);
        RL->run(FORWARD);
        }
      else {
        FL->run(BACKWARD);
        RL->run(BACKWARD);
        }
  
     if(rightWheels > 0) {
        FR->run(FORWARD);
        RR->run(FORWARD);
        } 
     else {
        FR->run(BACKWARD);
        RR->run(BACKWARD);
    }
      /*
      FL->run(FORWARD);
      RL->run(FORWARD);
      FR->run(FORWARD);
      RR->run(FORWARD);
      */
    }
  }
  public: void setSpeed(short leftWheels, short rightWheels){
    /*
    Setter for motor speeds. Also updates timeout timer.
    */
    leftSpeed = leftWheels;
    rightSpeed = rightWheels;
    lastCommand = millis();
  }
};

int initialSpeed = 100;
CarRunner car = CarRunner();
// Create an array of 3
int incomingByte[3];


long lastCommandMillis = 0;
int timeout = 1000;
void setup()
{
  Serial3.begin(115200);          // Rpi port
  Serial.begin(115200);           // Arduino port
  car.setSpeed(0,0);
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
      car.setSpeed(0,0);
      //Serial.println("no signal from Rpi! \n");
     }
     else
     {
       Serial.println(incomingByte[0]);
       Serial.println(incomingByte[1]);
       //car.setSpeed(incomingByte[1], incomingByte[0]);
       car.setSpeed(0, 0);
     }
     car.runCar();
  }

}




