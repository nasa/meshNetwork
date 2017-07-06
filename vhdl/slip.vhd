library ieee;

use ieee.std_logic_1164.all;
use ieee.numeric_std.all;
use work.meshPack.all;
use work.compDec.all;
use work.crc16.all;


-- logic
    -- byteIn is processed and checked for SLIP special bytes,
    -- running crc is kept and updated with each new byte(s) added to output
    -- processesed byte(s) and SLIP_END and other packaging bytes are placed into an output fifo


entity slipMsg is
    generic(
        msgSize : integer range 0 to slipMsgMaxLength := slipMsgMaxLength
    );
    port(
        clk                 : in std_logic;
        rst                 : in std_logic;
        byteIn              : in std_logic_vector(7 downto 0);
        slipEnable          : in std_logic;
        slipActionSel       : in slipAction;
        ready               : out std_logic;
        msgValid            : out std_logic;
        msgInvalid          : out std_logic;
        msgOutByte          : out std_logic_vector(7 downto 0);
        slipFifoRdEn        : in std_logic;
        slipFifoEmpty       : out std_logic;
        msgLengthOut        : out integer range 0 to slipMsgMaxLength;
        slipError           : out std_logic
    );
 end slipMsg;
         
 architecture behave of slipMsg is
    type slipMsgStates is (waitForData, performAction, parseByte, encodeByte, encodeEscEnd, encodeEscEsc, encodeEscEndTdma, encode2ndCRCByte, encodeEnd);
    signal slipMsgState : slipMsgStates;
    signal msgPos, msgLength : integer range 0 to msgSize;
    signal lastMsgByte : std_logic_vector(7 downto 0);
    signal crcCalc, crcCalc_1, crcCalc_2 : std_logic_vector(15 downto 0);
    signal crcByte1, crcByte2 : std_logic_vector(7 downto 0);
    signal lastAction : slipAction;
    signal msgFound : std_logic;
    signal escFound : std_logic;
    signal msgValidOut : std_logic;
    
    -- FIFO
    signal slipFifoIn : std_logic_vector(7 downto 0);
    signal slipFifoWrEn, slipFifoFull : std_logic;
    
    begin
        msgLengthOut <= msgLength;
        msgValid <= msgValidOut;
        
        -- Received mesh data
        slipFifo :  uartFifo 
            port map ( 
                din     => slipFifoIn,  
                dout 	=> msgOutByte, 
                wrEn 	=> slipFifoWrEn, 
                rdEn 	=> slipFifoRdEn, 
                clk  	=> clk,  
                full 	=> slipFifoFull, 
                empty	=> slipFifoEmpty,
                rst  	=> rst  
            );
        
        process(rst, clk)
            variable crcTemp : std_logic_vector(15 downto 0);
            
            procedure updateCRC(crc : std_logic_vector(15 downto 0); newData : std_logic_vector(7 downto 0)) is 
                begin
                    crcCalc <= crc16_update(crc, newData);
                    -- Store last two CRCs and bytes (since we don't know where the end of the message will be)
                    crcCalc_1 <= crcCalc;
                    crcCalc_2 <= crcCalc_1;
                    crcByte1 <= crcByte2;
                    crcByte2 <= newData;
            end procedure updateCRC;
            
            begin
                if (rst = '0') then
                    slipMsgState <= waitForData;
                    ready <= '1';
                    lastMsgByte <= X"00";
                    msgValidOut <= '0';
                    msgInvalid <= '0';
                    msgPos <= 0;
                    msgLength <= 0;
                    lastAction <= slipNone;
                    crcCalc <= X"0000";
                    msgFound <= '0';
                    escFound <= '0';
                    slipError <= '0';
                    slipFifoWrEn <= '0';
                    slipFifoIn <= X"00";

                elsif(clk'event and clk = '1') then
                    case slipMsgState is
                        when waitForData =>
                            slipFifoWrEn <= '0'; -- clear fifo write enable
                            if (slipEnable = '1' and msgValidOut = '0') then -- perform slip message action (if nothing waiting in fifo)
                                ready <= '0';
                                if (lastAction /= slipActionSel) then -- action change
                                    lastAction <= slipActionSel;
                                    if (slipActionSel = slipMsgEnd) then
                                        msgLength <= msgPos;
                                    end if;
                                    msgPos <= 0;
                                end if;
                                slipMsgState <= performAction;
                            end if;
                        when performAction =>
                            if (msgPos >= msgSize - 2) then -- potential msg overrun
                                slipError <= '1';
                                slipMsgState <= waitForData;
                            else
                                -- Perform action specific logic
                                if (slipActionSel = slipParse) then
                                    slipMsgState <= parseByte;
                                elsif (slipActionSel = slipEncode) then
                                    if (msgPos = 0) then -- first byte
                                        slipFifoWrEn <= '1';
                                        slipFifoIn <= slipEnd;
                                        msgPos <= msgPos + 1;
                                    end if;
                                    slipMsgState <= encodeByte;
                                elsif (slipActionSel = slipMsgEnd) then -- finalize message
                                    slipFifoWrEn <= '1';
                                    msgLength <= msgLength + 2;
                                    msgValidOut <= '1'; -- notify message ready
                                    slipFifoIn <= crcCalc(7 downto 0);
                                    slipMsgState <= encode2ndCRCByte;
                                else -- no action
                                    ready <= '1';
                                    slipMsgState <= waitForData;
                                end if;
                            end if;
                        when encodeByte =>
                            slipFifoWrEn <= '1';
                            crcCalc <= crc16_update(crcCalc, byteIn);
                            if (byteIn = slipEnd) then
                                slipFifoIn <= slipEsc;                                
                                msgPos <= msgPos + 2;
                                slipMsgState <= encodeEscEnd;            
                            elsif (byteIn = slipEsc) then
                                slipFifoIn <= slipEsc;
                                msgPos <= msgPos + 2;
                                slipMsgState <= encodeEscEsc;  
                            elsif (byteIn = slipEndTdma) then
                                slipFifoIn <= slipEsc;
                                msgPos <= msgPos + 2;
                                slipMsgState <= encodeEscEndTdma;
                            else
                                slipFifoIn <= byteIn;
                                msgPos <= msgPos + 1;
                                ready <= '1';
                                slipMsgState <= waitForData;
                            end if;
                            
                        when encodeEscEnd =>
                            slipFifoWrEn <= '1';
                            slipFifoIn <= slipEscEnd;
                            ready <= '1';
                            slipMsgState <= waitForData;
                            
                        when encodeEscEsc =>
                            slipFifoWrEn <= '1';
                            slipFifoIn <= slipEscEsc;
                            ready <= '1';
                            slipMsgState <= waitForData;
                            
                        when encodeEscEndTdma =>
                            slipFifoWrEn <= '1';
                            slipFifoIn <= slipEscEndTdma;
                            ready <= '1';
                            slipMsgState <= waitForData;   
                        
                        when encode2ndCRCByte =>
                            slipFifoWrEn <= '1';
                            slipFifoIn <= crcCalc(15 downto 8);
                            slipMsgState <= encodeEnd;
                            
                        when encodeEnd =>
                            ready <= '1';
                            slipFifoWrEn <= '1';
                            slipFifoIn <= slipEnd;
                            slipMsgState <= waitForData;
                            
                            
                        when parseByte =>
                            ready <= '1';
                            if (msgFound = '0') then -- no message found yet
                                if (byteIn = slipEnd) then
                                    msgFound <= '1';
                                end if;
                            else -- decode message
                                if (byteIn = slipEnd) then -- end of message
                                    if (msgPos /= 0) then -- guard against errant zero length message
                                        msgFound <= '0';
                                        -- Check CRC
                                        if (crcByte2 & crcByte1 = crcCalc_2) then -- little endian byte order
                                            msgValidOut <= '1';
                                            msgLength <= msgPos-3;
                                        else -- invalid message
                                            msgInvalid <= '1';
                                            msgPos <= 0;  
                                        end if;
                                    end if;
                                else -- parse message bytes
                                    if (escFound = '1') then -- previous byte was esc
                                        slipFifoWrEn <= '1';
                                        escFound <= '0'; -- clear escape status
                                        msgPos <= msgPos + 1;
                                        if (byteIn = slipEscEnd) then
                                            slipFifoIn <= slipEnd;
                                            updateCRC(crcCalc, slipEnd);
                                        elsif (byteIn = slipEscEndTdma) then
                                            slipFifoIn <= slipEndTdma;
                                            updateCRC(crcCalc, slipEndTdma);
                                        else 
                                            slipFifoIn <= slipEsc;
                                            updateCRC(crcCalc, slipEsc);
                                        end if;
                                    elsif (byteIn = slipEsc) then -- escape byte
                                        escFound <= '1';
                                    else -- parse raw byte
                                        slipFifoWrEn <= '1';
                                        slipFifoIn <= byteIn;
                                        updateCRC(crcCalc, byteIn);
                                        msgPos <= msgPos + 1;
                                    end if;
                                end if;
                            end if;
                            slipMsgState <= waitForData;

                           
                            
                            
                    end case;
                    
                end if;
        end process;
         
end architecture;   