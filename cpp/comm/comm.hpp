#ifndef COMM_COMM_HPP
#define COMM_COMM_HPP

#include "comm/msgProcessor.hpp"
#include "comm/commProcessor.hpp"
#include "comm/msgParser.hpp"
#include "comm/radio.hpp"
#include <vector>

namespace comm {

    class Comm {

        public:
            /**
             * Radio.
             */
            Radio * radio;

            /**
             * Message parser.
             */
            MsgParser * msgParser;
            
            /**
             * Comm processor.
             */
            CommProcessor * commProcessor;
            
            /**
             * Command relay buffer
             */
            std::vector< std::vector<uint8_t> > cmdRelayBuffer;

            /**
             * Time last message was sent.
             */
            double lastMsgSentTime;
            
            /**
             * Message sent counter.
             */
            unsigned int msgCounter;

            /**
             * Default constructor.
             */
            Comm() {};

            /**
             * Constructor.
             * @param commProcessorIn Comm message processor.
             * @param radioIn Radio to send/receive messages.
             * @param msgParserIn Message parser.
             */ 
            Comm(CommProcessor * commProcessorIn, Radio * radioIn, MsgParser * msgParserIn);
            
            /**
             * Send bytes in radio tx buffer.
             */
            void sendBuffer();
            
            /**
             * Perform communication operations.
             */
            void execute();
            
            /**
             * Read from radio and attempt to parse any data received.
             */
            virtual void readMsgs();

            /**
             * Parse messages in radio rx buffer.
             */
            void parseMsgs();
            
            /**
             * Read bytes from radio.
             * @param bufferFlag Flag to add new data to existing buffer.
             */
            void readBytes(bool bufferFlag);

            /**
             * Send bytes using radio
             * @param msgBytes Message bytes to send.
             */
            void sendBytes(std::vector<uint8_t> & msgBytes);

            /**
             * Format bytes into a message and send.
             * @param msgBytes Message bytes to encode and send.
             */
            void sendMsg(std::vector<uint8_t> & msgBytes);

            /**
             * Create and buffer a message for transmission.
             * @param msgBytes Message bytes to encode and buffer.
             */
            void bufferTxMsg(std::vector<uint8_t> & msgBytes);

            /**
             * Process parsed message.
             * @param msg Message to process.
             * @param args Arguments to use for message processing.
             * @return Returns -1 if message is not processed.
             */
            virtual int processMsg(std::vector<uint8_t> & msg, MsgProcessorArgs & args);
            
            /**
             * Read and process any received messages.
             */
            virtual void processMsgs(MsgProcessorArgs & args);

    };

}

#endif // COMM_COMM_HPP
