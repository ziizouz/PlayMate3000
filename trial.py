import cv2
import numpy as np

def findBoard(contours, img, coloured):
    """
    What this function does is that it takes the contours of the images taken by camera, and the image un gray scale and the coloured image, it returns the board
    colored image.
    """
    #get the dimensions of the grayscale image
    h, w = img.shape
    #measure the surface of the frame or the number of pixels in all the image, this will be used to limit the size of the board
    frameArea = h*w
    #measure the minimum area that could be set for a board, which is one tenth of the whole image
    s = frameArea / 10
    #this variable will contain the coordinates of the corners
    boardPts = []
    #this variable will take the cropped colored image
    board = []
    #loop in all the contours of the image, and check for the board by its surface
    for c in contours:
        # Compute the area of the contour
        area = cv2.contourArea(c)
        if area > s:  # Accept only large enough squares
            peri = cv2.arcLength(c, True)  # Calculate the perimeter of the contour
            # (0.10 was deduced experimentaly) Using Ramer-Douglas-Peucker algorithm for shape detection
            approx = cv2.approxPolyDP(c, 0.10 * peri, True)
            if len(approx) == 4:  # The shape has vertices => either square or rectangle, both are fine
                # Square detected
                #check if this square is the smallest square that is larger than image/10, this way we avoid having many squares like the page or the table which are bigger
                #than the board
                if area < frameArea:
                    frameArea = area
                    boardPts = approx
            else:
                # if not square, pass !
                pass
    if len(boardPts) > 1:
        pts = setPoints(boardPts)
        board = transformToBoard(coloured, pts)
    return board
def transformToBoard(img, pts):
    (tl, tr, br, bl) = pts
    widthA = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
    widthB = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
    maxWidth = max(int(widthA), int(widthB))

    heightA = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
    heightB = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
    maxHeight = max(int(heightA), int(heightB))

    dst = np.array([
        [0, 0],
        [maxWidth - 1, 0],
        [maxWidth - 1, maxHeight - 1],
        [0, maxHeight - 1]], np.float32)
    M = cv2.getPerspectiveTransform(pts, dst)
    board = cv2.warpPerspective(img, M, (maxWidth, maxHeight))
    return board

def setPoints(approx):
    rect = np.zeros((4, 2),np.float32)
    s = approx.sum(axis= 2)
    rect[2] = approx[np.argmax(s)]
    rect[0] = approx[np.argmin(s)]
    diff = np.diff(approx, axis= 2)
    rect[1] = approx[np.argmax(diff)]
    rect[3] = approx[np.argmin(diff)]
    return rect
