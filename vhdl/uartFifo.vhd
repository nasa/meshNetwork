-- Version: v11.6 11.6.0.34

library ieee;
use ieee.std_logic_1164.all;
library proasic3l;
use proasic3l.all;

entity uartFifo is

    port( din   : in    std_logic_vector(7 downto 0);
          dout  : out   std_logic_vector(7 downto 0);
          wrEn  : in    std_logic;
          rdEn  : in    std_logic;
          clk   : in    std_logic;
          full  : out   std_logic;
          empty : out   std_logic;
          rst   : in    std_logic
        );

end uartFifo;

architecture DEF_ARCH of uartFifo is 

  component AND2
    port( A : in    std_logic := 'U';
          B : in    std_logic := 'U';
          Y : out   std_logic
        );
  end component;

  component AND3
    port( A : in    std_logic := 'U';
          B : in    std_logic := 'U';
          C : in    std_logic := 'U';
          Y : out   std_logic
        );
  end component;

  component XNOR2
    port( A : in    std_logic := 'U';
          B : in    std_logic := 'U';
          Y : out   std_logic
        );
  end component;

  component AO1
    port( A : in    std_logic := 'U';
          B : in    std_logic := 'U';
          C : in    std_logic := 'U';
          Y : out   std_logic
        );
  end component;

  component XOR2
    port( A : in    std_logic := 'U';
          B : in    std_logic := 'U';
          Y : out   std_logic
        );
  end component;

  component DFN1C0
    port( D   : in    std_logic := 'U';
          CLK : in    std_logic := 'U';
          CLR : in    std_logic := 'U';
          Q   : out   std_logic
        );
  end component;

  component INV
    port( A : in    std_logic := 'U';
          Y : out   std_logic
        );
  end component;

  component DFN1E1C0
    port( D   : in    std_logic := 'U';
          CLK : in    std_logic := 'U';
          CLR : in    std_logic := 'U';
          E   : in    std_logic := 'U';
          Q   : out   std_logic
        );
  end component;

  component RAM4K9
    generic (MEMORYFILE:string := "");

    port( ADDRA11 : in    std_logic := 'U';
          ADDRA10 : in    std_logic := 'U';
          ADDRA9  : in    std_logic := 'U';
          ADDRA8  : in    std_logic := 'U';
          ADDRA7  : in    std_logic := 'U';
          ADDRA6  : in    std_logic := 'U';
          ADDRA5  : in    std_logic := 'U';
          ADDRA4  : in    std_logic := 'U';
          ADDRA3  : in    std_logic := 'U';
          ADDRA2  : in    std_logic := 'U';
          ADDRA1  : in    std_logic := 'U';
          ADDRA0  : in    std_logic := 'U';
          ADDRB11 : in    std_logic := 'U';
          ADDRB10 : in    std_logic := 'U';
          ADDRB9  : in    std_logic := 'U';
          ADDRB8  : in    std_logic := 'U';
          ADDRB7  : in    std_logic := 'U';
          ADDRB6  : in    std_logic := 'U';
          ADDRB5  : in    std_logic := 'U';
          ADDRB4  : in    std_logic := 'U';
          ADDRB3  : in    std_logic := 'U';
          ADDRB2  : in    std_logic := 'U';
          ADDRB1  : in    std_logic := 'U';
          ADDRB0  : in    std_logic := 'U';
          DINA8   : in    std_logic := 'U';
          DINA7   : in    std_logic := 'U';
          DINA6   : in    std_logic := 'U';
          DINA5   : in    std_logic := 'U';
          DINA4   : in    std_logic := 'U';
          DINA3   : in    std_logic := 'U';
          DINA2   : in    std_logic := 'U';
          DINA1   : in    std_logic := 'U';
          DINA0   : in    std_logic := 'U';
          DINB8   : in    std_logic := 'U';
          DINB7   : in    std_logic := 'U';
          DINB6   : in    std_logic := 'U';
          DINB5   : in    std_logic := 'U';
          DINB4   : in    std_logic := 'U';
          DINB3   : in    std_logic := 'U';
          DINB2   : in    std_logic := 'U';
          DINB1   : in    std_logic := 'U';
          DINB0   : in    std_logic := 'U';
          WIDTHA0 : in    std_logic := 'U';
          WIDTHA1 : in    std_logic := 'U';
          WIDTHB0 : in    std_logic := 'U';
          WIDTHB1 : in    std_logic := 'U';
          PIPEA   : in    std_logic := 'U';
          PIPEB   : in    std_logic := 'U';
          WMODEA  : in    std_logic := 'U';
          WMODEB  : in    std_logic := 'U';
          BLKA    : in    std_logic := 'U';
          BLKB    : in    std_logic := 'U';
          WENA    : in    std_logic := 'U';
          WENB    : in    std_logic := 'U';
          CLKA    : in    std_logic := 'U';
          CLKB    : in    std_logic := 'U';
          RESET   : in    std_logic := 'U';
          DOUTA8  : out   std_logic;
          DOUTA7  : out   std_logic;
          DOUTA6  : out   std_logic;
          DOUTA5  : out   std_logic;
          DOUTA4  : out   std_logic;
          DOUTA3  : out   std_logic;
          DOUTA2  : out   std_logic;
          DOUTA1  : out   std_logic;
          DOUTA0  : out   std_logic;
          DOUTB8  : out   std_logic;
          DOUTB7  : out   std_logic;
          DOUTB6  : out   std_logic;
          DOUTB5  : out   std_logic;
          DOUTB4  : out   std_logic;
          DOUTB3  : out   std_logic;
          DOUTB2  : out   std_logic;
          DOUTB1  : out   std_logic;
          DOUTB0  : out   std_logic
        );
  end component;

  component NAND2
    port( A : in    std_logic := 'U';
          B : in    std_logic := 'U';
          Y : out   std_logic
        );
  end component;

  component AND2A
    port( A : in    std_logic := 'U';
          B : in    std_logic := 'U';
          Y : out   std_logic
        );
  end component;

  component DFN1P0
    port( D   : in    std_logic := 'U';
          CLK : in    std_logic := 'U';
          PRE : in    std_logic := 'U';
          Q   : out   std_logic
        );
  end component;

  component GND
    port(Y : out std_logic); 
  end component;

  component VCC
    port(Y : out std_logic); 
  end component;

    signal \full\, \empty\, \MEM_RADDR[0]\, \RBINNXTSHIFT[0]\, 
        \MEM_WADDR[0]\, \WBINNXTSHIFT[0]\, \MEM_RADDR[1]\, 
        \RBINNXTSHIFT[1]\, \MEM_WADDR[1]\, \WBINNXTSHIFT[1]\, 
        \MEM_RADDR[2]\, \RBINNXTSHIFT[2]\, \MEM_WADDR[2]\, 
        \WBINNXTSHIFT[2]\, \MEM_RADDR[3]\, \RBINNXTSHIFT[3]\, 
        \MEM_WADDR[3]\, \WBINNXTSHIFT[3]\, \MEM_RADDR[4]\, 
        \RBINNXTSHIFT[4]\, \MEM_WADDR[4]\, \WBINNXTSHIFT[4]\, 
        \MEM_RADDR[5]\, \RBINNXTSHIFT[5]\, \MEM_WADDR[5]\, 
        \WBINNXTSHIFT[5]\, \MEM_RADDR[6]\, \RBINNXTSHIFT[6]\, 
        \MEM_WADDR[6]\, \WBINNXTSHIFT[6]\, \MEM_RADDR[7]\, 
        \RBINNXTSHIFT[7]\, \MEM_WADDR[7]\, \WBINNXTSHIFT[7]\, 
        \MEM_RADDR[8]\, \RBINNXTSHIFT[8]\, \MEM_WADDR[8]\, 
        \WBINNXTSHIFT[8]\, \MEM_RADDR[9]\, \RBINNXTSHIFT[9]\, 
        \MEM_WADDR[9]\, \WBINNXTSHIFT[9]\, FULLINT, MEMORYWE, 
        MEMWENEG, \WGRY[0]\, \WGRY[1]\, \WGRY[2]\, \WGRY[3]\, 
        \WGRY[4]\, \WGRY[5]\, \WGRY[6]\, \WGRY[7]\, \WGRY[8]\, 
        \WGRY[9]\, EMPTYINT, MEMORYRE, MEMRENEG, DVLDI, DVLDX, 
        \RGRY[0]\, \RGRY[1]\, \RGRY[2]\, \RGRY[3]\, \RGRY[4]\, 
        \RGRY[5]\, \RGRY[6]\, \RGRY[7]\, \RGRY[8]\, \RGRY[9]\, 
        \QXI[0]\, \QXI[1]\, \QXI[2]\, \QXI[3]\, \QXI[4]\, 
        \QXI[5]\, \QXI[6]\, \QXI[7]\, XOR2_9_Y, XOR2_17_Y, 
        XOR2_33_Y, XOR2_34_Y, XOR2_50_Y, XOR2_56_Y, XOR2_43_Y, 
        XOR2_14_Y, XOR2_42_Y, XOR2_26_Y, AND2_27_Y, AND2_13_Y, 
        AND2_33_Y, AND2_3_Y, AND2_12_Y, AND2_1_Y, AND2_24_Y, 
        AND2_19_Y, AND2_26_Y, XOR2_45_Y, XOR2_3_Y, XOR2_7_Y, 
        XOR2_1_Y, XOR2_8_Y, XOR2_19_Y, XOR2_40_Y, XOR2_2_Y, 
        XOR2_10_Y, XOR2_51_Y, AND2_20_Y, AO1_22_Y, AND2_6_Y, 
        AO1_7_Y, AND2_17_Y, AO1_27_Y, AND2_15_Y, AO1_23_Y, 
        AND2_38_Y, AND2_16_Y, AO1_6_Y, AND2_25_Y, AND2_34_Y, 
        AND2_29_Y, AO1_15_Y, AND2_44_Y, AND2_2_Y, AND2_41_Y, 
        AND2_0_Y, AND2_47_Y, AND2_46_Y, AO1_11_Y, AO1_25_Y, 
        AO1_12_Y, AO1_2_Y, AO1_0_Y, AO1_13_Y, AO1_24_Y, AO1_18_Y, 
        XOR2_4_Y, XOR2_6_Y, XOR2_39_Y, XOR2_30_Y, XOR2_48_Y, 
        XOR2_22_Y, XOR2_24_Y, XOR2_58_Y, XOR2_53_Y, NAND2_1_Y, 
        XOR2_25_Y, XOR2_20_Y, XOR2_13_Y, XOR2_41_Y, XOR2_37_Y, 
        XOR2_21_Y, XOR2_29_Y, XOR2_35_Y, XOR2_36_Y, XOR2_11_Y, 
        AND2_32_Y, AND2_7_Y, AND2_4_Y, AND2_35_Y, AND2_8_Y, 
        AND2_37_Y, AND2_11_Y, AND2_42_Y, AND2_36_Y, XOR2_28_Y, 
        XOR2_23_Y, XOR2_12_Y, XOR2_52_Y, XOR2_49_Y, XOR2_46_Y, 
        XOR2_0_Y, XOR2_38_Y, XOR2_15_Y, XOR2_32_Y, AND2_45_Y, 
        AO1_16_Y, AND2_14_Y, AO1_3_Y, AND2_9_Y, AO1_4_Y, 
        AND2_40_Y, AO1_14_Y, AND2_39_Y, AND2_43_Y, AO1_19_Y, 
        AND2_31_Y, AND2_5_Y, AND2_10_Y, AO1_5_Y, AND2_23_Y, 
        AND2_21_Y, AND2_30_Y, AND2_28_Y, AND2_18_Y, AND2_22_Y, 
        AO1_1_Y, AO1_10_Y, AO1_26_Y, AO1_8_Y, AO1_21_Y, AO1_9_Y, 
        AO1_17_Y, AO1_20_Y, XOR2_18_Y, XOR2_55_Y, XOR2_44_Y, 
        XOR2_47_Y, XOR2_16_Y, XOR2_27_Y, XOR2_5_Y, XOR2_54_Y, 
        XOR2_57_Y, \RAM4K9_QXI[7]_DOUTA0\, \RAM4K9_QXI[7]_DOUTA1\, 
        \RAM4K9_QXI[7]_DOUTA2\, \RAM4K9_QXI[7]_DOUTA3\, 
        \RAM4K9_QXI[7]_DOUTA4\, \RAM4K9_QXI[7]_DOUTA5\, 
        \RAM4K9_QXI[7]_DOUTA6\, \RAM4K9_QXI[7]_DOUTA7\, AND3_6_Y, 
        XNOR2_17_Y, XNOR2_7_Y, XNOR2_4_Y, XNOR2_8_Y, XNOR2_9_Y, 
        XNOR2_18_Y, XNOR2_6_Y, XNOR2_13_Y, XNOR2_15_Y, XNOR2_11_Y, 
        AND3_5_Y, AND3_7_Y, AND3_4_Y, AND2A_0_Y, AND3_0_Y, 
        XOR2_31_Y, XNOR2_1_Y, XNOR2_12_Y, XNOR2_16_Y, XNOR2_14_Y, 
        XNOR2_0_Y, XNOR2_3_Y, XNOR2_10_Y, XNOR2_5_Y, XNOR2_2_Y, 
        AND3_3_Y, AND3_2_Y, AND3_1_Y, NAND2_0_Y, \VCC\, \GND\
         : std_logic;
    signal GND_power_net1 : std_logic;
    signal VCC_power_net1 : std_logic;

