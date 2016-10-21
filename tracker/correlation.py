from skimage.measure import compare_ssim as ssim
import numpy as np
import cv2

def mse(imageA, imageB):
	# the 'Mean Squared Error' between the two images is the
	# sum of the squared difference between the two images;
	# NOTE: the two images must have the same dimension
	err = np.sum((imageA.astype("float") - imageB.astype("float")) ** 2)
	err /= float(imageA.shape[0] * imageA.shape[1])
	
	# return the MSE, the lower the error, the more "similar"
	# the two images are
	return err

def compare_images(imageA, imageB):
	# compute the mean squared error and structural similarity
	# index for the images
	m = mse(imageA, imageB)
	print m
	s = ssim(imageA, imageB)
	print s
	return mse, s

if __name__ == '__main__':

	file = "madison15.mp4"
	cap = cv2.VideoCapture(file)  # crashes here
	
	template = None
	i = 0 
	for frame in range(0, 300):
		cap.set(cv2.CAP_PROP_POS_FRAMES, frame)  # opencv3
		print 'Current frame: '+ str(frame)         
		frameNo = int(cap.get(cv2.CAP_PROP_POS_FRAMES))  # opencv3
		ret, f_base = cap.read()
		f_gray = cv2.cvtColor(f_base, cv2.COLOR_BGR2GRAY)
		if template == None:
			template = f_gray
			continue
		mse, s = compare_images(f_gray,template)
		if s<0.5:
			print 'recalculate'
			cv2.imshow('new template', f_gray)
			if cv2.waitKey(1) & 0xFF == ord('q'):
				break
			template = f_gray
		else:
			i+=1 
			print 'un-changed'
	cap.release()


print i


	# imageA = cv2.imread('imageA.jpg', 0)
	# imageB = cv2.imread('imageB.jpg',0) ## Reads in comparison images
	# compare_images(imageA, imageB)