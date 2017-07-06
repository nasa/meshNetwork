-- uartRx.vhd
--
-- UART transmitter model for the camera link interface.  
--
-- David Hyde
-- NASA MSFC EI31
-- 3/6/2006
library ieee;
use ieee.std_logic_1164.all;
use ieee.std_logic_unsigned.all;
use work.meshPack.all;

entity uartTx is
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
		txEmpty      : out std_logic );
end uartTx;

architecture behave of uartTx is

type txStates is (wait4Data,chkTxImm,txHigh,txStart,txByte,txStop);
signal txState,nextState : txStates;

signal baudEnCnt               : std_logic_vector(3 downto 0);
signal shiftCnt                : std_logic_vector(2 downto 0);
signal txDataReg               : std_logic_vector(7 downto 0);
signal cnt 						: integer range 0 to baudIntSize;
signal txEnDelCnt : integer range 0 to 3;
begin

-- transmitter
process(rst, clk)
begin
	if rst = '0' then
		txState <= wait4Data;
		txEmpty <= '1';
		txFifoRdEn <= '0';
		cnt <= 0;
		shiftCnt <= "000";
		tx <= '1';

        -- synthesis
        txDataReg <= X"00";

	elsif rising_edge(clk) then
		case txState is
			when wait4Data =>	
				tx <= '1';   
				if txFifoEmpty = '0' then
					txFifoRdEn <= '1';
					txEmpty <= '0';
                    tx <= '0';
                    cnt <= 1;
					txState <= txStart;
				end if;

			when txHigh =>
				txFifoRdEn <= '0';
                tx <= '1';
				if cnt = baudCnt then
					cnt <= 1;
                    tx <= '0';
					txState <= txStart;
				else
					cnt <= cnt + 1;
				end if;

			when chkTxImm => 
				--chk FIFO immediately after stop bit is tx'ed
				--if data is available, skip txHigh state
				--and immediately tx new byte
				if txFifoEmpty = '0' then
					txFifoRdEn <= '1';
					txEmpty <= '0';
                    tx <= '0';
					txState <= txStart;
				else
					txEmpty <= '1';
                    tx <= '1';
					txState <= wait4Data;
				end if;
			when txStart =>
				txFifoRdEn <= '0';
				if cnt = baudCnt then
					cnt <= 1;
					txState <= txByte;
					txDataReg <=  '0' & txDataReg(7 downto 1); 
					tx <= txDataReg(0);
				elsif cnt = 3 then
                    --load data from FIFO here (gives the FIFO time to output valid data)
                    txDataReg <= txData;
                    cnt <= cnt + 1;
				else
                    tx <= '0';
					cnt <= cnt + 1;
				end if;	
			when txByte =>
				if cnt = baudCnt then
					cnt <= 1;
					shiftCnt <= shiftCnt + '1';
					if shiftCnt = "111" then
						txState <= txStop;
						tx <= '1';	
                        cnt <= 1;
					else
						txDataReg <=  '0' & txDataReg(7 downto 1); 
						tx <= txDataReg(0);
					end if;
				else
					cnt <= cnt + 1;
				end if;
			when txStop =>
				if cnt = baudCnt-1 then
					cnt <= 0;
					
					txState <= chkTxImm;
				else
					cnt <= cnt + 1;
				end if;
		end case;
	end if;
end process;



------------------------------------------------------------------------------------------


end behave;

