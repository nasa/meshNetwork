
library ieee;
use ieee.std_logic_1164.all;
use work.meshPack.all;

package compDec is

    -- Clocks
    component customClock is
        generic(
            clockDivider : integer range 0 to 100000 := 2;
            halfClk : integer range 0 to 100000 := 1
        );
        port (
                clk     : in  std_logic;
                rst     : in  std_logic;
                clkOut  : out std_logic 
        );
    end component;

    -- Dual rank syncs
    component rstDualRankSync is
        generic ( asyncRstAssertVal : std_logic := '0');
        port (
            clk              : in  std_logic;
            asyncRst         : in  std_logic;
            syncRst          : out std_logic );
    end component;
    
    component dualRankSync is
    generic ( resetVal : std_logic := '0');
    port (
    	inData, clk, rst : in std_logic;
    	outData          : out std_logic );
    end component;

    component dualRankSyncBus is
    generic ( 
        resetVal    : std_logic := '0';
        busWidth    : integer := 2
    );
    port (
    	clk, rst        : in  std_logic;
        inData          : in  std_logic_vector(busWidth - 1 downto 0);
    	outData         : out std_logic_vector(busWidth - 1 downto 0)
    );
    end component;

    -- SLIP
    component slipMsg is
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
     end component;
    
    --User interface
    component userInterface is
        port (
            clk             : in std_logic;
            rst             : in std_logic;
            enable          : in std_logic;
            failsafe        : in std_logic;
            dipSwitch1      : in std_logic;
            dipSwitch2      : in std_logic;
            dipSwitch3      : in std_logic;
            dipSwitch4      : in std_logic;
            LED1In          : in std_logic;
            LED2In          : in std_logic;
            LED3In          : in std_logic;
            LED4In          : in std_logic;
            LED5In          : in std_logic;
            LED6In          : in std_logic;
            LED7In          : in std_logic;
            LED8In          : in std_logic;
            io1Out          : out std_logic;
            io2Out          : out std_logic;
            io3Out          : out std_logic;
            io4Out          : out std_logic;
            io5Out          : out std_logic;
            io6Out          : out std_logic;
            io7In           : in std_logic;
            io8In           : in std_logic;
            LED1Out         : out std_logic;
            LED2Out         : out std_logic;
            LED3Out         : out std_logic;
            LED4Out         : out std_logic;
            LED5Out         : out std_logic;
            LED6Out         : out std_logic;
            LED7Out         : out std_logic;
            LED8Out         : out std_logic
        );
    end component;
    
    -- Clock time
    component clockTime is
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
            timeSynced      : out std_logic;
            gps3DFix        : out std_logic;
            ppsMissed       : out std_logic
        );
    end component;
    
    -- TDMA
    component tdma is -- communication management
        port (
            clk                 : in std_logic;
            rst                 : in std_logic;
            second              : in integer range 0 to maxTimeSec;
            secondFrac          : in integer range 0 to clkInSpeed;
            timeSynced          : in std_logic;
            tdmaInited          : in std_logic;
            tdmaInitTime        : in integer range 0 to maxTimeSec;
            transmitData        : out std_logic;
            receiveData         : out std_logic;
            tdmaSleep           : out std_logic;
            radioModeOut        : out radioModes -- radio mode
        );
    end component;
    
    component tdmaCtrl is -- control
        port (
            clk                 : in std_logic;
            rst                 : in std_logic;
            second              : in integer range 0 to maxTimeSec;
            secondFrac          : in integer range 0 to clkInSpeed;
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
    end component;
    
    -- Data management
    component memInterface is
        port (
            clk                 : in std_logic;
            rst                 : in std_logic;
            nodeMemRd           : in std_logic;
            nodeMemWr           : in std_logic;
            nodeDataIn          : in std_logic_vector(7 downto 0);
            nodeDataAddr        : in std_logic_vector(17 downto 0);
            nodeDataOut         : out std_logic_vector(7 downto 0);
            nodeMemComp         : out std_logic;
            radioMemRd          : in std_logic;
            radioMemWr          : in std_logic;
            radioDataIn         : in std_logic_vector(7 downto 0);
            radioDataAddr       : in std_logic_vector(17 downto 0);
            radioDataOut        : out std_logic_vector(7 downto 0);
            radioMemComp        : out std_logic;
            tdmaCtrlMemRd       : in std_logic;
            tdmaCtrlMemWr       : in std_logic;
            tdmaCtrlDataIn      : in std_logic_vector(7 downto 0);
            tdmaCtrlDataAddr    : in std_logic_vector(17 downto 0);
            tdmaCtrlDataOut     : out std_logic_vector(7 downto 0);
            tdmaCtrlMemComp     : out std_logic;
            currMemAct          : out MemAction;
            memRdEn             : out std_logic;
            rdComplete          : in std_logic;
            memWrEn             : out std_logic;
            wrComplete          : in std_logic;
            memDataAddr         : out std_logic_vector(17 downto 0);
            dataToMem           : out std_logic_vector(7 downto 0);
            dataFromMem         : in std_logic_vector(7 downto 0)
        );
    end component;
    
    
    component memController is
        port(
            rst                 : in  std_logic;
            clk                 : in  std_logic;
            dataAddr            : in std_logic_vector(17 downto 0);
            rdEn                : in std_logic;
            rdData              : out std_logic_vector(7 downto 0);
            rdInProgress        : out std_logic;
            rdComplete          : out std_logic;
            wrEn                : in std_logic;
            wrData              : in std_logic_vector(7 downto 0);
            wrInProgress        : out std_logic;
            wrComplete          : out std_logic;
            framEn              : out std_logic; 
            framWrEn            : out std_logic; 
            framOeEn            : out std_logic; 
            framSleep           : out std_logic; 
            framData            : inout std_logic_vector(7 downto 0); 
            framAddr            : out std_logic_vector(17 downto 0)
        );
    end component;
    
    component dataProcessor is
        port (
            clk                 : in std_logic;
            rst                 : in std_logic;
            enable              : in std_logic;             
            --tdmaInited          : in std_logic;
            tdmaTransmitFlag    : in std_logic;
            --tdmaFifoWrEn        : out std_logic;
            --tdmaFifoOut         : out std_logic_vector(7 downto 0);
            radioRxFifoEmpty    : in std_logic;
            radioRxFifoRdEn     : out std_logic;          
            radioTxFifoFull     : in std_logic;
            radioTxFifoWrEn     : out std_logic;
            meshDataIn          : in std_logic_vector(7 downto 0);
            nodeDataOut         : out std_logic_vector(7 downto 0);
            nodeRxFifoEmpty     : in std_logic;
            nodeRxFifoRdEn      : out std_logic;          
            nodeTxFifoFull      : in std_logic;
            nodeTxFifoWrEn      : out std_logic;
            nodeDataIn          : in std_logic_vector(7 downto 0);
            meshDataOut         : out std_logic_vector(7 downto 0);
            tdmaCtrlFifoRdEn    : out std_logic;
            tdmaCtrlFifoEmpty   : in std_logic;
            tdmaCtrlIn          : in std_logic_vector(7 downto 0);
            parserFifoWrEn      : out std_logic;
            parserFifoOut       : out std_logic_vector(7 downto 0);
            parserFifoRdEn      : out std_logic;
            parserFifoEmpty     : in std_logic;
            parserIn            : in std_logic_vector(7 downto 0);
            nodeMemRd           : out std_logic;
            nodeMemWr           : out std_logic;
            nodeMemDataOut      : out std_logic_vector(7 downto 0);
            nodeDataAddr        : out std_logic_vector(17 downto 0);
            nodeMemDataIn       : in std_logic_vector(7 downto 0);
            nodeMemComp         : in std_logic;
            radioMemRd          : out std_logic;
            radioMemWr          : out std_logic;
            radioMemDataOut     : out std_logic_vector(7 downto 0);
            radioDataAddr       : out std_logic_vector(17 downto 0);
            radioMemDataIn      : in std_logic_vector(7 downto 0);
            radioMemComp        : in std_logic;
            tdmaCtrlMemRd       : out std_logic;
            tdmaCtrlMemWr       : out std_logic;
            tdmaCtrlMemDataOut  : out std_logic_vector(7 downto 0);
            tdmaCtrlDataAddr    : out std_logic_vector(17 downto 0);
            tdmaCtrlMemDataIn   : in std_logic_vector(7 downto 0);
            tdmaCtrlMemComp     : in std_logic;
            currMemAct          : in MemAction
        );
    end component;
    
    component dataParser is
        port (
            clk                 : in std_logic;
            rst                 : in std_logic;
            dataInFifoWrEn      : in std_logic;
            dataIn              : in std_logic_vector(7 downto 0);
            dataOutFifoEmpty    : out std_logic;
            dataOutFifoRdEn     : in std_logic;
            dataOut             : out std_logic_vector(7 downto 0);
            tdmaInited          : in std_logic;
            tdmaInitTimeRcvd    : out std_logic;
            tdmaInitTime        : out integer range 0 to maxTimeSec
        );
    end component;
    
    -- UART
    component uart is
        generic(
            ctrStrtCnt : integer range 0 to baudIntSize := baudCtrCnt;
            baudCnt : integer range 0 to baudIntSize := baudWidthCnt
        );
        port (
            clk          : in  std_logic;
            rst          : in  std_logic;
            rx           : in  std_logic;
            tx           : out std_logic;
            rxData       : out std_logic_vector(7 downto 0);
            rxFifoRdEn   : in  std_logic;
            rxFifoEmpty  : out std_logic;
            txData	     : in  std_logic_vector(7 downto 0);
            txFifoWrEn   : in  std_logic;
            txFifoFull   : out std_logic;
            txEmpty      : out std_logic;
            frameError   : out std_logic  
        );
    end component;
    
    -- FIFOs
    component uartFifo is
        port( 
            din   : in    std_logic_vector(7 downto 0);
            dout  : out   std_logic_vector(7 downto 0);
            wrEn  : in    std_logic;
            rdEn  : in    std_logic;
            clk   : in    std_logic;
            full  : out   std_logic;
            empty : out   std_logic;
            rst   : in    std_logic
        );
    end component;
    
    -- Hardware
    component radio is
        port (
            clk         : in std_logic;
            rst         : in std_logic;
            radioMode   : in radioModes;
            sendDataIn  : in std_logic;
            dataIn      : in std_logic_vector(7 downto 0);
            dataOut     : out std_logic_vector(7 downto 0);
            sendDataOut : out std_logic;
            sleepStatus : in std_logic;
            sleepOut    : out std_logic
        );
    end component;
    
end package;
