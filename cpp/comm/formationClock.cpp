#include "comm/formationClock.hpp"
#include "comm/utilities.hpp"
#include <thread>
#include "GPIOWrapper.hpp"
#include "comm/defines.hpp"

namespace comm {
    std::mutex FormationClock::timer_mutex;
    double FormationClock::tdmaTimerStart(0.0);
    double FormationClock::invalidOffset(127);

    FormationClock::FormationClock(bool referencedIn, double referenceTimeIn, std::string ppsPinIn) :
        referenced(referencedIn),
        referenceTime(referenceTimeIn)
    { 
        if (ppsPinIn.empty() == false) {
            ppsPin = GPIOWrapper::getPin(ppsPinIn); 
            GPIOWrapper::setupPin(ppsPin, GPIOWrapper::OUTPUT);
            monitorSyncPulse();
        } 
    }

    double FormationClock::getTime() {
        if (referenced == true) {
            return util::getTime() - referenceTime;
        }
        else {
            return util::getTime();
        }
    }

    double FormationClock::getTDMATimer() {
        std::lock_guard<std::mutex> lock(timer_mutex); // wait for lock if necessary
        double retValue = util::getTime() - tdmaTimerStart;
        return retValue;
    }
    
    void FormationClock::resetTDMATimer() {
        if (timer_mutex.try_lock()) {
            tdmaTimerStart = util::getTime();
            timer_mutex.unlock();
        }
    }

    double FormationClock::getOffset() {
        double offset = FormationClock::invalidOffset;
        util::getTimeOffset(util::PPS, offset);
        return offset;
    }

    void FormationClock::monitorSyncPulse() {

        if (HAS_GPIO) {
            auto pulseFunc = [this] () { 
                while (1) {
                    GPIOWrapper::waitForEdge(ppsPin, GPIOWrapper::RISING);
                    resetTDMATimer();
                }
            };
            // Start thread to monitor PPS signal
            //std::thread t(&FormationClock::watchPulse, this);
            std::thread t(pulseFunc);
            t.detach();
        }
        else if (IS_PI) {
            GPIOWrapper::registerInterrupt(ppsPin, GPIOWrapper::RISING, FormationClock::resetTDMATimer);   
        }
    }

/*    void FormationClock::watchPulse() {
        while (1) {
            GPIOWrapper::waitForEdge(ppsPin, GPIOWrapper::RISING);
            resetTDMATimer();
        }
    }*/
        
}
