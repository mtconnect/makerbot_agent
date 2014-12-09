/**
 * oscP5sendreceive by andreas schlegel
 * example shows how to send and receive osc messages.
 * oscP5 website at http://www.sojamo.de/oscP5
 */
 
import oscP5.*;
import netP5.*;
  
OscP5 oscP5;
NetAddress myRemoteLocation;

void setup() {
  size(400,400);
  frameRate(30);
  
  /* start oscP5, listening for incoming messages at port 12000 */
  oscP5 = new OscP5(this,10001);
  
  /* myRemoteLocation is a NetAddress. a NetAddress takes 2 parameters,
   * an ip address and a port number. myRemoteLocation is used as parameter in
   * oscP5.send() when sending osc packets to another computer, device, 
   * application. usage see below. for testing purposes the listening port
   * and the port of the remote location address are the same, hence you will
   * send messages back to this sketch.
   */
  myRemoteLocation = new NetAddress("127.0.0.1",10000);

  ChangeVelocity(450);
//  ToggleLed(true);
}


void draw() {
  background(0);  
  
//  println("down");
//  TogglePen(true);
//  ToggleLed(true);
//  delay(10);
//  println("up");
//  TogglePen(false);
//  ToggleLed(false);
//  delay(10);
}


void ChangeVelocity(float velocity) {
  // Only allow a range of velocities
  constrain(velocity,200,5000);

  OscMessage myMessage = new OscMessage("/velocity");
  myMessage.add(velocity);

  oscP5.send(myMessage, myRemoteLocation);
}

void ToggleLed(boolean state) {
  OscMessage myMessage = new OscMessage("/led");
  if (state == true) {
    myMessage.add(1);
  }
  else {
    myMessage.add(0);
  }

  oscP5.send(myMessage, myRemoteLocation);
}

void TogglePen(boolean state) {
  OscMessage myMessage = new OscMessage("/pen");
  if (state == true) {
    myMessage.add(1);
  }
  else {
    myMessage.add(0);
  }

  oscP5.send(myMessage, myRemoteLocation);
}

void Move(float x, float y) {
  OscMessage myMessage = new OscMessage("/move");
  
  myMessage.add(x);
  myMessage.add(y);

  oscP5.send(myMessage, myRemoteLocation);
}

void mouseClicked() {
  float x = map((float)constrain(mouseX, 0, width), 0.0, width, 0, 1);
  float y = map((float)constrain(mouseY, 0, height), 0.0, height,0, 1);
  
  Move(x,y);
}

void mouseDragged() {
  float x = map((float)constrain(mouseX, 0, width), 0.0, width, 0, 1);
  float y = map((float)constrain(mouseY, 0, height), 0.0, height,0, 1);
  
  Move(x,y);
}

/* incoming osc message are forwarded to the oscEvent method. */
void oscEvent(OscMessage theOscMessage) {
  /* print the address pattern and the typetag of the received OscMessage */
  print("### received an osc message.");
  print(" addrpattern: "+theOscMessage.addrPattern());
  println(" typetag: "+theOscMessage.typetag());
}
