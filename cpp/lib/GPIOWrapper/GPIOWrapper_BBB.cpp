#include "GPIOWrapper.hpp"
#include "BeagleBoneBlack-GPIO/GPIO/GPIOManager.h"
#include "BeagleBoneBlack-GPIO/GPIO/GPIOConst.h"

namespace GPIOWrapper {
    
    static GPIO::GPIOManager * gp = GPIO::GPIOManager::getInstance();

    int getPin(std::string name) {
        return GPIO::GPIOConst::getInstance()->getGpioByKey(name.c_str());
    }
    
    int setupPin(unsigned int pin) {
        return gp->exportPin(pin);
    }

    int setupPin(std::string pin) {
        int p = GPIO::GPIOConst::getInstance()->getGpioByKey(pin.c_str());
        return gp->exportPin(p);
    }
    
    int setupPin(unsigned int pin, PINMODE mode) {
        setupPin(pin);
        return setMode(pin, mode);
    }

    int setupPin(std::string pin, PINMODE mode) {
        int p = GPIO::GPIOConst::getInstance()->getGpioByKey(pin.c_str());
        setupPin(p);
        return setMode(p, mode);
    }

    int closePin(unsigned int pin) {
        return gp->unexportPin(pin);
    }

    int closePin(std::string pin) {
        int p = GPIO::GPIOConst::getInstance()->getGpioByKey(pin.c_str());
        return gp->unexportPin(p);
    }

    
    int setMode(unsigned int pin, PINMODE mode) {
        if (mode == INPUT) {
            return gp->setDirection(pin, GPIO::INPUT);
        }
        else {
            return gp->setDirection(pin, GPIO::OUTPUT);
        }
    }

    int setMode(std::string pin, PINMODE mode) {
        int p = GPIO::GPIOConst::getInstance()->getGpioByKey(pin.c_str());
        if (mode == INPUT) {
            return gp->setDirection(p, GPIO::INPUT);
        }
        else {
            return gp->setDirection(p, GPIO::OUTPUT);
        }
    }

    int getMode(unsigned int pin) {
        return gp->getDirection(pin);
    }

    int getMode(std::string pin) {
        int p = GPIO::GPIOConst::getInstance()->getGpioByKey(pin.c_str());
        return gp->getDirection(p);
    }

    int setValue(unsigned int pin, PINVALUE value) {
        if (value == HIGH) {
            return gp->setValue(pin, GPIO::HIGH);
        }
        else {
            return gp->setValue(pin, GPIO::LOW);
        }
    }

    int setValue(std::string pin, PINVALUE value) {
        int p = GPIO::GPIOConst::getInstance()->getGpioByKey(pin.c_str());
        if (value == HIGH) {
            return gp->setValue(p, GPIO::HIGH);
        }
        else {
            return gp->setValue(p, GPIO::LOW);
        }
    }

    int getValue(unsigned int pin) {
        return gp->getValue(pin);
    }

    int getValue(std::string pin) {
        int p = GPIO::GPIOConst::getInstance()->getGpioByKey(pin.c_str());
        return gp->getValue(p);
    }

    int waitForEdge(unsigned int pin, EDGEVALUE edge) {
        if (edge == NONE) {
            gp->setEdge(pin, GPIO::NONE);
            return gp->waitForEdge(pin, GPIO::NONE);
        }
        else if (edge == RISING) {
            gp->setEdge(pin, GPIO::RISING);
            return gp->waitForEdge(pin, GPIO::RISING);
        }
        else if (edge == FALLING) {
            gp->setEdge(pin, GPIO::FALLING);
            return gp->waitForEdge(pin, GPIO::FALLING);
        }
        else if (edge == BOTH) {
            gp->setEdge(pin, GPIO::BOTH);
            return gp->waitForEdge(pin, GPIO::BOTH);
        }
    }
    
    // Not implemented by BBB GPIO library
    int registerInterrupt(unsigned int pin, EDGEVALUE edge, void (*function)(void)) { return -1; };
}
        
