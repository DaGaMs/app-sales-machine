from urllib2 import *
from BeautifulSoup import *
import sys

COOKIE = 'uid=thaye0mr; dev_appserver_login="test@example.com:True:185804764220139124118"'

def main(queue):  
  failed_tasks = set()
  soup = BeautifulSoup(''.join(urlopen(Request(url='http://localhost:8080/_ah/admin/tasks?queue='+queue,
    headers={'Cookie':	COOKIE }))
      .readlines()))
  while True:               
    task = None
    for t in soup.findAll(id=re.compile("^runform")):
      task = parse(t)
      if task['name'] in failed_tasks:
        task = None        
      else:
        break
    if task is None:
      if len(failed_tasks) != 0:
        print 'There are',len(failed_tasks),'failed tasks in',queue
      else:
        print 'There are no tasks in',queue
      return
    
    print 'Executing task:',task['name']
    try:
      response = ''.join(urlopen(Request(
          url='http://localhost:8080'+task['action'],
          headers=task['headers'],
          data = task['payload']
        )).readlines())
      
      soup = BeautifulSoup(delete_task(task,queue))
    except Exception,e:
      print e
      failed_tasks.add(task['name'])
      
    
    
    

def delete_task(task,queue):
  import urllib
  #print 'deleting'
  
  return ''.join(urlopen(Request(
      url='http://localhost:8080/_ah/admin/tasks',
      headers={'Cookie':	COOKIE },
      data = urllib.urlencode([('queue',queue),
                             ('task',task['headers']['X-AppEngine-TaskName']),
                             ('action:deletetask','true')])
    )).readlines())


def parse(form):
  res = {}
  HEADER_KEY = 'header:'
  res['action'] = form['action']
  res['method'] = form['method']
  res['headers'] = {'Cookie':	COOKIE}
  for e in form:
    if isinstance(e,NavigableString) or e.name != 'input':      
      continue
    attrs = dict(e.attrs)
    if attrs.get('type','') != 'hidden':
      continue
    
    key = attrs['name']
    value = attrs['value']
    if key.startswith(HEADER_KEY):
      res['headers'][key[len(HEADER_KEY):]] = value
    
    elif key == 'payload':
      res['payload'] = value
  res['name'] = res['headers']['X-AppEngine-TaskName']
  return res  
  
  
  



if __name__ == '__main__':
  main(sys.argv[1])
