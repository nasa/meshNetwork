--
-- rstDualRankSync.vhd
-- 
--    This module is used to synchronize the asyncronous reset input.  The reset output can then be used as an async reset 
--      throughout the design.
-- 
--    The synchronous reset output will assert asynchronously as soon as the exteranl async reset is asserted but
--     it will de-assert synchronously.  This design guarantees the timing of the reset release with respect 
--      the the rising clock edge and allows the reset to remian out of the datapath feeding the D-input to the
--      flops in the design.  The design was taken from the paper:
--       http://www.sunburst-design.com/papers/CummingsSNUG2003Boston_Resets.pdf
-- 
-- David Hyde
-- NASA ES33
-- 
library ieee;
use ieee.std_logic_1164.all;
use ieee.std_logic_unsigned.all;

entity rstDualRankSync is
generic ( asyncRstAssertVal : std_logic := '0');
port (
    clk              : in  std_logic;
    asyncRst         : in  std_logic;
	syncRst          : out std_logic );
end rstDualRankSync;

architecture behave of rstDualRankSync is

signal ff0Q : std_logic;

begin

process (asyncRst, clk)
begin
	if asyncRst = asyncRstAssertVal then
		syncRst <= asyncRstAssertVal;
		ff0Q    <= asyncRstAssertVal;
	elsif rising_edge(clk) then
		ff0Q <= not(asyncRstAssertVal);
		syncRst <= ff0Q;
	end if;
end process;
end behave;

