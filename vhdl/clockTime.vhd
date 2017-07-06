library ieee;

use ieee.std_logic_1164.all;
use work.meshPack.all;
use work.compDec.all;
use ieee.numeric_std.all;

entity clockTime is
    generic(
        ppsResetDelay : integer range 0 to clkSpeed := clkSpeed/2
    );
    port(
        clk             : in std_logic;
        rst             : in std_logic;
        pps             : in std_logic;
        gpsRxFifoEmpty  : in std_logic;
        gpsRxFifoRdEn   : out std_logic;
        gpsRxData       : in  std_logic_vector(7 downto 0);
        second          : out integer range 0 to maxTimeSec; -- current time in seconds since epoch
        secFrac         : out integer range 0 to clkSpeed; -- current fraction of second in clock ticks
        timeSynced      : out std_logic; -- pps received and acted on
        gps3DFix        : out std_logic;
        ppsMissed       : out std_logic
    );
 end clockTime;
         
 architecture behave of clockTime is
    -- state
    type gpsReadStates is (waitForData, waitForRead, readData, parseData, calcChecksum, parseField, parseMsgType, parseFix, parseTime, parseChecksum, compareChecksum, processTimeMsg);
    type gpsMsgType is (none, gpsTime, gpsFix);
    signal gpsReadState : gpsReadStates;
    signal nextParseState : gpsReadStates;
    -- top level signals
    signal ppsRcvd : std_logic; 
    signal ppsCount : integer range 0 to maxTimeSec := 1;
    signal cycleCount : integer range 0 to clkSpeed := 1;
    signal gpsMsgFound : std_logic;
    signal fieldNum : integer range 0 to 15;
    signal fieldPos : integer range 0 to 31;
    signal currentSec : integer range 0 to maxTimeSec := 0;
    signal lastTimePPS : integer range 0 to maxTimeSec := 0;

    -- gps parsing
    signal msgType : gpsMsgType;
    signal pendingTimeMsg, pendingFixMsg : std_logic;
    
    -- time update signals
    type timeFieldArray is array(0 to 8) of std_logic_vector(7 downto 0);
    signal timeField : timeFieldArray;
    signal timeHr : integer range 0 to 99;
    signal timeMin : integer range 0 to 99;
    signal timeSec : integer range 0 to 99;
    signal timeSecFrac : integer range 0 to 99;
    signal timeUpdate_count : integer range 0 to maxTimeSec := 0;
    signal timeSyncOut : std_logic;
    signal pendingTimeUpdate : std_logic := '0';
    signal checksum : std_logic_vector(7 downto 0);
    signal rcvdChecksum : std_logic_vector(7 downto 0);
    signal checksumByte1 : std_logic_vector(3 downto 0);
    signal checksumByte2 : std_logic_vector(3 downto 0);
    
    -- gps status
    signal gps3DFixOut, pending3DFix : std_logic;
    
    begin

        second <= currentSec + ppsCount; -- why is it + ppsCount?
        secFrac <= cycleCount-1;
        --secSet <= ppsRcvd;
        gps3DFix <= gps3DFixOut;
        timeSynced <= timeSyncOut;
        -- update current time
        process(rst, clk)
    
            
        begin
            if rst = '0' then
                ppsRcvd <= '0';
                timeSyncOut <= '0';
                lastTimePPS <= 0;
                ppsMissed <= '0';
                ppsCount <= 0;
                cycleCount <= 1;
                gpsMsgFound <= '0';
                fieldPos <= 0;
                fieldNum <= 0;
                checksum <= X"00";
                pendingTimeUpdate <= '0';
                currentSec <= 0;
                gpsRxFifoRdEn <= '0';
                gps3DFixOut <= '0';
                gpsReadState <= waitForData;
                nextParseState <= parseMsgType;
                pendingTimeMsg <= '0';
                pendingFixMsg <= '0';
                pending3DFix <= '0';
                msgType <= none;

            elsif clk'event and clk = '1' then
                if (pps = '1' and ppsRcvd = '0') then
                    ppsCount <= ppsCount + 1; -- update current second count
                    cycleCount <= 1; -- reset second fraction count (bias 1 clock cycle)
                    ppsRcvd <= '1'; -- set pps received flag
                    ppsMissed <= '0';
                    -- if (timeSyncOut = '1') then -- update last time of pps
                        -- lastTimePPS <= currentSec + 1;
                    -- end if;
                    
                    -- Apply any pending time update
                    if (pendingTimeUpdate = '1') then
                        -- Apply update, accounting for count difference since update set
                        --currentSec <= to_integer(unsigned(timeHr)*3600 + unsigned(timeMin)*60 + unsigned(timeSec)) + ((ppsCount + 1) - timeUpdate_count); 
                        currentSec <= timeHr*3600 + timeMin*60 + timeSec + ((ppsCount + 1) - timeUpdate_count); -- plus 1 is because pps is received before time message
                        pendingTimeUpdate <= '0';
                        timeSyncOut <= '1';
                        ppsCount <= 1; -- reset pps count
                    end if;
                    
                    
                    
                else -- tick second fraction
                    if (cycleCount > ppsResetDelay and ppsRcvd = '1') then -- reset ppsRcvd before next expected pps signal
                        ppsRcvd <= '0';
                        cycleCount <= cycleCount + 1;
                    elsif (cycleCount >= clkSpeed) then -- reset cycleCount and increment second 
                        cycleCount <= 1;
                        currentSec <= currentSec + 1;
                        ppsMissed <= '1';
                    else
                        cycleCount <= cycleCount + 1;
                    end if;
                    
                    -- -- Check for clock failsafe
                    -- if (lastTimePPS /= 0 and ((currentSec - lastTimePPS) > 5)) then
                        -- clockFailsafe <= '1';
                    -- else
                        -- clockFailsafe <= '0';
                    -- end if;
                end if;
                
                -- state machine
                case gpsReadState is
                    when waitForData =>	-- check for new data
                        if (gpsMsgFound = '0') then -- reset msg parameters
                            fieldNum <= 0;
                            fieldPos <= 0;
                            checksum <= X"00";
                            pendingTimeMsg <= '0';
                            pendingFixMsg <= '0';
                            pending3DFix <= '0';
                            nextParseState <= parseMsgType;
                        end if;
                        if (gpsRxFifoEmpty = '0') then -- new data available
                            gpsRxFifoRdEn <= '1'; -- enable rx fifo read
                            gpsReadState <= waitForRead;
                        end if;
                        
                    when waitForRead => -- getting data from fifo delay
                        gpsRxFifoRdEn <= '0';
                        gpsReadState <= readData;
                        
                    when readData => -- gps data being read
                        if (gpsMsgFound = '0') then -- reset msg parameters
                            gpsReadState <= parseData;
                        else -- continue parsing message
                            gpsReadState <= calcChecksum;
                        end if;
                        
                    when parseData => -- parse through data to find time message
                        -- do something with data
                        if (gpsMsgFound = '0') then -- look for message start 
                            if (gpsRxData = X"24") then -- start of new nmea message
                                gpsMsgFound <= '1';
                                fieldNum <= 0;
                                fieldPos <= 0; -- bias so field position matches when read
                                --gpsMsgPos <= 2; -- bias so that message position is correct next clock  
                            end if;   
                        end if;
                        gpsReadState <= waitForData;    
                        
                    when calcChecksum => -- update CRC for current message
                        if (nextParseState /= parseChecksum) then
                            if (gpsRxData /= X"2A") then
                                checksum <= checksum xor gpsRxData;
                            else -- begin parsing checksum
                                nextParseState <= parseChecksum;
                            end if;
                        end if;
                        gpsReadState <= parseField;
    
                    when parseField => -- find next field in message                        
                        -- Look for new message field
                        if (gpsRxData = X"2C" or gpsRxData = X"2A") then -- new field
                            fieldNum <= fieldNum + 1;
                            fieldPos <= 0;
                            gpsReadState <= waitForData;
                        else 
                            fieldPos <= fieldPos + 1;
                            gpsReadState <= nextParseState;
                        end if;
                        
                    when parseMsgType =>
                        if (pendingTimeMsg = '1') then
                            if (fieldPos = 4) then
                                if (gpsRxData /= X"44") then -- not time message so start looking for new message
                                    gpsMsgFound <= '0'; 
                                end if;
                            elsif (fieldPos = 5) then
                                if (gpsRxData = X"41") then -- time message
                                    nextParseState <= parseTime;
                                else
                                    gpsMsgFound <= '0';
                                end if;
                                
                            else -- parsing error
                                gpsMsgFound <= '0';
                            end if;
                        elsif (pendingFixMsg = '1') then
                            if (fieldPos = 4) then
                                if (gpsRxData /= X"53") then -- not fix message so start looking for new message
                                    gpsMsgFound <= '0'; 
                                end if;
                            elsif (fieldPos = 5) then
                                if (gpsRxData = X"41") then -- fix message
                                    nextParseState <= parseFix;
                                else
                                    gpsMsgFound <= '0';                                   
                                end if;
                            else -- parsing error
                                gpsMsgFound <= '0';
                            end if;
                        else -- read first byte of message type
                            if (fieldPos = 3) then
                                if (gpsRxData = X"5A") then -- time message
                                    if (gps3DFixOut = '1') then -- wait for 3D fix
                                        pendingTimeMsg <= '1';
                                    else 
                                        gpsMsgFound <= '0';
                                    end if;
                                elsif (gpsRxData = X"47") then -- fix message
                                    pendingFixMsg <= '1';
                                else -- parsing error
                                    gpsMsgFound <= '0';
                                end if;
                            end if;
                        end if;
                        gpsReadState <= waitForData;
                        
                    when parseFix =>
                        -- Parse desired message fields
                        if (fieldNum = 2) then -- parse time
                            if (fieldPos = 1) then
                                msgType <= gpsFix;
                                if (gpsRxData = X"33") then -- 3d fix
                                    pending3DFix <= '1';
                                else
                                    pending3DFix <= '0';
                                end if;
                            end if;
                        end if;
                        gpsReadState <= waitForData;

                    when parseTime =>
                        -- Parse desired fields
                        if (fieldNum = 1) then -- parse time
                            if (fieldPos <= 9) then
                                timeField(fieldPos-1) <= gpsRxData;
                                if (fieldPos = 9) then -- end of time
                                    msgType <= gpsTime;
                                end if;
                            end if;
                        end if;
                        gpsReadState <= waitForData;
                        
                    when parseChecksum =>    
                        if (fieldPos = 1) then -- checksum byte 1
                            checkSumByte1 <= ascii_to_hex(gpsRxData);
                            --rcvdChecksum <= ascii_hex_number_to_hex(gpsRxData); 
                            --rcvdChecksum <= checksumByte1 & checksumByte2;
                            gpsReadState <= waitForData;
                        elsif (fieldPos = 2) then -- checksum byte 2, last byte in message
                            --rcvdChecksum <= rcvdChecksum(3 downto 0) & ascii_hex_number_to_hex(gpsRxData)(3 downto 0);
                            
                            -- Calculate received checksum
                            checksumByte2 <= ascii_to_hex(gpsRxData);
                            rcvdChecksum <= checksumByte1 & ascii_to_hex(gpsRxData);
                            --rcvdChecksum <= ascii_to_hex(checksumByte1) & ascii_to_hex(gpsRxData);
                            --rcvdChecksum <= std_logic_vector(unsigned(std_logic_vector(shift_left(unsigned(rcvdChecksum), 1))) +  unsigned(ascii_hex_number_to_hex(gpsRxData)));
                            --rcvdChecksum <= 
                            gpsReadState <= compareChecksum;
                        end if;
                    when compareChecksum =>
                        if (checksum = rcvdChecksum) then
                            if (msgType = gpsTime) then
                                gpsReadState <= processTimeMsg;
                            elsif (msgType = gpsFix) then
                                gps3DFixOut <= pending3DFix;
                                gpsMsgFound <= '0';
                                gpsReadState <= waitForData;
                            else
                                gpsMsgFound <= '0';
                                gpsReadState <= waitForData;
                            end if;
                        else -- invalid checksum
                            gpsMsgFound <= '0';
                            gpsReadState <= waitForData;
                        end if;
                    when processTimeMsg => -- check message validity and process
                        --rcvdChecksum <= 
                        if (checksum = rcvdChecksum) then -- valid message so use data
                            -- Parse time data
                            timeHr <= to_integer(unsigned(ascii_to_hex(timeField(0))))*10 + to_integer(unsigned(ascii_to_hex(timeField(1))));
                            timeMin <= to_integer(unsigned(ascii_to_hex(timeField(2))))*10 + to_integer(unsigned(ascii_to_hex(timeField(3))));
                            --timeMin <= std_logic_vector(unsigned(ascii_to_hex(timeField(2))) + unsigned(ascii_to_hex(timeField(3))));
                            timeSec <= to_integer(unsigned(ascii_to_hex(timeField(4))))*10 + to_integer(unsigned(ascii_to_hex(timeField(5))));
                            timeSecFrac <= to_integer(unsigned(ascii_to_hex(timeField(7))))*10 + to_integer(unsigned(ascii_to_hex(timeField(8))));
                            timeUpdate_count <= ppsCount;
                            pendingTimeUpdate <= '1';
                        end if;
                        
                        -- Clear message parsing status
                        gpsMsgFound <= '0';
                        gpsReadState <= waitForData;
                        
                end case;
                
            end if; 
        end process;
        
        
        
             
        -- monitor pps signal
        --process(pps)
        --begin
        --    if pps'event and pps = '1' then
        --        ppsRcvd <= '1';
        --    end if;
        --end process;
         
end architecture;