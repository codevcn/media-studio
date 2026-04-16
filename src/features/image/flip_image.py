from PIL import Image

img = Image.open("input.jpg")
flipped = img.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
flipped.save("output.jpg")
