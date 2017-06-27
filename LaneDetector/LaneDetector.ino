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
    FR = new AF_DCMotor(1); // create motor #4, 1KHz pwm
    FL = new AF_DCMotor(2); // create motor #3, 1KHz pwm
    RR = new AF_DCMotor(4); // create motor #1, 2KHz pwm
    RL = new AF_DCMotor(3); // create motor #2, 2KHz pwm
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
    uint8_t leftWheelOut_U = abs(leftSpeed);
    uint8_t rightWheelOut_U = abs(rightSpeed);

    
    counter++;
    if (counter > threshold){
      counter = 0;
    }
    
    if(abs(leftSpeed) < threshold){
      if(counter < leftSpeed)  {
        leftWheelOut_U = threshold;  // set speed to minimum functioning
      } else {
        leftWheelOut_U = 0;
      } 
    } else leftWheelOut_U = (uint8_t)abs(leftSpeed);
    
    if(abs(rightSpeed) < threshold) {
      if(counter < rightSpeed)  {
        rightWheelOut_U = threshold;  // set speed to minimum functioning
      } else {
        rightWheelOut_U = 0;
      } 
    } else {
      rightWheelOut_U = (uint8_t)abs(rightSpeed);
    }

    if(millis() > lastCommand + timeout_time){
      timeout = true;
    } else {
      timeout = false;
    }
    if (run and not timeout){
      
      FL->setSpeed(leftWheelOut_U);
      RL->setSpeed(leftWheelOut_U);
      FR->setSpeed(rightWheelOut_U);
      RR->setSpeed(rightWheelOut_U);
      if(leftSpeed > 0) {
        FL->run(FORWARD);
        RL->run(FORWARD);
        }
      else {
        FL->run(BACKWARD);
        Serial.print(leftSpeed);
        Serial.print(leftWheelOut_U);
        RL->run(BACKWARD);
        }
  
     if(rightSpeed > 0) {
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
  public: void setSpeed(int leftWheels, int rightWheels){
    /*
    Setter for motor speeds. Also updates timeout timer.
    */
    leftSpeed = leftWheels;
    rightSpeed = rightWheels;
    lastCommand = millis();
  }
};

int initialSpeed = 80;
CarRunner car = CarRunner();
// Create an array of 
int incomingByte;
int setPoint = 169;
float kp = 1.1;
float  pController;
int l_wheel = 0;
int leftW = 0;
int r_wheel = 0;
int rightW = 0;
signed int var = 0;
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
    if (Serial3.available()> 0)
     {
      
      while(true)
      {
        incomingByte = Serial3.parseInt();

        if(Serial3.read() == '\n')
        {
          lastCommandMillis = millis();
          break;
        }
      }
    }
    if (millis() - lastCommandMillis > timeout)
    {
      car.setSpeed(0,0);
      Serial.println("no signal from Rpi! \n");
     }
     else
     {
       Serial.println(incomingByte);
       
       pController = (kp * (setPoint - incomingByte));
       l_wheel = 0.7*initialSpeed - pController;
       r_wheel = 0.7*initialSpeed + pController;
       
       // limit range of PWM values to between -255 and 255 
       leftW  = constrain(l_wheel,  -255, 255);
       rightW = constrain(r_wheel, -255, 255);
       Serial.print("l_wheel: ");
       Serial.println(leftW);
       Serial.print("r_wheel ");
       Serial.println(rightW);
       car.setSpeed(leftW, rightW);
       //car.setSpeed(0, 0);
     }
     car.runCar();
  }