begin 

    full <= \full\;
    empty <= \empty\;
    \GND\ <= GND_power_net1;
    \VCC\ <= VCC_power_net1;

    AND2_2 : AND2
      port map(A => AND2_20_Y, B => XOR2_7_Y, Y => AND2_2_Y);
    
    AND3_6 : AND3
      port map(A => AND3_7_Y, B => AND3_5_Y, C => AND3_4_Y, Y => 
        AND3_6_Y);
    
    AND2_20 : AND2
      port map(A => XOR2_45_Y, B => XOR2_3_Y, Y => AND2_20_Y);
    
    XNOR2_13 : XNOR2
      port map(A => \RBINNXTSHIFT[6]\, B => \MEM_WADDR[6]\, Y => 
        XNOR2_13_Y);
    
    AO1_11 : AO1
      port map(A => XOR2_3_Y, B => AND2_46_Y, C => AND2_27_Y, Y
         => AO1_11_Y);
    
    AND2_11 : AND2
      port map(A => \MEM_WADDR[7]\, B => \GND\, Y => AND2_11_Y);
    
    \XOR2_WBINNXTSHIFT[2]\ : XOR2
      port map(A => XOR2_55_Y, B => AO1_1_Y, Y => 
        \WBINNXTSHIFT[2]\);
    
    AND2_22 : AND2
      port map(A => \MEM_WADDR[0]\, B => MEMORYWE, Y => AND2_22_Y);
    
    \DFN1C0_RGRY[9]\ : DFN1C0
      port map(D => XOR2_26_Y, CLK => clk, CLR => rst, Q => 
        \RGRY[9]\);
    
    DFN1C0_full : DFN1C0
      port map(D => FULLINT, CLK => clk, CLR => rst, Q => \full\);
    
    XNOR2_9 : XNOR2
      port map(A => \RBINNXTSHIFT[3]\, B => \MEM_WADDR[3]\, Y => 
        XNOR2_9_Y);
    
    XOR2_19 : XOR2
      port map(A => \MEM_RADDR[5]\, B => \GND\, Y => XOR2_19_Y);
    
    AND2_44 : AND2
      port map(A => AND2_34_Y, B => AND2_38_Y, Y => AND2_44_Y);
    
    XOR2_1 : XOR2
      port map(A => \MEM_RADDR[3]\, B => \GND\, Y => XOR2_1_Y);
    
    XOR2_23 : XOR2
      port map(A => \MEM_WADDR[1]\, B => \GND\, Y => XOR2_23_Y);
    
    XOR2_47 : XOR2
      port map(A => \MEM_WADDR[4]\, B => \GND\, Y => XOR2_47_Y);
    
    XOR2_38 : XOR2
      port map(A => \MEM_WADDR[7]\, B => \GND\, Y => XOR2_38_Y);
    
    \XOR2_RBINNXTSHIFT[0]\ : XOR2
      port map(A => \MEM_RADDR[0]\, B => MEMORYRE, Y => 
        \RBINNXTSHIFT[0]\);
    
    AO1_7 : AO1
      port map(A => XOR2_19_Y, B => AND2_3_Y, C => AND2_12_Y, Y
         => AO1_7_Y);
    
    \DFN1C0_WGRY[6]\ : DFN1C0
      port map(D => XOR2_29_Y, CLK => clk, CLR => rst, Q => 
        \WGRY[6]\);
    
    AND2_18 : AND2
      port map(A => AND2_5_Y, B => XOR2_15_Y, Y => AND2_18_Y);
    
    AND2_15 : AND2
      port map(A => XOR2_40_Y, B => XOR2_2_Y, Y => AND2_15_Y);
    
    AO1_25 : AO1
      port map(A => XOR2_7_Y, B => AO1_11_Y, C => AND2_13_Y, Y
         => AO1_25_Y);
    
    XOR2_45 : XOR2
      port map(A => \MEM_RADDR[0]\, B => MEMORYRE, Y => XOR2_45_Y);
    
    \XOR2_RBINNXTSHIFT[9]\ : XOR2
      port map(A => XOR2_53_Y, B => AO1_18_Y, Y => 
        \RBINNXTSHIFT[9]\);
    
    AND2_1 : AND2
      port map(A => \MEM_RADDR[6]\, B => \GND\, Y => AND2_1_Y);
    
    \DFN1C0_MEM_WADDR[0]\ : DFN1C0
      port map(D => \WBINNXTSHIFT[0]\, CLK => clk, CLR => rst, Q
         => \MEM_WADDR[0]\);
    
    \DFN1C0_MEM_WADDR[3]\ : DFN1C0
      port map(D => \WBINNXTSHIFT[3]\, CLK => clk, CLR => rst, Q
         => \MEM_WADDR[3]\);
    
    \DFN1C0_MEM_RADDR[1]\ : DFN1C0
      port map(D => \RBINNXTSHIFT[1]\, CLK => clk, CLR => rst, Q
         => \MEM_RADDR[1]\);
    
    AO1_8 : AO1
      port map(A => XOR2_49_Y, B => AO1_26_Y, C => AND2_35_Y, Y
         => AO1_8_Y);
    
    AND2_10 : AND2
      port map(A => AND2_43_Y, B => AND2_9_Y, Y => AND2_10_Y);
    
    AND2_7 : AND2
      port map(A => \MEM_WADDR[2]\, B => \GND\, Y => AND2_7_Y);
    
    XOR2_20 : XOR2
      port map(A => \WBINNXTSHIFT[1]\, B => \WBINNXTSHIFT[2]\, Y
         => XOR2_20_Y);
    
    AND2_12 : AND2
      port map(A => \MEM_RADDR[5]\, B => \GND\, Y => AND2_12_Y);
    
    \DFN1C0_WGRY[5]\ : DFN1C0
      port map(D => XOR2_21_Y, CLK => clk, CLR => rst, Q => 
        \WGRY[5]\);
    
    XOR2_52 : XOR2
      port map(A => \MEM_WADDR[3]\, B => \GND\, Y => XOR2_52_Y);
    
    \XOR2_WBINNXTSHIFT[0]\ : XOR2
      port map(A => \MEM_WADDR[0]\, B => MEMORYWE, Y => 
        \WBINNXTSHIFT[0]\);
    
    \DFN1C0_MEM_WADDR[4]\ : DFN1C0
      port map(D => \WBINNXTSHIFT[4]\, CLK => clk, CLR => rst, Q
         => \MEM_WADDR[4]\);
    
    AO1_15 : AO1
      port map(A => AND2_38_Y, B => AO1_24_Y, C => AO1_23_Y, Y
         => AO1_15_Y);
    
    \DFN1C0_WGRY[7]\ : DFN1C0
      port map(D => XOR2_35_Y, CLK => clk, CLR => rst, Q => 
        \WGRY[7]\);
    
    AND2_EMPTYINT : AND2
      port map(A => AND3_6_Y, B => XNOR2_17_Y, Y => EMPTYINT);
    
    XOR2_24 : XOR2
      port map(A => \MEM_RADDR[7]\, B => \GND\, Y => XOR2_24_Y);
    
    XOR2_21 : XOR2
      port map(A => \WBINNXTSHIFT[5]\, B => \WBINNXTSHIFT[6]\, Y
         => XOR2_21_Y);
    
    \XOR2_WBINNXTSHIFT[9]\ : XOR2
      port map(A => XOR2_57_Y, B => AO1_20_Y, Y => 
        \WBINNXTSHIFT[9]\);
    
    AND2_46 : AND2
      port map(A => \MEM_RADDR[0]\, B => MEMORYRE, Y => AND2_46_Y);
    
    \XOR2_RBINNXTSHIFT[8]\ : XOR2
      port map(A => XOR2_58_Y, B => AO1_24_Y, Y => 
        \RBINNXTSHIFT[8]\);
    
    XOR2_16 : XOR2
      port map(A => \MEM_WADDR[5]\, B => \GND\, Y => XOR2_16_Y);
    
    AND2_43 : AND2
      port map(A => AND2_45_Y, B => AND2_14_Y, Y => AND2_43_Y);
    
    AO1_24 : AO1
      port map(A => AND2_25_Y, B => AO1_12_Y, C => AO1_6_Y, Y => 
        AO1_24_Y);
    
    AND3_3 : AND3
      port map(A => XNOR2_1_Y, B => XNOR2_12_Y, C => XNOR2_16_Y, 
        Y => AND3_3_Y);
    
    MEMWEBUBBLE : INV
      port map(A => MEMORYWE, Y => MEMWENEG);
    
    AND2_6 : AND2
      port map(A => XOR2_7_Y, B => XOR2_1_Y, Y => AND2_6_Y);
    
    AND3_0 : AND3
      port map(A => AND3_2_Y, B => AND3_3_Y, C => AND3_1_Y, Y => 
        AND3_0_Y);
    
    \DFN1C0_MEM_RADDR[2]\ : DFN1C0
      port map(D => \RBINNXTSHIFT[2]\, CLK => clk, CLR => rst, Q
         => \MEM_RADDR[2]\);
    
    XOR2_57 : XOR2
      port map(A => \MEM_WADDR[9]\, B => \GND\, Y => XOR2_57_Y);
    
    \DFN1C0_RGRY[2]\ : DFN1C0
      port map(D => XOR2_33_Y, CLK => clk, CLR => rst, Q => 
        \RGRY[2]\);
    
    XOR2_33 : XOR2
      port map(A => \RBINNXTSHIFT[2]\, B => \RBINNXTSHIFT[3]\, Y
         => XOR2_33_Y);
    
    XNOR2_2 : XNOR2
      port map(A => \MEM_RADDR[8]\, B => \WBINNXTSHIFT[8]\, Y => 
        XNOR2_2_Y);
    
    XOR2_49 : XOR2
      port map(A => \MEM_WADDR[4]\, B => \GND\, Y => XOR2_49_Y);
    
    \XOR2_WBINNXTSHIFT[8]\ : XOR2
      port map(A => XOR2_54_Y, B => AO1_17_Y, Y => 
        \WBINNXTSHIFT[8]\);
    
    AO1_14 : AO1
      port map(A => XOR2_32_Y, B => AND2_42_Y, C => AND2_36_Y, Y
         => AO1_14_Y);
    
    XOR2_4 : XOR2
      port map(A => \MEM_RADDR[1]\, B => \GND\, Y => XOR2_4_Y);
    
    AND3_1 : AND3
      port map(A => XNOR2_14_Y, B => XNOR2_0_Y, C => XNOR2_3_Y, Y
         => AND3_1_Y);
    
    XOR2_55 : XOR2
      port map(A => \MEM_WADDR[2]\, B => \GND\, Y => XOR2_55_Y);
    
    AND2_24 : AND2
      port map(A => \MEM_RADDR[7]\, B => \GND\, Y => AND2_24_Y);
    
    XNOR2_0 : XNOR2
      port map(A => \MEM_RADDR[4]\, B => \WBINNXTSHIFT[4]\, Y => 
        XNOR2_0_Y);
    
    AND2_31 : AND2
      port map(A => AND2_9_Y, B => AND2_40_Y, Y => AND2_31_Y);
    
    XOR2_18 : XOR2
      port map(A => \MEM_WADDR[1]\, B => \GND\, Y => XOR2_18_Y);
    
    \DFN1E1C0_dout[0]\ : DFN1E1C0
      port map(D => \QXI[0]\, CLK => clk, CLR => rst, E => DVLDI, 
        Q => dout(0));
    
    \XOR2_RBINNXTSHIFT[4]\ : XOR2
      port map(A => XOR2_30_Y, B => AO1_12_Y, Y => 
        \RBINNXTSHIFT[4]\);
    
    \DFN1C0_MEM_WADDR[8]\ : DFN1C0
      port map(D => \WBINNXTSHIFT[8]\, CLK => clk, CLR => rst, Q
         => \MEM_WADDR[8]\);
    
    \DFN1C0_RGRY[1]\ : DFN1C0
      port map(D => XOR2_17_Y, CLK => clk, CLR => rst, Q => 
        \RGRY[1]\);
    
    \DFN1C0_WGRY[3]\ : DFN1C0
      port map(D => XOR2_41_Y, CLK => clk, CLR => rst, Q => 
        \WGRY[3]\);
    
    XOR2_8 : XOR2
      port map(A => \MEM_RADDR[4]\, B => \GND\, Y => XOR2_8_Y);
    
    XOR2_30 : XOR2
      port map(A => \MEM_RADDR[4]\, B => \GND\, Y => XOR2_30_Y);
    
    \XOR2_RBINNXTSHIFT[6]\ : XOR2
      port map(A => XOR2_22_Y, B => AO1_0_Y, Y => 
        \RBINNXTSHIFT[6]\);
    
    AND2_38 : AND2
      port map(A => XOR2_10_Y, B => XOR2_51_Y, Y => AND2_38_Y);
    
    AND2_35 : AND2
      port map(A => \MEM_WADDR[4]\, B => \GND\, Y => AND2_35_Y);
    
    MEMREBUBBLE : INV
      port map(A => MEMORYRE, Y => MEMRENEG);
    
    \DFN1C0_MEM_WADDR[7]\ : DFN1C0
      port map(D => \WBINNXTSHIFT[7]\, CLK => clk, CLR => rst, Q
         => \MEM_WADDR[7]\);
    
    AND2_29 : AND2
      port map(A => AND2_16_Y, B => AND2_17_Y, Y => AND2_29_Y);
    
    \DFN1C0_MEM_RADDR[4]\ : DFN1C0
      port map(D => \RBINNXTSHIFT[4]\, CLK => clk, CLR => rst, Q
         => \MEM_RADDR[4]\);
    
    XOR2_34 : XOR2
      port map(A => \RBINNXTSHIFT[3]\, B => \RBINNXTSHIFT[4]\, Y
         => XOR2_34_Y);
    
    XOR2_31 : XOR2
      port map(A => \MEM_RADDR[9]\, B => \WBINNXTSHIFT[9]\, Y => 
        XOR2_31_Y);
    
    AND2_3 : AND2
      port map(A => \MEM_RADDR[4]\, B => \GND\, Y => AND2_3_Y);
    
    AND2_30 : AND2
      port map(A => AND2_43_Y, B => XOR2_49_Y, Y => AND2_30_Y);
    
    \XOR2_WBINNXTSHIFT[4]\ : XOR2
      port map(A => XOR2_47_Y, B => AO1_26_Y, Y => 
        \WBINNXTSHIFT[4]\);
    
    \DFN1E1C0_dout[7]\ : DFN1E1C0
      port map(D => \QXI[7]\, CLK => clk, CLR => rst, E => DVLDI, 
        Q => dout(7));
    
    XNOR2_6 : XNOR2
      port map(A => \RBINNXTSHIFT[5]\, B => \MEM_WADDR[5]\, Y => 
        XNOR2_6_Y);
    
    AND2_14 : AND2
      port map(A => XOR2_12_Y, B => XOR2_52_Y, Y => AND2_14_Y);
    
    AND2_32 : AND2
      port map(A => \MEM_WADDR[1]\, B => \GND\, Y => AND2_32_Y);
    
    \DFN1C0_MEM_RADDR[5]\ : DFN1C0
      port map(D => \RBINNXTSHIFT[5]\, CLK => clk, CLR => rst, Q
         => \MEM_RADDR[5]\);
    
    \XOR2_WBINNXTSHIFT[6]\ : XOR2
      port map(A => XOR2_27_Y, B => AO1_21_Y, Y => 
        \WBINNXTSHIFT[6]\);
    
    \DFN1E1C0_dout[3]\ : DFN1E1C0
      port map(D => \QXI[3]\, CLK => clk, CLR => rst, E => DVLDI, 
        Q => dout(3));
    
    XOR2_46 : XOR2
      port map(A => \MEM_WADDR[5]\, B => \GND\, Y => XOR2_46_Y);
    
    XNOR2_11 : XNOR2
      port map(A => \RBINNXTSHIFT[8]\, B => \MEM_WADDR[8]\, Y => 
        XNOR2_11_Y);
    
    AO1_2 : AO1
      port map(A => XOR2_8_Y, B => AO1_12_Y, C => AND2_3_Y, Y => 
        AO1_2_Y);
    
    \DFN1C0_MEM_RADDR[8]\ : DFN1C0
      port map(D => \RBINNXTSHIFT[8]\, CLK => clk, CLR => rst, Q
         => \MEM_RADDR[8]\);
    
    \DFN1C0_WGRY[0]\ : DFN1C0
      port map(D => XOR2_25_Y, CLK => clk, CLR => rst, Q => 
        \WGRY[0]\);
    
    AND2_26 : AND2
      port map(A => \MEM_RADDR[9]\, B => \GND\, Y => AND2_26_Y);
    
    XOR2_9 : XOR2
      port map(A => \RBINNXTSHIFT[0]\, B => \RBINNXTSHIFT[1]\, Y
         => XOR2_9_Y);
    
    \RAM4K9_QXI[7]\ : RAM4K9
      port map(ADDRA11 => \GND\, ADDRA10 => \GND\, ADDRA9 => 
        \GND\, ADDRA8 => \MEM_WADDR[8]\, ADDRA7 => \MEM_WADDR[7]\, 
        ADDRA6 => \MEM_WADDR[6]\, ADDRA5 => \MEM_WADDR[5]\, 
        ADDRA4 => \MEM_WADDR[4]\, ADDRA3 => \MEM_WADDR[3]\, 
        ADDRA2 => \MEM_WADDR[2]\, ADDRA1 => \MEM_WADDR[1]\, 
        ADDRA0 => \MEM_WADDR[0]\, ADDRB11 => \GND\, ADDRB10 => 
        \GND\, ADDRB9 => \GND\, ADDRB8 => \MEM_RADDR[8]\, ADDRB7
         => \MEM_RADDR[7]\, ADDRB6 => \MEM_RADDR[6]\, ADDRB5 => 
        \MEM_RADDR[5]\, ADDRB4 => \MEM_RADDR[4]\, ADDRB3 => 
        \MEM_RADDR[3]\, ADDRB2 => \MEM_RADDR[2]\, ADDRB1 => 
        \MEM_RADDR[1]\, ADDRB0 => \MEM_RADDR[0]\, DINA8 => \GND\, 
        DINA7 => din(7), DINA6 => din(6), DINA5 => din(5), DINA4
         => din(4), DINA3 => din(3), DINA2 => din(2), DINA1 => 
        din(1), DINA0 => din(0), DINB8 => \GND\, DINB7 => \GND\, 
        DINB6 => \GND\, DINB5 => \GND\, DINB4 => \GND\, DINB3 => 
        \GND\, DINB2 => \GND\, DINB1 => \GND\, DINB0 => \GND\, 
        WIDTHA0 => \VCC\, WIDTHA1 => \VCC\, WIDTHB0 => \VCC\, 
        WIDTHB1 => \VCC\, PIPEA => \GND\, PIPEB => \GND\, WMODEA
         => \GND\, WMODEB => \GND\, BLKA => MEMWENEG, BLKB => 
        MEMRENEG, WENA => \GND\, WENB => \VCC\, CLKA => clk, CLKB
         => clk, RESET => rst, DOUTA8 => OPEN, DOUTA7 => 
        \RAM4K9_QXI[7]_DOUTA7\, DOUTA6 => \RAM4K9_QXI[7]_DOUTA6\, 
        DOUTA5 => \RAM4K9_QXI[7]_DOUTA5\, DOUTA4 => 
        \RAM4K9_QXI[7]_DOUTA4\, DOUTA3 => \RAM4K9_QXI[7]_DOUTA3\, 
        DOUTA2 => \RAM4K9_QXI[7]_DOUTA2\, DOUTA1 => 
        \RAM4K9_QXI[7]_DOUTA1\, DOUTA0 => \RAM4K9_QXI[7]_DOUTA0\, 
        DOUTB8 => OPEN, DOUTB7 => \QXI[7]\, DOUTB6 => \QXI[6]\, 
        DOUTB5 => \QXI[5]\, DOUTB4 => \QXI[4]\, DOUTB3 => 
        \QXI[3]\, DOUTB2 => \QXI[2]\, DOUTB1 => \QXI[1]\, DOUTB0
         => \QXI[0]\);
    
    AND3_5 : AND3
      port map(A => XNOR2_7_Y, B => XNOR2_4_Y, C => XNOR2_8_Y, Y
         => AND3_5_Y);
    
    AND2_23 : AND2
      port map(A => AND2_5_Y, B => AND2_39_Y, Y => AND2_23_Y);
    
    XNOR2_4 : XNOR2
      port map(A => \RBINNXTSHIFT[1]\, B => \MEM_WADDR[1]\, Y => 
        XNOR2_4_Y);
    
    \DFN1C0_MEM_WADDR[9]\ : DFN1C0
      port map(D => \WBINNXTSHIFT[9]\, CLK => clk, CLR => rst, Q
         => \MEM_WADDR[9]\);
    
    \DFN1C0_RGRY[8]\ : DFN1C0
      port map(D => XOR2_42_Y, CLK => clk, CLR => rst, Q => 
        \RGRY[8]\);
    
    XOR2_5 : XOR2
      port map(A => \MEM_WADDR[7]\, B => \GND\, Y => XOR2_5_Y);
    
    AND2_19 : AND2
      port map(A => \MEM_RADDR[8]\, B => \GND\, Y => AND2_19_Y);
    
    \DFN1C0_MEM_RADDR[6]\ : DFN1C0
      port map(D => \RBINNXTSHIFT[6]\, CLK => clk, CLR => rst, Q
         => \MEM_RADDR[6]\);
    
    XOR2_22 : XOR2
      port map(A => \MEM_RADDR[6]\, B => \GND\, Y => XOR2_22_Y);
    
    AO1_1 : AO1
      port map(A => XOR2_23_Y, B => AND2_22_Y, C => AND2_32_Y, Y
         => AO1_1_Y);
    
    XOR2_13 : XOR2
      port map(A => \WBINNXTSHIFT[2]\, B => \WBINNXTSHIFT[3]\, Y
         => XOR2_13_Y);
    
    XNOR2_18 : XNOR2
      port map(A => \RBINNXTSHIFT[4]\, B => \MEM_WADDR[4]\, Y => 
        XNOR2_18_Y);
    
    AO1_3 : AO1
      port map(A => XOR2_46_Y, B => AND2_35_Y, C => AND2_8_Y, Y
         => AO1_3_Y);
    
    AND2_47 : AND2
      port map(A => AND2_34_Y, B => XOR2_10_Y, Y => AND2_47_Y);
    
    AO1_18 : AO1
      port map(A => XOR2_10_Y, B => AO1_24_Y, C => AND2_19_Y, Y
         => AO1_18_Y);
    
    XOR2_48 : XOR2
      port map(A => \MEM_RADDR[5]\, B => \GND\, Y => XOR2_48_Y);
    
    \XOR2_RBINNXTSHIFT[3]\ : XOR2
      port map(A => XOR2_39_Y, B => AO1_25_Y, Y => 
        \RBINNXTSHIFT[3]\);
    
    \DFN1C0_MEM_RADDR[7]\ : DFN1C0
      port map(D => \RBINNXTSHIFT[7]\, CLK => clk, CLR => rst, Q
         => \MEM_RADDR[7]\);
    
    AND2_16 : AND2
      port map(A => AND2_20_Y, B => AND2_6_Y, Y => AND2_16_Y);
    
    \DFN1E1C0_dout[1]\ : DFN1E1C0
      port map(D => \QXI[1]\, CLK => clk, CLR => rst, E => DVLDI, 
        Q => dout(1));
    
    \DFN1C0_WGRY[9]\ : DFN1C0
      port map(D => XOR2_11_Y, CLK => clk, CLR => rst, Q => 
        \WGRY[9]\);
    
    AND2_13 : AND2
      port map(A => \MEM_RADDR[2]\, B => \GND\, Y => AND2_13_Y);
    
    XOR2_10 : XOR2
      port map(A => \MEM_RADDR[8]\, B => \GND\, Y => XOR2_10_Y);
    
    XNOR2_1 : XNOR2
      port map(A => \MEM_RADDR[0]\, B => \WBINNXTSHIFT[0]\, Y => 
        XNOR2_1_Y);
    
    \DFN1C0_RGRY[4]\ : DFN1C0
      port map(D => XOR2_50_Y, CLK => clk, CLR => rst, Q => 
        \RGRY[4]\);
    
    \DFN1C0_MEM_WADDR[2]\ : DFN1C0
      port map(D => \WBINNXTSHIFT[2]\, CLK => clk, CLR => rst, Q
         => \MEM_WADDR[2]\);
    
    XOR2_27 : XOR2
      port map(A => \MEM_WADDR[6]\, B => \GND\, Y => XOR2_27_Y);
    
    AND2_MEMORYRE : AND2
      port map(A => NAND2_1_Y, B => rdEn, Y => MEMORYRE);
    
    XOR2_7 : XOR2
      port map(A => \MEM_RADDR[2]\, B => \GND\, Y => XOR2_7_Y);
    
    AND2_5 : AND2
      port map(A => AND2_43_Y, B => AND2_31_Y, Y => AND2_5_Y);
    
    \XOR2_WBINNXTSHIFT[3]\ : XOR2
      port map(A => XOR2_44_Y, B => AO1_10_Y, Y => 
        \WBINNXTSHIFT[3]\);
    
    XOR2_56 : XOR2
      port map(A => \RBINNXTSHIFT[5]\, B => \RBINNXTSHIFT[6]\, Y
         => XOR2_56_Y);
    
    XOR2_14 : XOR2
      port map(A => \RBINNXTSHIFT[7]\, B => \RBINNXTSHIFT[8]\, Y
         => XOR2_14_Y);
    
    XNOR2_3 : XNOR2
      port map(A => \MEM_RADDR[5]\, B => \WBINNXTSHIFT[5]\, Y => 
        XNOR2_3_Y);
    
    XOR2_11 : XOR2
      port map(A => \WBINNXTSHIFT[9]\, B => \GND\, Y => XOR2_11_Y);
    
    XOR2_25 : XOR2
      port map(A => \WBINNXTSHIFT[0]\, B => \WBINNXTSHIFT[1]\, Y
         => XOR2_25_Y);
    
    AO1_22 : AO1
      port map(A => XOR2_1_Y, B => AND2_13_Y, C => AND2_33_Y, Y
         => AO1_22_Y);
    
    XNOR2_15 : XNOR2
      port map(A => \RBINNXTSHIFT[7]\, B => \MEM_WADDR[7]\, Y => 
        XNOR2_15_Y);
    
    AND2_34 : AND2
      port map(A => AND2_16_Y, B => AND2_25_Y, Y => AND2_34_Y);
    
    AO1_6 : AO1
      port map(A => AND2_15_Y, B => AO1_7_Y, C => AO1_27_Y, Y => 
        AO1_6_Y);
    
    \DFN1C0_MEM_RADDR[3]\ : DFN1C0
      port map(D => \RBINNXTSHIFT[3]\, CLK => clk, CLR => rst, Q
         => \MEM_RADDR[3]\);
    
    AND3_2 : AND3
      port map(A => XNOR2_10_Y, B => XNOR2_5_Y, C => XNOR2_2_Y, Y
         => AND3_2_Y);
    
    AO1_12 : AO1
      port map(A => AND2_6_Y, B => AO1_11_Y, C => AO1_22_Y, Y => 
        AO1_12_Y);
    
    XOR2_32 : XOR2
      port map(A => \MEM_WADDR[9]\, B => \GND\, Y => XOR2_32_Y);
    
    AND2_9 : AND2
      port map(A => XOR2_49_Y, B => XOR2_46_Y, Y => AND2_9_Y);
    
    XOR2_58 : XOR2
      port map(A => \MEM_RADDR[8]\, B => \GND\, Y => XOR2_58_Y);
    
    XOR2_43 : XOR2
      port map(A => \RBINNXTSHIFT[6]\, B => \RBINNXTSHIFT[7]\, Y
         => XOR2_43_Y);
    
    AO1_9 : AO1
      port map(A => XOR2_0_Y, B => AO1_21_Y, C => AND2_37_Y, Y
         => AO1_9_Y);
    
    AND2_39 : AND2
      port map(A => XOR2_15_Y, B => XOR2_32_Y, Y => AND2_39_Y);
    
    DFN1C0_DVLDX : DFN1C0
      port map(D => DVLDI, CLK => clk, CLR => rst, Q => DVLDX);
    
    NAND2_0 : NAND2
      port map(A => \full\, B => \VCC\, Y => NAND2_0_Y);
    
    \DFN1C0_RGRY[6]\ : DFN1C0
      port map(D => XOR2_43_Y, CLK => clk, CLR => rst, Q => 
        \RGRY[6]\);
    
    AND2_27 : AND2
      port map(A => \MEM_RADDR[1]\, B => \GND\, Y => AND2_27_Y);
    
    DFN1C0_DVLDI : DFN1C0
      port map(D => AND2A_0_Y, CLK => clk, CLR => rst, Q => DVLDI);
    
    XNOR2_10 : XNOR2
      port map(A => \MEM_RADDR[6]\, B => \WBINNXTSHIFT[6]\, Y => 
        XNOR2_10_Y);
    
    AND2_MEMORYWE : AND2
      port map(A => NAND2_0_Y, B => wrEn, Y => MEMORYWE);
    
    AO1_20 : AO1
      port map(A => XOR2_15_Y, B => AO1_17_Y, C => AND2_42_Y, Y
         => AO1_20_Y);
    
    \DFN1C0_WGRY[2]\ : DFN1C0
      port map(D => XOR2_13_Y, CLK => clk, CLR => rst, Q => 
        \WGRY[2]\);
    
    AO1_0 : AO1
      port map(A => AND2_17_Y, B => AO1_12_Y, C => AO1_7_Y, Y => 
        AO1_0_Y);
    
    XOR2_29 : XOR2
      port map(A => \WBINNXTSHIFT[6]\, B => \WBINNXTSHIFT[7]\, Y
         => XOR2_29_Y);
    
    XOR2_40 : XOR2
      port map(A => \MEM_RADDR[6]\, B => \GND\, Y => XOR2_40_Y);
    
    XOR2_2 : XOR2
      port map(A => \MEM_RADDR[7]\, B => \GND\, Y => XOR2_2_Y);
    
    \DFN1C0_RGRY[5]\ : DFN1C0
      port map(D => XOR2_56_Y, CLK => clk, CLR => rst, Q => 
        \RGRY[5]\);
    
    AND2_36 : AND2
      port map(A => \MEM_WADDR[9]\, B => \GND\, Y => AND2_36_Y);
    
    XOR2_37 : XOR2
      port map(A => \WBINNXTSHIFT[4]\, B => \WBINNXTSHIFT[5]\, Y
         => XOR2_37_Y);
    
    AND2A_0 : AND2A
      port map(A => \empty\, B => rdEn, Y => AND2A_0_Y);
    
    AO1_26 : AO1
      port map(A => AND2_14_Y, B => AO1_1_Y, C => AO1_16_Y, Y => 
        AO1_26_Y);
    
    \DFN1C0_RGRY[7]\ : DFN1C0
      port map(D => XOR2_14_Y, CLK => clk, CLR => rst, Q => 
        \RGRY[7]\);
    
    \XOR2_RBINNXTSHIFT[5]\ : XOR2
      port map(A => XOR2_48_Y, B => AO1_2_Y, Y => 
        \RBINNXTSHIFT[5]\);
    
    AO1_23 : AO1
      port map(A => XOR2_51_Y, B => AND2_19_Y, C => AND2_26_Y, Y
         => AO1_23_Y);
    
    AND2_33 : AND2
      port map(A => \MEM_RADDR[3]\, B => \GND\, Y => AND2_33_Y);
    
    XOR2_44 : XOR2
      port map(A => \MEM_WADDR[3]\, B => \GND\, Y => XOR2_44_Y);
    
    AO1_10 : AO1
      port map(A => XOR2_12_Y, B => AO1_1_Y, C => AND2_7_Y, Y => 
        AO1_10_Y);
    
    XOR2_41 : XOR2
      port map(A => \WBINNXTSHIFT[3]\, B => \WBINNXTSHIFT[4]\, Y
         => XOR2_41_Y);
    
    XOR2_35 : XOR2
      port map(A => \WBINNXTSHIFT[7]\, B => \WBINNXTSHIFT[8]\, Y
         => XOR2_35_Y);
    
    \DFN1C0_WGRY[1]\ : DFN1C0
      port map(D => XOR2_20_Y, CLK => clk, CLR => rst, Q => 
        \WGRY[1]\);
    
    DFN1P0_empty : DFN1P0
      port map(D => EMPTYINT, CLK => clk, PRE => rst, Q => 
        \empty\);
    
    AND2_41 : AND2
      port map(A => AND2_16_Y, B => XOR2_8_Y, Y => AND2_41_Y);
    
    \XOR2_RBINNXTSHIFT[7]\ : XOR2
      port map(A => XOR2_24_Y, B => AO1_13_Y, Y => 
        \RBINNXTSHIFT[7]\);
    
    AND2_0 : AND2
      port map(A => AND2_29_Y, B => XOR2_40_Y, Y => AND2_0_Y);
    
    AO1_16 : AO1
      port map(A => XOR2_52_Y, B => AND2_7_Y, C => AND2_4_Y, Y
         => AO1_16_Y);
    
    AND2_17 : AND2
      port map(A => XOR2_8_Y, B => XOR2_19_Y, Y => AND2_17_Y);
    
    XOR2_6 : XOR2
      port map(A => \MEM_RADDR[2]\, B => \GND\, Y => XOR2_6_Y);
    
    AO1_13 : AO1
      port map(A => XOR2_40_Y, B => AO1_0_Y, C => AND2_1_Y, Y => 
        AO1_13_Y);
    
    \XOR2_WBINNXTSHIFT[5]\ : XOR2
      port map(A => XOR2_16_Y, B => AO1_8_Y, Y => 
        \WBINNXTSHIFT[5]\);
    
    \DFN1C0_MEM_WADDR[6]\ : DFN1C0
      port map(D => \WBINNXTSHIFT[6]\, CLK => clk, CLR => rst, Q
         => \MEM_WADDR[6]\);
    
    XOR2_53 : XOR2
      port map(A => \MEM_RADDR[9]\, B => \GND\, Y => XOR2_53_Y);
    
    \DFN1E1C0_dout[5]\ : DFN1E1C0
      port map(D => \QXI[5]\, CLK => clk, CLR => rst, E => DVLDI, 
        Q => dout(5));
    
    \DFN1E1C0_dout[6]\ : DFN1E1C0
      port map(D => \QXI[6]\, CLK => clk, CLR => rst, E => DVLDI, 
        Q => dout(6));
    
    XNOR2_12 : XNOR2
      port map(A => \MEM_RADDR[1]\, B => \WBINNXTSHIFT[1]\, Y => 
        XNOR2_12_Y);
    
    XNOR2_7 : XNOR2
      port map(A => \RBINNXTSHIFT[0]\, B => \MEM_WADDR[0]\, Y => 
        XNOR2_7_Y);
    
    XOR2_12 : XOR2
      port map(A => \MEM_WADDR[2]\, B => \GND\, Y => XOR2_12_Y);
    
    AND2_45 : AND2
      port map(A => XOR2_28_Y, B => XOR2_23_Y, Y => AND2_45_Y);
    
    AO1_19 : AO1
      port map(A => AND2_40_Y, B => AO1_3_Y, C => AO1_4_Y, Y => 
        AO1_19_Y);
    
    \XOR2_WBINNXTSHIFT[7]\ : XOR2
      port map(A => XOR2_5_Y, B => AO1_9_Y, Y => 
        \WBINNXTSHIFT[7]\);
    
    XOR2_26 : XOR2
      port map(A => \RBINNXTSHIFT[9]\, B => \GND\, Y => XOR2_26_Y);
    
    AND2_4 : AND2
      port map(A => \MEM_WADDR[3]\, B => \GND\, Y => AND2_4_Y);
    
    AND2_FULLINT : AND2
      port map(A => AND3_0_Y, B => XOR2_31_Y, Y => FULLINT);
    
    AND2_40 : AND2
      port map(A => XOR2_0_Y, B => XOR2_38_Y, Y => AND2_40_Y);
    
    XOR2_50 : XOR2
      port map(A => \RBINNXTSHIFT[4]\, B => \RBINNXTSHIFT[5]\, Y
         => XOR2_50_Y);
    
    AND2_42 : AND2
      port map(A => \MEM_WADDR[8]\, B => \GND\, Y => AND2_42_Y);
    
    \DFN1C0_WGRY[8]\ : DFN1C0
      port map(D => XOR2_36_Y, CLK => clk, CLR => rst, Q => 
        \WGRY[8]\);
    
    XNOR2_5 : XNOR2
      port map(A => \MEM_RADDR[7]\, B => \WBINNXTSHIFT[7]\, Y => 
        XNOR2_5_Y);
    
    AO1_5 : AO1
      port map(A => AND2_39_Y, B => AO1_17_Y, C => AO1_14_Y, Y
         => AO1_5_Y);
    
    XNOR2_16 : XNOR2
      port map(A => \MEM_RADDR[2]\, B => \WBINNXTSHIFT[2]\, Y => 
        XNOR2_16_Y);
    
    \DFN1C0_RGRY[3]\ : DFN1C0
      port map(D => XOR2_34_Y, CLK => clk, CLR => rst, Q => 
        \RGRY[3]\);
    
    XOR2_39 : XOR2
      port map(A => \MEM_RADDR[3]\, B => \GND\, Y => XOR2_39_Y);
    
    AND2_8 : AND2
      port map(A => \MEM_WADDR[5]\, B => \GND\, Y => AND2_8_Y);
    
    XOR2_3 : XOR2
      port map(A => \MEM_RADDR[1]\, B => \GND\, Y => XOR2_3_Y);
    
    \DFN1E1C0_dout[2]\ : DFN1E1C0
      port map(D => \QXI[2]\, CLK => clk, CLR => rst, E => DVLDI, 
        Q => dout(2));
    
    XOR2_54 : XOR2
      port map(A => \MEM_WADDR[8]\, B => \GND\, Y => XOR2_54_Y);
    
    AO1_27 : AO1
      port map(A => XOR2_2_Y, B => AND2_1_Y, C => AND2_24_Y, Y
         => AO1_27_Y);
    
    XOR2_51 : XOR2
      port map(A => \MEM_RADDR[9]\, B => \GND\, Y => XOR2_51_Y);
    
    \DFN1C0_MEM_WADDR[1]\ : DFN1C0
      port map(D => \WBINNXTSHIFT[1]\, CLK => clk, CLR => rst, Q
         => \MEM_WADDR[1]\);
    
    \XOR2_RBINNXTSHIFT[1]\ : XOR2
      port map(A => XOR2_4_Y, B => AND2_46_Y, Y => 
        \RBINNXTSHIFT[1]\);
    
    XOR2_17 : XOR2
      port map(A => \RBINNXTSHIFT[1]\, B => \RBINNXTSHIFT[2]\, Y
         => XOR2_17_Y);
    
    AND3_7 : AND3
      port map(A => XNOR2_13_Y, B => XNOR2_15_Y, C => XNOR2_11_Y, 
        Y => AND3_7_Y);
    
    XOR2_28 : XOR2
      port map(A => \MEM_WADDR[0]\, B => MEMORYWE, Y => XOR2_28_Y);
    
    \DFN1C0_MEM_WADDR[5]\ : DFN1C0
      port map(D => \WBINNXTSHIFT[5]\, CLK => clk, CLR => rst, Q
         => \MEM_WADDR[5]\);
    
    XOR2_15 : XOR2
      port map(A => \MEM_WADDR[8]\, B => \GND\, Y => XOR2_15_Y);
    
    \DFN1C0_MEM_RADDR[0]\ : DFN1C0
      port map(D => \RBINNXTSHIFT[0]\, CLK => clk, CLR => rst, Q
         => \MEM_RADDR[0]\);
    
    AO1_17 : AO1
      port map(A => AND2_31_Y, B => AO1_26_Y, C => AO1_19_Y, Y
         => AO1_17_Y);
    
    XNOR2_17 : XNOR2
      port map(A => \RBINNXTSHIFT[9]\, B => \MEM_WADDR[9]\, Y => 
        XNOR2_17_Y);
    
    AND3_4 : AND3
      port map(A => XNOR2_9_Y, B => XNOR2_18_Y, C => XNOR2_6_Y, Y
         => AND3_4_Y);
    
    \DFN1C0_RGRY[0]\ : DFN1C0
      port map(D => XOR2_9_Y, CLK => clk, CLR => rst, Q => 
        \RGRY[0]\);
    
    \XOR2_WBINNXTSHIFT[1]\ : XOR2
      port map(A => XOR2_18_Y, B => AND2_22_Y, Y => 
        \WBINNXTSHIFT[1]\);
    
    AND2_21 : AND2
      port map(A => AND2_45_Y, B => XOR2_12_Y, Y => AND2_21_Y);
    
    \DFN1C0_WGRY[4]\ : DFN1C0
      port map(D => XOR2_37_Y, CLK => clk, CLR => rst, Q => 
        \WGRY[4]\);
    
    XOR2_0 : XOR2
      port map(A => \MEM_WADDR[6]\, B => \GND\, Y => XOR2_0_Y);
    
    NAND2_1 : NAND2
      port map(A => \empty\, B => \VCC\, Y => NAND2_1_Y);
    
    AO1_4 : AO1
      port map(A => XOR2_38_Y, B => AND2_37_Y, C => AND2_11_Y, Y
         => AO1_4_Y);
    
    \DFN1E1C0_dout[4]\ : DFN1E1C0
      port map(D => \QXI[4]\, CLK => clk, CLR => rst, E => DVLDI, 
        Q => dout(4));
    
    AND2_37 : AND2
      port map(A => \MEM_WADDR[6]\, B => \GND\, Y => AND2_37_Y);
    
    XNOR2_14 : XNOR2
      port map(A => \MEM_RADDR[3]\, B => \WBINNXTSHIFT[3]\, Y => 
        XNOR2_14_Y);
    
    XOR2_42 : XOR2
      port map(A => \RBINNXTSHIFT[8]\, B => \RBINNXTSHIFT[9]\, Y
         => XOR2_42_Y);
    
    \XOR2_RBINNXTSHIFT[2]\ : XOR2
      port map(A => XOR2_6_Y, B => AO1_11_Y, Y => 
        \RBINNXTSHIFT[2]\);
    
    AO1_21 : AO1
      port map(A => AND2_9_Y, B => AO1_26_Y, C => AO1_3_Y, Y => 
        AO1_21_Y);
    
    \DFN1C0_MEM_RADDR[9]\ : DFN1C0
      port map(D => \RBINNXTSHIFT[9]\, CLK => clk, CLR => rst, Q
         => \MEM_RADDR[9]\);
    
    XOR2_36 : XOR2
      port map(A => \WBINNXTSHIFT[8]\, B => \WBINNXTSHIFT[9]\, Y
         => XOR2_36_Y);
    
    XNOR2_8 : XNOR2
      port map(A => \RBINNXTSHIFT[2]\, B => \MEM_WADDR[2]\, Y => 
        XNOR2_8_Y);
    
    AND2_28 : AND2
      port map(A => AND2_10_Y, B => XOR2_0_Y, Y => AND2_28_Y);
    
    AND2_25 : AND2
      port map(A => AND2_17_Y, B => AND2_15_Y, Y => AND2_25_Y);
    
    GND_power_inst1 : GND
      port map( Y => GND_power_net1);

    VCC_power_inst1 : VCC
      port map( Y => VCC_power_net1);


