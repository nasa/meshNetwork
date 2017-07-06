-- dataParser.vhd
--
-- Parses and consolidates received mesh data before transmitting
-- to flight computer.
--
-- Chris Becker
-- NASA MSFC EV42
-- 10/18/2016

library ieee;
use ieee.std_logic_1164.all;
use ieee.std_logic_unsigned.all;
use ieee.numeric_std.all;
use work.meshPack.all;
use work.compDec.all;
use work.commandTypes.all;

entity dataParser is
    port (
        clk                 : in std_logic;
        rst                 : in std_logic;
        -- data in/out control/status
        dataInFifoWrEn      : in std_logic;
        dataIn              : in std_logic_vector(7 downto 0);
        dataOutFifoEmpty    : out std_logic;
        dataOutFifoRdEn     : in std_logic;
        dataOut             : out std_logic_vector(7 downto 0);   
        -- TDMA interface (TBD)
        tdmaInited          : in std_logic;
        tdmaInitTimeRcvd    : out std_logic;
        tdmaInitTime        : out integer range 0 to maxTimeSec

        
    );
end dataParser;

architecture behave of dataParser is
    type DataParserStates is (parserWait, dataInRdDelay, slipRdDelay, decodeSLIP, parseCmdId, parseSourceId, parseCmdCounter, parseBody, waitForValid); 
    signal dataParserState, nextParserState, nextMsgParserState : DataParserStates;
        
    -- FIFO signals
    signal dataInFifoOut : std_logic_vector(7 downto 0);  
    signal dataInFifoRdEn, dataInFifoFull, dataInFifoEmpty : std_logic;
    signal dataOutFifoIn : std_logic_vector(7 downto 0);  
    signal dataOutFifoWrEn, dataOutFifoFull : std_logic;
  
    -- SLIP control
    signal slipEnable, slipRst, slipRstIn, slipFifoRdEn, slipFifoEmpty, slipReady, slipValid, slipInvalid, slipError : std_logic;
    signal slipByteIn, slipByteOut : std_logic_vector( 7 downto 0);
    signal slipActionSel : slipAction;
    signal slipMsgPos : integer range 0 to slipMsgMaxLength;
    signal slipMsgLength : integer range 0 to slipMsgMaxLength;
    signal cnt : integer range 0 to 2 := 0;
    
    -- Current message info
    signal msgSourceId, msgCmdId : std_logic_vector(7 downto 0);
    signal msgCmdCounter : std_logic_vector(15 downto 0);
    signal msgBodyPos : integer range 0 to maxCmdSize;
    signal msgHeaderType : CmdHeaderType;
    
    -- State data message signals
    type StateTimeArray is array(0 to tdma_maxNumSlots) of std_logic_vector(31 downto 0);
    signal stateTimes : StateTimeArray; 
    
    -- TDMA
    signal initTime : integer range 0 to maxTimeSec;
    
    begin
        -- Populate command types            
    
        -- Received data fifo
        dataInFifo : uartFifo 
            port map ( 
                din     => dataIn,  
                dout 	=> dataInFifoOut, 
                wrEn 	=> dataInFifoWrEn, 
                rdEn 	=> dataInFifoRdEn, 
                clk  	=> clk,  
                full 	=> dataInFifoFull, 
                empty	=> dataInFifoEmpty,
                rst  	=> rst 
            );
                
        -- Parsed outgoing data fifo
        dataOutFifo : uartFifo 
            port map ( 
                din     => dataOutFifoIn,  
                dout 	=> dataOut, 
                wrEn 	=> dataOutFifoWrEn, 
                rdEn 	=> dataOutFifoRdEn, 
                clk  	=> clk,  
                full 	=> dataOutFifoFull, 
                empty	=> dataOutFifoEmpty,
                rst  	=> rst  
            );
        -- SLIP message instances
        slipMsg_i : slipMsg
            generic map(
                msgSize => 255
            )
            port map(
                clk             => clk,
                rst             => slipRstIn,
                byteIn          => slipByteIn,
                slipEnable      => slipEnable,
                slipActionSel   => slipActionSel,
                ready           => slipReady,
                msgValid        => slipValid,
                msgInvalid      => slipInvalid,
                msgOutByte      => slipByteOut,
                slipFifoRdEn    => slipFifoRdEn,
                slipFifoEmpty   => slipFifoEmpty,
                msgLengthOut    => slipMsgLength,
                slipError       => slipError
            );
  
            
        -- slipMsg_i : slipMsg
            -- generic map(
                -- msgSize => maxCmdSize
            -- )
            -- port map(
                -- clk             => clk,
                -- rst             => rst,
                -- byteIn          => slipByteIn,
                -- slipEnable      => slipEnable,
                -- slipActionSel   => slipActionSel,
                -- ready           => slipReady,
                -- msgEmpty        => slipEmpty,
                -- rawMsgEmpty     => slipRawEmpty,
                -- msgClear        => slipMsgClear,
                -- msgOutByte      => slipByteOut,
                -- msgLengthOut    => slipMsgLength,
                -- slipError       => slipError
            -- );
            
        -- Slip reset
        slipRstIn <= not slipRst;
        
        
        -- Data parsing state machine
        process(rst, clk)
            variable msgHeaderType_var : CmdHeaderType;
            variable initTimeTemp : std_logic_vector(31 downto 0);
            
            begin
                if (rst = '0') then
                    dataParserState <= parserWait;
                    nextParserState <= parseCmdId;
                    nextMsgParserState <= parseCmdId;
                    
                    -- Fifo control
                    dataInFifoRdEn <= '0';
                    dataOutFifoWrEn <= '0';
                    
                    -- Message parameters
                    msgHeaderType <= MinimalHeader;
                    msgCmdCounter <= X"0000";
                    
                    -- TDMA
                    tdmaInitTimeRcvd <= '0';
                    
                    cnt <= 1;
                    
                    -- SLIP
                    slipRst <= '1';
                    slipEnable <= '0';
                    slipFifoRdEn <= '0';
                    slipByteIn <= X"00";
                    
                    -- State message parameters
                    for i in 0 to tdma_maxNumSlots-1 loop
                        stateTimes(i) <= X"00000000";
                    end loop;

                
                elsif (clk'event and clk = '1') then                 
                    
                    case dataParserState is

                        when parserWait =>
                            slipRst <= '0'; -- clear slip reset
                            slipEnable <= '0'; -- clear previous slip action enable
                            --if (slipEmpty = '0' and slipReady = '1') then -- parse received message
                                -- slipEnable <= '1';
                                -- slipActionSel <= slipRead;
                                -- nextParserState <= parseMsg;
                                -- dataParserState <= slipDelay;
                            if (slipFifoEmpty = '0') then -- parse received message bytes
                                slipFifoRdEn <= '1';
                                dataParserState <= slipRdDelay;
                            elsif (dataInFifoEmpty = '0' and slipReady = '1') then -- pass data to slip parser
                                dataInFifoRdEn <= '1';
                                cnt <= 1;
                                dataParserState <= dataInRdDelay;
                            elsif (nextParserState = waitForValid) then -- check for validity result
                                dataParserState <= waitForValid;
                            end if;
                            -- if (dataInFifoEmpty = '0') then -- bypass and pipe data back out
                                -- dataInFifoRdEn <= '1';
                                -- cnt <= 0;
                                -- dataParserState <= rdDelay;
                            -- elsif (dataInFifoEmpty = '0' and slipReady = '1') then -- pass data to slip parser
                                -- dataInFifoRdEn <= '1';
                                -- cnt <= 0;
                                -- dataParserState <= rdDelay;
                            --else
                            --    dataParserState <= temp;
                            --end if;
                        when dataInRdDelay => -- delay for fifo read
                            dataInFifoRdEn <= '0';
                            if (cnt >= 2) then
                                --dataParserState <= decodeSLIP;
                                -- Still forward all data to node
                                dataOutFifoWrEn <= '1';
                                dataOutFifoIn <= dataInFifoOut;
                                
                                -- Decode SLIP                     
                                dataParserState <= decodeSLIP;    
                                cnt <= 1;
                            else
                                cnt <= cnt + 1;
                            end if;
                            
                        when slipRdDelay => -- delay for SLIP fifo read
                            slipFifoRdEn <= '0';
                            if (cnt >= 2) then
                                dataParserState <= nextParserState;
                                cnt <= 1;
                            else
                                cnt <= cnt + 1;
                            end if;
                        
                        -- when bypassRawOut =>
                            -- dataOutFifoWrEn <= '0';
                            -- --tdmaOutFifoWrEn <= '0';
                            -- dataParserState <= parserWait;     
                        
                        -- SLIP processing
                        when decodeSLIP => -- pass byte to SLIP for parsing
                            dataOutFifoWrEn <= '0'; -- clear output fifo write enable
                            slipActionSel <= slipParse;
                            slipEnable <= '1';
                            slipByteIn <= dataInFifoOut;
                            dataParserState <= parserWait;
                        -- when slipDelay => -- cleanup slip action start
                            -- slipEnable <= '0';
                            -- slipMsgClear <= '0';
                            -- dataParserState <= nextParserState;
                            
                        -- -- Message processing
                        -- when parseMsg => -- parse received init time message
                            -- slipEnable <= '0';
                            -- if (slipEmpty = '1') then
                                -- slipMsgPos <= 0;
                                -- dataParserState <= temp;
                                -- nextMsgParserState <= parseCmdId;
                            -- elsif (slipReady = '1') then -- parse message contents
                                -- dataParserState <= nextMsgParserState;
                            -- end if;

                        when parseCmdId =>
                            if (slipInvalid = '1') then
                                slipMsgPos <= 1;
                                slipRst <= '1';
                                nextParserState <= parseCmdId;
                            else
                                msgCmdId <= slipByteOut;
                                msgHeaderType_var := getCmdHeaderType(slipByteOut);
                                msgHeaderType <= msgHeaderType_var;
                            
                                if (msgHeaderType_var = MinimalHeader) then -- end of header
                                    nextParserState <= parseBody;
                                    slipMsgPos <= 1;
                                elsif (msgHeaderType_var = InvalidHeader) then -- not a valid command
                                    slipRst <= '1';
                                else -- more header bytes
                                    nextParserState <= parseSourceId;
                                end if;
                            end if;
                            
                            dataParserState <= parserWait;
                            
                            
                        when parseSourceId =>
                            if (slipInvalid = '1') then
                                slipMsgPos <= 1;
                                slipRst <= '1';
                                nextParserState <= parseCmdId;
                            else
                                msgSourceId <= slipByteOut;
                            
                                if (msgHeaderType = SourceHeader) then -- end of header
                                    nextParserState <= parseBody;
                                    slipMsgPos <= 1;
                                else
                                    nextParserState <= parseCmdCounter;
                                    slipMsgPos <= 1;
                                end if;
                            end if;
                            dataParserState <= parserWait;
                       
                        when parseCmdCounter =>
                            if (slipInvalid = '1') then
                                slipMsgPos <= 1;
                                slipRst <= '1';
                                nextParserState <= parseCmdId;
                            else
                                if (slipMsgPos = 1) then
                                    msgCmdCounter(15 downto 8) <= slipByteOut;
                                    slipMsgPos <= 2;
                                elsif (slipMsgPos = 2) then
                                    msgCmdCounter(7 downto 0) <= slipByteOut;
                                    nextParserState <= parseBody;
                                    slipMsgPos <= 1;
                                end if;
                            end if;
                            
                            dataParserState <= parserWait;
                            
                        when parseBody =>
                            if (slipInvalid = '1') then
                                slipMsgPos <= 1;
                                slipRst <= '1';
                                nextParserState <= parseCmdId;
                                dataParserState <= parserWait;
                            elsif (msgCmdId = tdmaStatusCmdId) then
                                if (slipMsgPos = 1) then -- parse first byte of comm start time
                                    slipMsgPos <= slipMsgPos + 1;
                                    initTimeTemp := X"000000" & slipByteOut;
                                    initTime <= to_integer(unsigned(initTimeTemp));
                                    dataParserState <= parserWait;
                                elsif (slipMsgPos = 2) then -- second byte
                                    slipMsgPos <= slipMsgPos + 1;
                                    initTimeTemp := X"0000" & slipByteOut & X"00";
                                    initTime <= initTime + to_integer(unsigned(initTimeTemp));
                                    dataParserState <= parserWait;
                                elsif (slipMsgPos = 3) then -- third byte
                                    slipMsgPos <= slipMsgPos + 1;
                                    initTimeTemp := X"00" & slipByteOut & X"0000";
                                    initTime <= initTime + to_integer(unsigned(initTimeTemp));
                                    dataParserState <= parserWait;
                                elsif (slipMsgPos = 4) then -- final byte
                                    slipMsgPos <= 0;
                                    initTimeTemp := slipByteOut & X"000000";
                                    if (initTime + to_integer(unsigned(initTimeTemp)) <= maxTimeSec) then -- valid init time
                                        initTime <= initTime + to_integer(unsigned(initTimeTemp));
                                        nextParserState <= waitForValid;
                                        dataParserState <= waitForValid;
                                    else -- init time not valid
                                        slipMsgPos <= 0;
                                        slipRst <= '1';
                                        dataParserState <= parserWait;
                                    end if;
                                else -- bad message
                                    slipMsgPos <= 0;
                                    slipRst <= '1';
                                    dataParserState <= parserWait;
                                end if;        
                            else -- ignore other command types for now
                                slipMsgPos <= 0;
                                slipRst <= '1';
                                nextParserState <= parseCmdId;
                                dataParserState <= parserWait;
                            end if; 
                            --if (msgCmdId /= 111) then -- not a NodeStateUpdate command
                                -- nextMsgParserState <= parseCmdId;
                                -- dataParserState <= forwardRawData;
                            -- --else
                            
                            -- --end if;
                        
                        when waitForValid =>
                            if (slipValid = '1') then
                                slipMsgPos <= 1;
                                slipRst <= '1';
                                if (msgCmdId = tdmaStatusCmdId) then
                                    tdmaInitTimeRcvd <= '1';
                                    tdmaInitTime <= initTime;
                                end if;
                                nextParserState <= parseCmdId;
                                
                            elsif (slipInvalid = '1') then
                                slipMsgPos <= 1;
                                slipRst <= '1';
                                nextParserState <= parseCmdId;
                            end if;
                            
                            dataParserState <= parserWait;
                            
                            
                        
                        -- -- Forward raw data
                        -- when forwardRawData =>
                            -- if (slipRawEmpty /= '1') then
                                -- slipActionSel <= slipReadRaw;
                                -- slipEnable <= '1';
                                -- nextParserState <= bufferRawData;
                                -- dataParserState <= slipDelay;
                            -- else
                                -- dataParserState <= temp;
                            -- end if;
                        -- when bufferRawData =>
                            -- dataOutFifoWrEn <= '1';
                            -- dataOutFifoIn <= slipByteOut;
                            -- dataParserState <= rawOutWrDelay;
                        -- when rawOutWrDelay =>
                            -- dataOutFifoWrEn <= '0';
                            -- dataParserState <= forwardRawData;            
                            
                        
                            
                        
                    end case;         
                end if;
        end process;
        
        
end behave;