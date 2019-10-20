import os
import sys

dir_path = os.path.dirname(os.path.realpath(__file__))
print("dir_path = ", dir_path)
cwd = os.getcwd()
print("cwd = ", cwd)

print("Path at terminal when executing this file")
print(os.getcwd() + "\n")

print("This file path, relative to os.getcwd()")
print(__file__ + "\n")

print("This file full path (following symlinks)")
full_path = os.path.realpath(__file__)
print(full_path + "\n")

print("This file directory and name")
path, filename = os.path.split(full_path)
print(path + ' --> ' + filename + "\n")

print("This file directory only")
print(os.path.dirname(full_path))


def process_file(f):
    print("processing : ", f)
    
    
def main():
    if len(sys.argv) < 2:
        print("ERROR: no file or directory specified")
        exit()
    a = sys.argv[1]
    if os.path.isfile(a):
        process_file(os.path.join(os.getcwd(), a))
    else:
        print("processing directory  : ", a)
        for file in os.listdir(a):
            file_with_path = os.path.join(a , file)
            print("file in dir =", file_with_path)
            if os.path.isfile(file_with_path):
                process_file(file_with_path)
  
if __name__== "__main__":
  main()

    
