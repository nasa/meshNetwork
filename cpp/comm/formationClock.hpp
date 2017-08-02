#ifndef COMM_FORMATION_CLOCK_HPP
#define COMM_FORMATION_CLOCK_HPP

#include <string>
#include <mutex>

namespace comm {

    class FormationClock {

        public:

            /**
             * Invalid clock offset value;
             */
            static double invalidOffset;


            /**
             * This function resets the TDMA timer.
             */
            static void resetTDMATimer();

            /**
             * Constructor.
             * @param referenced Referenced clock flag.
             * @param referenceTime Time to initialize reference clock.
             * @param ppsPin GPIO pin to use for PPS.
             */
            FormationClock(bool referenced = false, double referenceTime = 0.0, std::string ppsPin = "");

            /**
             * This functions returns the current clock time.
             * @return Current clock time.
             */
            double getTime();

            /**
             * This function gets the current value of the TDMA timer.
             * @return Current TDMA timer value.
             */
            double getTDMATimer();

            /**
             * This function returns the current clock offset.
             * @return Returns the current clock offset.
             */
            double getOffset();

            /**
             * This function sets up time sync pulse monitoring for TDMA comm scheme.
             */
            void monitorSyncPulse();

        private:
            /**
             * Time that tdma timer was started.
             */
            static double tdmaTimerStart;

            /**
             * Mutex for accessing tdmaTimerStart variable.
             */
            static std::mutex timer_mutex;

            /**
             * Flag of whether clock is referenced from some provided time or just provides system clock time.
             */
            bool referenced;

            /**
             * Reference time for referenced clocks.
             */
            double referenceTime;

            /**
             * PPS pin number.
             */
            unsigned int ppsPin;

    };

}

#endif // COMM_FORMATION_CLOCK_HPP
