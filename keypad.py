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
            8783: self.lock,       # numlock +
            8683: self.unlock,     # numlock -
            8842: self.shutdown,   # backsp  enter
            97: self.quick_right_helm,    # 9
            96: self.stop_helm,  # 8
            95: self.quick_left_helm,      # 7
            94: self.right_helm,    # 6
            93: self.stop_helm,  # 5
            92: self.left_helm,      # 4
            91: self.slow_right_helm,  # 3
            90: self.stop_helm,  # 2
            89: self.slow_left_helm,  # 1
            98: self.steer_course,  # 0
            8784: self.increase_tsf,  # /+
            8684: self.decrease_tsf,  # /-
            8785: self.increase_gain,  # *+
            8685: self.decrease_gain,  # *-
        }
        self.lock = True
        self.drive = 0
        self.gain = 80000
        self.tsf = 20

    def _action_key(self, val):
        method = self._key_map.get(val, None)
        if method:
            method()

    def do(self, key_array):
        value = key_array[3] * 100 + key_array[2]
        if value == 8683 or value == 8783:
            self._action_key(value)
        elif not self.lock:
            self._action_key(value)

    def lock(self):
        print("locked")
        self.lock = True

    def unlock(self):
        print("unlocked")
        self.lock = False

    @staticmethod
    def shutdown():
        os.system("sudo shutdown now -h")

    def _manual_mode(self, inc):
        r.hset("helm", "auto_mode", 3)
        if -100 - inc <= self.drive <= 100 - inc:
            self.drive += inc
        r.hset("helm", "drive", self.drive)

    def _gain(self, inc):
        if 100 - inc <= self.gain <= 8000000 - inc:
            self.gain += inc
            print(f"Gain = {self.gain}")
        r.hset("helm", "gain", int(self.gain))

    def _tsf(self, inc):
        if 10 - inc <= self.tsf <= 2000 - inc:
            self.tsf += inc
            print(f"tsf = {self.tsf}")
        r.hset("helm", "tsf", int(self.tsf))

    def quick_right_helm(self):
        self._manual_mode(33)

    def quick_left_helm(self):
        self._manual_mode(-33)

    def right_helm(self):
        self._manual_mode(10)

    def left_helm(self):
        self._manual_mode(-10)

    def slow_right_helm(self):
        self._manual_mode(1)

    def slow_left_helm(self):
        self._manual_mode(-1)

    def increase_gain(self):
        self._gain(int(self.gain / 10))

    def decrease_gain(self):
        self._gain(int(-self.gain / 10))

    def increase_tsf(self):
        self._tsf(int(self.tsf / 10))

    def decrease_tsf(self):
        self._tsf(int(-self.tsf / 10))

    def steer_course(self):
        self.drive = 0
        hts = float(r.hget("current_data", "compass"))
        print(hts)
        r.hset("helm", "hts", int(hts*10))
        r.hset("helm", "auto_mode", 2)

    def stop_helm(self):
        self.drive = 0
        r.hset("helm", "drive", self.drive)
        r.hset("helm", "auto_mode", 3)


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
