
queue = []

def makeRequest(task_id):
    queue.append(task_id)

def checkRequest():
    return len(queue) > 0

def getRequest():
    return queue.pop(0)