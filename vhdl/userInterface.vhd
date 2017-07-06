-- userInterface.vhd
--
-- Input/output with user.  
--
-- Chris Becker
-- NASA MSFC EV42
-- 3/22/2016

library ieee;
use ieee.std_logic_1164.all;
use work.meshPack.nodeId;

entity userInterface is
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
end userInterface;

architecture behave of userInterface is
    begin
    
        -- For now, pipe dip switches right out
        io1Out <= dipSwitch1;
        io2Out <= dipSwitch2;
        io3Out <= dipSwitch3;
        io4Out <= dipSwitch4;
        
        -- Output to BBB
        io5Out <= enable;
        io6Out <= failsafe;
        
        -- Set LED status
        LED1Out <= LED1In;
        LED2Out <= LED2In;
        LED3Out <= LED3In;
        LED4Out <= LED4In;
        LED5Out <= LED5In;
        LED6Out <= failsafe;
        LED7Out <= LED7In;
        LED8Out <= LED8In;
        
        
        process (clk)
            variable switchValue1, switchValue2, switchValue3, switchValue4 : integer range 0 to 4;
            
            begin
                if clk'event and clk = '1' then
                    -- Determine node id
                    if (dipSwitch1 = '1') then
                        switchValue1 := 1;
                    else
                        switchValue1 := 0;
                    end if;
                    if (dipSwitch2 = '1') then
                        switchValue2 := 2;
                    else
                        switchValue2 := 0;
                    end if;
                    if (dipSwitch3 = '1') then
                        switchValue3 := 4;
                    else
                        switchValue3 := 0;
                    end if;
            
                    nodeId <= switchValue1 + switchValue2 + switchValue3;
                end if;
        end process;
        
end behave;
