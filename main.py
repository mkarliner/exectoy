from machine import Pin, I2C
import ssd1306
import time
from simple import MQTTClient
from encoder import Encoder  # or from pyb_encoder import Encoder
import network
import uftpd
import ujson
import machine


from machine import Pin
from neopixel import NeoPixel


#Network

wlan = network.WLAN(network.STA_IF)

#Neo Pixels
active_led  = 0
brightness = 255
direction  = 1
pin = Pin(2, Pin.OUT)   # set GPIO0 to output to drive NeoPixels
np = NeoPixel(pin, 12)   # create NeoPixel driver on GPIO0 for 8 pixels
np[active_led] = (80, 20, 20) # set the first pixel to white
np.write()              # write data to all pixels
r, g, b = np[0]         # get first pixel colour
colour = "green"
# colours = {
#     "red": (255,0,0),
#     "green": (0,255,0),
#     "blue": (0,0,255)
# }

colours = ["red", "blue", "green"]

#Display
i2c = I2C(Pin(5), Pin(4))
display = ssd1306.SSD1306_I2C(128, 64, i2c)
# display.fill(True)
# for y in range(48):
#     for x in range(48):
#         display.pixel(40 + x, y, not logo[y * 6 + x // 8] & (1<<(7 - x % 8)))

display.text("Hello", 1,1)
display.text("RedSift", 1,20)

display.show()

#Encoder

menu = [
    "No menu",
    "Nada",
    "nothing",
    "Reset"
]

e = Encoder(14, 12, clicks=4)  # optional: add pin_mode=Pin.PULL_UP

def button_cb(p):
    global button_pushed
    #print('Button Push', p)
    button_pushed = True


lastval = 0
button_pushed = False
button = Pin(0, Pin.IN, Pin.PULL_UP)
button.irq(trigger=Pin.IRQ_FALLING, handler=button_cb)





# Publish test messages e.g. with:
# mosquitto_pub -t foo_topic -m hello

# Received messages from subscriptions will be delivered to this callback
def sub_cb(topic, msg):
    global colour, colours, menu
    
    print((topic, msg))
    if(topic == b'led_cmds'):
        col = msg.decode("utf-8")
        if(col in colours):
            print("Setting color to ", colour)
            colour = col
    elif(topic == b'oled_messages'):
        display.fill(False)
        disp = ujson.loads(msg)
        print(disp)
        for i in range(len(disp)):
            display.text(disp[i]['str'], disp[i]['x'], disp[i]['y'])       
        display.show()
    elif(topic == b'menu_cmds'):
        menu = ujson.loads(msg)
        print(menu)
        print(len(menu))
        #Set up new encoder
        #e = Encoder(14,12, min_val=0, max_val = len(menu))
    
            
    

    
def check_encoder():
    global lastval
    global button_pushed
    global menu
    
    val = e.value
    if lastval != val:
        lastval = val
        display.fill(0)
        # for x in range(1,120):
        #     for y in range(40,50):
        #         display.pixel(x,y,0)
        if(val > len(menu)-1):
            display.text(str(val), 1,40)
        else:
            display.text(menu[val], 1, 40)
        #display.text(str(val), 1,40)
        display.show()
        print(val)
    if(button_pushed):
        button_pushed = False
        return (True,menu[val])
    else:
        return (False,0)

def mqtt_main(server="192.168.10.22"):
    global np
    global active_led
    global colour
    global brightness
    global direction
    
    
    c = MQTTClient("umqtt_client2", server, user="guest", password="guest")
    c.set_callback(sub_cb)
    c.connect()
    c.subscribe(b"led_cmds")
    c.subscribe(b'oled_messages')
    c.subscribe(b'menu_cmds')
    while True:
        # Non-blocking wait for message
        c.check_msg()
        # # Rotate leds fast
        # np[active_led] = (0,0,0)
        # active_led+=1
        # if(active_led==12):
        #     active_led = 0
        # np[active_led] = colour
        # np.write()
        # Has the encoder value changed?
        if(colour == "red"):
            rgb = (0,brightness,0)
        elif(colour == "green"):
            rgb = (brightness,0,0)
        elif(colour == "blue"):
            rgb = (0,0,brightness)
        else:
            print(colour)
        np[active_led] = rgb
        np.write()
        brightness = brightness + direction
        if(brightness >= 255):
            direction = -1
            # np[active_led] = (0, 0,0)
            # active_led+=1
            # if(active_led==12):
            #     active_led = 0
        if(brightness <= 0):
            direction = 1
            np[active_led] = (0, 0,0)
            active_led+=1
            if(active_led==12):
                active_led = 0
        pushed, enc_value = check_encoder()
        if(pushed == True):
            if(enc_value == "Reset"):
                print("Resetting")
                machine.reset()
            print("ENC: ", pushed, enc_value)
            c.publish('button_pushes', enc_value)
        
        # Then need to sleep to avoid 100% CPU usage (in a real
        # app other useful actions would be performed instead)
        time.sleep_ms(10)

    c.disconnect()



while(wlan.isconnected() != True):
    print("Waiting for Wifi")
    time.sleep_ms(500)
display.text(wlan.ifconfig()[0], 1,40)
display.show()
mqtt_main()
