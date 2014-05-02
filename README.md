sublimetext-vhdl-utils
======================

Some basic utilities for writing VHDL with Sublime Text

Mostly tried to emulate some features from the VHDL support in Emacs.  Right now if you right-click on an entity, you can copy it to the clipboard as a component, instance, set of signals (with default names for the instance), and a few attempts to copy it as SystemVerilog module/instances (since I tend to write testbences in SV).

The code is ugly, because I wrote this for myself, but figured I should make it public in case anyone needs the same functionality.  Pull requests welcome to make it less terrible.


Example usage:

These context menu commands seem to work properly on the following entity:
```
entity add is
    port (
        clk, rst : in std_logic;
        in1, in2 : in std_logic_vector (0 to 7); 
        output : out std_logic_vector (0 to 7);
        start : in std_logic;
        done : out std_logic
    );
end add;
```

Copy as Component:
```
  component add
    port (
      rst : in std_logic;
      in2 : in std_logic_vector (0 to 7);
      output : out std_logic_vector (0 to 7);
      start : in std_logic;
      done : out std_logic);
  end component add;
```

Copy as Instance:
```
  add_inst : add
    port map (
      rst => rst,
      in2 => in2,
      output => output,
      start => start,
      done => done);  --std_logic
```

Copy as Signals:
```
  -- signals for add-----------------
  signal rst : std_logic;
  signal in2 : std_logic_vector (0 to 7);
  signal output : std_logic_vector (0 to 7);
  signal start : std_logic;
  signal done : std_logic;
  -- end signals for add
```

Copy as SV Module:
```
module add
  (
    input logic  rst,
    input logic [0:7] in2,
    output logic [0:7] output,
    input logic  start,
    output logic  done
  );

endmodule
```

Copy as SV Instance:
```
add  add_inst 
  (
    .rst(rst), //input logic 
    .in2(in2), //input logic [0:7]
    .output(output), //output logic [0:7]
    .start(start), //input logic 
    .done(done) //output logic 
  );
```
