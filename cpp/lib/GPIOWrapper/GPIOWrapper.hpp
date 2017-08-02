#ifndef GPIO_WRAPPER_HPP_
#define GPIO_WRAPPER_HPP_

#include <string>

namespace GPIOWrapper { 

    enum PINMODE {
        INPUT = 0,
        OUTPUT = 1
    };

    enum PINVALUE {
        LOW = 0,
        HIGH = 1
    };

    enum EDGEVALUE {
        NONE = 0,
        RISING = 1,
        FALLING = 2,
        BOTH = 3
    };
    
    int getPin(std::string name);
    int setupPin(unsigned int pin);
    int setupPin(std::string pin);
    int setupPin(unsigned int pin, PINMODE mode);
    int setupPin(std::string pin, PINMODE mode);
    int closePin(unsigned int pin);
    int closePin(std::string pin);
    int setMode(unsigned int pin, PINMODE mode);
    int setMode(std::string pin, PINMODE mode);
    int getMode(unsigned int pin); 
    int getMode(std::string pin); 
    int setValue(unsigned int pin, PINVALUE value);
    int setValue(std::string pin, PINVALUE value);
    int getValue(unsigned int pin);
    int getValue(std::string pin);
    int waitForEdge(unsigned int pin, EDGEVALUE edge);
    int registerInterrupt(unsigned int pin, EDGEVALUE edge, void (*function)(void));

} /* namespace GPIOWrapper */
#endif  // GPIO_WRAPPER_HPP_
