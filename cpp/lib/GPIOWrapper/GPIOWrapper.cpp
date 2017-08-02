#include "GPIOWrapper.hpp"

namespace GPIOWrapper {
    // Not implemented
    int setupPin(unsigned int pin, PINMODE mode) { return -1; };
    int setMode(unsigned int pin, PINMODE mode) { return -1; };
    int setValue(unsigned int pin, PINVALUE value) { return -1; };
    int getValue(unsigned int pin) { return -1; };
    int registerInterrupt(unsigned int pin, EDGEVALUE edge, void(*function)(void)) { return -1; };
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
        
