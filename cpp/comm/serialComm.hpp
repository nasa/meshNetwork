#ifndef COMM_SERIAL_COMM_HPP
#define COMM_SERIAL_COMM_HPP

#include "comm/comm.hpp"
#include "comm/msgProcessor.hpp"
#include <vector>
#include <string>
#include <cstdint>

namespace comm {

    class SerialComm : public Comm {

        public:
            /**
             * Time last message was sent.
             */
            double lastMsgSentTime;
            
            /**
             * Message sent counter.
             */
            unsigned int msgCounter;

            /**
             * Default constructor
             */
            SerialComm() {};

            /**
             * Constructor.
             * @param commProcessorIn Comm message processor.
             * @param radioIn Radio to send/receive messages.
             * @param msgParserIn Message parser.
             */ 
            SerialComm(CommProcessor * commProcessorIn, Radio * radioIn, MsgParser * msgParserIn);
            
            /**
             * Perform communication operations.
             */
            void execute();
            
            /**
             * Read bytes from serial.
             * @param bufferFlag Flag to add new data to existing buffer.
             */
            void readBytes(bool bufferFlag);

            /**
             * Read from radio and attempt to parse any data received.
             */
            virtual void readMsgs();

            /**
             * Parse messages in radio rx buffer.
             */
            void parseMsgs();

            /**
             * Create and buffer a message for transmission.
             * @param msgBytes Message bytes to encode and buffer.
             */
            void bufferTxMsg(std::vector<uint8_t> msgBytes);
        
            /**
             * Process parsed message.
             * @param msg Message to process.
             * @param args Arguments to use for message processing.
             * @return Returns -1 if message is not processed.
             */
            virtual int processMsg(std::vector<uint8_t> msg, MsgProcessorArgs & args);
            
    };

}

#endif // COMM_SERIAL_COMM_HPP
