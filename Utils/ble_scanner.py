from bluepy.btle import Scanner


def getDevices(full_info):
    """
    The method searches BLE devices around in the and prints them.
    SUDO is required.
    :param full_info: The method prints all device information if true, it prints just the MAC and name if false.
    """
    scanner = Scanner()
    devices = scanner.scan()
    print("Found {} devices".format(len(devices)))
    for dev in devices:
        if full_info:
            print("Device {} ({}), RSSI={} dB".format(dev.addr, dev.addrType, dev.rssi))
            for (adtype, desc, value) in dev.getScanData():
                print("  {} = {}".format(desc, value))
        else:
            print("MAC: {}\tName: {}".format(dev.addr, dev.getValueText(9)))


if __name__ == "__main__":
    getDevices(False)