end DEF_ARCH; 

-- _Disclaimer: Please leave the following comments in the file, they are for internal purposes only._


-- _GEN_File_Contents_

-- Version:11.6.0.34
-- ACTGENU_CALL:1
-- BATCH:T
-- FAM:PA3LDP
-- OUTFORMAT:VHDL
-- LPMTYPE:LPM_SOFTFIFO
-- LPM_HINT:MEMFF
-- INSERT_PAD:NO
-- INSERT_IOREG:NO
-- GEN_BHV_VHDL_VAL:F
-- GEN_BHV_VERILOG_VAL:F
-- MGNTIMER:F
-- MGNCMPL:T
-- DESDIR:C:/Users/admin/logicDesign/logicDesign/coreGen/uartFifo/uartFifo/smartgen\uartFifo
-- GEN_BEHV_MODULE:F
-- SMARTGEN_DIE:IT14X14M4LDP
-- SMARTGEN_PACKAGE:fg484
-- AGENIII_IS_SUBPROJECT_LIBERO:T
-- WWIDTH:8
-- WDEPTH:512
-- RWIDTH:8
-- RDEPTH:512
-- CLKS:1
-- CLOCK_PN:clk
-- WCLK_EDGE:RISE
-- ACLR_PN:rst
-- RESET_POLARITY:0
-- INIT_RAM:F
-- WE_POLARITY:1
-- RE_POLARITY:1
-- FF_PN:full
-- AF_PN:AFULL
-- WACK_PN:WACK
-- OVRFLOW_PN:OVERFLOW
-- WRCNT_PN:WRCNT
-- WE_PN:wrEn
-- EF_PN:empty
-- AE_PN:AEMPTY
-- DVLD_PN:DVLD
-- UDRFLOW_PN:UNDERFLOW
-- RDCNT_PN:RDCNT
-- RE_PN:rdEn
-- CONTROLLERONLY:F
-- FSTOP:YES
-- ESTOP:YES
-- WRITEACK:NO
-- OVERFLOW:NO
-- WRCOUNT:NO
-- DATAVALID:NO
-- UNDERFLOW:NO
-- RDCOUNT:NO
-- AF_PORT_PN:AFVAL
-- AE_PORT_PN:AEVAL
-- AFFLAG:NONE
-- AEFLAG:NONE
-- DATA_IN_PN:din
-- DATA_OUT_PN:dout
-- CASCADE:1

-- _End_Comments_

