-- uart.vhd
--
-- UART model for the camera link interface.  
--
-- David Hyde
-- NASA MSFC EI31
-- 3/6/2006
library ieee;
use ieee.std_logic_1164.all;
use ieee.std_logic_unsigned.all;
use work.compDec.all;
use work.meshPack.all;

entity uart is
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
end uart;

architecture struct of uart is

    component uartRx is
        generic(
            ctrStrtCnt : integer range 0 to baudIntSize := baudCtrCnt;
            baudCnt : integer range 0 to baudIntSize := baudWidthCnt
        );
        port (
            clk          : in  std_logic;
            rst          : in  std_logic;
            rx           : in  std_logic;
            rxData       : out std_logic_vector(7 downto 0);
            rxFifoWrEn   : out std_logic;
            rxFifoFull   : in  std_logic;
            frameError   : out std_logic  
        );
    end component;
     
    component uartTx is
        generic(
            ctrStrtCnt : integer range 0 to baudIntSize := baudCtrCnt;
            baudCnt : integer range 0 to baudIntSize := baudWidthCnt
        );
        port (
            clk          : in  std_logic;
            rst          : in  std_logic;
            tx           : out std_logic;
            txData	     : in  std_logic_vector(7 downto 0);
            txFifoRdEn   : out std_logic;
            txFifoEmpty  : in  std_logic;
            txEmpty      : out std_logic 
        );
    end component;

    signal rxFifoDin,txFifoDout : std_logic_vector(7 downto 0);
    signal txFifoRdEn,txFifoEmpty,rxFifoWrEn,rxFifoFull : std_logic;

    begin

        --fifos
        txFifo :  uartFifo port map ( 
            din  	=> txData,  
            dout 	=> txFifoDout, 
            wrEn 	=> txFifoWrEn, 
            rdEn 	=> txFifoRdEn, 
            clk  	=> clk,  
            full 	=> txFifoFull, 
            empty	=> txFifoEmpty,
            rst  	=> rst  
        );

        rxFifo :  uartFifo port map ( 
            din  	=> rxFifoDin,  
            dout 	=> rxData, 
            wrEn 	=> rxFifoWrEn, 
            rdEn 	=> rxFifoRdEn, 
            clk  	=> clk,  
            full 	=> rxFifoFull, 
            empty	=> rxFifoEmpty,
            rst  	=> rst  
        );

        uartRx_i: uartRx 
        generic map(
            ctrStrtCnt 	=> ctrStrtCnt,
            baudCnt	=> baudCnt
        )
        port map (
            clk          => clk,
            rst          => rst,
            rx           => rx,
            rxData       => rxFifoDin,
            rxFifoWrEn   => rxFifoWrEn,
            rxFifoFull   => rxFifoFull,
            frameError   => frameError 
        );
        
        uartTx_i: uartTx 
        generic map(
            ctrStrtCnt 	=> ctrStrtCnt,
            baudCnt	=> baudCnt
        )
        port map(
            clk          => clk,
            rst          => rst,
            tx           => tx,
            txData	     => txFifoDout,
            txFifoRdEn   => txFifoRdEn, 
            txFifoEmpty  => txFifoEmpty,
            txEmpty      => txEmpty 
        );
end struct;

