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
            8483: self.ext_compass, # numlock /
            8583: self.int_compass,  # numlock *
            8842: self.shutdown,   # backsp  enter
            8742: self.increase_base,  # backsp +
            8642: self.decrease_base,  # backsp -
            9488: self.tack_right, # enter 6
            9288: self.tack_left, # enter 4
            97: self.quick_right_helm,    # 9
            96: self.stop_helm,  # 8
            95: self.quick_left_helm,      # 7
            94: self.right_helm,    # 6
            93: self.stop_helm,  # 5
            92: self.left_helm,      # 4
            91: self.trim_auto_right,  # 3
            90: self.return_auto_course,  # 2
            89: self.trim_auto_left,  # 1
            98: self.steer_course,  # 0
            8784: self.increase_tsf,  # /+
            8684: self.decrease_tsf,  # /-
            8785: self.increase_gain,  # *+
            8685: self.decrease_gain,  # *-
        }
        self.lock = True
        self.hts = 0
        self.auto = False
        self.drive = 0
        self.gain = 325
        self.tsf = 1454
        self.base_duty = 100000
        self.compass_mode = 1
        self.trim = 1
        self.trim_dir = 0
        r.hset("helm", "tsf", self.tsf)
        r.hset("helm", "compass_mode", self.compass_mode)
        r.hset("helm", "gain", self.gain)
        r.hset("helm", "base_duty", self.base_duty)

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

    def int_compass(self):
        self.compass_mode = 1
        r.hset("helm", "compass_mode", self.compass_mode)

    def ext_compass(self):
        self.compass_mode = 2
        r.hset("helm", "compass_mode", self.compass_mode)

    @staticmethod
    def shutdown():
        os.system("sudo shutdown now -h")

    def _manual_mode(self, inc):
        self.auto = False
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
        if 10 - inc <= self.tsf <= 5000 - inc:
            self.tsf += inc
            print(f"tsf = {self.tsf}")
        r.hset("helm", "tsf", int(self.tsf))

    def _base(self, inc):
        if 50000 - inc <= self.base_duty <= 500000 - inc:
            self.base_duty += inc
            print(f"base_duty = {self.base_duty}")
        r.hset("helm", "base_duty", self.base_duty)

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
        self._tsf(int(self.tsf / 5))

    def decrease_tsf(self):
        self._tsf(int(-self.tsf / 5))

    def increase_base(self):
        self._base(int(self.base_duty / 10))

    def decrease_base(self):
        self._base(int(-self.base_duty / 10))

    def steer_course(self):
        self.drive = 0
        self.hts = float(r.hget("current_data", "compass"))
        self.auto = True
        self.set_hts()
        self.trim_dir = 0

    def return_auto_course(self):
        self.auto = True
        self.set_hts()
        self.trim_dir = 0

    def trim_auto_right(self):
        if self.trim_dir != 2:
            self.trim = 1
            self.trim_dir = 2
        else:
            self.trim += 1
        if not self.auto:
            steer_course()
        else:
            self.hts = compass_direction(self.hts + self.trim)
            self.set_hts()

    def trim_auto_left(self):
        if self.trim_dir != 1:
            self.trim = 1
            self.trim_dir = 1
        else:
            self.trim += 1
        if not self.auto:
            steer_course()
        else:
            self.hts = compass_direction(self.hts - self.trim)
            self.set_hts()

    def set_hts(self):
        print(self.hts)
        r.hset("helm", "hts", int(self.hts*10))
        r.hset("helm", "auto_mode", 2)


    def stop_helm(self):
        self.auto = False
        self.drive = 0
        r.hset("helm", "drive", self.drive)
        r.hset("helm", "auto_mode", 3)

    def tack_right(self):
        self.tack(1)

    def tack_left(self):
        self.tack(-1)

    def tack(self, dir):
        if not self.auto:
            steer_course()
        self.hts = compass_direction(self.hts + dir*85)
        print(f"new course = {self.hts}")
        r.hset("helm", "auto_mode", 3)
        r.hset("helm", "drive", dir*100)
        print("driving helm over")
        time.sleep(3)  # drive helm hard for 3 seconds to start tac(k
        print("new course set")
        r.hset("helm", "tsf", 100)
        r.hset("helm", "hts", int(self.hts*10))
        r.hset("helm", "auto_mode", 2)
        time.sleep(3)  # continue to auto mode for 3 seconds low damping
        # restore damping
        r.hset("helm", "tsf", self.tsf)
        print(f"Normal damping tsf = {self.tsf}")


def compass_direction(diff):
    if diff < 0:
        diff += 360
    elif diff >= 360:
        diff -= 360
    return diff


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
