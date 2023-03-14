from greatfet import GreatFET

gf = GreatFET()

def test():
    # First check for shorts at each EUT USB-C port.
    for port in ('CONTROL', 'AUX', 'TARGET-C'):
        connect_tester_to(port)
        check_for_short(port, 'GND', ' VBUS')
        check_for_short(port, 'VBUS', 'SBU2')
        check_for_short(port, 'SBU2', 'CC1' )
        check_for_short(port, 'CC1',  'D-'  )
        check_for_short(port, 'D-',   'D+'  )
        check_for_short(port, 'D+',   'SBU1')
        check_for_short(port, 'SBU1', 'CC2' )
        check_for_short(port, 'CC2',  'VBUS')

    # Test supplying VBUS through CONTROL and AUX ports.
    for port in ('CONTROL', 'AUX'):

        # Connect 5V supply via this port.
        set_supply(5.0, 0.1)
        connect_supply_to(port)

        # Expected diode drop range:
        drop_min, drop_max = 0.2, 0.3

        # Ramp the supply in 50mV steps up to 6.25V.
        for voltage in range(5.0, 6.25, 0.05):
            set_supply(voltage, 0.1)
            sleep(0.05)

            # Up to 5.5V, there must be only a diode drop.
            if voltage <= 5.5:
                minimum = voltage - drop_max
                maximum = voltage - drop_min
            # Between 5.5V and 6.0V, OVP may kick in.
            else if 5.5 <= 6.0:
                minimum = 0
                maximum = voltage - drop_min
            # Above 6.0V, OVP must kick in.
            else:
                minimum = 0
                maximum = 6.0 - drop_min

            # Check voltage at +5V rail.
            test_voltage('+5V', minimum, maximum)

        disconnect_supply_and_discharge()

    # Test passthrough of Target-C VBUS to Target-A VBUS with power off.
    set_supply(5.0, 0.1)
    connect_supply_to('TARGET-C')
    test_voltage('TARGET_A_VBUS', 4.95, 5.05)
    disconnect_supply_and_discharge()

    # Power at +5V through the control port for following tests.
    set_supply(5.0, 0.1)
    connect_supply_to('CONTROL')

    # Check all supply voltages.
    for (testpoint, minimum, maximum) in (
            ('+3V3',            3.25, 3.35),
            ('+2V5',            2.45, 2.55),
            ('+1V1',            1.05, 1.15),
            ('VCCRAM',          3.25, 3.35),
            ('CONTROL_PHY_3V3', 3.25, 3.35),
            ('CONTROL_PHY_1V8', 1.75, 1.85),
            ('AUX_PHY_3V3',     3.25, 3.35),
            ('AUX_PHY_1V8',     1.75, 1.85),
            ('TARGET_PHY_3V3',  3.25, 3.35),
            ('TARGET_PHY_3V3',  3.25, 3.35)):
        test_voltage(testpoint, minimum, maximum)

    # Check 60MHz clock.
    test_clock()

    # Flash Saturn-V bootloader to MCU via SWD.
    flash_bootloader()

    # Connect host D+/D- to control port.
    connect_host_to('CONTROL')

    # Flash Apollo firmware to MCU via DFU.
    flash_firmware()

    # Check Apollo debugger shows up.
    test_apollo()

    # Check JTAG scan via Apollo finds the FPGA.
    test_jtag_scan()

    # Configure FPGA with test gateware.
    configure_fpga()

    # Run self-test routine. Should include:
    #
    # - ULPI test to each PHY.
    # - HyperRAM read/write test.
    # - I2C test to all peripherals.
    # - PMOD loopback test.
    # 
    run_self_test()

    # Test USB HS comms on each port against the self-test gateware.
    for port in ('CONTROL', 'AUX', 'TARGET-C'):
        connect_host_to(port)
        test_usb_hs(port)

    # Tell the FPGA to put the target PHY in passive mode, then test
    # passthrough to a USB FS device created on the GF1.
    connect_host_to('CONTROL')
    set_target_passive()
    connect_host_to('TARGET-C')
    test_usb_fs(port)

    # TODO: CC/SBU pin testing (fixed resistors and I2C control).

    # TODO: VBUS distribution testing

    # TODO: VBUS voltage/current monitoring testing and calibration.

    # TODO: LED forward voltage testing.

    # Flash analyzer bitstream.
    flash_analyzer()

    # Power cycle and check analyzer shows up.
    connect_supply_to(None)
    sleep(0.5)
    connect_supply_to('CONTROL')
    test_analyzer()

    # TODO: Speed detection?

    # TODO: Manual button tests & LED visual checks.
