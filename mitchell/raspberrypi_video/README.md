Make sure to build after you make changes to any .cpp or .h files:
qmake && make

To clean:
make sdkclean && make distclean

Lepton's GND pin should be connected to RPi ground.
Lepton's CS pin should be connected to RPi CE0 pin.
Lepton's MISO pin should be connected to RPi MISO pin.
Lepton's CLK pin should be connected to RPi SCLK pin.
Lepton's VIN pin should be connected to RPi 3v3 pin.
Lepton's SDA pin should be connected to RPi SDA pin.
Lepton's SCL pin should be connected to RPi SCL pin.