def getBoard(capture):
    _, frame1 = capture.read()  # Getting frame from the cameras
    frame = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
    thresholded = cv2.adaptiveThreshold(frame, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,cv2.THRESH_BINARY, 15, 0)
    _, contours, _ = cv2.findContours(thresholded, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    board = findBoard(contours, frame, frame1)
    bordersize = 10
    bordererImage = cv2.copyMakeBorder(board, top=bordersize, bottom=bordersize, left=bordersize, right=bordersize,
                                borderType=cv2.BORDER_CONSTANT, value=[255, 255, 255])
    return bordererImage
def nothing(x):
    pass
def main():
    capture = cv2.VideoCapture(r"C:\Users\moham\Desktop\chess.mp4")  # Opening the webcam
    cv2.namedWindow('frame')  # Giving a name to the window I'll open, needed for the Trackbars
    cv2.createTrackbar('threshold', 'frame', 0, 255,
                       nothing)  # Trackbar to manage threshold values (Threshold filtering)
    cv2.setTrackbarPos('threshold', 'frame', 228)  # Setting Initial threshold value
    cv2.createTrackbar('Area', 'frame', 0, 3000,
                       nothing)  # Trackbar to set threshold area of the accepted squares (used with shape recognition)
    cv2.setTrackbarPos('Area', 'frame', 300)  # Setting the initial accepted square area to 300 px
    while True:
        try:
            p = getBoard(capture)
            frame = cv2.cvtColor(p, cv2.COLOR_BGR2GRAY)
            w, h = frame.shape
            s = w*h
            # Kernel used to apply the morphological filter
            kernel = np.ones((5, 5), np.uint8)
            # Thresholding (We got the value f the threshold from the trackbar)
            threshold = cv2.getTrackbarPos('threshold', 'frame')
            _, thresholded = cv2.threshold(frame, threshold, 255, cv2.THRESH_BINARY)  # Applying threshold
            # Laplacian operator for edge detection
            lap = cv2.Laplacian(thresholded, cv2.CV_64F)  # Applying Laplacian transform
            # Applying gradient morephological filter
            lap = cv2.morphologyEx(lap, cv2.MORPH_GRADIENT, kernel)
            #
            cv2.imshow("lap", lap)
            #################################### Preprocessing ended ###########################################################

            #################################### Contours manipulation ########################################################
            # Calculating the contour from the edge detected matrix (Output of the Laplacian operator)
            _, contours, _ = cv2.findContours(lap.astype(np.uint8), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
            # Initializing the nbr of detected squares
            nbrofsquares = 0  # Will be needed to detect the board type and thus the game !
            nbrofcircles = 0
            # Getting min required area of the square to be accepted !
            maxArea = cv2.getTrackbarPos('Area', 'frame')
            # Looping through the contours detected previously
            for c in contours:
                # Compute the area of the contour
                area = cv2.contourArea(c)
                if area > maxArea and area < (s/10):  # Accept only large enough squares
                    peri = cv2.arcLength(c, True)  # Calculate the perimeter of the contour
                    # (0.15 was deduced experimentaly) Using Ramer-Douglas-Peucker algorithm for shape detection
                    approx = cv2.approxPolyDP(c, 0.15 * peri, True)
                    if len(approx) == 4:  # The shape has vertices => either square or rectangle, both are fine
                        # Square detected
                        nbrofsquares += 1  # Increment the nbr of squres seen
                        M = cv2.moments(c)  # Getting the moments of the contour
                        cX = int(M["m10"] / M["m00"])  # Getting the x coordinate of the center of the square
                        cY = int(M["m01"] / M["m00"])  # Getting the y coordinate of the center of the square
                        cv2.drawContours(frame, [c], -1, (0, 255, 0), 2)  # Drawing the contour
                    else:
                        # if not square, pass !
                        pass
            #################################### Contours manipulation ended ! ########################################################

            print('I detected %d square !' % (nbrofsquares))  # Printing out the nbr of squares detected !

            if nbrofsquares > 63 and nbrofsquares < 67:
                cv2.putText(frame, "Chess board detected !", (5, 5), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255),
                            1)
                # Getting circles from gray image using hough circle
                circles = cv2.HoughCircles(frame, cv2.HOUGH_GRADIENT, 1, 24, param1=50, param2=28, minRadius=10,
                                           maxRadius=20)
                # Casting the content of circles
                if circles is not None:
                    circles = np.round(circles[0, :]).astype('int')

                    # If board detected, let's detect the pieces !
                    for (Cx, Cy, r) in circles:
                        nbrofcircles += 1
                        cv2.circle(frame, (Cx, Cy), r, (255, 255, 255), 3)
                        cv2.rectangle(frame, (Cx - 5, Cy - 5), (Cx + 5, Cy + 5), (0, 128, 255), -1)
            elif nbrofsquares < 64 and nbrofsquares > 10:
                cv2.putText(frame, "Chess board partially detected !", (5, 5), cv2.FONT_HERSHEY_SIMPLEX, 0.8,
                            (255, 255, 255), 1)
            else:
                cv2.putText(frame, "I Can't see the board !", (5, 5), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 255),
                            1)
            print('I detected %d piece !' % nbrofcircles)

            cv2.imshow("frame", frame)  # Showing the frame !

            # If 'q' key was pressed, the loop will break, consequently, the program will exit !
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        except (TypeError, ZeroDivisionError, AttributeError):
            pass
    capture.release()
    cv2.destroyAllWindows()
if __name__ == '__main__':
    main()