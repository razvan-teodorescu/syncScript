import filecmp, os, shutil, datetime, argparse
from time import sleep


# Check if it's directory
def dir_path(path):
    if os.path.isdir(path):
        return path
    else:
        raise argparse.ArgumentTypeError(f"readable_dir:{path} is not a valid path")

# Set flags
def flags():
    msg='''Periodically synchronizes a user defined directory to a 
    defined destination directory. Outputs logs to console and creates a 
    file at a user defined location.'''
    parser=argparse.ArgumentParser(description=msg)
    parser.add_argument("-s", "--source", help="Set a Source Directory for synchronization", type=dir_path, required=True)
    parser.add_argument("-d", "--destination", help="Set a Destination Directory for synchronization", type=dir_path, required=True)
    parser.add_argument("-l", "--log", help="Set the path for the log.txt file",type=dir_path, required=True)
    parser.add_argument("-t", "--timeout", help="Set a synchronization frequency, in minutes", type=int, required=True)
    return parser.parse_args()

# Use flags in script
sourcePath=flags().source
destinationPath=flags().destination
logs=os.path.join(flags().log,"logs.txt")
timeout=flags().timeout

# Get time
def timestmp():
    now = datetime.datetime.now()
    return now.strftime('%d-%m-%Y %H:%M:%S')

# Write Logs to file
def writeLogs(path, time, fileSource, fileDestination, action ):
    file=open(path, "a")
    temp=time+"    Source: "+fileSource+"        Action: "+action+"        Destination: "+fileDestination+"\n"
    file.write(temp)
    file.close()

# Print to console with color 
def printConsole(time, source, destination, action):
    if os.name != 'nt':
        if "Removing" in action:
            print(time+"    \033[1mSource:\033[0m "+source+"    \033[1mAction:\033[0m \033[1;31m"+action+"\033[0m"+"    \033[1mDestination:\033[0m "+destination)
        elif "Modified" in action:
            print(time+"    \033[1mSource:\033[0m "+source+"    \033[1mAction:\033[0m \033[1;33m"+action+"\033[0m"+"    \033[1mDestination:\033[0m "+destination)
        elif "Created" in action:
            print(time+"    \033[1mSource:\033[0m "+source+"    \033[1mAction:\033[0m \033[1;32m"+action+"\033[0m"+"    \033[1mDestination:\033[0m "+destination)
    else:
        if "Removing" in action:
            print(time+"    Source: "+source+"    Action: "+action+"    Destination: "+destination)
        elif "Modified" in action:
            print(time+"    Source: "+source+"    Action: "+action+"    Destination: "+destination)
        elif "Created" in action:
            print(time+"    Source: "+source+"    Action: "+action+"    Destination:\ "+destination)


# Verbose copy2 for copytree
def copy2_verbose(src, dst):
    shutil.copy2(src,dst)
    writeLogs(logs, timestmp(), src,dst, "Created In")
    printConsole(timestmp(), src, dst, "Created In")
    

def diff_port(src,dst):
    compare=filecmp.dircmp(src,dst)

    common=list(set(os.listdir(src)) & set(os.listdir(dst)))
    common_files=[f for f in common if os.path.isfile(os.path.join(src, f))]

    # Search differences in Source directory
    inSource=list(set(os.listdir(src)) - set(os.listdir(dst)))

    # Search differences in Destination directory
    inDestination=list(set(os.listdir(dst)) - set(os.listdir(src)))

    

    # Find mismatched files
    match, mismatched, errors = filecmp.cmpfiles(src,dst,common_files,shallow=False)

    # No files and dirs in Destination
    if len(compare.right_list)==0 and len(compare.left_list)>0:
        # If destination is empty Copy from source to destination
        for noDestination in compare.left_list:
            srcPath=os.path.join(src,os.path.basename(noDestination))
            dstPath=os.path.join(dst,os.path.basename(noDestination))
            try:
                shutil.copy2(srcPath,dstPath)
            except:
                shutil.copytree(srcPath, dstPath, symlinks=False, ignore=None, copy_function=shutil.copy2, ignore_dangling_symlinks=False, dirs_exist_ok=False)
            writeLogs(logs, timestmp(), srcPath,dstPath, "Created In")
            printConsole(timestmp(), srcPath, dstPath, "Created In")
    elif len(inSource)>0:
        # If destination not empty Copy from source to destination
        for destNotEmpty in inSource:
            sPath=os.path.join(src,destNotEmpty)
            dPath=os.path.join(dst,destNotEmpty)
            try:
                shutil.copy2(sPath,dPath)
            except:
                shutil.copytree(sPath, dPath, symlinks=False, ignore=None, copy_function=copy2_verbose, ignore_dangling_symlinks=False, dirs_exist_ok=True)
            writeLogs(logs, timestmp(), sPath,dPath, "Created In")
            printConsole(timestmp(), sPath, dPath, "Created In")
        

    # No files and dirs in Source
    if len(compare.left_list)==0 and len(compare.right_list)>0:
        # if Source is empty Remove from destination
        for noSource in compare.right_list:
            destRemove=os.path.join(dst,noSource)
            try:
                os.remove(destRemove)
            except:
                shutil.rmtree(destRemove)
            writeLogs(logs, timestmp(), "Item doesn't exit",destRemove, "Removing From")
            printConsole(timestmp(), "Item doesn't exit", destRemove, "Removing From")
    elif len(inDestination)>0:
        # If list destination has extra remove extra
        for extraDestination in inDestination:
            dstRemove=os.path.join(dst,extraDestination)
            try:
                os.remove(dstRemove)
            except:
                shutil.rmtree(dstRemove)
            writeLogs(logs, timestmp(), "Item doesn't exit",dstRemove, "Removing From")
            printConsole(timestmp(), "Item doesn't exit", dstRemove, "Removing From")


    # Common files that differ
    if len(mismatched) != 0:
        # Copy mismatched from Source to Destination
        for mismatch in mismatched:
            srcFile=os.path.join(src,mismatch)
            dstFile=os.path.join(dst,mismatch)
            shutil.copy2(srcFile, dstFile)
            writeLogs(logs, timestmp(), srcFile,dstFile, "Modified In")
            printConsole(timestmp(), srcFile, dstFile, "Modified In")

    for common_dir in compare.common_dirs:
        newSrc = os.path.join(src, common_dir)
        newDst = os.path.join(dst, common_dir)
        if not diff_port(newSrc, newDst):
            return False
    return True # checks all directories from the same level 

while True:
    diff_port(sourcePath, destinationPath)
    sleep(timeout)
