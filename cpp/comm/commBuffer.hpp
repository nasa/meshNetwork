#ifndef COMM_COMM_BUFFER_HPP
#define COMM_COMM_BUFFER_HPP

#include <vector>
#include <deque>
#include <cstdint>
#include <algorithm>

namespace comm {

    template<typename T>
    class CommBuffer {

        public:
            /**
             * Maximum size of buffer.
             */
            unsigned int maxSize;

            /**
             * This function adds data to the back of the deque.
             */
            void push(T entry) {
                if (buffer.size() >= maxSize) {
                    unsigned int extraEntries = buffer.size() - maxSize;
                    for (unsigned int i = 0; i <= extraEntries; i++) {
                        buffer.pop_front(); // Remove entry(ies) before adding new data
                    }
                }

                // Queue new data
                buffer.push_back(entry);
            };

            /**
             * This functions pops data from the front of the deque.
             @return Returns first element in the deque.
             */
            T pop(void) {
                T retValue = buffer.front();
                buffer.pop_front(); // remove returned entry
                return retValue;
            }

            /**
             * This function returns the current size of the buffer.
             */
            unsigned int size() {
                return buffer.size();
            }

            /**
             * This functions checks if the provided value is in the buffer.
             * @param value Value to search for.
             */
            bool find(T value) {
                typename std::deque<T>::iterator it = std::find(buffer.begin(), buffer.end(), value);
                if (it != buffer.end()) {
                    return true;
                }
                else {
                    return false;
                }
            }

            /**
             * Constructor.
             * @param maxSizeIn Maximum size;
             */
            CommBuffer<T> (unsigned int maxSizeIn) :
                maxSize(maxSizeIn)
            {}



        private:

            /*
             * Internal deque used to implement the buffer.
             */
            std::deque<T> buffer;

    };
}
#endif // COMM_COMM_BUFFER_HPP
