#!/usr/bin/python3
# -*- coding: UTF-8 -*-

from datetime import datetime
import sys, os, subprocess, tarfile, smtplib, re, socket
import configparser, shutil, requests
rsyncfailure = False
errormap = {}
curr_date = datetime.now().strftime('%Y-%B-%d')
curr_time = datetime.now().strftime(('%H-%M-%S'))
hostname = socket.gethostname()
pwd = sys.path[0]
path = "/var/lib/etcd_dir/"
etcdpath = "/var/lib/etcd/"
tarpath = "/var/lib/etcd_tar/"
password_file = "/etc/rsyncd.password"

def print_usage(script):
    print('Usage:', script, '--hostlist <host configuration file>' )
    sys.exit(1)

def usage(args):
    if not len(args) != 5:
        print_usage(args[0])
    else:
        #req_args = ['--hostlist','--todir']
        req_args = ['--hostlist']
        for a in req_args:
            if not a in req_args:
                print_usage()
            if not os.path.exists(args[args.index(a)+1]):
                print('Error: Path not found:', args[args.index(a)+1])
                print_usage()
    hconf=args[args.index('--hostlist')+1]
    #dir = args[args.index('--todir')+1]
    return hconf

def create_host_directories():
    #Config = configparser.ConfigParser()
    #Config.read(hconf)
    #for section in Config.sections():
    #global path, tarpath
    shutil.rmtree(path) 
    try:
        os.makedirs(path)
    except OSError:
        if not os.path.isdir(path):
            raise
    shutil.rmtree(tarpath) 
    try:
        os.makedirs(tarpath)
    except OSError:
        if not os.path.isdir(tarpath):
            raise
    etcddir = hostname.split('.')[0] + ".etcd"
    etcdcmd = ['etcdctl backup --data-dir ' + etcdpath + etcddir + ' --backup-dir ' + path]
    p1=subprocess.Popen(etcdcmd, shell=True)
    p1.wait()
    return path


def rsync_data(hconf):
    Config = configparser.ConfigParser()
    Config.read(hconf)
    for section in Config.sections():
        backupdirs = Config.get(section, 'backupdirs').split(',')
        path = create_host_directories()
        backup_compress()
        if not len(backupdirs)==0:
            for bakdirs in backupdirs:
                cmd=['/bin/rsync -avz '+ tarpath + ' ' + Config.get(section, 'username')+'@'+Config.get(section, 'ipaddress')+'::'+bakdirs + ' --password-file='+password_file]
                print(curr_time, cmd)
                p2 = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
                stdout, stderr = p2.communicate()
                if p2.returncode > 0:
                    global rsyncfailure, errormap
                    rsyncfailure = True
                    if not Config.get(section, 'ipaddress') in errormap:
                        errormap[Config.get(section, 'ipaddress')] = stderr.decode(encoding='UTF-8')
                    else:
                        errormap[Config.get(section, 'ipaddress')] = str(errormap[Config.get(section, 'ipaddress')]) + stderr.decode(encoding='UTF-8')
                    continue

def backup_compress():
    tar = tarfile.open(tarpath + "/" + curr_date + "_" + curr_time + "_" + hostname + '.tar.gz', 'w:gz')
    for root,dir,files in os.walk(path):
        root_ = os.path.relpath(root,start=path)
        for file in files:
            fullpath=os.path.join(root,file)
            tar.add(path,arcname=os.path.join(root_,file))
    tar.close()
    #shutil.rmtree(path+'/member')

def sendmail(data):
    pattern = r"((([01]?[0-9]?[0-9]|2[0-4][0-9]|25[0-5])[ (\[]?(\.|dot)[ )\]]?){3}([01]?[0-9]?[0-9]|2[0-4][0-9]|25[0-5]))"
    fromaddr="vasavakrishna@greenbuds.co.in"
    toaddr=["vasavakrishna@greenbuds.co.in"]
    header = 'From: %s\n' % fromaddr
    header += 'To: %s\n' % ','.join(toaddr)
    subject = 'Backup  Intimation'
  # header += 'Cc: %s\n' % ','.join(cc_addr_list)
    header += 'Subject: %s\n\n' % subject
    #cmd = ['hostname', '-I']
    #p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    #stout, stderr = p.communicate()
    #iplist = ipaddress
    #ips = [match[0] for match in re.findall(pattern, iplist)]
    errmsg = data
    text="Backup Status"+'\n'+'Error Message : '+data
    message = header + text
    server = smtplib.SMTP('smtp.yourdomain.com:25')
    server.starttls()
    server.login("username@domain.com", "password")
    server.sendmail(fromaddr, toaddr, message)


def status_mail():
    if rsyncfailure:
        sendmail(str(errormap))
    else:
        sendmail('Rsynsing done successfully')

def isleader():
    r = requests.get(url = 'http://127.0.0.1:2379/v2/members')
    l = requests.get(url = 'http://127.0.0.1:2379/v2/stats/leader')
    r = str(r.json())
    l = str(l.json())
    isleader = 'followers'
    notleader = 'not current leader'
    filename = pwd+'/../conf/members'
    lmatch = l.find(notleader) + 1
    if lmatch:
        print(curr_time + " system exit!(not current leader)")
        sys.exit()
        #lines = filename.readlines(100)
    with open(filename,"r") as f:
        content=list(map(lambda x:x.strip() , f.readlines()))
    #contents = list(content)
    for index in range(len(content)):
        match = r.find(content[index]) + 1
        #print(str(match) + ',' + contents[index])
        if match == 0:
            print(curr_time + " system exit!(cluster exception)")
            sys.exit()
        else:
            continue

def main():
    isleader()
    hconf = usage(sys.argv)
    #create_host_directories(hconf, dir)
    rsync_data(hconf)
    #status_mail()

if __name__ == '__main__':
    main()

