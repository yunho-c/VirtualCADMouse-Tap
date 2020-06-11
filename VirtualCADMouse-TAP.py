from tapsdk import TapSDK, TapInputMode
import pyautogui
import statistics
import time

strap = TapSDK()
connected = False
IMU_A = [0, 0, 0]
IMU_G = [0, 0, 0]
DEV1 = [0, 0, 0]
DEV2 = [0, 0, 0]
UpA = 0
UpZero = 0
CALIBRATE_SAMPLE = 20
LIFTDOWN_THRESHOLD = 0
dCursor = [0, 0]
MAIN_FREQ = 60
LIFT_FREQ = 12


def connection(identifier, name, firmware):
    strap.set_input_mode(TapInputMode("raw"))
    global connected
    connected = True

def disconnection(identifier):
    global connected
    connected = False

def stream(identifier, data):
    global IMU_A, IMU_G, DEV1, DEV2, UpA
    if data.type == 1:
        IMU_A = [data.GetPoint(1).x, data.GetPoint(1).y, data.GetPoint(1).z]
        IMU_G = [data.GetPoint(0).x, data.GetPoint(0).y, data.GetPoint(0).z]
    if data.type == 2:
        DEV1 = [data.GetPoint(1).x, data.GetPoint(1).y, data.GetPoint(1).z]
        DEV2 = [data.GetPoint(2).x, data.GetPoint(2).y, data.GetPoint(2).z]
        UpA = int((-IMU_A[1] + DEV1[2] + DEV2[2]) / 3)


def Calibrate():
    global UpZero
    for i in range(CALIBRATE_SAMPLE):
        UpZero += UpA
        time.sleep(0.02)
    UpZero = int(UpZero / CALIBRATE_SAMPLE)


def LiftUpDetection():
    if abs(UpA - UpZero) > 100:
        feature = []
        for i in range(15): # or 30
            feature.append(UpA)
            time.sleep(0.01)

        if max(feature) - min(feature) > 150:
            if feature.index(max(feature)) > feature.index(min(feature)):
                return True


def LiftDownDetection(DeltaCursor):
    global CursorCache
    error = [pyautogui.position()[0] - DeltaCursor[0] - CursorCache[0], pyautogui.position()[1] - DeltaCursor[1] - CursorCache[1]]
    print(error)
    if abs(error[0]) + abs(error[1]) > LIFTDOWN_THRESHOLD:
        return True
    else:
        return False
    CursorCache = pyautogui.position()


def Orbit():
    dOx = int(IMU_G[0]/10000)
    dOy = -int(IMU_G[2]/10000)
    return (dOx, dOy)


def Push(dOrbit):
    dProcessed = [dOrbit[0], dOrbit[1]]
    pyautogui.moveRel(dProcessed)
    return dProcessed


pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.0

engaged = False
K = MAIN_FREQ / LIFT_FREQ
if not K % 1 == 0:
    raise("Bad lift frequency")
k = 0

strap.run()
strap.register_connection_events(connection)
strap.register_disconnection_events(disconnection)
strap.register_raw_data_events(stream)

while not connected:
    pass

time.sleep(3)

Calibrate()

while True:
    k += 1
    if k == K:
        if not engaged and LiftUpDetection():
            LiftPoint = pyautogui.position()
            CursorCache = pyautogui.position()
            for i in range(10):
                pyautogui.moveRel(1, 0)
                time.sleep(0.002)
            for i in range(10):
                pyautogui.moveRel(-2, 2)
                time.sleep(0.002)
            for i in range(10):
                pyautogui.moveRel(-2, -2)
                time.sleep(0.002)
            for i in range(10):
                pyautogui.moveRel(2, -2)
                time.sleep(0.002)
            for i in range(10):
                pyautogui.moveRel(2, 2)
                time.sleep(0.002)
            for i in range(10):
                pyautogui.moveRel(-1, 0)
                time.sleep(0.002)
            pyautogui.mouseDown(button="MIDDLE")
            engaged = True
        elif engaged and LiftDownDetection(dCursor):
            pyautogui.mouseUp(button="MIDDLE")
            time.sleep(0.03) # 0.015 didn't work
            pyautogui.moveTo(LiftPoint)
            engaged = False
            Calibrate()
            k = 0
            dCursor = [0, 0]
        k = 0

    if engaged:
        # add two elements from Push(Orbit()) to two elements of dCursor
        # calling Push(Orbit()) only once
        pushed = Push(Orbit())
        dCursor[0] += pushed[0]
        dCursor[1] += pushed[1]

    time.sleep(0.015) # 1/LIFT_FREQ

    if not connected:
        pyautogui.mouseUp(button="MIDDLE")
        break
