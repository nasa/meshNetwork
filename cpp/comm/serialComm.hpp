#ifndef COMM_COMM_HPP
#define COMM_COMM_HPP

#include "comm/msgProcessor.hpp"
#include "comm/msgParser.hpp"
#include "comm/radio.hpp"
#include "comm/command.hpp"
#include <vector>
#include <unordered_map>
#include <memory>

namespace comm {

    class SerialComm {

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
            //CommProcessor * commProcessor;
            
            /**
             * Message processors.
             */
            std::vector<MsgProcessor *> msgProcessors;

            /**
             * Command queue.
             */
            //std::unordered_map<uint8_t, Command> cmdQueue;
            std::unordered_map<uint8_t, std::vector<uint8_t> > cmdQueue;

            /**
             * Buffer of commands to send.
             */
            std::unordered_map<uint8_t, std::vector<uint8_t> > cmdBuffer;

            /**
             * Command relay buffer
             */
            std::vector<uint8_t> cmdRelayBuffer;

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
            SerialComm() {};

            /**
             * Constructor.
             * @param msgProcessorsIn Vector of message processors.
             * @param radioIn Radio to send/receive messages.
             * @param msgParserIn Message parser.
             */ 
            SerialComm(std::vector<MsgProcessor *> msgProcessorsIn, Radio * radioIn, MsgParser * msgParserIn = NULL);
            
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
            virtual bool readMsgs();

            /**
             * Parse messages in radio rx buffer.
             */
            void parseMsgs();
            
            /**
             * Read bytes from radio.
             * @param bufferFlag Flag to add new data to existing buffer.
             */
            void readBytes(bool bufferFlag = false);

            /**
             * Send bytes using radio
             * @param msgBytes Message bytes to send.
             * @return Returns number of bytes sent.
             */
            unsigned int sendBytes(std::vector<uint8_t> & msgBytes);

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
             * This function processes received and parsed serial messages.
             * @param msg The parsed bytes of a message.
             * @param args Arguments to use when processing the message.
             * @return Returns true if message processed successfully.
             */
            virtual bool processMsg(std::vector<uint8_t> & msg, MsgProcessorArgs args);

            
            /**
             * Read and process any received messages.
             * @param args Arguments to use when processing the message.
             */
            virtual void processMsgs(MsgProcessorArgs & args);
    
            /**
             * Process command buffers.
             */
            void processBuffers();

    };

}

#endif // COMM_COMM_HPP
