import evdev

apple_keyboard_keywords = ['apple','internal','keyboard']
apple_touchpad_keywords = ['bcm5974']

def get_device_by_keywords(keywords):
    devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
    for i in devices:
        name = i.name.lower()
        found_all_keywords = True
        for keyword in keywords:
            found_all_keywords &= keyword in name
        if found_all_keywords:
            return i
    return None

def get_apple_keyboard():
    return get_device_by_keywords(apple_keyboard_keywords)

def get_apple_touchpad():
    return get_device_by_keywords(apple_touchpad_keywords)

