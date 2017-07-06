library ieee;

use ieee.std_logic_1164.all;
use ieee.numeric_std.all;
use work.meshPack.all;
use work.compDec.all;
use work.crc16.all;

entity tdmaCtrl is
    port(
        clk                 : in std_logic;
        rst                 : in std_logic;
        second              : in integer range 0 to maxTimeSec;
        secondFrac          : in integer range 0 to clkSpeed;
        timeSynced          : in std_logic;
        tdmaSleep           : in std_logic;
        tdmaInited          : out std_logic;
        tdmaInitTime        : out integer range 0 to maxTimeSec;
        tdmaInitAck         : in std_logic;
        tdmaCtrlFifoRdEn    : in std_logic;
        tdmaCtrlFifoEmpty   : out std_logic;
        tdmaCtrlOut         : out std_logic_vector(7 downto 0);
        tdmaInitTimeRcvd    : in std_logic;
        tdmaInitTimeIn      : in integer range 0 to maxTimeSec
    );
 end tdmaCtrl;
         
 architecture behave of tdmaCtrl is
    -- Process states
    type TdmaCtrlStates is (initStart, initCheck, ctrlWait, slipClear, sendStatusMsg, sendWait); -- tdma control states
    signal tdmaCtrlState, nextCtrlState : TdmaCtrlStates;
    
    -- clock time output
    signal clockTimePos : integer range 0 to 3;
    signal frameCnt : integer range 0 to tdma_frameRate := 0;
    signal oldSecond : integer range 0 to maxTimeSec := 0;
    
    -- tdma parameters
    signal inited : std_logic; -- tdma intialization complete flag
    signal initStartTime : integer range 0 to maxTimeSec := 0;
    signal initTime : integer range 0 to maxTimeSec;
    
    
    -- tdma control messages
    signal sendInitTime : std_logic;
    signal initTimeVec : std_logic_vector(31 downto 0);   
    signal initTimeCrc : std_logic_vector(15 downto 0); 
    signal tdmaCtrlIn : std_logic_vector(7 downto 0);
    signal tdmaCtrlFifoWrEn, tdmaCtrlFifoFull : std_logic;
    signal tdmaCtrlSentTime : integer range 0 to maxTimeSec;
    signal tdmaCtrlMsgEnd, tdmaCtrlMsgPos : integer range 0 to 11;
    signal meshFifoOut : std_logic_vector(7 downto 0);
    signal meshFifoRdEn, meshFifoEmpty, meshFifoFull : std_logic;
    
    --signal frameStartFrac_ms : integer range 0 to 1000 := 0;
    signal receiveComplete : std_logic := '0';
    signal transmitComplete : std_logic := '0';
    signal slotTime : integer range 0 to tdma_slotLength := 0;
    signal slotNum, oldSlotNum : integer range 0 to tdma_maxNumSlots := 0;
    signal inCycle : std_logic := '0';
    signal slotNumSet : std_logic := '0';
    signal newSlot : std_logic := '0';
    signal lastSecondFrac : integer range 0 to clkSpeed := 0;
 
    -- SLIP
    signal slipOutEnable, slipOutRst, slipOutRstIn, slipOutFifoRdEn, slipOutFifoEmpty, slipOutReady, slipOutValid, slipOutInvalid, slipOutError : std_logic;
    signal slipOutByteIn, slipOutByteOut : std_logic_vector( 7 downto 0);
    signal slipOutActionSel : slipAction;
    signal slipOutMsgPos : integer range 0 to slipMsgMaxLength;
    signal slipOutMsgLength : integer range 0 to slipMsgMaxLength;
    signal cnt : integer range 0 to 2 := 0;
    
    begin
        -- TDMA control data
        -- tdmaCtrlFifo :  uartFifo 
            -- port map ( 
                -- din     => tdmaCtrlIn,  
                -- dout 	=> tdmaCtrlOut, 
                -- wrEn 	=> tdmaCtrlFifoWrEn, 
                -- rdEn 	=> tdmaCtrlFifoRdEn, 
                -- clk  	=> clk,  
                -- full 	=> tdmaCtrlFifoFull, 
                -- empty	=> tdmaCtrlFifoEmpty,
                -- rst  	=> rst  
            -- );
            
        -- TDMA mesh status slip
        -- slipMsg_i : slipMsg
            -- generic map(
                -- msgSize => 15
            -- )
            -- port map(
                -- clk             => clk,
                -- rst             => slipRstIn,
                -- byteIn          => slipByteIn,
                -- slipEnable      => slipEnable,
                -- slipActionSel   => slipActionSel,
                -- ready           => slipReady,
                -- msgValid        => slipValid,
                -- msgInvalid      => slipInvalid,
                -- msgOutByte      => slipByteOut,
                -- slipFifoRdEn    => slipFifoRdEn,
                -- slipFifoEmpty   => slipFifoEmpty,
                -- msgLengthOut    => slipMsgLength,
                -- slipError       => slipError
            -- );
            
        slipMsgOut_i : slipMsg
            generic map(
                msgSize => 255
            )
            port map(
                clk             => clk,
                rst             => slipOutRstIn,
                byteIn          => slipOutByteIn,
                slipEnable      => slipOutEnable,
                slipActionSel   => slipOutActionSel,
                ready           => slipOutReady,
                msgValid        => slipOutValid,
                msgInvalid      => slipOutInvalid,
                msgOutByte      => tdmaCtrlOut,
                slipFifoRdEn    => tdmaCtrlFifoRdEn,
                slipFifoEmpty   => tdmaCtrlFifoEmpty,
                msgLengthOut    => slipOutMsgLength,
                slipError       => slipOutError
            );

        -- Init status
        tdmaInited <= inited;
        tdmaInitTime <= initTime;
        
        -- Slip reset
        slipOutRstIn <= not slipOutRst;
        
        process(rst, clk) -- frame time
            variable initTimeTemp : std_logic_vector(31 downto 0);
            variable temp : std_logic_vector(15 downto 0);
            
            begin
                if (rst = '0') then
                    inited <= '0';
                    initTime <= 0;
                    nextCtrlState <= initStart;
                    tdmaCtrlState <= initStart;
                    lastSecondFrac <= 0;
                    sendInitTime <= '0';
                    meshFifoRdEn <= '0';
                    tdmaCtrlFifoWrEn <= '0';
                    tdmaCtrlSentTime <= 0;
                    
                    -- TDMA Ctrl Output
                    tdmaCtrlMsgPos <= 0;
                    tdmaCtrlMsgEnd <= 7;
                    slipOutRst <= '0';
                    slipOutEnable <= '0';
                    
                elsif (clk'event and clk = '1') then
                    case tdmaCtrlState is
                        when initStart =>
                            if (timeSynced = '1') then
                                initStartTime <= second;
                                tdmaCtrlState <= initCheck;
                            end if;
                        when initCheck => -- parse incoming data to check for existing mesh
                            if (second < initStartTime - 5) then -- clock reset so restart timer
                                initStartTime <= second;
                            elsif ((second - initStartTime) >= tdma_initTimeToWait) then -- init timer elapsed
                                initTime <= second;
                                sendInitTime <= '1';
                                inited <= '1';
                                tdmaCtrlState <= ctrlWait;
                            elsif (tdmaInitTimeRcvd = '1') then -- init time received
                                sendInitTime <= '1';
                                initTime <= tdmaInitTimeIn;
                                inited <= '1';
                                tdmaCtrlState <= ctrlWait;
                            end if;
 
                        when ctrlWait =>
                            if (tdmaSleep = '1' and tdmaInitAck = '0' and sendInitTime = '1' and (second - tdmaCtrlSentTime) > 2) then
                                slipOutRst <= '1'; -- clear SLIP
                                -- Send control signals to BBB
                                tdmaCtrlState <= slipClear;
                                tdmaCtrlMsgPos <= 0;
                                initTimeVec <= std_logic_vector(to_unsigned(initTime, initTimeVec'length));
                                initTimeCrc <= X"0000"; -- reset CRC for next calculation
                            end if;
                            
                        when slipClear =>
                            slipOutRst <= '0';
                            tdmaCtrlState <= sendStatusMsg;
                            
                        when sendStatusMsg => -- this isn't getting slip encoded but it should
                            if (slipOutReady = '1') then
                                slipOutEnable <= '1';
                                if (tdmaCtrlMsgPos < tdmaCtrlMsgEnd) then
                                    tdmaCtrlMsgPos <= tdmaCtrlMsgPos + 1;
                                    slipOutActionSel <= slipEncode;
                                    -- Send TDMA Mesh Status message
                                    if (tdmaCtrlMsgPos = 0) then
                                        slipOutByteIn <= tdmaStatusCmdId;
                                    elsif (tdmaCtrlMsgPos = 1) then
                                        slipOutByteIn <= std_logic_vector(to_unsigned(nodeId, slipOutByteIn'length));    
                                    elsif (tdmaCtrlMsgPos = 2) then -- little endian
                                        slipOutByteIn <= initTimeVec(7 downto 0);
                                    elsif (tdmaCtrlMsgPos = 3) then
                                        slipOutByteIn <= initTimeVec(15 downto 8);
                                    elsif (tdmaCtrlMsgPos = 4) then
                                        slipOutByteIn <= initTimeVec(23 downto 16);
                                    elsif (tdmaCtrlMsgPos = 5) then
                                        slipOutByteIn <= initTimeVec(31 downto 24);
                                    elsif (tdmaCtrlMsgPos = 6) then 
                                        slipOutByteIn <= X"01"; -- status nominal
                                        -- Calculate message crc
                                        -- temp := crc16_update(X"0000", tdmaStatusCmdId);
                                        -- temp := crc16_update(temp, std_logic_vector(to_unsigned(nodeId, tdmaCtrlByteOut'length)));
                                        -- temp := crc16_update(temp, initTimeVec(7 downto 0));
                                        -- temp := crc16_update(temp, initTimeVec(15 downto 8));
                                        -- temp := crc16_update(temp, initTimeVec(23 downto 16));
                                        -- temp := crc16_update(temp, initTimeVec(31 downto 24));
                                        -- initTimeCrc <= crc16_update(temp, X"01");
                                    -- elsif (tdmaCtrlMsgPos = 7) then -- little endian
                                        -- tdmaCtrlByteOut <= initTimeCrc(7 downto 0);
                                    -- elsif (tdmaCtrlMsgPos = 8) then
                                        -- tdmaCtrlByteOut <= initTimeCrc(15 downto 8);
                                    -- elsif (tdmaCtrlMsgPos = 9) then
                                        -- tdmaCtrlByteOut <= slipEnd;
                                    end if;
                                    tdmaCtrlState <= sendWait;
                                else -- end message
                                    slipOutActionSel <= slipMsgEnd;
                                    tdmaCtrlSentTime <= second;
                                    tdmaCtrlState <= sendWait;
                                end if;
                            end if;
                    
                        when sendWait =>
                            slipOutEnable <= '0';
                            if (slipOutReady = '1') then
                                if (slipOutActionSel = slipMsgEnd) then
                                    tdmaCtrlState <= ctrlWait;
                                else
                                    tdmaCtrlState <= sendStatusMsg;
                                end if;
                            end if;
                        
                    end case;
                end if;
        end process;                    
        
         
end architecture;   