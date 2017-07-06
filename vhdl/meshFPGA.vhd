library ieee;
library proasic3l;

use proasic3l.all;
use ieee.std_logic_1164.all;
use IEEE.STD_LOGIC_unsigned.all;
use ieee.numeric_std.all;
use work.compDec.all;  -- components defined in compDec
use work.meshPack.all;
use work.commandTypes.all;

entity meshFPGA is
    generic(
        ctrStrtCnt : integer range 0 to baudIntSize := baudCtrCnt; -- bit center start count
        baudCnt : integer range 0 to baudIntSize := baudWidthCnt; -- bit width in counts
        gpsCtrStrtCnt : integer range 0 to baudIntSize := gpsBaudCtrCnt; -- bit center start count
        gpsBaudCnt : integer range 0 to baudIntSize := gpsBaudWidthCnt; -- bit width in counts
        ppsResetDelay : integer range 0 to clkSpeed := clkSpeed/2
    );   

    port(
        rstIn :             in std_logic;
        clkIn_p :           in std_logic;
        clkIn_n :           in std_logic;
        --clkIn :             in std_logic; -- for testing only
        ppsIn :             in std_logic;
        -- UARTs
        nodeRxIn :          in std_logic;
        nodeTxOut :         out std_logic;
        radioRxIn :         in std_logic;
        radioTxOut :        out std_logic;
        gpsRxIn :           in std_logic;
        -- LEDs
        LED1Out :           out std_logic;
        LED2Out :           out std_logic;
        LED3Out :           out std_logic;
        LED4Out :           out std_logic;
        LED5Out :           out std_logic;
        LED6Out :           out std_logic;
        LED7Out :           out std_logic;
        LED8Out :           out std_logic;
        -- IO Pins to BBB
        io1Out :            out std_logic;
        io2Out :            out std_logic;
        io3Out :            out std_logic;
        io4Out :            out std_logic;
        io5Out :            out std_logic;
        io6Out :            out std_logic;
        io7In  :            in std_logic;
        io8In  :            in std_logic;
        -- User-configurable switches
        dipSwitch1In :      in std_logic;
        dipSwitch2In :      in std_logic;
        dipSwitch3In :      in std_logic;
        dipSwitch4In :      in std_logic;
        enableIn :          in std_logic;
        -- Radio control
        radioSleepStatus :  in std_logic;
        radioSleepOut :     out std_logic;
        -- Memory pins
        framEn :            out std_logic; 
        framWrEn :          out std_logic; 
        framOeEn :          out std_logic; 
        framSleep :         out std_logic; 
        framData :          inout std_logic_vector(7 downto 0);
        framAddr :          out std_logic_vector(17 downto 0);
        framUb :            out std_logic
    );
    
 end meshFPGA;
         
 architecture struct of meshFPGA is
    
    -- top level signals
    signal clk, clk25MHzRaw, clk25MHz, clk10MHz : std_logic; -- clocks
    signal rst, rstSync, rstAsync : std_logic; -- reset
    signal enable : std_logic; -- enable switch
    signal rstTemp : std_logic; -- reset flip
    signal cnt1, cnt2 : integer range 0 to 5 := 0;
    signal pps : std_logic; -- pps time signal
    signal enableAndRst : std_logic; -- combined enable and reset flag
    signal enableRstInit : std_logic; -- combined enable, reset, and init flag
    signal enableBBBRst : std_logic; -- wait for BBB to start logic before executing
    signal inited : std_logic; -- status of initialization
    
    -- UART_node signals
    signal nodeRx, nodeTx: std_logic; -- rx in and tx out signals
    signal nodeTxEmpty : std_logic;
    signal nodeRxFifoRdEn, nodeTxFifoWrEn, nodeRxFifoEmpty, nodeTxFifoFull : std_logic;
    signal nodeRxData, nodeTxData : std_logic_vector(7 downto 0); -- node UART in and out
    
    -- UART_radio signals
    signal radioRx, radioTx: std_logic; -- rx in and tx out signals
    signal radioTxEmpty : std_logic;
    signal radioRxFifoRdEn, radioTxFifoWrEn, radioRxFifoEmpty, radioTxFifoFull : std_logic;
    signal radioRxData, radioTxData : std_logic_vector(7 downto 0); -- radio UART in and out
    
    -- UART_gps signals
    signal gpsRx : std_logic; -- rx in
    signal gpsTxEmpty : std_logic;
    signal gpsRxFifoRdEn, gpsRxFifoEmpty, gpsTxFifoFull : std_logic;
    signal gpsRxData, gpsTxData : std_logic_vector(7 downto 0);
    
    -- TDMA signals
    signal nodeDataAvail : std_logic;
    signal radioDataAvail : std_logic;
    signal nodeDataReady : std_logic;
    signal radioDataReady : std_logic;
    signal radioMode : radioModes := sleep; -- sleep
    signal radioSleep : std_logic;
    signal tdmaTransmitData : std_logic;
    signal tdmaReceiveData : std_logic;
    signal tdmaInitTimeRcvd : std_logic;
    signal tdmaInitTime, tdmaInitTimeIn : integer range 0 to maxTimeSec;
    signal tdmaInited, tdmaSleep : std_logic;
    signal tdmaCtrlFifoRdEn, tdmaFifoWrEn, tdmaCtrlFifoEmpty : std_logic;
    signal tdmaCtrlOut, tdmaFifoIn : std_logic_vector(7 downto 0);
    
    -- Data parser signals
    signal parserFifoRdEn, parserFifoWrEn, parserFifoEmpty : std_logic;
    signal parserFifoIn, parserFifoOut : std_logic_vector(7 downto 0);
    
    -- Clock time signals
    signal second : integer range 0 to maxTimeSec := 0;
    signal secondFrac : integer range 0 to clkInSpeed := 0;
    signal timeSynced : std_logic;
    signal ppsMissed : std_logic;

    -- User I/O
    --signal io1, io2, io3, io4, io5, io6, io7, io8 : std_logic := '0';
    signal LED1, LED2, LED3, LED4, LED5, LED6, LED7, LED8 : std_logic := '0';
    signal dipSwitch1, dipSwitch2, dipSwitch3, dipSwitch4 : std_logic; -- dip switch positions
    
    -- Memory controller
    signal framDataAddr, framAddrOut : std_logic_vector(17 downto 0);
    signal framRdComplete, framWrComplete : std_logic;
    signal framRdEn, framRdInProgress, framAccessWrEn : std_logic;
    signal framRdData, framWrData : std_logic_vector(7 downto 0);
    signal framNodeDataEmpty, framMeshDataEmpty, framMeshFifoEmpty : std_logic;
    signal framNodeInFifoWrEn, framNodeOutFifoRdEn, framMeshInFifoWrEn, framMeshOutFifoRdEn : std_logic;
    
    -- Memory interface
    signal nodeMemRd, nodeMemWr, nodeMemComp, radioMemRd, radioMemWr, radioMemComp, tdmaCtrlMemRd, tdmaCtrlMemWr, tdmaCtrlMemComp : std_logic;
    signal nodeDataAddr, radioDataAddr, tdmaCtrlDataAddr : std_logic_vector(17 downto 0);
    signal nodeDataToMem, radioDataToMem, tdmaCtrlDataToMem, nodeDataFromMem, radioDataFromMem, tdmaCtrlDataFromMem : std_logic_vector(7 downto 0);
    signal currMemAct : MemAction;
    
    type testStates is (checkNodeRx, checkRadioRx, radioRxDebug1, radioRxDebug2, nodeRxDebug1, nodeRxDebug2, readRadioDelay, readNodeDelay); -- delayForRdEn, readData, 
    signal nodeState : testStates;
    signal radioState : testStates;
    
    component INBUF_LVPECL is
    port(
      Y     :  out    STD_ULOGIC;
      PADP  :  in   STD_ULOGIC;
      PADN  :  in   STD_ULOGIC);
    end component;
    begin

        --rstTemp <= not rstIn; -- dev board
        rstTemp <= rstIn;
        rstAsync <= rstTemp;
        rst <= rstSync; -- reset in signal
        enableAndRst <= enable and rst;
        enableRstInit <= enable and rst and inited;
        enableBBBRst <= enable and rst and io8In;
        --clk <= clkIn; -- clock in signal -- dev board testing
        
        --rx <= rxIn; -- rx data in signal
        nodeTxOut <= nodeTx;
        radioTxOut <= radioTx;

        -- status
        LED1 <= enable;
        LED2 <= io8In; -- BBB status
        LED4 <= timeSynced;
        LED5 <= radioSleepStatus;        
        LED7 <= tdmaTransmitData;
        LED8 <= tdmaReceiveData;
        
        -- Radio
        radioSleepOut <= radioSleep;
        
        -- Memory
        framUb <= not framAddrOut(17);
        framAddr <= framAddrOut;
        
        -- Differential clock
        clk_buf : INBUF_LVPECL 
            port map(
                Y     => clk,
                PADP  => clkIn_p,
                PADN  => clkIn_n
           );
        
        -- 25 MHz clock
        clock25MHz_i: customClock
            generic map(
                clockDivider => clkDivider
            )
            port map(
                clk          => clk,
                rst          => rstSync,
                clkOut       => clk25MHz
            );
        
        clock10MHz_i: customClock
            generic map(
                clockDivider => tdmaClkDivider
            )
            port map(
                clk          => clk,
                rst          => rstSync,
                clkOut       => clk10MHz
            );
        
        -- Dual rank syncs
        rstDualRankSync_rst : rstDualRankSync -- reset signal
            generic map ( asyncRstAssertVal => '0')
            port map(
                clk         => clk,              
                asyncRst    => rstAsync,     
                syncRst     => rstSync
            );
            
        -- dualRankSync_clk25MHz : dualRankSync -- enable signal
            -- generic map ( resetVal => '0')
            -- port map(
                -- rst         => rst,
                -- clk         => clk,
                -- inData      => clk25MHzRaw,
                -- outData     => clk25MHz
            -- );
            
        dualRankSync_enable : dualRankSync -- enable signal
            generic map ( resetVal => '0')
            port map(
                rst         => rst,
                clk         => clk,
                inData      => enableIn,
                outData     => enable
            );
        
        dualRankSync_dipSwitch1 : dualRankSync -- dip switch 1
            generic map ( resetVal => '0')
            port map(
                rst         => rst,
                clk         => clk,
                inData      => dipSwitch1In,
                outData     => dipSwitch1
            );

        dualRankSync_dipSwitch2 : dualRankSync -- dip switch 2
            generic map ( resetVal => '0')
            port map(
                rst         => rst,
                clk         => clk,
                inData      => dipSwitch2In,
                outData     => dipSwitch2
            );

        dualRankSync_dipSwitch3 : dualRankSync -- dip switch 3
            generic map ( resetVal => '0')
            port map(
                rst         => rst,
                clk         => clk,
                inData      => dipSwitch3In,
                outData     => dipSwitch3
            );

        dualRankSync_dipSwitch4 : dualRankSync -- dip switch 4
            generic map ( resetVal => '0')
            port map(
                rst         => rst,
                clk         => clk,
                inData      => dipSwitch4In,
                outData     => dipSwitch4
            );            
            
        dualRankSync_nodeRx : dualRankSync 
            generic map (resetVal => '1')
            port map (
                rst         => rst,
                clk         => clk25MHz,
                inData      => nodeRxIn,
                outData     => nodeRx
            );
            
        dualRankSync_radioRx : dualRankSync 
            generic map (resetVal => '1')
            port map (
                rst         => rst,
                clk         => clk25MHz,
                inData      => radioRxIn,
                outData     => radioRx
            );
            
        dualRankSync_gpsRx : dualRankSync 
            generic map (resetVal => '1')
            port map (
                rst         => rst,
                clk         => clk25MHz,
                inData      => gpsRxIn,
                outData     => gpsRx
            );
    
        dualRankSync_pps : dualRankSync 
            generic map (resetVal => '0')
            port map (
                rst         => rst,
                clk         => clk25MHz,
                inData      => ppsIn,
                outData     => pps
            );
        
        -- User input/output to user
        userInterface_i : userInterface
            port map(
                clk         => clk25MHz,
                rst         => rst,
                enable      => enable,
                failsafe    => ppsMissed,
                dipSwitch1  => dipSwitch1,
                dipSwitch2  => dipSwitch2,
                dipSwitch3  => dipSwitch3,
                dipSwitch4  => dipSwitch4,
                LED1In      => LED1,
                LED2In      => LED2,
                LED3In      => LED3,
                LED4In      => LED4,
                LED5In      => LED5,
                LED6In      => LED6,
                LED7In      => LED7,
                LED8In      => LED8,
                io1Out      => io1Out,
                io2Out      => io2Out,
                io3Out      => io3Out,
                io4Out      => io4Out,
                io5Out      => io5Out,
                io6Out      => io6Out,
                io7In       => io7In,
                io8In       => io8In,
                LED1Out     => LED1Out,
                LED2Out     => LED2Out,
                LED3Out     => LED3Out,
                LED4Out     => LED4Out,
                LED5Out     => LED5Out,
                LED6Out     => LED6Out,
                LED7Out     => LED7Out,
                LED8Out     => LED8Out
            );
        
        -- UARTs
        UART_node : uart
            generic map(
                ctrStrtCnt => ctrStrtCnt,
                baudCnt => baudCnt
            )
            port map(
                clk             => clk25MHz,
                rst             => enableRstInit,
                rx              => nodeRx,          
                tx              => nodeTx,          
                rxData          => nodeRxData,      
                rxFifoRdEn      => nodeRxFifoRdEn,
                rxFifoEmpty     => nodeRxFifoEmpty,
                txData	        => nodeTxData,      
                txFifoWrEn      => nodeTxFifoWrEn,
                txFifoFull      => nodeTxFifoFull,
                txEmpty         => nodeTxEmpty,     
                frameError      => open
            );
            
        UART_radio : uart
        generic map(
            ctrStrtCnt => ctrStrtCnt,
            baudCnt => baudCnt
        )
        port map(
            clk             => clk25MHz,
            rst             => enableRstInit,
            rx              => radioRx,          
            tx              => radioTx,          
            rxData          => radioRxData,      
            rxFifoRdEn      => radioRxFifoRdEn,
            rxFifoEmpty     => radioRxFifoEmpty,
            txData	        => radioTxData,      
            txFifoWrEn      => radioTxFifoWrEn,
            txFifoFull      => radioTxFifoFull,
            txEmpty         => radioTxEmpty,     
            frameError      => open
        );
        
        UART_gps : uart -- used for timing/pps
            generic map(
                ctrStrtCnt => gpsCtrStrtCnt,
                baudCnt => gpsBaudCnt
            )
            port map(
                clk             => clk25MHz,
                rst             => rst,
                rx              => gpsRx,          
                tx              => open, -- gps is read only         
                rxData          => gpsRxData,      
                rxFifoRdEn      => gpsRxFifoRdEn,
                rxFifoEmpty     => gpsRxFifoEmpty,
                txData	        => gpsTxData,      
                txFifoWrEn      => '0', -- gps is read-only
                txFifoFull      => gpsTxFifoFull,
                txEmpty         => gpsTxEmpty,     
                frameError      => open
            );
         
        -- Radio
        radio_i : radio
            port map(
                clk         => clk25MHz,
                rst         => rst,
                radioMode   => radioMode,
                sendDataIn  => '0',
                dataIn      => radioTxData,
                dataOut     => open,
                sendDataOut => open,
                sleepStatus => radioSleepStatus,
                sleepOut    => radioSleep
            );
 
        -- TDMA
        TDMA_i : tdma
            port map(
                clk                 => clk25MHz,
                rst                 => enableRstInit,
                second              => second,
                secondFrac          => secondFrac,
                timeSynced          => timeSynced,
                tdmaInited          => tdmaInited,
                tdmaInitTime        => tdmaInitTime,
                transmitData        => tdmaTransmitData,
                receiveData         => tdmaReceiveData,
                tdmaSleep           => tdmaSleep,
                radioModeOut        => radioMode                     
            ); 
            
        TDMACtrl_i : tdmaCtrl
            port map(
                clk                 => clk25MHz,
                rst                 => enableRstInit,
                second              => second,
                secondFrac          => secondFrac,
                timeSynced          => timeSynced,
                tdmaSleep           => tdmaSleep,
                tdmaInited          => tdmaInited,
                tdmaInitTime        => tdmaInitTime,
                tdmaInitAck         => '0',
                tdmaCtrlFifoRdEn    => tdmaCtrlFifoRdEn,
                tdmaCtrlFifoEmpty   => tdmaCtrlFifoEmpty,
                tdmaCtrlOut         => tdmaCtrlOut,
                tdmaInitTimeRcvd    => tdmaInitTimeRcvd,
                tdmaInitTimeIn      => tdmaInitTimeIn                
            ); 
            
        -- Clock
        ClockTime_i : clockTime
            generic map(
                ppsResetDelay => ppsResetDelay
            )
             port map(
                clk             => clk25MHz,
                rst             => rst,
                pps             => pps,
                gpsRxFifoEmpty  => gpsRxFifoEmpty,
                gpsRxFifoRdEn   => gpsRxFifoRdEn,
                gpsRxData	    => gpsRxData,
                second          => second,
                secFrac         => secondFrac,
                timeSynced      => timeSynced,
                gps3DFix        => LED3,
                ppsMissed       => ppsMissed
            );
         
        -- Data management
        memController_i : memController
            port map(
                rst                 => rst,
                clk                 => clk25MHz,
                dataAddr            => framDataAddr,
                rdEn                => framRdEn,
                rdData              => framRdData,
                rdInProgress        => framRdInProgress,
                rdComplete          => framRdComplete,
                wrEn                => framAccessWrEn,
                wrData              => framWrData,
                wrInProgress        => open,
                wrComplete          => framWrComplete,  
                framEn              => framEn, 
                framWrEn            => framWrEn,
                framOeEn            => framOeEn,
                framSleep           => framSleep,
                framData            => framData,
                framAddr            => framAddrOut
            );
            
        memInterface_i : memInterface
            port map(
                clk                 => clk25MHz,
                rst                 => rst,
                nodeMemRd           => nodeMemRd,
                nodeMemWr           => nodeMemWr,
                nodeDataIn          => nodeDataToMem,
                nodeDataAddr        => nodeDataAddr,
                nodeDataOut         => nodeDataFromMem,
                nodeMemComp         => nodeMemComp,
                radioMemRd          => radioMemRd,
                radioMemWr          => radioMemWr,
                radioDataIn         => radioDataToMem,
                radioDataAddr       => radioDataAddr,
                radioDataOut        => radioDataFromMem,
                radioMemComp        => radioMemComp,
                tdmaCtrlMemRd       => tdmaCtrlMemRd,
                tdmaCtrlMemWr       => tdmaCtrlMemWr,
                tdmaCtrlDataIn      => tdmaCtrlDataToMem,
                tdmaCtrlDataAddr    => tdmaCtrlDataAddr,
                tdmaCtrlDataOut     => tdmaCtrlDataFromMem,
                tdmaCtrlMemComp     => tdmaCtrlMemComp,
                currMemAct          => currMemAct,
                memRdEn             => framRdEn,
                rdComplete          => framRdComplete,
                memWrEn             => framAccessWrEn,
                wrComplete          => framWrComplete, 
                memDataAddr         => framDataAddr, 
                dataToMem           => framWrData,
                dataFromMem         => framRdData
            );
    
        
        dataProcessor_i : dataProcessor
            port map (
                clk                 => clk25Mhz,
                rst                 => enableRstInit,
                enable              => enable,
                tdmaTransmitFlag    => tdmaTransmitData,
                radioRxFifoEmpty    => radioRxFifoEmpty,
                radioRxFifoRdEn     => radioRxFifoRdEn,        
                radioTxFifoFull     => radioTxFifoFull,
                radioTxFifoWrEn     => radioTxFifoWrEn,
                meshDataIn          => radioRxData,
                nodeDataOut         => radioTxData,
                nodeRxFifoEmpty     => nodeRxFifoEmpty,
                nodeRxFifoRdEn      => nodeRxFifoRdEn,       
                nodeTxFifoFull      => nodeTxFifoFull,
                nodeTxFifoWrEn      => nodeTxFifoWrEn,
                nodeDataIn          => nodeRxData,
                meshDataOut         => nodeTxData,  
                tdmaCtrlFifoRdEn    => tdmaCtrlFifoRdEn,
                tdmaCtrlFifoEmpty   => tdmaCtrlFifoEmpty,
                tdmaCtrlIn          => tdmaCtrlOut,
                parserFifoWrEn      => parserFifoWrEn,
                parserFifoOut       => parserFifoIn,
                parserFifoRdEn      => parserFifoRdEn,
                parserFifoEmpty     => parserFifoEmpty,
                parserIn            => parserFifoOut,
                nodeMemRd           => nodeMemRd,
                nodeMemWr           => nodeMemWr,
                nodeMemDataOut      => nodeDataToMem,
                nodeDataAddr        => nodeDataAddr,
                nodeMemDataIn       => nodeDataFromMem,
                nodeMemComp         => nodeMemComp,
                radioMemRd          => radioMemRd,
                radioMemWr          => radioMemWr,
                radioMemDataOut     => radioDataToMem,
                radioDataAddr       => radioDataAddr,
                radioMemDataIn      => radioDataFromMem,
                radioMemComp        => radioMemComp,
                tdmaCtrlMemRd       => tdmaCtrlMemRd,
                tdmaCtrlMemWr       => tdmaCtrlMemWr,
                tdmaCtrlMemDataOut  => tdmaCtrlDataToMem,
                tdmaCtrlDataAddr    => tdmaCtrlDataAddr,
                tdmaCtrlMemDataIn   => tdmaCtrlDataFromMem,
                tdmaCtrlMemComp     => tdmaCtrlMemComp,
                currMemAct          => currMemAct
            );
        
    
        dataParser_i : dataParser
            port map (
                clk                 => clk25MHz,
                rst                 => enableRstInit,
                dataInFifoWrEn      => parserFifoWrEn,
                dataIn              => parserFifoIn,
                dataOutFifoEmpty    => parserFifoEmpty,
                dataOutFifoRdEn     => parserFifoRdEn,
                dataOut             => parserFifoOut,
                tdmaInited          => tdmaInited,
                tdmaInitTimeRcvd    => tdmaInitTimeRcvd,
                tdmaInitTime        => tdmaInitTimeIn
            );
         
        -- -- node uart logic
        process(enableAndRst, clk25MHz)
            variable memAddr : std_logic_vector(17 downto 0);
            begin
                if (enableAndRst = '0') then 
                    inited <= '0';
                elsif (inited = '0') then -- run initialization
                    -- Populate command type array
                    for i in 0 to numCmds loop
                        cmdTypes(i).valid <= '0';
                        cmdTypes(i).timestamp <= 0;
                        cmdTypes(i).unique <= '0';
                    end loop;
                
                    inited <= '1';
                end if;
                -- nodeState <= checkRadioRx;
                -- nodeRxFifoRdEn <= '0';
                -- nodeTxFifoWrEn <= '0';
                -- radioRxFifoRdEn <= '0';
                -- radioTxFifoWrEn <= '0';
                -- nodeDataAvail <= '0';
                -- cnt1 <= 1;

            -- elsif clk25MHz'event and clk25MHz = '1' then
                -- case nodeState is
                    -- when checkRadioRx =>
                            -- if (radioRxFifoEmpty = '0') then -- new mesh data from radio
                                -- radioRxFifoRdEn <= '1'; -- enable read from radio uart fifo
                                -- nodeState <= readRadioDelay;
                                -- cnt1 <= 1;
                            -- else
                                -- nodeState <= checkNodeRx;
                            -- end if;
                        -- when readRadioDelay =>
                            -- radioRxFifoRdEn <= '0';    
                            -- if (cnt1 >= 1) then

                                -- nodeState <= radioRxDebug1;
                                -- cnt1 <= 1;
                            -- else
                                -- cnt1 <= cnt1 + 1;
                            -- end if;
                        -- when radioRxDebug1 =>
                            -- nodeTxFifoWrEn <= '1';
                            -- nodeTxData <= radioRxData;
                            -- nodeState <= radioRxDebug2;
                        -- when radioRxDebug2 =>
                            -- nodeTxFifoWrEn <= '0';
                            -- nodeState <= checkNodeRx; 

                        -- when checkNodeRx => 
                            
                            -- if (nodeRxFifoEmpty = '0') then -- new data from node
                                -- nodeRxFifoRdEn <= '1'; -- enable read from node uart fifo
                                -- cnt1 <= 1;
                                -- nodeState <= readNodeDelay;
                            -- else
                                -- nodeState <= checkRadioRx;
                            -- end if;
                            
                        -- -- Read node data from BBB and place in fram
                        -- when readNodeDelay => -- delay to read from fifo
                            -- nodeRxFifoRdEn <= '0';
                            -- if (cnt1 >= 1) then
                                -- --dataProcState <= nextNodeReadState;
                                -- nodeState <= nodeRxDebug1;
                                -- cnt1 <= 1;
                            -- else
                                -- cnt1 <= cnt1 + 1;
                            -- end if;
                        -- when nodeRxDebug1 =>
                            -- radioTxFifoWrEn <= '1';
                            -- radioTxData <= nodeRxData;
                            -- nodeState <= nodeRxDebug2;
                        -- when nodeRxDebug2 =>
                            -- radioTxFifoWrEn <= '0';
                            -- nodeState <= checkRadioRx;                            
                
                    -- -- when waitForData =>	-- check for new data
                        -- -- -- nodeDataAvail <= '0'; -- clear data availability
                        -- -- -- if (nodeRxFifoEmpty = '0') then -- new data available
                            -- -- -- nodeRxFifoRdEn <= '1'; -- enable rx fifo read
                            -- -- -- nodeState <= forwardData;
                        -- -- -- end if;
                    -- -- -- when forwardData =>
                        -- -- -- nodeRxFifoRdEn <= '0';
                        -- -- -- nodeDataAvail <= '1'; -- notify TDMA of node data availability
                        -- -- -- nodeState <= waitForData;
                        -- -- -- --if (txFifoFull = '0') then -- loop back data to transmit back out
                            -- -- -- --txFifoWrEn <= '1';
                    -- -- -- --when readData =>   
                    -- -- -- --    dataBuffer <= rxData; -- read data received by uart
                    -- -- -- --    testState <= waitForData;
                        -- -- -- --txFifoWrEn <= '1'; -- enable tx fifo write
                    -- -- -- --when forwardData => -- pipe received data back to uart for transmission
                    -- -- -- --    if (txFifoFull = '0') then -- put data into transmit fifo
                    -- -- -- --        txData <= dataBuffer;
                    -- -- -- --        dataBuffer <= X"00"; -- clear buffer
                    -- -- -- --        txFifoWrEn <= '0';
                    -- -- -- --        testState <= waitForData;
                    -- -- -- --    end if;
                -- end case;
            -- end if;
        end process;
        -- -- node uart logic
        -- process(rst, clk)
        -- begin
            -- if rst = '0' then 
                -- nodeState <= waitForData;
                -- nodeRxFifoRdEn <= '0';
                -- nodeTxFifoWrEn <= '0';
                -- nodeDataAvail <= '0';
                -- cnt1 <= 0;

            -- elsif clk'event and clk = '1' then
                -- case nodeState is
                    -- when waitForData =>	-- check for new data
                        -- nodeDataAvail <= '0'; -- clear data availability
                        -- if (nodeRxFifoEmpty = '0') then -- new data available
                            -- nodeRxFifoRdEn <= '1'; -- enable rx fifo read
                            -- nodeState <= forwardData;
                        -- end if;
                    -- when forwardData =>
                        -- nodeRxFifoRdEn <= '0';
                        -- nodeDataAvail <= '1'; -- notify TDMA of node data availability
                        -- nodeState <= waitForData;
                        -- --if (txFifoFull = '0') then -- loop back data to transmit back out
                            -- --txFifoWrEn <= '1';
                    -- --when readData =>   
                    -- --    dataBuffer <= rxData; -- read data received by uart
                    -- --    testState <= waitForData;
                        -- --txFifoWrEn <= '1'; -- enable tx fifo write
                    -- --when forwardData => -- pipe received data back to uart for transmission
                    -- --    if (txFifoFull = '0') then -- put data into transmit fifo
                    -- --        txData <= dataBuffer;
                    -- --        dataBuffer <= X"00"; -- clear buffer
                    -- --        txFifoWrEn <= '0';
                    -- --        testState <= waitForData;
                    -- --    end if;
                -- end case;
            -- end if;
        -- end process;
        
        -- -- radio uart logic
        -- process(rst, clk)
        -- begin
            -- if rst = '0' then
                -- radioState <= waitForData;
                -- radioRxFifoRdEn <= '0';
                -- radioTxFifoWrEn <= '0';
                -- radioDataAvail <= '0';
                -- cnt2 <= 0;

            -- elsif clk'event and clk = '1' then
                -- case radioState is
                    -- when waitForData =>	-- check for new data
                        -- radioDataAvail <= '0'; -- clear data availability
                        -- if (radioRxFifoEmpty = '0') then -- new data available
                            -- radioRxFifoRdEn <= '1'; -- enable rx fifo read
                            -- radioState <= forwardData;
                        -- end if;
                    -- when forwardData =>
                        -- radioRxFifoRdEn <= '0';
                        -- radioDataAvail <= '1'; -- notify TDMA of node data availability
                        -- radioState <= waitForData;
                        -- --if (txFifoFull = '0') then -- loop back data to transmit back out
                            -- --txFifoWrEn <= '1';
                    -- --when readData =>   
                    -- --    dataBuffer <= rxData; -- read data received by uart
                    -- --    testState <= waitForData;
                        -- --txFifoWrEn <= '1'; -- enable tx fifo write
                    -- --when forwardData => -- pipe received data back to uart for transmission
                    -- --    if (txFifoFull = '0') then -- put data into transmit fifo
                    -- --        txData <= dataBuffer;
                    -- --        dataBuffer <= X"00"; -- clear buffer
                    -- --        txFifoWrEn <= '0';
                    -- --        testState <= waitForData;
                    -- --    end if;
                -- end case;
            -- end if;
        -- end process;
         
end architecture;
