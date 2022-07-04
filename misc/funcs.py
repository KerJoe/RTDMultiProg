import time

def poll(func, exception_message=None, timeout=2, step=0.1):
    """ Execute function until it returns True or times out """
    t_start = time.time()
    while not func():
        time.sleep(step)
        if time.time() - t_start >= timeout:
            raise TimeoutError(exception_message)

def div_to_chunks(L, n):
    """ Yield successive n-sized chunks from L """
    for i in range(0, len(L), n):
        yield L[i:i+n]

def progress_bar(value):
    """ Print progress line. 'value' range is from 0 to 1 """
    print(f"Progress: |{('#' * int(value * 25)).ljust(25)}| {value:6.1%}",
          end="\r") # Go back to the beggining of line
    if (value == 1):
        print() # Auto new line on 100%