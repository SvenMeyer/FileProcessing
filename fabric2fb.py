import os
import sys
from dotmap import DotMap


def process_file(datafile):

    print("process_file : >", datafile, "<")
     
    with open(datafile) as f:
        lines = f.readlines()
        li = iter(lines)
    
        # line 1 - header
        if next(li)[2:36] != 'Crashlytics - plaintext stacktrace':
            return("ERROR: This is not a 'Crashlytics plaintext stacktrace from fabric.io")
    
        # create an empty dictionary
        d = {}
        
        #   line 2 .. 14 - main info > map into dictionary
        l = next(li)
        while l != '\n':
            name, value = l[2:].split(':', 1)
            d[name.strip()] = value.strip()
            l = next(li)
    
        '''
        d = 
        {
            'URL': 'https://fabric.io/daimler-south-east-asia-pte-ltd/ios/apps/com.daimler.salestouch.internal.ipad/issues/96ff39125311fe7a76ba88811218bdb1?time=last-seven-days/sessions/092e306ec3584eee87c9751b8d1bff6c_DNE_0_v2',
            'Organization': 'Daimler South East Asia Pte. Ltd.',
            'Platform': 'ios',
            'Application': 'SalesTouch',
            'Version': '0.9576 (1)',
            'Bundle Identifier': 'com.daimler.SalesTouch.internal.iPad',
            'Issue ID': '96ff39125311fe7a76ba88811218bdb1',
            'Session ID': '092e306ec3584eee87c9751b8d1bff6c_DNE_0_v2',
            'Date': '2019-10-19T03:57:00Z',
            'OS Version': '12.2.0 (16E227)',
            'Device': 'iPad Pro (10.5 inch)',
            'RAM Free': '35.3%',
            'Disk Free': '94.8%'
        }
        '''
        
        # https://stackoverflow.com/questions/2352181/how-to-use-a-dot-to-access-members-of-dictionary
        # https://github.com/drgrib/dotmap
        m = DotMap()
    
        # map header data from fabric fields into firebase crashlytics data fields
        m.platform = d['Platform']
        m.bundle_identifier = d['Bundle Identifier']
        m.event_id = d['Session ID']
        m.is_fatal = True
        m.issue_id = d['Issue ID']
        m.event_timestamp = d['Date']
        # device
        m.device.manufacturer = 'Apple'
        m.device.model = d['Device']
        m.device.architecture = ''
        # memory =
        m.memory.used = ''
        m.memory.free = d['RAM Free'] # value in % not absolute Bytes !
        # storage =
        m.storage.used = ''
        m.storage.free = d['Disk Free'] # value in % not absolute GiB !
        # operating_system
        m.operating_system.display_version = d['OS Version']
        m.operating_system.name = d['Platform']
        m.operating_system.modification_state = ''
        # application
        m.application.build_version = d['Version']
        m.application.display_version = d['Version']
    
        m.threads = []
#       m.exceptions.threads = []   # not sure if we want to populate this as well
        processed_threads = []
    
        blamed = False
    
        try:
    
            while True: # repeat until we reach end-of-file > exit with exeption
                
                # search for first/next thread
                while l[:1] != '#':
                    l = next(li)
        
                # new thread
                number, rest = l[1:].split('.', 1)
                crashed = rest.strip().startswith('Crashed')
                if crashed:
                    rest = rest.split(':', 1)[1]
                thread_number = int(number)
                thread_name = rest.strip()
        
    #           print(thread_number, crashed, thread_name)
                
                thread = DotMap({
                    "number"  : thread_number,
                    "crashed": crashed,
                    "thread_name"    : thread_name,
                    "blamed" : crashed and not blamed,
                    "frames" : []
                })
        
                if not (thread_number in processed_threads):
        #           m.exceptions.threads.append(thread)
                    m.threads.append(thread)

                processed_threads.append(thread_number)
        
                '''
                process frame
        
                blame_frame 	RECORD 	The frame identified as the root cause of the crash or error
                blame_frame.line 	INT64 	The line number of the file of the frame
                blame_frame.file 	STRING 	The name of the frame file
                blame_frame.symbol 	STRING 	The hydrated symbol, or raw symbol if it's unhydrateable
                blame_frame.offset 	INT64 	The byte offset into the binary image that contains the code, unset for Java exceptions
                blame_frame.address 	INT64 	The address in the binary image which contains the code, unset for Java frames
                blame_frame.library 	STRING 	The display name of the library that includes the frame
                blame_frame.owner 	STRING 	DEVELOPER, VENDOR, RUNTIME, PLATFORM, or SYSTEM
                blame_frame.blamed 	BOOLEAN 	Whether Crashlytics's analysis determined that this frame is the cause of the crash or error
                '''
        
                l = next(li)
                
                while l != '\n':
                    n = int(l[:3])
        
                    bin_image, rest = l[3:].split(' 0x', 1)
        
                    address, rest = rest.split(' ', 1)
        
                    symbol_line = rest.split('+', 1)
                    symbol = symbol_line[0].strip()
        
                    if len(symbol_line) == 2:
                        line_rest = symbol_line[1].strip().split(' ', 1)
                        line = line_rest[0].strip()
                        if len(line_rest) == 2:
                            rest = line_rest[1].strip()
                        else:
                            rest = ''
                    else:
                        line = ''
        
        #           print(n, bin_image, address, symbol, line, rest)
                        
                    frame_line = DotMap({
                        "number" : n,
                        "line"   : line,
                        "file"   : bin_image.strip(),
                        "symbol" : symbol,
                        #                "offset" : offset,
                        "address": "0x" + address,
                        #                "library" : '',
                        #                "owner" : '',
                        "blamed" : crashed and not blamed                     
                    })
                    
                    # append to last thread - thread_number / index can be > len(threads)
                    m.threads[-1].frames.append(frame_line)
                    
                    # first frame line of crashed thread
                    if (crashed and not blamed) and (n==0):
                        m.blame_frame = frame_line
        
                    # get next stack trace / frame - line
                    l = next(li)
                # END WHILE - frame-lines
                    
                # once we have blamed one theread, we wont do it any more
                blamed = crashed or blamed
            # END WHILE - threads
        # END - try
    
        except StopIteration:
            print("StopIteration - End of File reached")
   
        
        # WRITE TO FILE
        import json     
        with open(datafile + '.json', "w") as f:
            json.dump(m.toDict(), f, indent=4, sort_keys=False)
            
        return('OK')

# END - process_file
    
    
def main():
    if len(sys.argv) < 2:
        print("ERROR: no file or directory specified")
        # exit()
        a = "/home/sum/DEV/DMSIN/data/fabric/com.daimler.salestouch.internal.ipad_issue_crash_d9f02a6a1e954b19b9288921672e3be4_DNE_0_v2 - fatal ex - jailbroken.txt"
    else:
        a = sys.argv[1]
        
    if os.path.isfile(a):
        print(process_file(os.path.abspath(a)))
    else:
        print("processing directory  : ", a)
        for file in os.listdir(a):
            file_with_path = os.path.join(a , file)
            print()
            # print("file in dir =", file_with_path)
            if os.path.isfile(file_with_path):
                print(process_file(file_with_path))
  

if __name__== "__main__":
  main()
