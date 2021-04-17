import usb
import time
import redis
import os

USB_IF = 0  # Interface
USB_TIMEOUT = 10     # Timeout in MS

USB_VENDOR = 0x062a    # Creative Labs
USB_PRODUCT = 0x4101  # Wireless Keyboard/Mouse


class Action:

    def __init__(self):
        self._key_map = {
            8683: self.lock,       # numlock +
            8783: self.unlock,     # numlock -
            8842: self.shutdown,   # backsp  enter
            94: self.right_helm,    # 6
            93: self.steer_course,  # 5
            92: self.left_helm      # 4
        }
        self.lock = True

    def _action_key(self, val):
        method = self._key_map.get(val, None)
        if method:
            method()

    def do(self, key_array):
        value = key_array[3] * 100 + key_array[2]
        if value == 8683 or value == 8783:
            self._action_key(value)
        elif self.unlock:
            self._action_key(value)

        elif control[2]:
            print(control[2])
            if control[2] == 94:
                x = int(r.hget("helm", "hts"))
                r.hset("helm", "hts", x + 10)

    def lock(self):
        self.lock = True

    def unlock(self):
        self.lock = False

    @staticmethod
    def shutdown():
        os.system("sudo shutdown now -h")

    @staticmethod
    def right_helm():
        r.hset("helm", "auto_mode", 0)
        r.hset("helm", "drive", 10)

    @staticmethod
    def left_helm():
        r.hset("helm", "auto_mode", 0)
        r.hset("helm", "drive", -10)

    @staticmethod
    def steer_course():
        r.hset("helm", "auto_mode", 1)


if __name__ == '__main__':
    r = redis.Redis(host='localhost', port=6379, db=0)
    key_action = Action()
    dev = usb.core.find(idVendor=USB_VENDOR, idProduct=USB_PRODUCT)
    endpoint = dev[0][(0, 0)][0]

    if dev.is_kernel_driver_active(USB_IF) is True:
        dev.detach_kernel_driver(USB_IF)

    usb.util.claim_interface(dev, USB_IF)

    while True:
        control = None
        try:
            control = dev.read(endpoint.bEndpointAddress, endpoint.wMaxPacketSize, USB_TIMEOUT)
            key_action.do(control)
        except:
            pass

        time.sleep(0.01)  # Let CTRL+C actually exit
