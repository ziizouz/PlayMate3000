import multiprocessing as mp
import numpy as np
import time, sys, netifaces
import cv2 as cv
import TCP_IP, I2C



def com_init():
    count = 1

    print("Welcome to the PLAYMATE 3000 computer vision interface")
    print("Please select one of the following communication protocols")
    print("1)TCP/IP\t\t2)Serial")
    choice = sys.stdin.readline().rstrip("\n")

    if choice == '1' :
        print("You have chosen TCP/IP protocol as the main communication interface !")
        print("Please select the interface you're going to use :")
        for x in netifaces.interfaces():
            print(str(count) + " : " + x)
            count+=1
	tmp = netifaces.interfaces()[input()-1]
	self_ip = netifaces.ifaddresses(tmp)[netifaces.AF_INET][0]['addr']
	print(self_ip)
        print("Please enter Master's IP address:")
        master_ip = sys.stdin.readline().rstrip("\n")  # IP address of Master device
        master2slave = int(input("Please enter Master-to-Slave port: \n"))  # Com port
        slave2master = int(input("Please enter Slave-to-Master port: \n")) # Com port
        buffer_size = int(input("Please specify buffer size (Default = 1024)\n"))  # Buffer size
        com_param = [master_ip, self_ip, master2slave, slave2master, buffer_size]
        return  com_param

    elif choice == '2' :
        print("You have chosen I2C protocol as the main communication interface !")
    else:
        print("Seriously dude !")



com = [I2C, TCP_IP]
communication = 0

# Initialization of communication parameters
com_param = com_init()

# A queue that will have the data shared between processes
sharedData = mp.Queue()
# A lock to block the access of critical section when either main code is writing or communication process is reading
lock = mp.Lock()

#start the I2C process or the TCP/IP
if __name__ == '__main__':
    proc = mp.Process(target=com[1].start, name='Communication', args=(sharedData, lock, com_param))

    proc.start()
    
    image = cv.imread(r"F:\sw\0.jpg")
    board = np.zeros((8, 8))
    pieces = np.zeros((8, 8, 3))
    piece = [1, 2, 3]
    arm = [7, 1, 10]
    i = 0
    while True:
            lock.acquire()
            while sharedData.empty() is False:
                sharedData.get()
            sharedData.put(["image" , image])
            sharedData.put(["pieces", pieces])
            sharedData.put(["board", board])
            sharedData.put(["piece", piece])
            sharedData.put(["arm", arm])
            lock.release()
            i+=1
