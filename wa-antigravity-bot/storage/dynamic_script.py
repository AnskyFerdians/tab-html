import cv2
cap = cv2.VideoCapture(0)
ret, frame = cap.read()
if ret:
    cv2.imwrite('storage/foto_kamera.png', frame)
    print("SUKSES")
else:
    print("GAGAL")
cap.release()