#ifndef COMM_RADIO_HPP
#define COMM_RADIO_HPP

#include <string>
#include <vector>
#include <cstdint>

#include "comm/defines.hpp"
#include "comm/message.hpp"

namespace comm {
    
    enum RadioMode {
        OFF = 0,
        SLEEP = 1,
        RECEIVE = 2,
        TRANSMIT = 3
    };

    struct RadioConfig {

        /**
         * Number of bytes to attempt to read from radio.
         */
        unsigned int numBytesToRead;

        /**
         * Receive buffer size.
         */
        unsigned int rxBufferSize;

        /**
         * Received commands buffer size.
         */
        unsigned int cmdRxBufferSize;

        /**
         * Default constructor.
         */
        RadioConfig() :
            numBytesToRead(100),
            rxBufferSize(500),
            cmdRxBufferSize(1000)
        {};

        /**
         * Constructor with provided inputs.
         * @param numBytesToReadIn Maximum bumber of bytes to attempt to read from radio.
         * @param rxBufferSizeIn Receive buffer size.
         * @param cmdRxBufferSizeIn Received commands buffer size.
         */
        RadioConfig(unsigned int numBytesToReadIn, unsigned int rxBufferSizeIn, unsigned int cmdRxBufferSizeIn) :
            numBytesToRead(numBytesToReadIn),
            rxBufferSize(rxBufferSizeIn),
            cmdRxBufferSize(cmdRxBufferSizeIn)
        {};

    };

    class Radio {

        public:
            /**
             * Current radio mode.
             */
            RadioMode mode;

            /**
             * Radio configuration settings.
             */
            RadioConfig config; 

            /**
             * Buffer of received bytes.
             */
            std::vector<uint8_t> rxBuffer;

            /**
             * Buffer of bytes to send.
             */
            std::vector<uint8_t> txBuffer;

            /**
             * This function sets the radio mode.
             * @param modeIn Radio mode to set.
             * @return True on successful mode change.
             */
            bool setMode(RadioMode modeIn);

            /**
             * This function sets the radio mode to OFF.
             * @return True on successful mode change.
             */
            virtual bool setOff(void);

            /**
             * This function sets the radio mode to SLEEP.
             * @return True on successful mode change.
             */
            virtual bool setSleep(void);

            /**
             * This function sets the radio mode to RECEIVE.
             * @return True on successful mode change.
             */
            virtual bool setReceive(void);

            /**
             * This function sets the radio mode to TRANSMIT.
             * @return True on successful mode change.
             */
            virtual bool setTransmit(void);

            /**
             * Default constructor.
             */
            Radio() {};

            /**
             * Constructor.
             * @param configIn Radio configuration.
             */
            Radio(RadioConfig & configIn);

            /**
             * This function clears the receive buffer.
             */
            void clearRxBuffer(void);

            /**
             * This function clears the receive buffer.
             * @param bufferFlag Whether or not to buffer new bytes or replace existing.
             * @param bytesToRead Number of bytes to attempt to read.
             * @return Returns number of new bytes buffered.
             */
            virtual int readBytes(bool bufferFlag, int bytesToRead = 65536);

            /**
             * This function processes newly received bytes.
             * @param newBytes Bytes to process.
             * @param bufferFlag Whether or not to buffer new bytes or replace existing.
             * @return Returns number of new bytes buffered.
             */
            virtual int processRxBytes(std::vector<uint8_t> & newBytes, bool bufferFlag);

            /**
             * This function stores bytes into the receive buffer.
             * @param newBytes Bytes to buffer.
             * @param bufferFlag Whether or not to buffer new bytes or replace existing.
             * @return Returns number of new bytes buffered.
             */
            int bufferRxMsg(std::vector<uint8_t> & newBytes, bool bufferFlag);

            /**
             * This function returns the bytes currently in the receive buffer.
             * @return Returns vector of bytes currently in receive buffer.
             */
            std::vector<uint8_t> getRxBytes(void);

            /**
             * This function stores bytes into the transmit buffer.
             * @param msgBytes Bytes to add to transmit buffer.
             */
            void bufferTxMsg(std::vector<uint8_t> & msgBytes);

            /**
             * This function sends bytes over the radio connetion.
             * @param msgBytes Bytes to send.
             * @return Returns number of messages sent.
             */
            virtual unsigned int sendMsg(std::vector<uint8_t> & msgBytes);

            /**
             * This function sends a message over the radio connetion.
             * @param msg Message to send.
             * @return Returns number of messages sent.
             */
            virtual unsigned int sendMsg(Message & msg);
            
            /**
             * This function creates a message for serial transmission.
             * @param msgBytes Bytes to create message from.
             * @return Returns message.
             */
            virtual std::vector<uint8_t> createMsg(std::vector<uint8_t> msgBytes);

            /**
             * This function sends the bytes currently in the transmit buffer.
             * @param maxBytesToSend Maximum number of bytes to send from buffer.
             * @return Returns 1 if only part of the buffer is sent.
             */
            unsigned int sendBuffer(unsigned int maxBytesToSend = 0);
    };
}
#endif // COMM_RADIO_HPP
