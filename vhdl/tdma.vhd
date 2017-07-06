library ieee;

use ieee.std_logic_1164.all;
use ieee.numeric_std.all;
use work.meshPack.all;
use work.compDec.all;

entity tdma is
    port(
        clk                 : in std_logic;
        rst                 : in std_logic;
        second              : in integer range 0 to maxTimeSec;
        secondFrac          : in integer range 0 to clkSpeed;
        timeSynced          : in std_logic;
        -- TDMA control interface
        tdmaInited          : in std_logic;
        tdmaInitTime        : in integer range 0 to maxTimeSec;
        -- TDMA timing control
        transmitData        : out std_logic;
        receiveData         : out std_logic;
        tdmaSleep           : out std_logic;
        radioModeOut        : out radioModes -- radio mode
    );
 end tdma;
         
 architecture behave of tdma is
    --type initStates is (initStart, initCheck, initNow);
    --signal initState : initStates;
    -- Process states
    type TdmaFrameStates is (initStart, initCheck, updateTime, updateFrameCnt); -- tdma frame control
    type TdmaCycleStates is (cycle_updateSlotNum, cycle_updateSlotTime, sleep); -- tdma cycle control
    type TdmaStates is (sleep, startSlot, receive, transmit, init); -- tdma slot control
    signal tdmaCycleState : TdmaCycleStates;
    signal tdmaFrameState : TdmaFrameStates;
    signal tdmaState : TdmaStates;
       
    -- clock time output
    signal clockTimePos : integer range 0 to 3;
    signal frameCnt : integer range 0 to tdma_frameRate := 0;
    signal oldSecond : integer range 0 to maxTimeSec := 0;
    
    -- tdma parameters
    signal transmitSlot : integer range 0 to tdma_maxNumSlots;
    signal receiveComplete : std_logic := '0';
    signal transmitComplete : std_logic := '0';
    signal frameTime : integer range 0 to clkSpeed := 0;
    signal frameTime_saved : integer range 0 to clkSpeed := 0;
    signal slotTime : integer range 0 to tdma_slotLength := 0;
    signal slotNum, oldSlotNum : integer range 0 to tdma_maxNumSlots := 0;
    signal inCycle : std_logic := '0';
    signal slotNumSet : std_logic := '0';
    signal newSlot : std_logic := '0';
    signal frameTimeConverged : std_logic := '0';
    signal lastSecondFrac : integer range 0 to clkSpeed := 0;
    
    begin
        
        tdmaSleep <= not inCycle;
        
        process(rst, clk) -- frame time
            variable initTimeTemp : std_logic_vector(31 downto 0);
            variable temp : integer range 0 to maxTimeSec;
            
            begin
                if (rst = '0') then
                    frameTime <= 0;
                    frameTimeConverged <= '0';
                    tdmaFrameState <= initStart;
                    lastSecondFrac <= 0;
                    frameCnt <= 0;

                    if (nodeId = 0) then -- ground node
                        transmitSlot <= tdma_maxNumSlots;
                    else
                        transmitSlot <= nodeId;
                    end if;
                    
                elsif (clk'event and clk = '1') then
                    case tdmaFrameState is
                        when initStart => 
                            if (timeSynced = '1') then
                                tdmaFrameState <= initCheck;
                            end if;
                        when initCheck => -- parse incoming data to check for existing mesh
                            if (tdmaInited = '1') then
                                frameCnt <= 0;
                                frameTimeConverged <= '0';
                                tdmaFrameState <= updateTime;
                            end if;           
                        
                        when updateTime => -- synchronize with external clock time
                            --if (enable = '1') then
                                lastSecondFrac <= secondFrac;
                                if secondFrac >= tdma_frameEnd(frameCnt) or secondFrac < lastSecondFrac then -- account for sub-1 second frame lengths and second incrementing
                                    tdmaFrameState <= updateFrameCnt;
                                else 
                                    frameTime <= secondFrac - frameCnt*tdma_frameLength;
                                    frameTimeConverged <= '1';
                                end if;
                            --else -- disabled
                            --    frameTimeConverged <= '0';
                            --    inited <= '0';
                            --    tdmaFrameState <= initStart;
                            --end if;
                        
                        when updateFrameCnt =>
                            frameTimeConverged <= '0';
                            if (frameCnt+1 >= tdma_frameRate) then -- new frame
                                frameCnt <= 0;
                            else -- increment counter
                                frameCnt <= frameCnt + 0;
                            end if;
                            tdmaFrameState <= updateTime;
                        
                    end case;
                        
                end if;
        end process;
 
                        
        process(rst, clk) -- slot time
            --variable slotNum_var : integer range 0 to tdma_maxNumSlots := 0;
            variable temp : std_logic_vector(15 downto 0);
            begin
                if (rst = '0' or frameTimeConverged = '0') then
                    tdmaCycleState <= sleep;
                    slotNum <= 1;
                    --slotNumSet <= '0';
                    oldSlotNum <= 0;
                    inCycle <= '0';
                    newSlot <= '0';
                elsif (clk'event and clk = '1') then
                    case tdmaCycleState is
                        when sleep =>
                            slotNumSet <= '0';
                            if (frameTime < tdma_cycleLength) then
                                tdmaCycleState <= cycle_updateSlotNum;
                            end if;
                        when cycle_updateSlotNum =>
                            if (frameTime < tdma_cycleLength) then
                                inCycle <= '1';
                                --slotNum <= frameTime + 1;
                                if frameTime >= tdma_slotEnd(slotNum-1) then
                                    slotNum <= slotNum + 1;
                                end if;
                                --slotNum <= frameTime/tdma_slotLength + 1;
                                frameTime_saved <= frameTime;
                                --slotNum <= slotNum_var;
                                --slotNumSet <= '1'; 
                                tdmaCycleState <= cycle_updateSlotTime;
                            else
                                slotNum <= 1; -- reset slot number for next cycle
                                inCycle <= '0';
                                tdmaCycleState <= sleep;
                            end if;
                        when cycle_updateSlotTime =>
                            -- Check for slot change
                            if (oldSlotNum /= slotNum) then
                                newSlot <= '1';
                            else
                                newSlot <= '0';
                            end if;
                            oldSlotNum <= slotNum;
                            
                            -- Update slot time
                            --if (slotNumSet = '1') then -- slot number previously set
                            if (slotNum = 1) then
                                slotTime <= frameTime_saved;
                            else 
                                slotTime <= frameTime_saved - tdma_slotEnd(slotNum-2); -- will lag slotNum by one clock cycle
                            end if;
                            --end if;
                            tdmaCycleState <= cycle_updateSlotNum;
                        
                    end case;
                end if;
        end process;
                
        process(rst, clk) -- slot control
            begin
                if (rst = '0' or newSlot = '1') then
                    tdmaState <= sleep;
                    transmitData <= '0';
                    receiveData <= '0';
                elsif (clk'event and clk = '1') then
                    case tdmaState is
                        when sleep => -- everything should be quiescent
                            radioModeOut <= sleep;
                            transmitData <= '0';
                            receiveData <= '0';
                            if (inCycle = '1') then
                                tdmaState <= startSlot;
                            elsif (tdmaInited = '0') then
                                tdmaState <= init;
                            end if;
                       
                        when startSlot =>
                            if (slotNum = transmitSlot) then -- transmit slot
                                tdmaState <= transmit;
                            else -- receive slot
                                tdmaState <= receive;
                            end if;
                        
                        when transmit =>
                            if (slotTime >= tdma_beginTxTime and slotTime <= tdma_endTxTime) then
                                radioModeOut <= transmit;
                                transmitData <= '1';
                            else
                                radioModeOut <= sleep;
                                transmitData <= '0';
                            end if;
                            
                        when receive => 
                            if (slotTime >= tdma_beginRxTime and slotTime <= tdma_endRxTime) then
                                radioModeOut <= receive;
                                receiveData <= '1';
                            else
                                radioModeOut <= sleep;
                                receiveData <= '0';
                            end if;
                            
                        when init => -- turn on radio during TDMA init
                            radioModeOut <= receive;
                            if (tdmaInited = '1') then
                                tdmaState <= sleep;
                            end if;
                            
                    end case;
                end if;
        end process;            
        
        
         
end architecture;   