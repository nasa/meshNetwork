#include "GPIOWrapper.hpp"
#include <wiringPi.h>

namespace GPIOWrapper {
    int setupPin(unsigned int pin, PINMODE mode) {
        return setMode(pin, mode);
    }

    int setMode(unsigned int pin, PINMODE mode) {
        if (mode == INPUT) {
            pinMode(pin, INPUT);
        }
        else {
            pinMode(pin, OUTPUT);
        }
        
        return 0;
    }


    int setValue(unsigned int pin, PINVALUE value) {
        digitalWrite(pin, value); 
        return 0;
    }

    int getValue(unsigned int pin) {
        return digitalRead(pin);
    }

    int registerInterrupt(unsigned int pin, EDGEVALUE edge, void(*function)(void)) {
        if (edge == NONE) {
            // Invalid value
            return -1;
        }
        else if (edge == RISING) {
            return wiringPiISR(pin, INT_EDGE_RISING, function);
        }
        else if (edge == FALLING) {
            return wiringPiISR(pin, INT_EDGE_FALLING, function);
        }
        else if (edge == BOTH) {
            return wiringPiISR(pin, INT_EDGE_BOTH, function);
        }
    }

    // Not implemented by wiringPi
    int getPin(std::string name) { return -1; };
    int setupPin(unsigned int pin) { return -1; };
    int setupPin(std::string pin) { return -1; };
    int setupPin(std::string pin, PINMODE mode) { return -1; };
    int closePin(unsigned int pin) { return -1; };
    int closePin(std::string pin) { return -1; };
    int setMode(std::string pin, PINMODE mode) { return -1; };
    int getMode(unsigned int pin) { return -1; };
    int getMode(std::string pin) { return -1; };
    int setValue(std::string pin, PINVALUE value) { return -1; };
    int getValue(std::string pin) { return -1; };
    int waitForEdge(unsigned int pin, EDGEVALUE edge) { return -1; };

}
        
